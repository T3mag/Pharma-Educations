"""Use case слой генерации учебных мини-игр."""

from __future__ import annotations

import json
import random
import re
from functools import lru_cache
from typing import Any, Optional

from ..api_models import (
    AggregateSearchRequest,
    FlashcardResponse,
    FlashcardsRequest,
    FlashcardsResponse,
    FoundDrugResponse,
    MatchPairResponse,
    MatchRequest,
    MatchResponse,
    MatchTaskResponse,
    QuizQuestionResponse,
    QuizRequest,
    QuizResponse,
    SourceResponse,
)
from ..clients import retry_on_transient_error
from ..common import extract_chat_message_text, load_jsonl_records, run_find_all_retrieval
from ..config import (
    DEFAULT_ENTITY_RELATIONS_PATH,
    DEFAULT_QUERY_RESULTS,
    DEFAULT_SEARCH_OVERFETCH_FACTOR,
    DEFAULT_STRUCTURED_DOCUMENTS_PATH,
)
from ..generation import build_find_all_summary_text, build_rag_context_text, build_retrieval_summary
from ..search import run_hybrid_retrieval, select_context_chunks
from .aggregate_search_service import execute_aggregate_search
from .errors import BadRequestError, NotFoundError
from .runtime import get_runtime, get_topic_tree, load_structured_documents_index

MAX_GAME_TOPIC_COUNT = 6
MAX_GAME_DOC_COUNT = 10
GAME_SECTION_TEXT_LIMIT = 80
MAX_MATCH_TOPIC_COUNT = 8
MAX_MATCH_DOC_COUNT = 16
MATCH_SECTION_TEXT_LIMIT = 80
QUIZ_BATCH_SIZE = 3
FLASHCARD_BATCH_SIZE = 4

MATCH_TYPE_CONFIG = {
    "drug_to_active_substance": {
        "left_label": "Лекарство",
        "right_label": "Действующее вещество",
        "instruction": (
            "Подбирай пары вида лекарство -> действующее вещество. "
            "Для каждого лекарства выбирай одно короткое и точное действующее вещество. "
            "Пиши действующее вещество на русском языке."
        ),
    },
    "drug_to_contraindication": {
        "left_label": "Лекарство",
        "right_label": "Противопоказание",
        "instruction": (
            "Подбирай пары вида лекарство -> противопоказание. "
            "Для каждого лекарства выбирай одно короткое и четкое противопоказание, а не длинный абзац."
        ),
    },
    "drug_to_indication": {
        "left_label": "Лекарство",
        "right_label": "Показание",
        "instruction": (
            "Подбирай пары вида лекарство -> показание. "
            "Для каждого лекарства выбирай одно короткое и проверяемое показание."
        ),
    },
    "drug_to_dosage_form": {
        "left_label": "Лекарство",
        "right_label": "Лекарственная форма",
        "instruction": (
            "Подбирай пары вида лекарство -> лекарственная форма. "
            "Используй краткую форму записи, например: таблетки, капли, спрей."
        ),
    },
    "drug_to_clinical_group": {
        "left_label": "Лекарство",
        "right_label": "Клинико-фармакологическая группа",
        "instruction": (
            "Подбирай пары вида лекарство -> клинико-фармакологическая группа. "
            "Используй короткую и содержательную формулировку группы."
        ),
    },
}

RANDOM_MATCH_TYPES = tuple(MATCH_TYPE_CONFIG.keys())


@lru_cache(maxsize=1)
def load_active_substance_names_by_doc_id() -> dict[str, list[str]]:
    """Строит индекс doc_id -> русские названия действующих веществ."""

    names_by_doc_id: dict[str, list[str]] = {}
    for relation_record in load_jsonl_records(DEFAULT_ENTITY_RELATIONS_PATH):
        if str(relation_record.get("entity_type") or "") != "active_substance":
            continue
        doc_id = str(relation_record.get("target_doc_id") or "").strip()
        entity_name = str(relation_record.get("entity_name") or "").strip()
        if not doc_id or not entity_name:
            continue
        names = names_by_doc_id.setdefault(doc_id, [])
        if entity_name not in names:
            names.append(entity_name)
    return names_by_doc_id


def get_display_active_substances(document_record: dict[str, Any]) -> list[str]:
    """Возвращает русские названия действующих веществ, если они есть в индексе."""

    doc_id = str(document_record.get("doc_id") or "").strip()
    russian_names = load_active_substance_names_by_doc_id().get(doc_id, [])
    if russian_names:
        return russian_names
    return [str(item) for item in document_record.get("active_substances") or [] if str(item).strip()]


def extract_json_object(text: str) -> dict[str, Any]:
    """Достает JSON-объект из ответа модели, даже если модель случайно добавила markdown."""

    normalized_text = text.strip()
    if normalized_text.startswith("```"):
        normalized_text = re.sub(r"^```(?:json)?\s*", "", normalized_text, flags=re.IGNORECASE)
        normalized_text = re.sub(r"\s*```$", "", normalized_text)

    try:
        parsed_value = json.loads(normalized_text)
    except json.JSONDecodeError:
        json_match = re.search(r"\{.*\}", normalized_text, flags=re.DOTALL)
        if not json_match:
            raise RuntimeError("Модель не вернула JSON-объект.")
        parsed_value = json.loads(json_match.group(0))

    if not isinstance(parsed_value, dict):
        raise RuntimeError("Модель вернула JSON, но верхний уровень не является объектом.")

    return parsed_value


def sanitize_json_text(text: str) -> str:
    """Пытается локально исправить частые синтаксические ошибки в JSON-ответе модели."""

    sanitized = text.strip()
    if sanitized.startswith("```"):
        sanitized = re.sub(r"^```(?:json)?\s*", "", sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r"\s*```$", "", sanitized)

    json_match = re.search(r"\{.*\}", sanitized, flags=re.DOTALL)
    if json_match:
        sanitized = json_match.group(0)

    sanitized = sanitized.replace("\u201c", '"').replace("\u201d", '"')
    sanitized = sanitized.replace("\u2018", "'").replace("\u2019", "'")

    sanitized = re.sub(r",(\s*[\]}])", r"\1", sanitized)

    sanitized = re.sub(r"(\})(\s*\{)", r"\1,\2", sanitized)

    sanitized = re.sub(r'("|\]|\}|\d)(\s*\n?\s*)("([^"]+)":)', r"\1,\2\3", sanitized)

    return sanitized


def extract_json_object_with_repair(text: str) -> dict[str, Any]:
    """Парсит JSON-объект, а при неудаче применяет локальные эвристики починки."""

    try:
        return extract_json_object(text)
    except Exception:
        sanitized_text = sanitize_json_text(text)
        return extract_json_object(sanitized_text)


def repair_json_object(
    gigachat_client: Any,
    chat_model_name: str,
    invalid_text: str,
    answer_max_tokens: int,
) -> dict[str, Any]:
    """Просит модель починить невалидный JSON, не меняя его смысловую структуру."""

    repair_messages = [
        {
            "role": "system",
            "content": (
                "Ты исправляешь невалидный JSON. "
                "Верни только валидный JSON-объект без markdown, комментариев и пояснений. "
                "Не меняй смысл, ключи и значения больше, чем это нужно для исправления синтаксиса."
            ),
        },
        {
            "role": "user",
            "content": (
                "Исправь этот JSON и верни только валидный JSON-объект:\n\n"
                f"{invalid_text}"
            ),
        },
    ]
    repair_payload = {
        "model": chat_model_name,
        "messages": repair_messages,
        "temperature": 0.0,
        "max_tokens": answer_max_tokens,
    }
    repair_response = retry_on_transient_error(gigachat_client.chat, repair_payload)
    repair_text = extract_chat_message_text(repair_response)
    return extract_json_object_with_repair(repair_text)


def call_gigachat_json(
    gigachat_client: Any,
    chat_model_name: str,
    messages: list[dict[str, str]],
    answer_max_tokens: int,
) -> dict[str, Any]:
    """Вызывает GigaChat и парсит ответ как JSON."""

    chat_payload = {
        "model": chat_model_name,
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": answer_max_tokens,
    }
    chat_response = retry_on_transient_error(gigachat_client.chat, chat_payload)
    answer_text = extract_chat_message_text(chat_response)
    try:
        return extract_json_object_with_repair(answer_text)
    except Exception as parse_error:
        try:
            return repair_json_object(
                gigachat_client=gigachat_client,
                chat_model_name=chat_model_name,
                invalid_text=answer_text,
                answer_max_tokens=answer_max_tokens,
            )
        except Exception as repair_error:
            raise RuntimeError(
                "Модель вернула невалидный JSON, и автоматическое исправление тоже не удалось. "
                f"Ошибка парсинга: {parse_error}. Ошибка исправления: {repair_error}"
            ) from repair_error


def build_game_context(
    topic: str,
    embedding_model_name: str,
    n_results: int,
    overfetch_factor: int,
    context_chunk_limit: int,
    summary_limit: int,
) -> tuple[str, list[FoundDrugResponse], list[SourceResponse]]:
    """Собирает grounded-контекст для генерации мини-игры по свободной теме."""

    aggregate_context, aggregate_drugs = build_aggregate_game_context(
        topic=topic,
        summary_limit=summary_limit,
    )
    if aggregate_context:
        return aggregate_context, aggregate_drugs, []

    embedding_client, _chat_client, collection = get_runtime()
    find_all_bundle = run_find_all_retrieval(
        query=topic,
        entity_relations_path=DEFAULT_ENTITY_RELATIONS_PATH,
        structured_documents_path=DEFAULT_STRUCTURED_DOCUMENTS_PATH,
    )
    retrieval_bundle = run_hybrid_retrieval(
        collection=collection,
        gigachat_client=embedding_client,
        query=topic,
        embedding_model_name=embedding_model_name,
        n_results=n_results,
        overfetch_factor=overfetch_factor,
        entity_relations_path=DEFAULT_ENTITY_RELATIONS_PATH,
        structured_documents_path=DEFAULT_STRUCTURED_DOCUMENTS_PATH,
    )

    if (
        not find_all_bundle.catalog_matches
        and not retrieval_bundle.matched_entities
        and not retrieval_bundle.matched_drug_documents
    ):
        raise NotFoundError("Тема не распознана по справочнику. Выберите тему из /topics или проверьте написание.")

    retrieval_summary = build_retrieval_summary(retrieval_bundle)
    context_chunks = select_context_chunks(
        grouped_results=retrieval_bundle.grouped_results,
        context_chunk_limit=context_chunk_limit,
        answer_mode=retrieval_summary.answer_mode,
    )

    if not find_all_bundle.catalog_matches and not context_chunks:
        raise NotFoundError("По этой теме не найдено данных в справочнике. Выберите другую тему или проверьте написание.")

    context_parts: list[str] = []
    if find_all_bundle.catalog_matches:
        context_parts.append(
            "Полнотный поиск по структурированному справочнику:\n"
            + build_find_all_summary_text(
                query=topic,
                find_all_bundle=find_all_bundle,
                summary_limit=summary_limit,
            )
        )

    if context_chunks:
        context_parts.append("Фрагменты инструкций из retrieval:\n" + build_rag_context_text(context_chunks))

    found_drug_map: dict[str, FoundDrugResponse] = {}
    for catalog_match in find_all_bundle.catalog_matches[:summary_limit]:
        found_drug_map[catalog_match.doc_id] = FoundDrugResponse(
            doc_id=catalog_match.doc_id,
            drug_name_ru=catalog_match.drug_name_ru,
            drug_name_lat=catalog_match.drug_name_lat,
            score=catalog_match.score,
            match_reasons=catalog_match.match_reasons,
        )

    for context_chunk in context_chunks:
        if context_chunk.doc_id in found_drug_map:
            continue
        found_drug_map[context_chunk.doc_id] = FoundDrugResponse(
            doc_id=context_chunk.doc_id,
            drug_name_ru=context_chunk.drug_name_ru,
            drug_name_lat="",
            score=context_chunk.reranked_score,
            match_reasons=[f"retrieval section: {context_chunk.section_name}"],
        )

    sources = [
        SourceResponse(
            drug=context_chunk.drug_name_ru,
            doc_id=context_chunk.doc_id,
            section=context_chunk.section_name,
            chunk_id=context_chunk.chunk_id,
        )
        for context_chunk in context_chunks
    ]

    return "\n\n".join(context_parts), list(found_drug_map.values()), sources


def build_aggregate_game_context(
    topic: str,
    summary_limit: int,
) -> tuple[str, list[FoundDrugResponse]]:
    """Собирает разнообразный контекст по препаратам из полного структурного поиска."""

    aggregate_response = execute_aggregate_search(
        request=AggregateSearchRequest(
            query=topic,
            limit=max(summary_limit * 3, 30),
        )
    )
    if aggregate_response.total_found == 0:
        return "", []

    active_filter = aggregate_response.filters.get("active_substance", "")
    indication_filter = aggregate_response.filters.get("indication", "")
    if not active_filter and not indication_filter:
        return "", []

    selected_results = []
    seen_drug_names: set[str] = set()
    for result in aggregate_response.results:
        normalized_drug_name = result.drug_name_ru.upper().strip()
        if normalized_drug_name in seen_drug_names:
            continue
        seen_drug_names.add(normalized_drug_name)
        selected_results.append(result)
        if len(selected_results) >= summary_limit:
            break

    if len(selected_results) < summary_limit:
        selected_doc_ids = {result.doc_id for result in selected_results}
        for result in aggregate_response.results:
            if result.doc_id in selected_doc_ids:
                continue
            selected_results.append(result)
            if len(selected_results) >= summary_limit:
                break

    filters_text = ", ".join(
        f"{filter_name}: {filter_value}"
        for filter_name, filter_value in aggregate_response.filters.items()
        if filter_value
    )
    context_lines = [
        "Полнотный структурный поиск по всем карточкам препаратов:",
        f"Фильтры: {filters_text}",
        f"Всего найдено препаратов: {aggregate_response.total_found}",
        f"В контекст для игры включено разных препаратов: {len(selected_results)}",
        "Используй разные препараты. Не делай несколько карточек подряд про один и тот же препарат.",
        "Препараты и проверенные признаки:",
    ]
    found_drugs: list[FoundDrugResponse] = []
    for result_index, result in enumerate(selected_results, start=1):
        found_drugs.append(
            FoundDrugResponse(
                doc_id=result.doc_id,
                drug_name_ru=result.drug_name_ru,
                drug_name_lat=result.drug_name_lat,
                score=1.0,
                match_reasons=result.matched_reasons,
            )
        )
        context_lines.extend(
            [
                f"{result_index}. Препарат: {result.drug_name_ru or 'Не указан'}",
                f"   Doc ID: {result.doc_id}",
                f"   Латинское название: {result.drug_name_lat or 'не указано'}",
                f"   Действующие вещества: {', '.join(result.active_substances) if result.active_substances else 'не указаны'}",
                f"   ATC: {', '.join(result.atc_codes) if result.atc_codes else 'не указаны'}",
                f"   КФГ: {result.clinical_pharmacological_group or 'не указана'}",
                f"   Лекарственная форма: {result.dosage_form or 'не указана'}",
                f"   Показания: {truncate_text(result.indications, limit=450) or 'не указаны'}",
                f"   Противопоказания: {truncate_text(result.contraindications, limit=450) or 'не указаны'}",
            ]
        )

    return "\n".join(context_lines), found_drugs


def truncate_text(value: Any, limit: int = 600) -> str:
    """Ограничивает длинный текст раздела для компактного prompt-контекста."""

    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


def build_topic_id_game_context(
    topic_id: str,
    summary_limit: int,
) -> tuple[str, str, list[FoundDrugResponse], list[SourceResponse]]:
    """Собирает игровой контекст по выбранному узлу дерева тем."""

    topic_tree = get_topic_tree()
    topic_node = topic_tree.nodes.get(topic_id)
    if topic_node is None:
        raise NotFoundError("Тема с таким topic_id не найдена.")

    if not topic_node.doc_ids:
        raise NotFoundError("У выбранной темы нет связанных препаратов. Выберите более конкретную тему.")

    documents_by_id = load_structured_documents_index()
    selected_doc_ids = [
        doc_id
        for doc_id in topic_node.doc_ids[: min(max(summary_limit, 1), 30)]
        if doc_id in documents_by_id
    ]
    if not selected_doc_ids:
        raise NotFoundError("Для выбранной темы не найдены структурированные карточки препаратов.")

    topic_title = " / ".join(topic_node.path)
    context_lines = [
        f"Выбранная тема: {topic_title}",
        f"Указатель: {topic_node.catalog}",
        f"Source page: {topic_node.source_page_path}",
        f"Всего связанных препаратов в теме: {topic_node.doc_count}",
        f"В контекст для игры включено препаратов: {len(selected_doc_ids)}",
        "Препараты и проверенные данные:",
    ]
    found_drugs: list[FoundDrugResponse] = []
    sources: list[SourceResponse] = []
    useful_sections = [
        "Фармакологическое действие",
        "Показания",
        "Противопоказания",
        "Побочное действие",
        "Применение при беременности и кормлении грудью",
        "Лекарственное взаимодействие",
    ]

    for drug_index, doc_id in enumerate(selected_doc_ids, start=1):
        document_record = documents_by_id[doc_id]
        drug_name_ru = str(document_record.get("drug_name_ru") or "").strip()
        drug_name_lat = str(document_record.get("drug_name_lat") or "").strip()
        active_substances = get_display_active_substances(document_record)
        atc_codes = document_record.get("atc_codes") or []
        clinical_group = str(document_record.get("clinical_pharmacological_group") or "").strip()
        dosage_form = str(document_record.get("dosage_form") or "").strip()
        sections = document_record.get("sections") or {}

        found_drugs.append(
            FoundDrugResponse(
                doc_id=doc_id,
                drug_name_ru=drug_name_ru,
                drug_name_lat=drug_name_lat,
                score=1.0,
                match_reasons=[f"selected topic: {topic_node.title}"],
            )
        )
        context_lines.extend(
            [
                f"{drug_index}. Препарат: {drug_name_ru or 'Не указан'}",
                f"   Doc ID: {doc_id}",
                f"   Латинское название: {drug_name_lat or 'не указано'}",
                f"   Лекарственная форма: {dosage_form or 'не указана'}",
                f"   КФГ: {clinical_group or 'не указана'}",
                f"   Активные вещества: {', '.join(active_substances) if active_substances else 'не указаны'}",
                f"   ATC: {', '.join(atc_codes) if atc_codes else 'не указаны'}",
            ]
        )

        for section_name in useful_sections:
            section_text = truncate_text(sections.get(section_name), limit=500)
            if not section_text:
                continue
            context_lines.append(f"   {section_name}: {section_text}")
            sources.append(
                SourceResponse(
                    drug=drug_name_ru,
                    doc_id=doc_id,
                    section=section_name,
                    chunk_id=f"{doc_id}__structured__{section_name.replace(' ', '_')}",
                )
            )

    return "\n".join(context_lines), topic_title, found_drugs, sources


def resolve_selected_topic_nodes(topic_ids: list[str]) -> list[Any]:
    """Разворачивает выбранные id тем в реальные узлы, поддерживая id верхних каталогов."""

    topic_tree = get_topic_tree()
    catalog_ids = {catalog.id for catalog in topic_tree.catalogs}
    selected_topic_nodes = []
    seen_topic_ids: set[str] = set()

    for topic_id in topic_ids:
        if topic_id in catalog_ids:
            catalog_child_ids = [
                child_id
                for child_id in topic_tree.children_by_parent.get("", [])
                if child_id in topic_tree.nodes and topic_tree.nodes[child_id].catalog == topic_id
            ]
            if not catalog_child_ids:
                raise NotFoundError(f"В каталоге '{topic_id}' не найдено тем.")
            for child_id in catalog_child_ids:
                if child_id in seen_topic_ids:
                    continue
                seen_topic_ids.add(child_id)
                selected_topic_nodes.append(topic_tree.nodes[child_id])
            continue

        topic_node = topic_tree.nodes.get(topic_id)
        if topic_node is None:
            raise NotFoundError(f"Тема с id '{topic_id}' не найдена.")
        if topic_node.id in seen_topic_ids:
            continue
        seen_topic_ids.add(topic_node.id)
        selected_topic_nodes.append(topic_node)

    return selected_topic_nodes


def resolve_selected_topic_nodes_with_descendants(topic_ids: list[str]) -> list[Any]:
    """Разворачивает выбранные темы и рекурсивно добавляет все дочерние узлы с препаратами."""

    normalized_topic_ids = [
        topic_id.strip()
        for topic_id in topic_ids
        if topic_id and topic_id.strip()
    ]
    if not normalized_topic_ids:
        raise BadRequestError("Передайте непустой список topic_ids.")

    topic_tree = get_topic_tree()
    catalog_ids = {catalog.id for catalog in topic_tree.catalogs}
    root_node_ids: list[str] = []

    for topic_id in normalized_topic_ids:
        if topic_id in catalog_ids:
            root_node_ids.extend(
                child_id
                for child_id in topic_tree.children_by_parent.get("", [])
                if child_id in topic_tree.nodes and topic_tree.nodes[child_id].catalog == topic_id
            )
            continue

        if topic_id not in topic_tree.nodes:
            raise NotFoundError(f"Тема с id '{topic_id}' не найдена.")
        root_node_ids.append(topic_id)

    collected_nodes = []
    seen_node_ids: set[str] = set()
    stack = list(root_node_ids)

    while stack:
        current_node_id = stack.pop()
        if current_node_id in seen_node_ids:
            continue
        seen_node_ids.add(current_node_id)

        current_node = topic_tree.nodes.get(current_node_id)
        if current_node is None:
            continue
        if current_node.doc_ids:
            collected_nodes.append(current_node)

        for child_id in topic_tree.children_by_parent.get(current_node_id, []):
            if child_id not in seen_node_ids:
                stack.append(child_id)

    if not collected_nodes:
        for root_node_id in root_node_ids:
            root_node = topic_tree.nodes.get(root_node_id)
            if root_node is not None and root_node.doc_ids:
                collected_nodes.append(root_node)

    if not collected_nodes:
        raise NotFoundError("Для выбранных тем не найдено дочерних узлов с препаратами.")

    return collected_nodes


def resolve_match_type(match_type: Optional[str], feature_name: str) -> str:
    """Выбирает итоговый тип Match-игры, включая случайный режим по умолчанию."""

    normalized_match_type = (match_type or "").strip()
    if normalized_match_type:
        return normalized_match_type

    if feature_name.strip():
        return "drug_to_feature"

    return random.choice(RANDOM_MATCH_TYPES)


def get_match_type_config(match_type: str, feature_name: str) -> tuple[str, str, str]:
    """Возвращает подписи и prompt-инструкцию для выбранного вида Match-игры."""

    normalized_match_type = match_type.strip() or "drug_to_active_substance"
    if normalized_match_type == "drug_to_feature":
        normalized_feature_name = feature_name.strip()
        if not normalized_feature_name:
            raise BadRequestError("Для match_type='drug_to_feature' передайте непустое поле feature_name.")
        return (
            "Лекарство",
            normalized_feature_name,
            (
                f"Подбирай пары вида лекарство -> {normalized_feature_name}. "
                f"Используй только такой признак, который явно есть в контексте, и формулируй его кратко."
            ),
        )

    config = MATCH_TYPE_CONFIG.get(normalized_match_type)
    if config is None:
        raise BadRequestError(
            "Неподдерживаемый match_type. Используйте один из: "
            "drug_to_active_substance, drug_to_contraindication, drug_to_indication, "
            "drug_to_dosage_form, drug_to_clinical_group, drug_to_feature."
        )

    return (
        str(config["left_label"]),
        str(config["right_label"]),
        str(config["instruction"]),
    )


def build_match_context_from_topic_ids(
    topic_ids: list[str],
    pair_count: int,
    summary_limit: int,
    match_type: str = "",
) -> tuple[str, str]:
    """Собирает компактный контекст для Match-игры по темам и их дочерним узлам."""

    documents_by_id = load_structured_documents_index()
    candidate_topic_nodes = resolve_selected_topic_nodes_with_descendants(topic_ids)
    random.shuffle(candidate_topic_nodes)
    selected_topic_nodes = candidate_topic_nodes[: min(max(pair_count * 2, 4), MAX_MATCH_TOPIC_COUNT)]

    topic_titles = [" / ".join(topic_node.path) for topic_node in selected_topic_nodes]
    visible_topic_titles = topic_titles[:4]
    topic_title = "; ".join(visible_topic_titles)
    if len(topic_titles) > len(visible_topic_titles):
        topic_title += f"; и еще {len(topic_titles) - len(visible_topic_titles)} тем"

    total_doc_budget = min(max(pair_count * 2, 4), max(summary_limit, 1), MAX_MATCH_DOC_COUNT)
    doc_limit_per_topic = max(1, min(total_doc_budget // max(len(selected_topic_nodes), 1), 3))

    context_lines = [
        f"Выбрано тем для Match: {len(selected_topic_nodes)}",
        f"Темы: {topic_title}",
        "Используй разные темы и разные препараты.",
        "Ниже приведены проверенные данные по препаратам:",
    ]

    total_selected_docs = 0
    seen_doc_ids: set[str] = set()

    for topic_index, topic_node in enumerate(selected_topic_nodes, start=1):
        if total_selected_docs >= total_doc_budget:
            break

        available_doc_ids = [
            doc_id
            for doc_id in topic_node.doc_ids
            if doc_id in documents_by_id and doc_id not in seen_doc_ids
        ]
        random.shuffle(available_doc_ids)
        selected_doc_ids = available_doc_ids[:doc_limit_per_topic]
        if not selected_doc_ids:
            continue

        context_lines.extend(
            [
                "",
                f"Тема {topic_index}: {' / '.join(topic_node.path)}",
                f"Всего связанных препаратов в теме: {topic_node.doc_count}",
            ]
        )

        for drug_index, doc_id in enumerate(selected_doc_ids, start=1):
            if total_selected_docs >= total_doc_budget:
                break

            seen_doc_ids.add(doc_id)
            total_selected_docs += 1
            document_record = documents_by_id[doc_id]
            sections = document_record.get("sections") or {}
            drug_name_ru = str(document_record.get("drug_name_ru") or "").strip()
            drug_name_lat = str(document_record.get("drug_name_lat") or "").strip()
            active_substances = get_display_active_substances(document_record)
            atc_codes = document_record.get("atc_codes") or []
            clinical_group = str(document_record.get("clinical_pharmacological_group") or "").strip()
            dosage_form = str(document_record.get("dosage_form") or "").strip()

            context_lines.extend(
                [
                    f"{drug_index}. Препарат: {drug_name_ru or 'Не указан'}",
                    f"   Латинское название: {drug_name_lat or 'не указано'}",
                    f"   Активные вещества: {', '.join(active_substances) if active_substances else 'не указаны'}",
                    f"   Лекарственная форма: {dosage_form or 'не указана'}",
                    f"   КФГ: {clinical_group or 'не указана'}",
                    f"   ATC: {', '.join(atc_codes) if atc_codes else 'не указаны'}",
                ]
            )

            if match_type == "drug_to_indication":
                section_names = ("Показания",)
            elif match_type == "drug_to_contraindication":
                section_names = ("Противопоказания",)
            elif match_type == "drug_to_feature":
                section_names = ("Показания", "Противопоказания")
            else:
                section_names = ()

            for section_name in section_names:
                section_text = truncate_text(sections.get(section_name), limit=MATCH_SECTION_TEXT_LIMIT)
                if section_text:
                    context_lines.append(f"   {section_name}: {section_text}")

    if total_selected_docs < 2:
        raise NotFoundError("Для выбранных тем не удалось собрать достаточно препаратов для Match-игры.")

    return "\n".join(context_lines), topic_title


def build_random_descendant_topic_context(
    topic_ids: list[str],
    item_count: int,
    summary_limit: int,
) -> tuple[str, str]:
    """Собирает компактный контекст из одной случайной дочерней темы."""

    documents_by_id = load_structured_documents_index()
    candidate_topic_nodes = resolve_selected_topic_nodes_with_descendants(topic_ids)
    random.shuffle(candidate_topic_nodes)

    for topic_node in candidate_topic_nodes:
        available_doc_ids = [
            doc_id
            for doc_id in topic_node.doc_ids
            if doc_id in documents_by_id
        ]
        if not available_doc_ids:
            continue

        random.shuffle(available_doc_ids)
        doc_budget = min(max(item_count * 2, 2), max(summary_limit, 1), MAX_GAME_DOC_COUNT)
        selected_doc_ids = available_doc_ids[:doc_budget]
        topic_title = " / ".join(topic_node.path)
        context_lines = [
            f"Выбранная случайная тема: {topic_title}",
            f"Указатель: {topic_node.catalog}",
            f"Всего связанных препаратов в теме: {topic_node.doc_count}",
            f"В контекст включено препаратов: {len(selected_doc_ids)}",
            "Препараты и проверенные данные:",
        ]

        for drug_index, doc_id in enumerate(selected_doc_ids, start=1):
            document_record = documents_by_id[doc_id]
            sections = document_record.get("sections") or {}
            drug_name_ru = str(document_record.get("drug_name_ru") or "").strip()
            drug_name_lat = str(document_record.get("drug_name_lat") or "").strip()
            active_substances = get_display_active_substances(document_record)
            atc_codes = document_record.get("atc_codes") or []
            clinical_group = str(document_record.get("clinical_pharmacological_group") or "").strip()
            dosage_form = str(document_record.get("dosage_form") or "").strip()

            context_lines.extend(
                [
                    f"{drug_index}. Препарат: {drug_name_ru or 'Не указан'}",
                    f"   Латинское название: {drug_name_lat or 'не указано'}",
                    f"   Лекарственная форма: {dosage_form or 'не указана'}",
                    f"   КФГ: {clinical_group or 'не указана'}",
                    f"   Активные вещества: {', '.join(active_substances) if active_substances else 'не указаны'}",
                    f"   ATC: {', '.join(atc_codes) if atc_codes else 'не указаны'}",
                ]
            )

            for section_name in (
                "Фармакологическое действие",
                "Показания",
                "Противопоказания",
                "Побочное действие",
                "Применение при беременности и кормлении грудью",
                "Лекарственное взаимодействие",
            ):
                section_text = truncate_text(sections.get(section_name), limit=GAME_SECTION_TEXT_LIMIT)
                if section_text:
                    context_lines.append(f"   {section_name}: {section_text}")

        return "\n".join(context_lines), topic_title

    raise NotFoundError("Для выбранных тем не удалось собрать контекст из дочерних тем.")


def build_random_descendant_topic_context_batch(
    topic_ids: list[str],
    batch_size: int,
    summary_limit: int,
) -> tuple[str, list[str]]:
    """Собирает компактный батч-контекст из нескольких случайных дочерних тем."""

    context_parts: list[str] = []
    topic_titles: list[str] = []
    for item_index in range(batch_size):
        context_text, topic_title = build_random_descendant_topic_context(
            topic_ids=topic_ids,
            item_count=1,
            summary_limit=summary_limit,
        )
        topic_titles.append(topic_title)
        context_parts.append(
            f"Элемент {item_index + 1}. Тема: {topic_title}\n{context_text}"
        )

    return "\n\n".join(context_parts), topic_titles


def build_match_context_for_request(request: MatchRequest) -> tuple[str, str]:
    """Выбирает источник контекста для Match-игры."""

    if request.topic_ids:
        return build_match_context_from_topic_ids(
            topic_ids=request.topic_ids,
            pair_count=request.pair_count,
            summary_limit=request.summary_limit,
            match_type=resolve_match_type(request.match_type, request.feature_name),
        )

    if request.topic_id:
        return build_match_context_from_topic_ids(
            topic_ids=[request.topic_id],
            pair_count=request.pair_count,
            summary_limit=request.summary_limit,
            match_type=resolve_match_type(request.match_type, request.feature_name),
        )

    normalized_topic = request.topic.strip()
    if not normalized_topic:
        raise BadRequestError("Передайте topic_id, topic_ids из /topics/tree или непустое поле topic.")

    context_text, topic_title, _found_drugs, _sources = build_game_context_for_request(
        topic=normalized_topic,
        topic_id=None,
        topic_ids=[],
        embedding_model_name=request.embedding_model,
        context_chunk_limit=request.context_chunks,
        summary_limit=request.summary_limit,
    )
    return context_text, topic_title


def build_topic_ids_game_context(
    topic_ids: list[str],
    summary_limit: int,
) -> tuple[str, str, list[FoundDrugResponse], list[SourceResponse]]:
    """Собирает общий игровой контекст по нескольким выбранным темам из каталога."""

    normalized_topic_ids = [
        topic_id.strip()
        for topic_id in topic_ids
        if topic_id and topic_id.strip()
    ]
    if not normalized_topic_ids:
        raise BadRequestError("Передайте непустой список topic_ids.")

    documents_by_id = load_structured_documents_index()
    useful_sections = [
        "Фармакологическое действие",
        "Показания",
        "Противопоказания",
        "Побочное действие",
        "Применение при беременности и кормлении грудью",
        "Лекарственное взаимодействие",
    ]

    selected_topic_nodes = resolve_selected_topic_nodes(normalized_topic_ids)
    for topic_node in selected_topic_nodes:
        if not topic_node.doc_ids:
            raise NotFoundError(f"У выбранной темы '{topic_node.title}' нет связанных препаратов.")

    selected_topic_nodes = sorted(selected_topic_nodes, key=lambda item: item.doc_count, reverse=True)[:MAX_GAME_TOPIC_COUNT]
    topic_titles = [" / ".join(topic_node.path) for topic_node in selected_topic_nodes]
    visible_topic_titles = topic_titles[:4]
    topic_title = "; ".join(visible_topic_titles)
    if len(topic_titles) > len(visible_topic_titles):
        topic_title += f"; и еще {len(topic_titles) - len(visible_topic_titles)} тем"

    requested_doc_budget = max(summary_limit, 1)
    total_doc_budget = min(requested_doc_budget, MAX_GAME_DOC_COUNT)
    doc_limit_per_topic = max(1, min(total_doc_budget // max(len(selected_topic_nodes), 1), 3))

    context_lines = [
        f"Выбрано тем: {len(selected_topic_nodes)}",
        f"Темы: {topic_title}",
        "Ниже приведен объединенный контекст по выбранным темам.",
    ]
    found_drugs_by_id: dict[str, FoundDrugResponse] = {}
    sources: list[SourceResponse] = []
    total_selected_docs = 0

    for topic_index, topic_node in enumerate(selected_topic_nodes, start=1):
        if total_selected_docs >= total_doc_budget:
            break
        selected_doc_ids = [
            doc_id
            for doc_id in topic_node.doc_ids[:doc_limit_per_topic]
            if doc_id in documents_by_id
        ]
        if not selected_doc_ids:
            raise NotFoundError(
                f"Для выбранной темы '{topic_node.title}' не найдены структурированные карточки препаратов."
            )

        context_lines.extend(
            [
                "",
                f"Тема {topic_index}: {' / '.join(topic_node.path)}",
                f"Указатель: {topic_node.catalog}",
                f"Source page: {topic_node.source_page_path}",
                f"Всего связанных препаратов в теме: {topic_node.doc_count}",
                f"В контекст этой темы включено препаратов: {len(selected_doc_ids)}",
                "Препараты и проверенные данные:",
            ]
        )

        for drug_index, doc_id in enumerate(selected_doc_ids, start=1):
            if total_selected_docs >= total_doc_budget:
                break
            document_record = documents_by_id[doc_id]
            drug_name_ru = str(document_record.get("drug_name_ru") or "").strip()
            drug_name_lat = str(document_record.get("drug_name_lat") or "").strip()
            active_substances = get_display_active_substances(document_record)
            atc_codes = document_record.get("atc_codes") or []
            clinical_group = str(document_record.get("clinical_pharmacological_group") or "").strip()
            dosage_form = str(document_record.get("dosage_form") or "").strip()
            sections = document_record.get("sections") or {}

            if doc_id not in found_drugs_by_id:
                found_drugs_by_id[doc_id] = FoundDrugResponse(
                    doc_id=doc_id,
                    drug_name_ru=drug_name_ru,
                    drug_name_lat=drug_name_lat,
                    score=1.0,
                    match_reasons=[f"selected topic: {topic_node.title}"],
                )
            elif f"selected topic: {topic_node.title}" not in found_drugs_by_id[doc_id].match_reasons:
                found_drugs_by_id[doc_id].match_reasons.append(f"selected topic: {topic_node.title}")

            context_lines.extend(
                [
                    f"{drug_index}. Препарат: {drug_name_ru or 'Не указан'}",
                    f"   Doc ID: {doc_id}",
                    f"   Латинское название: {drug_name_lat or 'не указано'}",
                    f"   Лекарственная форма: {dosage_form or 'не указана'}",
                    f"   КФГ: {clinical_group or 'не указана'}",
                    f"   Активные вещества: {', '.join(active_substances) if active_substances else 'не указаны'}",
                    f"   ATC: {', '.join(atc_codes) if atc_codes else 'не указаны'}",
                ]
            )

            for section_name in useful_sections:
                section_text = truncate_text(sections.get(section_name), limit=GAME_SECTION_TEXT_LIMIT)
                if not section_text:
                    continue
                context_lines.append(f"   {section_name}: {section_text}")
                sources.append(
                    SourceResponse(
                        drug=drug_name_ru,
                        doc_id=doc_id,
                        section=section_name,
                        chunk_id=f"{doc_id}__structured__{section_name.replace(' ', '_')}",
                    )
                )
            total_selected_docs += 1

    return "\n".join(context_lines), topic_title, list(found_drugs_by_id.values()), sources


def build_game_context_for_request(
    topic: str,
    topic_id: Optional[str],
    topic_ids: list[str],
    embedding_model_name: str,
    context_chunk_limit: int,
    summary_limit: int,
) -> tuple[str, str, list[FoundDrugResponse], list[SourceResponse]]:
    """Выбирает источник игрового контекста: точный topic_id или свободный текст."""

    if topic_ids:
        return build_topic_ids_game_context(topic_ids=topic_ids, summary_limit=summary_limit)

    if topic_id:
        topic_tree = get_topic_tree()
        if topic_id in {catalog.id for catalog in topic_tree.catalogs}:
            return build_topic_ids_game_context(topic_ids=[topic_id], summary_limit=summary_limit)
        return build_topic_id_game_context(topic_id=topic_id, summary_limit=summary_limit)

    normalized_topic = topic.strip()
    if not normalized_topic:
        raise BadRequestError("Передайте topic_id из /topics или непустое поле topic.")

    context_text, found_drugs, sources = build_game_context(
        topic=normalized_topic,
        embedding_model_name=embedding_model_name,
        n_results=DEFAULT_QUERY_RESULTS,
        overfetch_factor=DEFAULT_SEARCH_OVERFETCH_FACTOR,
        context_chunk_limit=context_chunk_limit,
        summary_limit=summary_limit,
    )
    return context_text, normalized_topic, found_drugs, sources


def normalize_quiz_questions(raw_questions: Any, expected_count: int) -> list[QuizQuestionResponse]:
    """Проверяет и нормализует вопросы викторины, полученные от модели."""

    if not isinstance(raw_questions, list):
        raise RuntimeError("В JSON-ответе модели отсутствует массив questions.")

    normalized_questions: list[QuizQuestionResponse] = []
    for raw_question in raw_questions[:expected_count]:
        if not isinstance(raw_question, dict):
            continue

        question_text = str(raw_question.get("question", "")).strip()
        options = [
            str(option).strip()
            for option in raw_question.get("options", [])
            if str(option).strip()
        ]
        correct_answer = str(raw_question.get("correct_answer", "")).strip()
        explanation = str(raw_question.get("explanation", "")).strip()

        if not question_text or len(options) < 2 or not correct_answer:
            continue
        if correct_answer not in options:
            options.append(correct_answer)

        normalized_questions.append(
            QuizQuestionResponse(
                question=question_text,
                options=options,
                correct_answer=correct_answer,
                explanation=explanation,
            )
        )

    if not normalized_questions:
        raise RuntimeError("Модель не вернула корректные вопросы для викторины.")

    return normalized_questions


def normalize_flashcards(raw_cards: Any, expected_count: int) -> list[FlashcardResponse]:
    """Проверяет и нормализует карточки, полученные от модели."""

    if not isinstance(raw_cards, list):
        raise RuntimeError("В JSON-ответе модели отсутствует массив cards.")

    normalized_cards: list[FlashcardResponse] = []
    for raw_card in raw_cards[:expected_count]:
        if not isinstance(raw_card, dict):
            continue

        front = str(raw_card.get("front", "")).strip()
        back = str(raw_card.get("back", "")).strip()
        front_title = str(raw_card.get("front_title", "") or "Лекарство").strip()
        back_title = str(raw_card.get("back_title", "") or "Ответ").strip()
        explanation = str(raw_card.get("explanation", "")).strip()
        if not front or not back:
            continue

        normalized_cards.append(
            FlashcardResponse(
                front_title=front_title,
                front=front,
                back_title=back_title,
                back=back,
                explanation=explanation,
            )
        )

    if not normalized_cards:
        raise RuntimeError("Модель не вернула корректные карточки.")

    return normalized_cards


def normalize_match_pairs(raw_pairs: Any, expected_count: int) -> list[MatchPairResponse]:
    """Проверяет и нормализует пары для Match-игры, полученные от модели."""

    if not isinstance(raw_pairs, list):
        raise RuntimeError("В JSON-ответе модели отсутствует массив pairs.")

    normalized_pairs: list[MatchPairResponse] = []
    seen_left: set[str] = set()
    seen_right: set[str] = set()

    for raw_pair in raw_pairs[: max(expected_count * 3, expected_count)]:
        if not isinstance(raw_pair, dict):
            continue

        left = str(raw_pair.get("left", "")).strip()
        right = str(raw_pair.get("right", "")).strip()
        explanation = str(raw_pair.get("explanation", "")).strip()
        if not left or not right:
            continue

        normalized_left = left.casefold()
        normalized_right = right.casefold()
        if normalized_left in seen_left or normalized_right in seen_right:
            continue

        seen_left.add(normalized_left)
        seen_right.add(normalized_right)
        normalized_pairs.append(
            MatchPairResponse(
                pair_id=f"pair_{len(normalized_pairs) + 1}",
                left=left,
                right=right,
                explanation=explanation,
            )
        )

        if len(normalized_pairs) >= expected_count:
            break

    if len(normalized_pairs) < 2:
        raise RuntimeError("Модель не вернула корректные пары для Match-игры.")

    return normalized_pairs


def normalize_match_tasks(raw_tasks: Any, expected_task_count: int, expected_pair_count: int) -> list[MatchTaskResponse]:
    """Проверяет и нормализует наборы карточек для Match-игры, полученные от модели."""

    if not isinstance(raw_tasks, list):
        raise RuntimeError("В JSON-ответе модели отсутствует массив tasks.")

    normalized_tasks: list[MatchTaskResponse] = []
    for raw_task in raw_tasks[:expected_task_count]:
        if not isinstance(raw_task, dict):
            continue

        task_pairs = normalize_match_pairs(
            raw_pairs=raw_task.get("pairs"),
            expected_count=expected_pair_count,
        )
        if len(task_pairs) < expected_pair_count:
            continue

        normalized_tasks.append(
            MatchTaskResponse(
                task_id=f"task_{len(normalized_tasks) + 1}",
                pairs=task_pairs,
            )
        )

    if len(normalized_tasks) < expected_task_count:
        raise RuntimeError("Модель не вернула достаточное количество заданий для Match-игры.")

    return normalized_tasks


def build_match_tasks_from_pairs(raw_pairs: Any, task_count: int, pair_count: int) -> list[MatchTaskResponse]:
    """Строит задания Match-игры из одного плоского списка пар."""

    total_pair_count = task_count * pair_count
    normalized_pairs = normalize_match_pairs(
        raw_pairs=raw_pairs,
        expected_count=total_pair_count,
    )
    if len(normalized_pairs) < total_pair_count:
        raise RuntimeError("Модель вернула недостаточно пар для формирования всех заданий Match-игры.")

    tasks: list[MatchTaskResponse] = []
    pair_index = 0
    for task_number in range(task_count):
        task_pairs: list[MatchPairResponse] = []
        for inner_index in range(pair_count):
            base_pair = normalized_pairs[pair_index]
            task_pairs.append(
                MatchPairResponse(
                    pair_id=f"task_{task_number + 1}_pair_{inner_index + 1}",
                    left=base_pair.left,
                    right=base_pair.right,
                    explanation=base_pair.explanation,
                )
            )
            pair_index += 1
        tasks.append(
            MatchTaskResponse(
                task_id=f"task_{task_number + 1}",
                pairs=task_pairs,
            )
        )

    return tasks


def generate_quiz(request: QuizRequest) -> QuizResponse:
    """Генерирует викторину по выбранной теме из справочника."""

    _embedding_client, chat_client, _collection = get_runtime()
    if request.topic_ids or request.topic_id:
        selected_topic_ids = request.topic_ids or ([request.topic_id] if request.topic_id else [])
        questions: list[QuizQuestionResponse] = []
        topic_titles: list[str] = []
        title = ""

        while len(questions) < request.question_count:
            current_batch_size = min(QUIZ_BATCH_SIZE, request.question_count - len(questions))
            context_text, batch_topic_titles = build_random_descendant_topic_context_batch(
                topic_ids=selected_topic_ids,
                batch_size=current_batch_size,
                summary_limit=request.summary_limit,
            )
            topic_titles.extend(batch_topic_titles)
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Ты создаешь учебную викторину по лекарственному справочнику. "
                        "Для каждого вопроса используй соответствующий элемент контекста с тем же номером. "
                        "Не добавляй медицинские факты вне контекста. "
                        "Верни только валидный JSON без markdown."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Количество вопросов: {current_batch_size}\n"
                        f"Вариантов ответа: {request.options_per_question}\n\n"
                        f"Контексты справочника:\n{context_text}\n\n"
                        "Сформируй JSON строго такого вида:\n"
                        "{\n"
                        '  "title": "короткое название викторины",\n'
                        '  "questions": [\n'
                        "    {\n"
                        '      "question": "текст вопроса",\n'
                        '      "options": ["вариант 1", "вариант 2", "вариант 3", "вариант 4"],\n'
                        '      "correct_answer": "точный текст правильного варианта из options",\n'
                        '      "explanation": "короткое объяснение со ссылкой на данные из контекста"\n'
                        "    }\n"
                        "  ]\n"
                        "}"
                    ),
                },
            ]
            game_json = call_gigachat_json(
                gigachat_client=chat_client,
                chat_model_name=request.chat_model,
                messages=messages,
                answer_max_tokens=request.answer_max_tokens,
            )
            if not title:
                title = str(game_json.get("title") or "").strip()
            questions.extend(
                normalize_quiz_questions(
                    raw_questions=game_json.get("questions"),
                    expected_count=current_batch_size,
                )
            )

        visible_topics = topic_titles[:4]
        response_topic = "; ".join(visible_topics)
        if len(topic_titles) > len(visible_topics):
            response_topic += f"; и еще {len(topic_titles) - len(visible_topics)} тем"
        return QuizResponse(
            game_type="quiz",
            topic=response_topic,
            title=title or f"Викторина: {response_topic}",
            questions=questions[:request.question_count],
        )

    context_text, topic_title, _found_drugs, _sources = build_game_context_for_request(
        topic=request.topic,
        topic_id=request.topic_id,
        topic_ids=request.topic_ids,
        embedding_model_name=request.embedding_model,
        context_chunk_limit=request.context_chunks,
        summary_limit=request.summary_limit,
    )
    messages = [
        {
            "role": "system",
            "content": (
                "Ты создаешь учебную мини-игру по лекарственному справочнику. "
                "Используй только предоставленный контекст. "
                "Не добавляй препараты, противопоказания, показания, дозировки или факты, которых нет в контексте. "
                "Верни только валидный JSON без markdown."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Тема игры: {topic_title}\n"
                f"Количество вопросов: {request.question_count}\n"
                f"Вариантов ответа в каждом вопросе: {request.options_per_question}\n\n"
                f"Контекст справочника:\n{context_text}\n\n"
                "Сформируй JSON строго такого вида:\n"
                "{\n"
                '  "title": "короткое название викторины",\n'
                '  "questions": [\n'
                "    {\n"
                '      "question": "текст вопроса",\n'
                '      "options": ["вариант 1", "вариант 2", "вариант 3", "вариант 4"],\n'
                '      "correct_answer": "точный текст правильного варианта из options",\n'
                '      "explanation": "короткое объяснение со ссылкой на данные из контекста"\n'
                "    }\n"
                "  ]\n"
                "}\n"
                "Сделай вопросы разнообразными: название препарата, действующее вещество, показания, "
                "противопоказания или особенности применения, если эти данные есть в контексте. "
                "Если в контексте есть несколько тем или несколько препаратов, распределяй вопросы между ними. "
                "Не используй один препарат более одного раза, пока можно использовать другие препараты."
            ),
        },
    ]
    game_json = call_gigachat_json(
        gigachat_client=chat_client,
        chat_model_name=request.chat_model,
        messages=messages,
        answer_max_tokens=request.answer_max_tokens,
    )
    return QuizResponse(
        game_type="quiz",
        topic=topic_title,
        title=str(game_json.get("title") or f"Викторина: {topic_title}"),
        questions=normalize_quiz_questions(
            raw_questions=game_json.get("questions"),
            expected_count=request.question_count,
        ),
    )


def generate_flashcards(request: FlashcardsRequest) -> FlashcardsResponse:
    """Генерирует карточки для запоминания по выбранной теме из справочника."""

    _embedding_client, chat_client, _collection = get_runtime()
    if request.topic_ids or request.topic_id:
        selected_topic_ids = request.topic_ids or ([request.topic_id] if request.topic_id else [])
        cards: list[FlashcardResponse] = []
        topic_titles: list[str] = []
        title = ""

        while len(cards) < request.card_count:
            current_batch_size = min(FLASHCARD_BATCH_SIZE, request.card_count - len(cards))
            context_text, batch_topic_titles = build_random_descendant_topic_context_batch(
                topic_ids=selected_topic_ids,
                batch_size=current_batch_size,
                summary_limit=request.summary_limit,
            )
            topic_titles.extend(batch_topic_titles)
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Ты создаешь учебные карточки по лекарственному справочнику. "
                        "Для каждой карточки используй соответствующий элемент контекста с тем же номером. "
                        "Не выдумывай медицинские факты и не добавляй препараты вне контекста. "
                        "Верни только валидный JSON без markdown."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Количество карточек: {current_batch_size}\n\n"
                        f"Контексты справочника:\n{context_text}\n\n"
                        "Сформируй JSON строго такого вида:\n"
                        "{\n"
                        '  "title": "короткое название набора карточек",\n'
                        '  "cards": [\n'
                        "    {\n"
                        '      "front_title": "Лекарство",\n'
                        '      "front": "название препарата",\n'
                        '      "back_title": "тип признака на обратной стороне: Показание, Противопоказание, Действующее вещество, Лекарственная форма или КФГ",\n'
                        '      "back": "краткое значение признака",\n'
                        '      "explanation": "пояснение, почему ответ правильный по контексту"\n'
                        "    }\n"
                        "  ]\n"
                        "}"
                        "\nЛицевая сторона всегда должна быть названием лекарства. "
                        "Обратная сторона должна быть одним конкретным признаком этого лекарства. "
                        "Все значения для пользователя пиши на русском языке."
                    ),
                },
            ]
            game_json = call_gigachat_json(
                gigachat_client=chat_client,
                chat_model_name=request.chat_model,
                messages=messages,
                answer_max_tokens=request.answer_max_tokens,
            )
            if not title:
                title = str(game_json.get("title") or "").strip()
            cards.extend(
                normalize_flashcards(
                    raw_cards=game_json.get("cards"),
                    expected_count=current_batch_size,
                )
            )

        visible_topics = topic_titles[:4]
        response_topic = "; ".join(visible_topics)
        if len(topic_titles) > len(visible_topics):
            response_topic += f"; и еще {len(topic_titles) - len(visible_topics)} тем"
        return FlashcardsResponse(
            game_type="flashcards",
            topic=response_topic,
            title=title or f"Карточки: {response_topic}",
            cards=cards[:request.card_count],
        )

    context_text, topic_title, _found_drugs, _sources = build_game_context_for_request(
        topic=request.topic,
        topic_id=request.topic_id,
        topic_ids=[],
        embedding_model_name=request.embedding_model,
        context_chunk_limit=request.context_chunks,
        summary_limit=request.summary_limit,
    )
    messages = [
        {
            "role": "system",
            "content": (
                "Ты создаешь учебные карточки по лекарственному справочнику. "
                "Используй только предоставленный контекст. "
                "Не выдумывай медицинские факты и не добавляй препараты вне контекста. "
                "Верни только валидный JSON без markdown."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Тема карточек: {topic_title}\n"
                f"Количество карточек: {request.card_count}\n\n"
                f"Контекст справочника:\n{context_text}\n\n"
                "Сформируй JSON строго такого вида:\n"
                "{\n"
                '  "title": "короткое название набора карточек",\n'
                '  "cards": [\n'
                "    {\n"
                '      "front_title": "Лекарство",\n'
                '      "front": "название препарата",\n'
                '      "back_title": "тип признака на обратной стороне: Показание, Противопоказание, Действующее вещество, Лекарственная форма или КФГ",\n'
                '      "back": "краткое значение признака",\n'
                '      "explanation": "пояснение, почему ответ правильный по контексту"\n'
                "    }\n"
                "  ]\n"
                "}\n"
                "Лицевая сторона всегда должна быть названием лекарства. "
                "Обратная сторона должна быть одним конкретным признаком этого лекарства. "
                "Все значения для пользователя пиши на русском языке. "
                "Карточки должны помогать запоминать препараты, вещества, показания, противопоказания "
                "или другие признаки, если они есть в контексте. "
                "Если в контексте есть несколько препаратов, распределяй карточки между разными препаратами. "
                "Не используй один препарат более одного раза, пока можно использовать другие препараты."
            ),
        },
    ]
    game_json = call_gigachat_json(
        gigachat_client=chat_client,
        chat_model_name=request.chat_model,
        messages=messages,
        answer_max_tokens=request.answer_max_tokens,
    )
    return FlashcardsResponse(
        game_type="flashcards",
        topic=topic_title,
        title=str(game_json.get("title") or f"Карточки: {topic_title}"),
        cards=normalize_flashcards(
            raw_cards=game_json.get("cards"),
            expected_count=request.card_count,
        ),
    )


def generate_match_game(request: MatchRequest) -> MatchResponse:
    """Генерирует Match-игру по выбранным темам справочника через LLM."""

    resolved_match_type = resolve_match_type(
        match_type=request.match_type,
        feature_name=request.feature_name,
    )
    left_label, right_label, match_instruction = get_match_type_config(
        match_type=resolved_match_type,
        feature_name=request.feature_name,
    )
    _embedding_client, chat_client, _collection = get_runtime()
    generated_tasks: list[MatchTaskResponse] = []
    response_title = ""
    response_topic_title = ""

    for task_index in range(request.task_count):
        last_error: Optional[Exception] = None
        for _attempt in range(2):
            try:
                context_text, topic_title = build_match_context_for_request(request)
                if not response_topic_title:
                    response_topic_title = topic_title

                messages = [
                    {
                        "role": "system",
                        "content": (
                            "Ты создаешь одно задание Match-игры по лекарственному справочнику. "
                            "Используй только предоставленный контекст. "
                            "Не добавляй факты, препараты, признаки или противопоказания, которых нет в контексте. "
                            "Верни только валидный JSON без markdown."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Тема Match-игры: {topic_title}\n"
                            f"Номер задания: {task_index + 1}\n"
                            f"Количество пар в этом задании: {request.pair_count}\n"
                            f"Левая колонка: {left_label}\n"
                            f"Правая колонка: {right_label}\n"
                            f"Тип сопоставления: {resolved_match_type}\n\n"
                            f"Контекст справочника:\n{context_text}\n\n"
                            f"{match_instruction}\n"
                            "Выбирай разные препараты, если это возможно. "
                            "Не повторяй одинаковые значения слева или справа внутри задания. "
                            "Правые значения формулируй кратко, чтобы их было удобно сопоставлять в интерфейсе. "
                            "Все значения для пользователя пиши на русском языке.\n\n"
                            "Сформируй JSON строго такого вида:\n"
                            "{\n"
                            '  "title": "короткое название Match-игры",\n'
                            '  "pairs": [\n'
                            "    {\n"
                            f'      "left": "значение для колонки {left_label}",\n'
                            f'      "right": "значение для колонки {right_label}",\n'
                            '      "explanation": "краткое пояснение, почему это соответствие верно по контексту"\n'
                            "    }\n"
                            "  ]\n"
                            "}"
                        ),
                    },
                ]

                game_json = call_gigachat_json(
                    gigachat_client=chat_client,
                    chat_model_name=request.chat_model,
                    messages=messages,
                    answer_max_tokens=request.answer_max_tokens,
                )
                if not response_title:
                    response_title = str(game_json.get("title") or "").strip()

                task_pairs = normalize_match_pairs(
                    raw_pairs=game_json.get("pairs"),
                    expected_count=request.pair_count,
                )
                if len(task_pairs) < request.pair_count:
                    raise RuntimeError("Модель вернула недостаточно пар для задания Match-игры.")

                generated_tasks.append(
                    MatchTaskResponse(
                        task_id=f"task_{task_index + 1}",
                        pairs=[
                            MatchPairResponse(
                                pair_id=f"task_{task_index + 1}_pair_{pair_index + 1}",
                                left=pair.left,
                                right=pair.right,
                                explanation=pair.explanation,
                            )
                            for pair_index, pair in enumerate(task_pairs[:request.pair_count])
                        ],
                    )
                )
                break
            except Exception as error:
                last_error = error
        else:
            raise RuntimeError(f"Не удалось сгенерировать Match-задание {task_index + 1}: {last_error}") from last_error

    return MatchResponse(
        game_type="match",
        topic=response_topic_title,
        title=response_title or f"Match: {response_topic_title}",
        match_type=resolved_match_type,
        left_label=left_label,
        right_label=right_label,
        task_count=request.task_count,
        pair_count=request.pair_count,
        tasks=generated_tasks,
    )
