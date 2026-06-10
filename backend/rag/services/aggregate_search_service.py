"""Полнотный структурный поиск по всем карточкам препаратов."""

from __future__ import annotations

import re
from typing import Any, Optional

from ..api_models import (
    AggregateDrugResult,
    AggregateSearchRequest,
    AggregateSearchResponse,
    AskResponse,
)
from ..common import find_entity_matches, load_entity_matches, normalize_search_text, tokenize_feature_query
from ..config import DEFAULT_ENTITY_RELATIONS_PATH
from .runtime import load_structured_documents_index


AGGREGATE_QUERY_MARKERS = (
    "все лекар",
    "все препарат",
    "назови все",
    "покажи все",
    "перечисли все",
    "полный список",
)


def normalize_field_text(value: Any) -> str:
    """Нормализует поле карточки для лексического сравнения."""

    return normalize_search_text(str(value or ""))


def section_text(document_record: dict[str, Any], section_name: str) -> str:
    """Возвращает текст раздела карточки препарата."""

    sections = document_record.get("sections") or {}
    return str(sections.get(section_name) or "").strip()


def contains_all_query_tokens(text: str, query: str) -> bool:
    """Проверяет, что текст содержит все значимые токены пользовательского признака."""

    normalized_text = normalize_field_text(text)
    query_tokens = tokenize_feature_query(query)
    if not query_tokens:
        return False

    return all(token in normalized_text for token in query_tokens)


def extract_after_patterns(query: str, patterns: list[str]) -> str:
    """Извлекает короткую фразу после одного из regex-паттернов."""

    normalized_query = normalize_search_text(query)
    for pattern in patterns:
        match = re.search(pattern, normalized_query)
        if not match:
            continue
        extracted_text = match.group(1).strip()
        extracted_text = re.split(
            r"\s+(?:и\s+их|и\s+не|без|не\s+имеющ|с\s+признак|их\s+признак)",
            extracted_text,
            maxsplit=1,
        )[0].strip()
        return extracted_text
    return ""


def extract_exclude_contraindication(query: str) -> str:
    """Извлекает противопоказание, которое нужно исключить."""

    normalized_query = normalize_search_text(query)
    patterns = [
        r"(?:не\s+имеющ\w*|без)\s+(?:таких\s+то\s+)?противопоказан\w*\s+(.+)$",
        r"(?:не\s+имеющ\w*|без)\s+(.+?)\s+(?:в\s+)?противопоказан\w*",
    ]
    for pattern in patterns:
        match = re.search(pattern, normalized_query)
        if match:
            return match.group(1).strip()
    return ""


def extract_structured_filters(request: AggregateSearchRequest) -> dict[str, str]:
    """Извлекает фильтры из явных полей и естественно-языкового query."""

    query = request.query
    entity_matches = find_entity_matches(
        query=query,
        entity_matches=load_entity_matches(DEFAULT_ENTITY_RELATIONS_PATH),
    )

    active_entity = next((item for item in entity_matches if item.entity_type == "active_substance"), None)
    nosology_entity = next((item for item in entity_matches if item.entity_type == "nosology"), None)

    active_substance = request.active_substance.strip()
    if not active_substance and active_entity is not None:
        active_substance = active_entity.entity_name or active_entity.entity_name_lat
    if not active_substance:
        active_substance = extract_after_patterns(
            query,
            [
                r"действующ\w*\s+веществ\w*\s+([0-9a-zа-я\-\s]+)",
                r"активн\w*\s+веществ\w*\s+([0-9a-zа-я\-\s]+)",
                r"\bс\s+веществ\w*\s+([0-9a-zа-я\-\s]+)",
            ],
        )

    indication = request.indication.strip()
    if not indication and nosology_entity is not None:
        indication = nosology_entity.entity_name
    if not indication:
        indication = extract_after_patterns(
            query,
            [
                r"(?:для\s+лечени\w*|показан\w*\s+для\s+лечени\w*)\s+(.+)",
                r"\bпри\s+([0-9a-zа-я\-\s]+)",
            ],
        )

    exclude_contraindication = request.exclude_contraindication.strip()
    if not exclude_contraindication:
        exclude_contraindication = extract_exclude_contraindication(query)

    return {
        "active_substance": active_substance,
        "indication": indication,
        "exclude_contraindication": exclude_contraindication,
    }


def resolve_filter_entities(query: str) -> tuple[set[str], set[str]]:
    """Возвращает doc_id, найденные через entity_relations для вещества и нозологии."""

    entity_matches = find_entity_matches(
        query=query,
        entity_matches=load_entity_matches(DEFAULT_ENTITY_RELATIONS_PATH),
    )
    active_doc_ids = {
        doc_id
        for entity_match in entity_matches
        if entity_match.entity_type == "active_substance"
        for doc_id in entity_match.candidate_doc_ids
    }
    nosology_doc_ids = {
        doc_id
        for entity_match in entity_matches
        if entity_match.entity_type == "nosology"
        for doc_id in entity_match.candidate_doc_ids
    }
    return active_doc_ids, nosology_doc_ids


def matches_active_substance(document_record: dict[str, Any], active_substance: str) -> bool:
    """Проверяет совпадение препарата с действующим веществом."""

    if not active_substance:
        return True

    searchable_parts = [
        document_record.get("active_substance_raw"),
        " ".join(document_record.get("active_substances") or []),
    ]
    return contains_all_query_tokens(" ".join(str(part or "") for part in searchable_parts), active_substance)


def matches_indication(document_record: dict[str, Any], indication: str) -> bool:
    """Проверяет совпадение препарата с показанием или заболеванием."""

    if not indication:
        return True

    indication_text = section_text(document_record, "Показания")
    return contains_all_query_tokens(indication_text, indication)


def has_excluded_contraindication(document_record: dict[str, Any], excluded_contraindication: str) -> bool:
    """Проверяет, содержит ли препарат противопоказание, которое нужно исключить."""

    if not excluded_contraindication:
        return False

    contraindication_text = section_text(document_record, "Противопоказания")
    return contains_all_query_tokens(contraindication_text, excluded_contraindication)


def is_aggregate_query(query: str) -> bool:
    """Определяет, похож ли query на полнотный запрос по всем препаратам."""

    normalized_query = normalize_search_text(query)
    if not normalized_query:
        return False

    has_marker = any(marker in normalized_query for marker in AGGREGATE_QUERY_MARKERS)
    has_filter = any(
        marker in normalized_query
        for marker in (
            "действующ",
            "активн",
            "веществ",
            "показан",
            "для лечения",
            "не имеющ",
            "противопоказ",
        )
    )
    return has_marker and has_filter


def execute_aggregate_search(request: AggregateSearchRequest) -> AggregateSearchResponse:
    """Выполняет полнотный структурный поиск без top-k ограничения."""

    filters = extract_structured_filters(request)
    active_entity_doc_ids, nosology_entity_doc_ids = resolve_filter_entities(request.query)
    documents_by_id = load_structured_documents_index()
    results: list[AggregateDrugResult] = []

    for document_record in documents_by_id.values():
        matched_reasons: list[str] = []
        doc_id = str(document_record.get("doc_id") or "")

        if filters["active_substance"]:
            if active_entity_doc_ids:
                if doc_id not in active_entity_doc_ids:
                    continue
                matched_reasons.append(f"действующее вещество: {filters['active_substance']}")
            else:
                if not matches_active_substance(document_record, filters["active_substance"]):
                    continue
                matched_reasons.append(f"действующее вещество: {filters['active_substance']}")

        if filters["indication"]:
            if nosology_entity_doc_ids:
                if doc_id not in nosology_entity_doc_ids:
                    continue
                matched_reasons.append(f"нозология: {filters['indication']}")
            else:
                if not matches_indication(document_record, filters["indication"]):
                    continue
                matched_reasons.append(f"показание: {filters['indication']}")

        if has_excluded_contraindication(document_record, filters["exclude_contraindication"]):
            continue
        if filters["exclude_contraindication"]:
            matched_reasons.append(f"исключено противопоказание: {filters['exclude_contraindication']}")

        results.append(
            AggregateDrugResult(
                doc_id=doc_id,
                drug_name_ru=str(document_record.get("drug_name_ru") or ""),
                drug_name_lat=str(document_record.get("drug_name_lat") or ""),
                dosage_form=str(document_record.get("dosage_form") or ""),
                clinical_pharmacological_group=str(document_record.get("clinical_pharmacological_group") or ""),
                active_substances=[str(item) for item in document_record.get("active_substances") or []],
                atc_codes=[str(item) for item in document_record.get("atc_codes") or []],
                indications=section_text(document_record, "Показания"),
                contraindications=section_text(document_record, "Противопоказания"),
                matched_reasons=matched_reasons,
            )
        )

    sorted_results = sorted(
        results,
        key=lambda item: (item.drug_name_ru, item.doc_id),
    )

    return AggregateSearchResponse(
        query=request.query,
        filters=filters,
        total_found=len(sorted_results),
        results=sorted_results[: request.limit],
    )


def format_aggregate_answer(response: AggregateSearchResponse) -> str:
    """Формирует человекочитаемый ответ для /ask поверх structured search."""

    if response.total_found == 0:
        return "По структурированным данным препараты с такими условиями не найдены."

    filters_text = ", ".join(
        f"{name}: {value}"
        for name, value in response.filters.items()
        if value
    ) or "без явных фильтров"
    lines = [
        "Выполнен полнотный структурный поиск по всем карточкам препаратов, без top-k ограничения.",
        f"Фильтры: {filters_text}.",
        f"Найдено препаратов: {response.total_found}.",
        "",
    ]

    for index, result in enumerate(response.results, start=1):
        lines.extend(
            [
                f"{index}. {result.drug_name_ru} ({result.doc_id})",
                f"   Действующие вещества: {', '.join(result.active_substances) if result.active_substances else 'не указаны'}",
                f"   КФГ: {result.clinical_pharmacological_group or 'не указана'}",
                f"   Лекарственная форма: {result.dosage_form or 'не указана'}",
                f"   Показания: {result.indications or 'не указаны'}",
                f"   Противопоказания: {result.contraindications or 'не указаны'}",
            ]
        )

    if response.total_found > len(response.results):
        lines.append(f"Показано {len(response.results)} из {response.total_found}; увеличьте limit для полного JSON-списка.")

    return "\n".join(lines)


def try_execute_aggregate_ask(query: str, limit: int = 200) -> Optional[AskResponse]:
    """Автоматически обрабатывает aggregate-запросы внутри /ask."""

    if not is_aggregate_query(query):
        return None

    aggregate_response = execute_aggregate_search(
        AggregateSearchRequest(
            query=query,
            limit=limit,
        )
    )
    return AskResponse(
        query=query,
        answer=format_aggregate_answer(aggregate_response),
        matched_entities=[],
        matched_drug_documents=[],
        section_hints=[],
        sources=[],
        validation=None,
    )
