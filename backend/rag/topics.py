"""Построение дерева учебных тем по указателям Vidal."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from pathlib import Path
import posixpath
import re
from typing import Any, Optional

from bs4 import BeautifulSoup, Tag

from .common import load_jsonl_records, normalize_scalar_text


@dataclass
class TopicCatalog:
    """Описывает верхнеуровневый указатель, из которого выбирается тема."""

    id: str
    title: str
    description: str


@dataclass
class TopicNode:
    """Один узел дерева учебных тем."""

    id: str
    catalog: str
    title: str
    parent_id: str
    level: int
    path: list[str]
    source_page_path: str = ""
    code: str = ""
    doc_ids: list[str] = field(default_factory=list)
    doc_count: int = 0
    has_children: bool = False


@dataclass
class TopicTree:
    """Готовое дерево тем и быстрые индексы для API."""

    catalogs: list[TopicCatalog]
    nodes: dict[str, TopicNode]
    children_by_parent: dict[str, list[str]]


CATALOGS = [
    TopicCatalog(
        id="kfu",
        title="Клинико-фармакологический указатель",
        description="Темы по клинико-фармакологическим группам Vidal.",
    ),
    TopicCatalog(
        id="noz",
        title="Нозологический указатель",
        description="Темы по заболеваниям и состояниям.",
    ),
    TopicCatalog(
        id="atc",
        title="АТХ система классификации",
        description="Темы по ATC-классификации лекарственных средств.",
    ),
    TopicCatalog(
        id="active_substance",
        title="Активные вещества",
        description="Темы по действующим веществам препаратов.",
    ),
]


def normalize_href(current_source_path: str, href: str) -> str:
    """Нормализует относительную ссылку Vidal до source_page_path внутри data/."""

    href_without_anchor = href.split("#", 1)[0].strip()
    if not href_without_anchor:
        return ""

    current_directory = posixpath.dirname(current_source_path)
    normalized_path = posixpath.normpath(posixpath.join(current_directory, href_without_anchor))
    return normalized_path.lstrip("./")


def clean_topic_text(value: str) -> str:
    """Очищает текст узла от лишних пробелов и HTML-артефактов."""

    text = value.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def get_cell_text(cell: Optional[Tag]) -> str:
    """Возвращает очищенный текст ячейки таблицы."""

    if cell is None:
        return ""
    return clean_topic_text(cell.get_text(" ", strip=False))


def count_leading_nbsp(cell: Optional[Tag]) -> int:
    """Считает число ведущих неразрывных пробелов в ячейке."""

    if cell is None:
        return 0
    raw_text = cell.get_text("", strip=False)
    return len(raw_text) - len(raw_text.lstrip("\xa0 "))


def iter_info_rows(record: dict[str, Any]) -> list[Tag]:
    """Возвращает строки основной таблицы normalized Vidal-страницы."""

    soup = BeautifulSoup(normalize_scalar_text(record.get("content_html")), "html.parser")
    info_table = soup.find("table", id="info")
    if not isinstance(info_table, Tag):
        return []
    return [row for row in info_table.find_all("tr", recursive=False) if isinstance(row, Tag)]


def load_pages_by_path(normalized_pages_path: Path) -> dict[str, dict[str, Any]]:
    """Загружает normalized_pages.jsonl в индекс по source_path."""

    pages_by_path: dict[str, dict[str, Any]] = {}
    for page_record in load_jsonl_records(normalized_pages_path):
        source_path = normalize_scalar_text(page_record.get("source_path"))
        if source_path:
            pages_by_path[source_path] = page_record
    return pages_by_path


def load_relation_doc_ids(entity_relations_path: Path) -> dict[str, list[str]]:
    """Строит индекс source_page_path -> doc_id для всех указателей."""

    doc_ids_by_source_path: dict[str, list[str]] = {}
    for relation_record in load_jsonl_records(entity_relations_path):
        source_page_path = normalize_scalar_text(relation_record.get("source_page_path"))
        target_doc_id = normalize_scalar_text(relation_record.get("target_doc_id"))
        if not source_page_path or not target_doc_id:
            continue
        doc_ids = doc_ids_by_source_path.setdefault(source_page_path, [])
        if target_doc_id not in doc_ids:
            doc_ids.append(target_doc_id)
    return doc_ids_by_source_path


def get_row_link_path(row: Tag, current_source_path: str) -> str:
    """Возвращает нормализованную ссылку из строки таблицы, если она есть."""

    link = row.find("a", href=True)
    if not isinstance(link, Tag):
        return ""
    return normalize_href(current_source_path, normalize_scalar_text(link.get("href")))


def add_node(
    nodes: dict[str, TopicNode],
    children_by_parent: dict[str, list[str]],
    catalog: str,
    title: str,
    parent_id: str,
    level: int,
    path: list[str],
    source_page_path: str = "",
    code: str = "",
) -> str:
    """Добавляет узел в дерево или обновляет существующий."""

    safe_title = clean_topic_text(title)
    if not safe_title:
        return ""

    if source_page_path:
        node_id = f"{catalog}:{source_page_path}"
    else:
        node_hash = hashlib.sha1(f"{catalog}|{parent_id}|{level}|{safe_title}".encode("utf-8")).hexdigest()[:12]
        node_id = f"{catalog}:synthetic:{node_hash}"

    if node_id not in nodes:
        nodes[node_id] = TopicNode(
            id=node_id,
            catalog=catalog,
            title=safe_title,
            parent_id=parent_id,
            level=level,
            path=path + [safe_title],
            source_page_path=source_page_path,
            code=code,
        )
        children = children_by_parent.setdefault(parent_id, [])
        if node_id not in children:
            children.append(node_id)
    else:
        node = nodes[node_id]
        if not node.parent_id and parent_id:
            node.parent_id = parent_id
        if not node.path:
            node.path = path + [safe_title]
        if code and not node.code:
            node.code = code

    return node_id


def get_nearest_parent_id(stack_by_level: dict[int, str], level: int, fallback_parent_id: str) -> str:
    """Возвращает ближайшего доступного родителя для уровня вложенности."""

    for parent_level in range(level - 1, -1, -1):
        parent_id = stack_by_level.get(parent_level)
        if parent_id:
            return parent_id
    return fallback_parent_id


def parse_kfu_tree(
    pages_by_path: dict[str, dict[str, Any]],
    nodes: dict[str, TopicNode],
    children_by_parent: dict[str, list[str]],
) -> None:
    """Строит дерево клинико-фармакологического указателя."""

    index_record = pages_by_path.get("kfu/kf_index.htm")
    if not index_record:
        return

    category_paths: list[str] = []
    for row in iter_info_rows(index_record):
        cells = row.find_all("td", recursive=False)
        if not cells:
            continue
        source_path = get_row_link_path(row, "kfu/kf_index.htm")
        title = get_cell_text(cells[-1])
        if source_path and title:
            category_id = add_node(
                nodes=nodes,
                children_by_parent=children_by_parent,
                catalog="kfu",
                title=title,
                parent_id="",
                level=0,
                path=[],
                source_page_path=source_path,
            )
            if category_id:
                category_paths.append(source_path)

    for category_source_path in category_paths:
        category_record = pages_by_path.get(category_source_path)
        category_id = f"kfu:{category_source_path}"
        if not category_record or category_id not in nodes:
            continue

        category_node = nodes[category_id]
        stack_by_level: dict[int, str] = {0: category_id}
        skipped_category_title = False

        for row_index, row in enumerate(iter_info_rows(category_record), start=1):
            cells = row.find_all("td", recursive=False)
            if not cells:
                continue

            title_cell = cells[-1]
            if "h1" in title_cell.get("class", []):
                continue

            title = get_cell_text(title_cell)
            if not title:
                continue

            if not skipped_category_title and title.casefold() == category_node.title.casefold():
                skipped_category_title = True
                continue

            source_path = get_row_link_path(row, category_source_path)
            indent_level = max(count_leading_nbsp(title_cell) // 4, 1)
            parent_id = get_nearest_parent_id(stack_by_level, indent_level, category_id)
            parent_path = nodes[parent_id].path if parent_id in nodes else category_node.path

            node_id = add_node(
                nodes=nodes,
                children_by_parent=children_by_parent,
                catalog="kfu",
                title=title,
                parent_id=parent_id,
                level=indent_level,
                path=parent_path,
                source_page_path=source_path,
                code="",
            )
            if not node_id:
                continue

            stack_by_level[indent_level] = node_id
            for level in list(stack_by_level):
                if level > indent_level:
                    del stack_by_level[level]


def atc_level_from_code(code: str) -> int:
    """Определяет уровень ATC-узла по длине кода."""

    code_length = len(code)
    if code_length <= 1:
        return 0
    if code_length <= 3:
        return 1
    if code_length <= 4:
        return 2
    if code_length <= 5:
        return 3
    return 4


def parse_atc_tree(
    pages_by_path: dict[str, dict[str, Any]],
    nodes: dict[str, TopicNode],
    children_by_parent: dict[str, list[str]],
) -> None:
    """Строит дерево ATC-классификации."""

    index_record = pages_by_path.get("atc/at_index.htm")
    if not index_record:
        return

    root_paths: list[str] = []
    for row in iter_info_rows(index_record):
        cells = row.find_all("td", recursive=False)
        if len(cells) < 2:
            continue
        code = get_cell_text(cells[0])
        title = get_cell_text(cells[1])
        source_path = get_row_link_path(row, "atc/at_index.htm")
        if source_path and code and title:
            root_id = add_node(
                nodes=nodes,
                children_by_parent=children_by_parent,
                catalog="atc",
                title=title,
                parent_id="",
                level=0,
                path=[],
                source_page_path=source_path,
                code=code,
            )
            if root_id:
                root_paths.append(source_path)

    for root_source_path in root_paths:
        root_record = pages_by_path.get(root_source_path)
        root_id = f"atc:{root_source_path}"
        if not root_record or root_id not in nodes:
            continue

        stack_by_level: dict[int, str] = {0: root_id}
        root_code = nodes[root_id].code
        for row in iter_info_rows(root_record):
            cells = row.find_all("td", recursive=False)
            if len(cells) < 2:
                continue

            code = get_cell_text(cells[0])
            title = get_cell_text(cells[1])
            if not code or not title:
                continue
            if code == root_code:
                continue

            level = atc_level_from_code(code)
            source_path = get_row_link_path(row, root_source_path)
            parent_id = stack_by_level.get(level - 1, root_id)
            parent_path = nodes[parent_id].path if parent_id in nodes else nodes[root_id].path
            node_id = add_node(
                nodes=nodes,
                children_by_parent=children_by_parent,
                catalog="atc",
                title=title,
                parent_id=parent_id,
                level=level,
                path=parent_path,
                source_page_path=source_path,
                code=code,
            )
            if node_id:
                stack_by_level[level] = node_id


def parse_noz_tree(
    pages_by_path: dict[str, dict[str, Any]],
    nodes: dict[str, TopicNode],
    children_by_parent: dict[str, list[str]],
) -> None:
    """Строит дерево нозологического указателя."""

    index_record = pages_by_path.get("noz/no_index.htm")
    if not index_record:
        return

    class_paths: list[str] = []
    for row in iter_info_rows(index_record):
        cells = row.find_all("td", recursive=False)
        if len(cells) < 2:
            continue

        code = get_cell_text(cells[0])
        title = get_cell_text(cells[1])
        source_path = get_row_link_path(row, "noz/no_index.htm")
        if source_path and title:
            class_id = add_node(
                nodes=nodes,
                children_by_parent=children_by_parent,
                catalog="noz",
                title=title,
                parent_id="",
                level=0,
                path=[],
                source_page_path=source_path,
                code=code,
            )
            if class_id:
                class_paths.append(source_path)

    for class_source_path in class_paths:
        class_record = pages_by_path.get(class_source_path)
        class_id = f"noz:{class_source_path}"
        if not class_record or class_id not in nodes:
            continue

        stack_by_level: dict[int, str] = {0: class_id}
        for row in iter_info_rows(class_record):
            cells = row.find_all("td", recursive=False)
            if not cells:
                continue

            title_cell = cells[-1]
            if "h1" in title_cell.get("class", []):
                continue

            code = get_cell_text(cells[0]) if len(cells) > 1 else ""
            title = get_cell_text(title_cell)
            if not title:
                continue
            if title.casefold() == nodes[class_id].title.casefold():
                continue

            source_path = get_row_link_path(row, class_source_path)
            indent_level = max(count_leading_nbsp(title_cell) // 4, 1)
            parent_id = get_nearest_parent_id(stack_by_level, indent_level, class_id)
            parent_path = nodes[parent_id].path if parent_id in nodes else nodes[class_id].path
            node_id = add_node(
                nodes=nodes,
                children_by_parent=children_by_parent,
                catalog="noz",
                title=title,
                parent_id=parent_id,
                level=indent_level,
                path=parent_path,
                source_page_path=source_path,
                code=code,
            )
            if not node_id:
                continue
            stack_by_level[indent_level] = node_id
            for level in list(stack_by_level):
                if level > indent_level:
                    del stack_by_level[level]


def parse_active_substance_tree(
    pages_by_path: dict[str, dict[str, Any]],
    nodes: dict[str, TopicNode],
    children_by_parent: dict[str, list[str]],
) -> None:
    """Строит дерево активных веществ: буква -> вещество."""

    index_record = pages_by_path.get("find/fi_index.htm")
    if not index_record:
        return

    letter_paths: list[str] = []
    for row in iter_info_rows(index_record):
        cells = row.find_all("td", recursive=False)
        if len(cells) < 2:
            continue

        letter = clean_topic_text(get_cell_text(cells[0]).replace("[", "").replace("]", ""))
        title = letter or get_cell_text(cells[1])
        source_path = get_row_link_path(row, "find/fi_index.htm")
        if source_path and title:
            letter_id = add_node(
                nodes=nodes,
                children_by_parent=children_by_parent,
                catalog="active_substance",
                title=title,
                parent_id="",
                level=0,
                path=[],
                source_page_path=source_path,
                code=letter,
            )
            if letter_id:
                letter_paths.append(source_path)

    for letter_source_path in letter_paths:
        letter_record = pages_by_path.get(letter_source_path)
        letter_id = f"active_substance:{letter_source_path}"
        if not letter_record or letter_id not in nodes:
            continue

        for row in iter_info_rows(letter_record):
            cells = row.find_all("td", recursive=False)
            if len(cells) < 2:
                continue

            title_cell = cells[0]
            title_node = title_cell.find("b")
            title = get_cell_text(title_node if isinstance(title_node, Tag) else title_cell)
            source_path = get_row_link_path(row, letter_source_path)
            if not title or not source_path:
                continue

            add_node(
                nodes=nodes,
                children_by_parent=children_by_parent,
                catalog="active_substance",
                title=title,
                parent_id=letter_id,
                level=1,
                path=nodes[letter_id].path,
                source_page_path=source_path,
                code=posixpath.splitext(posixpath.basename(source_path))[0],
            )


def attach_doc_counts(
    nodes: dict[str, TopicNode],
    children_by_parent: dict[str, list[str]],
    doc_ids_by_source_path: dict[str, list[str]],
) -> None:
    """Заполняет direct и aggregate doc_count для всех узлов дерева."""

    for node in nodes.values():
        node.doc_ids = list(doc_ids_by_source_path.get(node.source_page_path, []))
        node.has_children = bool(children_by_parent.get(node.id))

    def collect_doc_ids(node_id: str, visited: Optional[set[str]] = None) -> list[str]:
        visited = visited or set()
        if node_id in visited:
            return []
        visited.add(node_id)

        node = nodes[node_id]
        aggregate_doc_ids = list(node.doc_ids)
        for child_id in children_by_parent.get(node_id, []):
            for child_doc_id in collect_doc_ids(child_id, visited):
                if child_doc_id not in aggregate_doc_ids:
                    aggregate_doc_ids.append(child_doc_id)

        node.doc_ids = aggregate_doc_ids
        node.doc_count = len(aggregate_doc_ids)
        return aggregate_doc_ids

    for root_child_id in children_by_parent.get("", []):
        collect_doc_ids(root_child_id)


def build_topic_tree(normalized_pages_path: Path, entity_relations_path: Path) -> TopicTree:
    """Строит дерево тем по четырем указателям Vidal."""

    pages_by_path = load_pages_by_path(normalized_pages_path)
    doc_ids_by_source_path = load_relation_doc_ids(entity_relations_path)
    nodes: dict[str, TopicNode] = {}
    children_by_parent: dict[str, list[str]] = {"": []}

    parse_kfu_tree(pages_by_path, nodes, children_by_parent)
    parse_noz_tree(pages_by_path, nodes, children_by_parent)
    parse_atc_tree(pages_by_path, nodes, children_by_parent)
    parse_active_substance_tree(pages_by_path, nodes, children_by_parent)
    attach_doc_counts(nodes, children_by_parent, doc_ids_by_source_path)

    return TopicTree(
        catalogs=CATALOGS,
        nodes=nodes,
        children_by_parent=children_by_parent,
    )
