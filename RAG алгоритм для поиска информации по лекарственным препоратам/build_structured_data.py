"""Build structured documents and relations from normalized Vidal pages.

The script solves the second preparation stage for the future RAG pipeline:
1. Reads normalized pages produced by HTMLparser.py.
2. Extracts structured fields from drug documents.
3. Extracts entity-to-document relations from handbook index pages.
4. Saves the results into separate JSONL files.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Iterator, Optional

from bs4 import BeautifulSoup, NavigableString, Tag


# DEFAULT_INPUT_FILE хранит путь к JSONL-файлу с уже нормализованными HTML-страницами.
DEFAULT_INPUT_FILE = Path(__file__).resolve().parent / "normalized_pages.jsonl"

# DEFAULT_DOCUMENTS_FILE хранит путь к выходному файлу со структурированными карточками препаратов.
DEFAULT_DOCUMENTS_FILE = Path(__file__).resolve().parent / "structured_documents.jsonl"

# DEFAULT_RELATIONS_FILE хранит путь к выходному файлу со связями между сущностями и карточками препаратов.
DEFAULT_RELATIONS_FILE = Path(__file__).resolve().parent / "entity_relations.jsonl"

# WHITESPACE_PATTERN схлопывает повторяющиеся пробелы и переводы строк в один пробел.
WHITESPACE_PATTERN = re.compile(r"\s+")

# DOC_LINK_PATTERN извлекает идентификатор карточки препарата из относительной ссылки на docs/doc_*.htm.
DOC_LINK_PATTERN = re.compile(r"\.\./docs/(?P<doc_id>doc_[^./]+)\.htm$")

# CODE_IN_PARENTHESES_PATTERN извлекает код из строки вида "(R01AD12)".
CODE_IN_PARENTHESES_PATTERN = re.compile(r"^\((?P<code>[^)]+)\)$")

# ACTIVE_SUBSTANCE_TITLE_PATTERN извлекает русское и латинское название действующего вещества из заголовка.
ACTIVE_SUBSTANCE_TITLE_PATTERN = re.compile(
    r"^Результаты поиска препаратов по активному веществу\s+"
    r"(?P<name_ru>.+?)"
    r"(?:\s+\((?P<name_lat>.+)\))?$"
)

# REGISTRATION_ENTRY_PATTERN извлекает одну регистрационную запись вида "номер от дата".
REGISTRATION_ENTRY_PATTERN = re.compile(
    r"(?P<number>[A-Za-zА-Яа-я0-9\s\-№/().]+?)\s+от\s+(?P<date>\d{2}\.\d{2}\.\d{2,4})"
)


@dataclass
class StructuredDocument:
    """Хранит структурированные данные одной карточки препарата."""

    # doc_id хранит идентификатор карточки препарата, совпадающий с именем HTML-файла без расширения.
    doc_id: str

    # title хранит заголовок исходной HTML-страницы.
    title: str

    # source_path хранит путь к исходному HTML-файлу относительно каталога data.
    source_path: str

    # drug_name_ru хранит торговое название препарата на русском языке.
    drug_name_ru: str

    # drug_name_lat хранит латинское или международное написание торгового названия.
    drug_name_lat: str

    # active_substance_raw хранит исходную строку с действующим веществом из шапки карточки.
    active_substance_raw: str

    # active_substances хранит список веществ, если в карточке указано несколько компонентов.
    active_substances: list[str]

    # dosage_form хранит лекарственную форму из шапки карточки.
    dosage_form: str

    # clinical_pharmacological_group хранит строку из поля "Клинико-фармакологическая группа".
    clinical_pharmacological_group: str

    # registration_info_raw хранит исходную строку регистрации без дополнительных преобразований.
    registration_info_raw: str

    # registration_entries хранит все найденные пары "регистрационный номер + дата".
    registration_entries: list[dict[str, str]]

    # registration_number хранит регистрационный номер, если он был успешно извлечен регулярным выражением.
    registration_number: str

    # registration_date_raw хранит дату регистрации в исходном текстовом виде, если она была извлечена.
    registration_date_raw: str

    # atc_codes хранит список ATX-кодов, найденных в карточке препарата.
    atc_codes: list[str]

    # holder_information хранит сведения о владельце регистрационного удостоверения.
    holder_information: str

    # representative_information хранит сведения о представительстве компании, если они указаны.
    representative_information: str

    # composition_and_packaging хранит текст раздела "Форма выпуска, состав и упаковка".
    composition_and_packaging: str

    # sections хранит словарь разделов инструкции: название раздела -> текст раздела.
    sections: dict[str, str]

    # links хранит ссылки, которые присутствуют в карточке препарата внутри основного контента.
    links: list[str]

    # headings хранит список заголовков, найденных на странице после нормализации.
    headings: list[str]


@dataclass
class EntityRelation:
    """Хранит одну связь между сущностью справочника и карточкой препарата."""

    # relation_id хранит стабильный идентификатор связи для последующей индексации и отладки.
    relation_id: str

    # relation_type хранит тип связи, например active_substance_to_document или atc_to_document.
    relation_type: str

    # entity_type хранит тип исходной сущности: active_substance, atc, nosology или clinical_pharmacology_group.
    entity_type: str

    # entity_code хранит код сущности, если он существует, например R01AD12 или J30.1.
    entity_code: str

    # entity_name хранит основное человекочитаемое название сущности.
    entity_name: str

    # entity_name_lat хранит латинское название сущности, если оно есть.
    entity_name_lat: str

    # source_page_id хранит идентификатор страницы-источника, на которой была найдена связь.
    source_page_id: str

    # source_page_path хранит путь страницы-источника относительно каталога data.
    source_page_path: str

    # target_doc_id хранит идентификатор карточки препарата, на которую указывает связь.
    target_doc_id: str

    # target_doc_path хранит относительный путь к карточке препарата.
    target_doc_path: str

    # target_doc_title хранит текст ссылки на карточку препарата, найденный в индексной странице.
    target_doc_title: str


def parse_arguments() -> argparse.Namespace:
    """Разбирает аргументы командной строки и возвращает объект конфигурации."""

    # parser описывает интерфейс запуска скрипта из терминала.
    parser = argparse.ArgumentParser(
        description="Build structured documents and relations from normalized Vidal pages.",
    )

    # input_file_argument указывает путь к JSONL с нормализованными страницами.
    parser.add_argument(
        "--input-file",
        type=Path,
        default=DEFAULT_INPUT_FILE,
        help="Path to normalized_pages.jsonl.",
    )

    # documents_file_argument указывает путь к выходному JSONL с карточками препаратов.
    parser.add_argument(
        "--documents-file",
        type=Path,
        default=DEFAULT_DOCUMENTS_FILE,
        help="Path to structured_documents.jsonl.",
    )

    # relations_file_argument указывает путь к выходному JSONL со связями между сущностями и препаратами.
    parser.add_argument(
        "--relations-file",
        type=Path,
        default=DEFAULT_RELATIONS_FILE,
        help="Path to entity_relations.jsonl.",
    )

    # limit_argument позволяет ограничить число строк во входном файле во время отладки.
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit of processed normalized pages.",
    )

    # return_value содержит разобранные значения аргументов.
    return parser.parse_args()


def normalize_text(raw_text: str) -> str:
    """Очищает текст от лишних пробелов и переводов строк."""

    # stripped_text удаляет пробелы по краям строки.
    stripped_text = raw_text.strip()

    # normalized_text заменяет последовательности пробельных символов одним пробелом.
    normalized_text = WHITESPACE_PATTERN.sub(" ", stripped_text)

    # return_value содержит чистый однострочный текст.
    return normalized_text


def load_jsonl_records(input_file: Path, limit: Optional[int] = None) -> Iterator[dict]:
    """Читает входной JSONL-файл и возвращает записи по одной."""

    with input_file.open("r", encoding="utf-8") as input_stream:
        # line_index хранит порядковый номер текущей строки для поддержки параметра limit.
        for line_index, line in enumerate(input_stream, start=1):
            if limit is not None and line_index > limit:
                break

            # record хранит одну JSON-запись, считанную из файла.
            record = json.loads(line)
            yield record


def parse_html_fragment(content_html: str) -> BeautifulSoup:
    """Преобразует HTML-фрагмент из JSONL в объект BeautifulSoup."""

    # soup хранит дерево HTML-тегов для дальнейшего структурного парсинга.
    soup = BeautifulSoup(content_html, "html.parser")

    # return_value содержит готовый объект BeautifulSoup.
    return soup


def extract_doc_id_from_href(href: str) -> str:
    """Возвращает идентификатор карточки препарата из ссылки на docs/doc_*.htm."""

    # match хранит результат регулярного выражения для ссылки на карточку препарата.
    match = DOC_LINK_PATTERN.search(href)
    if not match:
        return ""

    # doc_id хранит имя файла карточки без расширения.
    doc_id = match.group("doc_id")

    # return_value содержит извлеченный идентификатор карточки препарата.
    return doc_id


def extract_code_from_heading(heading_text: str) -> str:
    """Возвращает код из строки вида '(R01AD12)' или пустую строку."""

    # match хранит результат регулярного выражения для строки с кодом в круглых скобках.
    match = CODE_IN_PARENTHESES_PATTERN.match(heading_text)
    if not match:
        return ""

    # code хранит извлеченный код без круглых скобок.
    code = normalize_text(match.group("code"))

    # return_value содержит код сущности.
    return code


def split_active_substances(active_substance_raw: str) -> list[str]:
    """Разбивает строку действующего вещества на список компонентов."""

    if not active_substance_raw:
        return []

    # raw_parts хранит фрагменты строки после разбиения по запятым и точкам с запятой.
    raw_parts = re.split(r"[;,]", active_substance_raw)

    # normalized_parts хранит очищенные названия веществ без пустых значений.
    normalized_parts = [
        normalize_text(raw_part)
        for raw_part in raw_parts
        if normalize_text(raw_part)
    ]

    # return_value содержит список выделенных компонентов.
    return normalized_parts


def extract_primary_text_from_header(header_cell: Tag) -> str:
    """Извлекает русское торговое название препарата из верхней ячейки карточки."""

    # header_copy хранит копию HTML-узла, чтобы можно было удалить служебные span без побочных эффектов.
    header_copy = BeautifulSoup(str(header_cell), "html.parser")

    # copied_cell хранит корневую ячейку из созданной копии.
    copied_cell = header_copy.find("td") or header_copy

    # removable_node по очереди удаляет вложенные span с латинским названием, МНН и формой выпуска.
    for removable_node in copied_cell.find_all(["span", "a"]):
        removable_node.decompose()

    # primary_text хранит оставшийся текст заголовка после удаления служебных частей.
    primary_text = normalize_text(copied_cell.get_text(" ", strip=True))

    # return_value содержит русское торговое название препарата.
    return primary_text


def extract_labeled_values(container_tag: Optional[Tag]) -> dict[str, str]:
    """Извлекает пары 'метка -> значение' из блока, где метки оформлены тегом <i>."""

    if container_tag is None:
        return {}

    # labeled_values хранит итоговые значения, извлеченные из текущего блока.
    labeled_values: dict[str, str] = {}

    # current_label хранит метку, текст которой был прочитан последней.
    current_label = ""

    # current_value_parts накапливает текстовые фрагменты текущего поля до появления следующей метки.
    current_value_parts: list[str] = []

    # child_node по очереди перебирает прямых потомков контейнера.
    for child_node in container_tag.children:
        if isinstance(child_node, NavigableString):
            # child_text хранит текстовый фрагмент текущего текстового узла.
            child_text = normalize_text(str(child_node))
        elif isinstance(child_node, Tag) and child_node.name == "i":
            # saved_value хранит накопленный текст предыдущего поля перед переключением на новую метку.
            saved_value = normalize_text(" ".join(current_value_parts))
            if current_label and saved_value:
                labeled_values[current_label] = saved_value

            # current_label обновляется текстом новой метки без двоеточия на конце.
            current_label = normalize_text(child_node.get_text(" ", strip=True)).rstrip(":")

            # current_value_parts очищается для накопления значения следующего поля.
            current_value_parts = []
            continue
        elif isinstance(child_node, Tag):
            # child_text хранит текст вложенного HTML-тега, который относится к значению текущей метки.
            child_text = normalize_text(child_node.get_text(" ", strip=True))
        else:
            continue

        if child_text:
            current_value_parts.append(child_text)

    # saved_value хранит текст последнего поля после завершения цикла.
    saved_value = normalize_text(" ".join(current_value_parts))
    if current_label and saved_value:
        labeled_values[current_label] = saved_value

    # return_value содержит словарь всех найденных полей.
    return labeled_values


def extract_registration_entries(registration_info_raw: str) -> list[dict[str, str]]:
    """Извлекает все регистрационные записи из строки регистрации."""

    if not registration_info_raw:
        return []

    # matches хранит все совпадения шаблона "номер от дата" внутри строки регистрации.
    matches = REGISTRATION_ENTRY_PATTERN.finditer(registration_info_raw)

    # registration_entries хранит все найденные записи в виде списка словарей.
    registration_entries: list[dict[str, str]] = []

    # match по очереди перебирает найденные регистрационные записи.
    for match in matches:
        # registration_number хранит регистрационный номер текущей записи.
        registration_number = normalize_text(match.group("number"))

        # registration_date_raw хранит дату текущей регистрационной записи.
        registration_date_raw = normalize_text(match.group("date"))

        registration_entries.append(
            {
                "registration_number": registration_number,
                "registration_date_raw": registration_date_raw,
            }
        )

    # return_value содержит список всех найденных регистрационных записей.
    return registration_entries


def choose_single_registration(registration_entries: list[dict[str, str]]) -> tuple[str, str]:
    """Возвращает одну пару номер/дата только если в карточке найдена ровно одна регистрационная запись."""

    if len(registration_entries) != 1:
        return "", ""

    # registration_entry хранит единственную найденную регистрационную запись.
    registration_entry = registration_entries[0]

    # registration_number хранит регистрационный номер единственной записи.
    registration_number = registration_entry["registration_number"]

    # registration_date_raw хранит дату единственной записи.
    registration_date_raw = registration_entry["registration_date_raw"]

    # return_value содержит однозначно определенную пару номер/дата.
    return registration_number, registration_date_raw


def extract_composition_section(document_soup: BeautifulSoup) -> str:
    """Извлекает текст блока 'Форма выпуска, состав и упаковка'."""

    # composition_title хранит искомое название раздела, расположенного до div[colref].
    composition_title = "Форма выпуска, состав и упаковка"

    # bold_node по очереди проверяет жирные заголовки внутри документа.
    for bold_node in document_soup.find_all("b"):
        # bold_text хранит текст текущего жирного заголовка.
        bold_text = normalize_text(bold_node.get_text(" ", strip=True))
        if bold_text != composition_title:
            continue

        # parent_cell хранит контейнер, внутри которого лежит найденный заголовок и содержимое раздела.
        parent_cell = bold_node.find_parent("td")
        if parent_cell is None:
            continue

        # section_copy хранит копию HTML-узла, чтобы можно было безопасно удалить заголовок.
        section_copy = BeautifulSoup(str(parent_cell), "html.parser")

        # copied_bold хранит копию найденного жирного заголовка внутри клонированного блока.
        copied_bold = section_copy.find("b")
        if copied_bold is not None:
            copied_bold.decompose()

        # section_text хранит текст содержимого раздела без заголовка.
        section_text = normalize_text(section_copy.get_text(" ", strip=True))
        return section_text

    return ""


def extract_instruction_sections(document_soup: BeautifulSoup) -> dict[str, str]:
    """Извлекает основные разделы инструкции из div[colref]."""

    # sections хранит итоговый словарь разделов инструкции.
    sections: dict[str, str] = {}

    # section_div по очереди перебирает div-узлы, размеченные атрибутом colref.
    for section_div in document_soup.find_all("div", attrs={"colref": True}):
        # title_tag хранит первый жирный заголовок внутри блока раздела.
        title_tag = section_div.find("b")
        if title_tag is None:
            continue

        # section_title хранит очищенный текст заголовка раздела.
        section_title = normalize_text(title_tag.get_text(" ", strip=True))
        if not section_title:
            continue

        # section_copy хранит копию HTML-блока раздела для безопасного удаления заголовка и внутренних якорей.
        section_copy = BeautifulSoup(str(section_div), "html.parser")

        # copied_div хранит корневой блок раздела внутри копии.
        copied_div = section_copy.find("div")
        if copied_div is None:
            continue

        # removable_anchor удаляет технические ссылки-якоря внутри раздела.
        for removable_anchor in copied_div.find_all("a"):
            removable_anchor.decompose()

        # copied_title удаляет заголовок раздела, чтобы в тексте не было дублирования названия.
        copied_title = copied_div.find("b")
        if copied_title is not None:
            copied_title.decompose()

        # section_text хранит текст содержимого раздела без заголовка.
        section_text = normalize_text(copied_div.get_text(" ", strip=True))
        if not section_text:
            continue

        sections[section_title] = section_text

    # return_value содержит словарь разделов инструкции.
    return sections


def extract_document_links(content_soup: BeautifulSoup) -> list[dict[str, str]]:
    """Извлекает уникальные ссылки на карточки препаратов из HTML-фрагмента страницы."""

    # document_links хранит итоговый список ссылок на карточки препаратов.
    document_links: list[dict[str, str]] = []

    # seen_doc_ids предотвращает дублирование одной и той же карточки внутри страницы.
    seen_doc_ids: set[str] = set()

    # anchor_tag по очереди перебирает все ссылки из текущего HTML-фрагмента.
    for anchor_tag in content_soup.find_all("a", href=True):
        # href_value хранит адрес ссылки.
        href_value = anchor_tag["href"].strip()

        # doc_id хранит идентификатор карточки препарата, извлеченный из ссылки.
        doc_id = extract_doc_id_from_href(href_value)
        if not doc_id or doc_id in seen_doc_ids:
            continue

        # anchor_text хранит читаемый текст ссылки на карточку препарата.
        anchor_text = normalize_text(anchor_tag.get_text(" ", strip=True))

        # target_doc_path хранит путь к карточке препарата в формате data/docs/doc_*.htm.
        target_doc_path = f"docs/{doc_id}.htm"

        document_links.append(
            {
                "doc_id": doc_id,
                "target_doc_path": target_doc_path,
                "anchor_text": anchor_text,
            }
        )
        seen_doc_ids.add(doc_id)

    # return_value содержит список уникальных ссылок на карточки препаратов.
    return document_links


def parse_drug_document(record: dict) -> Optional[StructuredDocument]:
    """Преобразует одну страницу типа drug_document в структурированную карточку препарата."""

    # document_soup хранит HTML-дерево очищенного содержимого страницы.
    document_soup = parse_html_fragment(record["content_html"])

    # header_cell хранит верхнюю ячейку с названием препарата и краткими метаданными.
    header_cell = document_soup.find("td", class_="h1")
    if header_cell is None:
        return None

    # drug_name_ru хранит русское торговое название препарата.
    drug_name_ru = extract_primary_text_from_header(header_cell)

    # drug_name_lat_tag хранит span с латинским названием торгового наименования.
    drug_name_lat_tag = header_cell.find("span", class_="eng")

    # active_substance_tag хранит span с действующим веществом.
    active_substance_tag = header_cell.find("span", class_="mnn")

    # dosage_form_tag хранит span с лекарственной формой препарата.
    dosage_form_tag = header_cell.find("span", class_="ext")

    # drug_name_lat хранит очищенное латинское название без внешних скобок.
    drug_name_lat = normalize_text(drug_name_lat_tag.get_text(" ", strip=True)).strip("()") if drug_name_lat_tag else ""

    # active_substance_raw хранит исходную строку действующего вещества.
    active_substance_raw = normalize_text(active_substance_tag.get_text(" ", strip=True)) if active_substance_tag else ""

    # active_substances хранит список отдельных веществ, если заголовок описывает комбинацию компонентов.
    active_substances = split_active_substances(active_substance_raw)

    # dosage_form хранит лекарственную форму препарата.
    dosage_form = normalize_text(dosage_form_tag.get_text(" ", strip=True)) if dosage_form_tag else ""

    # left_info_cell хранит левую колонку с клинико-фармакологической группой и регистрацией.
    left_info_cell = document_soup.find("td", class_="fr1")

    # right_info_cell хранит правую колонку с владельцем регистрационного удостоверения и представительством.
    right_info_cell = document_soup.find("td", class_="fr")

    # left_values хранит пары "метка -> значение" из левой колонки карточки.
    left_values = extract_labeled_values(left_info_cell)

    # right_values хранит пары "метка -> значение" из правой колонки карточки.
    right_values = extract_labeled_values(right_info_cell)

    # clinical_pharmacological_group хранит строку из поля группы препарата.
    clinical_pharmacological_group = left_values.get("Клинико-фармакологическая группа", "")

    # registration_info_raw хранит исходную строку с номером и датой регистрации.
    registration_info_raw = left_values.get("Номер и дата регистрации", "")

    # registration_entries хранит все регистрационные записи, найденные в карточке препарата.
    registration_entries = extract_registration_entries(registration_info_raw)

    # registration_number хранит номер только если регистрационная запись в карточке однозначна.
    # registration_date_raw хранит дату только если регистрационная запись в карточке однозначна.
    registration_number, registration_date_raw = choose_single_registration(registration_entries)

    # atc_codes хранит все ATX-коды из ссылок внутри карточки препарата.
    atc_codes = sorted(
        {
            normalize_text(anchor_tag.get_text(" ", strip=True))
            for anchor_tag in document_soup.find_all("a", href=True)
            if "atc/" in anchor_tag["href"]
        }
    )

    # holder_information хранит сведения о владельце регистрационного удостоверения.
    holder_information = right_values.get("Владелец регистрационного удостоверения", "")

    # representative_information хранит сведения о представительстве компании.
    representative_information = right_values.get("Представительство", "")

    # composition_and_packaging хранит текст раздела с составом и упаковкой.
    composition_and_packaging = extract_composition_section(document_soup)

    # sections хранит содержательные разделы инструкции по применению.
    sections = extract_instruction_sections(document_soup)

    # structured_document хранит итоговую структуру одной карточки препарата.
    structured_document = StructuredDocument(
        doc_id=record["page_id"],
        title=record["title"],
        source_path=record["source_path"],
        drug_name_ru=drug_name_ru,
        drug_name_lat=drug_name_lat,
        active_substance_raw=active_substance_raw,
        active_substances=active_substances,
        dosage_form=dosage_form,
        clinical_pharmacological_group=clinical_pharmacological_group,
        registration_info_raw=registration_info_raw,
        registration_entries=registration_entries,
        registration_number=registration_number,
        registration_date_raw=registration_date_raw,
        atc_codes=atc_codes,
        holder_information=holder_information,
        representative_information=representative_information,
        composition_and_packaging=composition_and_packaging,
        sections=sections,
        links=record["links"],
        headings=record["headings"],
    )

    # return_value содержит структурированную карточку препарата.
    return structured_document


def build_active_substance_entity(record: dict) -> Optional[dict[str, str]]:
    """Строит описание сущности 'действующее вещество' на основе страницы результатов поиска."""

    # match хранит результат регулярного выражения для заголовка страницы по МНН.
    match = ACTIVE_SUBSTANCE_TITLE_PATTERN.match(record["title"])
    if not match:
        return None

    # name_ru хранит русское название активного вещества.
    name_ru = normalize_text(match.group("name_ru"))

    # name_lat_group хранит латинское название активного вещества из регулярного выражения.
    name_lat_group = match.group("name_lat")

    # name_lat хранит латинское название активного вещества или пустую строку.
    name_lat = normalize_text(name_lat_group) if name_lat_group else ""

    # return_value содержит словарь с атрибутами сущности.
    return {
        "relation_type": "active_substance_to_document",
        "entity_type": "active_substance",
        "entity_code": record["page_id"],
        "entity_name": name_ru,
        "entity_name_lat": name_lat,
    }


def build_heading_based_entity(record: dict) -> Optional[dict[str, str]]:
    """Строит описание сущности для страниц ATX, нозологий и КФУ по заголовкам normalized_pages."""

    # headings хранит список заголовков, извлеченных на предыдущем этапе нормализации.
    headings = record.get("headings", [])
    if len(headings) < 3:
        return None

    # entity_code хранит код сущности, если второй заголовок записан в круглых скобках.
    entity_code = extract_code_from_heading(headings[1])

    # entity_name хранит человекочитаемое название сущности.
    entity_name = normalize_text(headings[2])

    if record["page_type"] == "atc_index":
        # relation_type хранит тип связи для ATX-страниц.
        relation_type = "atc_to_document"

        # entity_type хранит тип сущности для ATX-страниц.
        entity_type = "atc"
    elif record["page_type"] == "nosology_index":
        # relation_type хранит тип связи для нозологических страниц.
        relation_type = "nosology_to_document"

        # entity_type хранит тип сущности для нозологических страниц.
        entity_type = "nosology"
    elif record["page_type"] == "clinical_pharmacology_index":
        # relation_type хранит тип связи для КФУ-страниц.
        relation_type = "clinical_pharmacology_group_to_document"

        # entity_type хранит тип сущности для КФУ-страниц.
        entity_type = "clinical_pharmacology_group"
    else:
        return None

    # return_value содержит словарь с атрибутами сущности.
    return {
        "relation_type": relation_type,
        "entity_type": entity_type,
        "entity_code": entity_code,
        "entity_name": entity_name,
        "entity_name_lat": "",
    }


def build_relations_from_record(record: dict) -> list[EntityRelation]:
    """Строит список связей между одной индексной страницей и карточками препаратов."""

    # supported_page_types хранит типы страниц, из которых на текущем этапе извлекаются связи.
    supported_page_types = {
        "active_substance_index",
        "atc_index",
        "nosology_index",
        "clinical_pharmacology_index",
    }

    if record["page_type"] not in supported_page_types:
        return []

    # content_soup хранит HTML-дерево текущего основного контента страницы.
    content_soup = parse_html_fragment(record["content_html"])

    # document_links хранит все уникальные ссылки на карточки препаратов из текущей страницы.
    document_links = extract_document_links(content_soup)
    if not document_links:
        return []

    if record["page_type"] == "active_substance_index":
        # entity_description хранит метаданные активного вещества.
        entity_description = build_active_substance_entity(record)
    else:
        # entity_description хранит метаданные сущности ATX, нозологии или КФУ.
        entity_description = build_heading_based_entity(record)

    if entity_description is None:
        return []

    # relations хранит все связи, извлеченные из текущей страницы.
    relations: list[EntityRelation] = []

    # document_link по очереди перебирает найденные ссылки на карточки препаратов.
    for document_link in document_links:
        # relation_id хранит стабильный идентификатор связи.
        relation_id = (
            f"{entity_description['relation_type']}:"
            f"{record['page_id']}:"
            f"{document_link['doc_id']}"
        )

        # relation хранит одну итоговую связь для текущей сущности и карточки препарата.
        relation = EntityRelation(
            relation_id=relation_id,
            relation_type=entity_description["relation_type"],
            entity_type=entity_description["entity_type"],
            entity_code=entity_description["entity_code"],
            entity_name=entity_description["entity_name"],
            entity_name_lat=entity_description["entity_name_lat"],
            source_page_id=record["page_id"],
            source_page_path=record["source_path"],
            target_doc_id=document_link["doc_id"],
            target_doc_path=document_link["target_doc_path"],
            target_doc_title=document_link["anchor_text"],
        )
        relations.append(relation)

    # return_value содержит список извлеченных связей для текущей страницы.
    return relations


def write_jsonl(records: Iterable[object], output_file: Path) -> int:
    """Записывает произвольные dataclass-объекты в JSONL и возвращает число строк."""

    # output_directory хранит каталог, который должен существовать до открытия файла на запись.
    output_directory = output_file.parent
    output_directory.mkdir(parents=True, exist_ok=True)

    # written_rows хранит число записанных объектов.
    written_rows = 0

    with output_file.open("w", encoding="utf-8") as output_stream:
        # record по очереди перебирает объекты, подготовленные к сериализации.
        for record in records:
            # serialized_record хранит JSON-представление текущего dataclass-объекта.
            serialized_record = json.dumps(asdict(record), ensure_ascii=False)
            output_stream.write(serialized_record + "\n")
            written_rows += 1

    # return_value содержит число успешно записанных строк.
    return written_rows


def build_outputs(
    input_file: Path,
    documents_file: Path,
    relations_file: Path,
    limit: Optional[int] = None,
) -> tuple[int, int]:
    """Обрабатывает входной JSONL и сохраняет два выходных JSONL-файла."""

    # structured_documents хранит все карточки препаратов, извлеченные из drug_document.
    structured_documents: list[StructuredDocument] = []

    # entity_relations хранит все связи сущностей справочника с карточками препаратов.
    entity_relations: list[EntityRelation] = []

    # record по очереди перебирает записи normalized_pages.jsonl.
    for record in load_jsonl_records(input_file=input_file, limit=limit):
        if record["page_type"] == "drug_document":
            # structured_document хранит результат парсинга одной карточки препарата.
            structured_document = parse_drug_document(record)
            if structured_document is not None:
                structured_documents.append(structured_document)

        # extracted_relations хранит связи, найденные на текущей странице.
        extracted_relations = build_relations_from_record(record)
        if extracted_relations:
            entity_relations.extend(extracted_relations)

    # documents_count хранит число записанных структурированных карточек препаратов.
    documents_count = write_jsonl(records=structured_documents, output_file=documents_file)

    # relations_count хранит число записанных связей между сущностями и карточками препаратов.
    relations_count = write_jsonl(records=entity_relations, output_file=relations_file)

    # return_value содержит количества записанных документов и связей.
    return documents_count, relations_count


def main() -> None:
    """Запускает полный конвейер построения структурированных данных."""

    # arguments хранит разобранные аргументы командной строки.
    arguments = parse_arguments()

    # input_file хранит абсолютный путь к входному JSONL с нормализованными страницами.
    input_file = arguments.input_file.resolve()

    # documents_file хранит абсолютный путь к выходному JSONL со структурированными карточками.
    documents_file = arguments.documents_file.resolve()

    # relations_file хранит абсолютный путь к выходному JSONL со связями сущностей.
    relations_file = arguments.relations_file.resolve()

    # documents_count и relations_count хранят число записанных документов и связей после обработки.
    documents_count, relations_count = build_outputs(
        input_file=input_file,
        documents_file=documents_file,
        relations_file=relations_file,
        limit=arguments.limit,
    )

    # summary_message хранит итоговое сообщение для терминала после завершения обработки.
    summary_message = (
        f"Saved {documents_count} structured drug documents to '{documents_file}' "
        f"and {relations_count} entity relations to '{relations_file}'."
    )
    print(summary_message)


if __name__ == "__main__":
    main()
