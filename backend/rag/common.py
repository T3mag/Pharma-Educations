"""Общие вспомогательные функции для поиска, нормализации и индексации."""

from __future__ import annotations

import difflib
import json
import re
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional

from .config import (
    CORE_SECTION_NAMES,
    FEATURE_QUERY_VARIANTS,
    QUERY_SECTION_HINT_PATTERNS,
    SEARCH_STOPWORDS,
    SERVICE_SECTION_NAMES,
)
from .models import (
    DrugCatalogEntry,
    DrugCatalogMatch,
    DrugDocumentEntry,
    DrugDocumentMatch,
    EntityMatch,
    FindAllBundle,
)


def load_jsonl_records(input_path: Path, limit: Optional[int] = None) -> Iterator[dict[str, Any]]:
    """Читает JSONL-файл и возвращает записи по одной."""

    with input_path.open("r", encoding="utf-8") as input_stream:
        for line_index, line in enumerate(input_stream, start=1):
            if limit is not None and line_index > limit:
                break

            record = json.loads(line)
            yield record


def normalize_scalar_text(value: Any) -> str:
    """Приводит значение metadata к чистой строке для надежного хранения в ChromaDB."""

    if value is None:
        return ""

    text_value = str(value).strip()

    return text_value


def normalize_string_list(values: Any) -> list[str]:
    """Приводит входное значение к списку непустых строк без дубликатов."""

    if not isinstance(values, list):
        return []

    normalized_values: list[str] = []

    for raw_value in values:
        normalized_value = normalize_scalar_text(raw_value)
        if not normalized_value:
            continue
        if normalized_value in normalized_values:
            continue
        normalized_values.append(normalized_value)

    return normalized_values


def normalize_search_text(value: Any) -> str:
    """Нормализует текст для поиска: приводит к нижнему регистру, схлопывает пробелы и заменяет ё на е."""

    raw_text = normalize_scalar_text(value)
    if not raw_text:
        return ""

    lowered_text = raw_text.lower()

    normalized_yo_text = lowered_text.replace("ё", "е")

    collapsed_text = " ".join(normalized_yo_text.split())

    return collapsed_text


def normalize_drug_name_lookup_text(value: Any) -> str:
    """Нормализует торговое название препарата для устойчивого lookup по названию."""

    normalized_text = normalize_search_text(value)
    if not normalized_text:
        return ""

    without_trademark_text = (
        normalized_text
        .replace("®", " ")
        .replace("™", " ")
        .replace("«", " ")
        .replace("»", " ")
    )

    collapsed_text = " ".join(without_trademark_text.split())

    return collapsed_text


def build_query_fuzzy_fragments(normalized_query: str) -> list[str]:
    """Строит короткие фрагменты запроса для fuzzy-сравнения с названиями препаратов."""

    if not normalized_query:
        return []

    query_tokens = normalized_query.split()
    if not query_tokens:
        return []

    max_fragment_length = min(4, len(query_tokens))

    fragments: list[str] = []

    for start_index in range(len(query_tokens)):
        for fragment_length in range(1, max_fragment_length + 1):
            end_index = start_index + fragment_length
            if end_index > len(query_tokens):
                break

            fragment_text = " ".join(query_tokens[start_index:end_index]).strip()
            if len(fragment_text) < 4:
                continue
            if fragment_text in fragments:
                continue
            fragments.append(fragment_text)

    return fragments


def calculate_fuzzy_name_similarity(
    query_fragment: str,
    candidate_variant: str,
) -> float:
    """Считает грубую similarity между фрагментом запроса и названием препарата."""

    normalized_query_fragment = normalize_drug_name_lookup_text(query_fragment)

    normalized_candidate_variant = normalize_drug_name_lookup_text(candidate_variant)

    if not normalized_query_fragment or not normalized_candidate_variant:
        return 0.0

    fragment_token_count = len(normalized_query_fragment.split())

    candidate_token_count = len(normalized_candidate_variant.split())

    if abs(fragment_token_count - candidate_token_count) > 1:
        return 0.0

    if normalized_query_fragment[0] != normalized_candidate_variant[0]:
        return 0.0

    if (
        len(normalized_query_fragment) >= 5
        and len(normalized_candidate_variant) >= 5
        and normalized_query_fragment[:2] != normalized_candidate_variant[:2]
    ):
        return 0.0

    similarity_ratio = difflib.SequenceMatcher(
        None,
        normalized_query_fragment,
        normalized_candidate_variant,
    ).ratio()

    return similarity_ratio


def build_entity_match_pattern(entity_text: str) -> Optional[re.Pattern[str]]:
    """Создает регулярное выражение для безопасного поиска сущности внутри смешанного запроса."""

    normalized_entity_text = normalize_search_text(entity_text)
    if len(normalized_entity_text) < 3:
        return None

    escaped_entity_text = re.escape(normalized_entity_text)

    pattern_text = rf"(?<![0-9a-zа-я]){escaped_entity_text}(?![0-9a-zа-я])"

    entity_pattern = re.compile(pattern_text)

    return entity_pattern


def build_drug_document_entries(structured_documents_path: Path) -> list[DrugDocumentEntry]:
    """Загружает структурированные карточки препаратов и строит индекс по торговым названиям."""

    drug_document_entries: list[DrugDocumentEntry] = []

    for document_record in load_jsonl_records(input_path=structured_documents_path):
        doc_id = normalize_scalar_text(document_record.get("doc_id"))

        drug_name_ru = normalize_scalar_text(document_record.get("drug_name_ru"))

        drug_name_lat = normalize_scalar_text(document_record.get("drug_name_lat"))

        normalized_name_ru = normalize_drug_name_lookup_text(drug_name_ru)

        normalized_name_lat = normalize_drug_name_lookup_text(drug_name_lat)

        if not doc_id:
            continue
        if not normalized_name_ru and not normalized_name_lat:
            continue

        drug_document_entries.append(
            DrugDocumentEntry(
                doc_id=doc_id,
                drug_name_ru=drug_name_ru,
                drug_name_lat=drug_name_lat,
                normalized_name_ru=normalized_name_ru,
                normalized_name_lat=normalized_name_lat,
            )
        )

    return drug_document_entries


def load_entity_matches(entity_relations_path: Path) -> list[EntityMatch]:
    """Агрегирует entity_relations.jsonl в список уникальных сущностей со связанными doc_id."""

    aggregated_entities: dict[tuple[str, str, str, str], dict[str, Any]] = {}

    for relation_record in load_jsonl_records(input_path=entity_relations_path):
        entity_key = (
            normalize_scalar_text(relation_record.get("entity_type")),
            normalize_scalar_text(relation_record.get("entity_code")),
            normalize_scalar_text(relation_record.get("entity_name")),
            normalize_scalar_text(relation_record.get("entity_name_lat")),
        )

        if entity_key not in aggregated_entities:
            aggregated_entities[entity_key] = {
                "entity_type": entity_key[0],
                "entity_code": entity_key[1],
                "entity_name": entity_key[2],
                "entity_name_lat": entity_key[3],
                "candidate_doc_ids": [],
            }

        aggregated_entity = aggregated_entities[entity_key]

        target_doc_id = normalize_scalar_text(relation_record.get("target_doc_id"))
        if target_doc_id and target_doc_id not in aggregated_entity["candidate_doc_ids"]:
            aggregated_entity["candidate_doc_ids"].append(target_doc_id)

    entity_matches = [
        EntityMatch(
            entity_type=aggregated_entity["entity_type"],
            entity_code=aggregated_entity["entity_code"],
            entity_name=aggregated_entity["entity_name"],
            entity_name_lat=aggregated_entity["entity_name_lat"],
            source_query_fragment="",
            candidate_doc_ids=aggregated_entity["candidate_doc_ids"],
        )
        for aggregated_entity in aggregated_entities.values()
    ]

    return entity_matches


def find_entity_matches(query: str, entity_matches: list[EntityMatch]) -> list[EntityMatch]:
    """Ищет в запросе точные и встроенные совпадения с сущностями справочника."""

    normalized_query = normalize_search_text(query)
    if not normalized_query:
        return []

    exact_matches: list[EntityMatch] = []

    embedded_matches: list[EntityMatch] = []

    for entity_match in entity_matches:
        candidate_variants = [
            normalize_search_text(entity_match.entity_code),
            normalize_search_text(entity_match.entity_name),
            normalize_search_text(entity_match.entity_name_lat),
        ]

        candidate_variants = [
            candidate_variant
            for candidate_variant in dict.fromkeys(candidate_variants)
            if candidate_variant
        ]

        exact_variant = next(
            (
                candidate_variant
                for candidate_variant in candidate_variants
                if candidate_variant == normalized_query
            ),
            "",
        )

        if exact_variant:
            exact_matches.append(
                EntityMatch(
                    entity_type=entity_match.entity_type,
                    entity_code=entity_match.entity_code,
                    entity_name=entity_match.entity_name,
                    entity_name_lat=entity_match.entity_name_lat,
                    source_query_fragment=exact_variant,
                    candidate_doc_ids=entity_match.candidate_doc_ids,
                )
            )
            continue

        matched_fragment = ""

        for candidate_variant in candidate_variants:
            entity_pattern = build_entity_match_pattern(candidate_variant)
            if entity_pattern is None:
                continue
            if entity_pattern.search(normalized_query):
                matched_fragment = candidate_variant
                break

        if matched_fragment:
            embedded_matches.append(
                EntityMatch(
                    entity_type=entity_match.entity_type,
                    entity_code=entity_match.entity_code,
                    entity_name=entity_match.entity_name,
                    entity_name_lat=entity_match.entity_name_lat,
                    source_query_fragment=matched_fragment,
                    candidate_doc_ids=entity_match.candidate_doc_ids,
                )
            )

    if exact_matches:
        sorted_exact_matches = sorted(
            exact_matches,
            key=lambda item: len(item.source_query_fragment),
            reverse=True,
        )
        return sorted_exact_matches

    sorted_embedded_matches = sorted(
        embedded_matches,
        key=lambda item: len(item.source_query_fragment),
        reverse=True,
    )

    return sorted_embedded_matches


def find_drug_document_matches(
    query: str,
    drug_document_entries: list[DrugDocumentEntry],
) -> list[DrugDocumentMatch]:
    """Ищет в запросе точные, встроенные и fuzzy-совпадения с торговыми названиями препаратов."""

    normalized_query = normalize_drug_name_lookup_text(query)
    if not normalized_query:
        return []

    exact_matches: list[DrugDocumentMatch] = []

    embedded_matches: list[DrugDocumentMatch] = []

    fuzzy_candidates: list[tuple[float, DrugDocumentMatch]] = []

    query_fuzzy_fragments = build_query_fuzzy_fragments(normalized_query)

    for drug_document_entry in drug_document_entries:
        candidate_variants = [
            drug_document_entry.normalized_name_ru,
            drug_document_entry.normalized_name_lat,
        ]

        candidate_variants = [
            candidate_variant
            for candidate_variant in dict.fromkeys(candidate_variants)
            if candidate_variant
        ]

        exact_variant = next(
            (
                candidate_variant
                for candidate_variant in candidate_variants
                if candidate_variant == normalized_query
            ),
            "",
        )

        if exact_variant:
            exact_matches.append(
                DrugDocumentMatch(
                    doc_id=drug_document_entry.doc_id,
                    drug_name_ru=drug_document_entry.drug_name_ru,
                    drug_name_lat=drug_document_entry.drug_name_lat,
                    source_query_fragment=exact_variant,
                )
            )
            continue

        matched_fragment = ""

        for candidate_variant in candidate_variants:
            drug_pattern = build_entity_match_pattern(candidate_variant)
            if drug_pattern is None:
                continue
            if drug_pattern.search(normalized_query):
                matched_fragment = candidate_variant
                break

        if matched_fragment:
            embedded_matches.append(
                DrugDocumentMatch(
                    doc_id=drug_document_entry.doc_id,
                    drug_name_ru=drug_document_entry.drug_name_ru,
                    drug_name_lat=drug_document_entry.drug_name_lat,
                    source_query_fragment=matched_fragment,
                )
            )
            continue

        best_fuzzy_fragment = ""

        best_fuzzy_score = 0.0

        for candidate_variant in candidate_variants:
            for query_fuzzy_fragment in query_fuzzy_fragments:
                fuzzy_score = calculate_fuzzy_name_similarity(
                    query_fragment=query_fuzzy_fragment,
                    candidate_variant=candidate_variant,
                )
                if fuzzy_score <= best_fuzzy_score:
                    continue
                best_fuzzy_score = fuzzy_score
                best_fuzzy_fragment = query_fuzzy_fragment

        if best_fuzzy_score >= 0.83 and best_fuzzy_fragment:
            fuzzy_candidates.append(
                (
                    best_fuzzy_score,
                    DrugDocumentMatch(
                        doc_id=drug_document_entry.doc_id,
                        drug_name_ru=drug_document_entry.drug_name_ru,
                        drug_name_lat=drug_document_entry.drug_name_lat,
                        source_query_fragment=best_fuzzy_fragment,
                    ),
                )
            )

    if exact_matches:
        sorted_exact_matches = sorted(
            exact_matches,
            key=lambda item: len(item.source_query_fragment),
            reverse=True,
        )
        return sorted_exact_matches

    sorted_embedded_matches = sorted(
        embedded_matches,
        key=lambda item: len(item.source_query_fragment),
        reverse=True,
    )

    if sorted_embedded_matches:
        return sorted_embedded_matches

    if fuzzy_candidates:
        best_fuzzy_score = max(fuzzy_candidate[0] for fuzzy_candidate in fuzzy_candidates)

        filtered_fuzzy_matches = [
            fuzzy_match
            for fuzzy_score, fuzzy_match in fuzzy_candidates
            if fuzzy_score >= best_fuzzy_score - 0.02
        ]

        sorted_fuzzy_matches = sorted(
            filtered_fuzzy_matches,
            key=lambda item: len(item.source_query_fragment),
            reverse=True,
        )

        return sorted_fuzzy_matches

    return []


def collect_candidate_doc_ids(matched_entities: list[EntityMatch]) -> list[str]:
    """Объединяет doc_id из найденных сущностей в один список без дубликатов."""

    candidate_doc_ids: list[str] = []

    for matched_entity in matched_entities:
        for candidate_doc_id in matched_entity.candidate_doc_ids:
            if candidate_doc_id not in candidate_doc_ids:
                candidate_doc_ids.append(candidate_doc_id)

    return candidate_doc_ids


def collect_drug_document_ids(matched_drug_documents: list[DrugDocumentMatch]) -> list[str]:
    """Собирает уникальные doc_id из найденных по названию карточек препаратов."""

    candidate_doc_ids: list[str] = []

    for matched_drug_document in matched_drug_documents:
        if matched_drug_document.doc_id and matched_drug_document.doc_id not in candidate_doc_ids:
            candidate_doc_ids.append(matched_drug_document.doc_id)

    return candidate_doc_ids


def build_search_scope_doc_ids(
    matched_entities: list[EntityMatch],
    matched_drug_documents: list[DrugDocumentMatch],
) -> list[str]:
    """Определяет итоговое множество документов для constrained retrieval."""

    drug_document_ids = collect_drug_document_ids(matched_drug_documents)
    if drug_document_ids:
        return drug_document_ids

    entity_document_ids = collect_candidate_doc_ids(matched_entities)

    return entity_document_ids


def tokenize_feature_query(query: str) -> list[str]:
    """Разбивает запрос на значимые токены для полнотного поиска по признакам."""

    normalized_query = normalize_search_text(query)

    raw_tokens = re.findall(r"[0-9a-zа-я]+", normalized_query)

    feature_tokens: list[str] = []

    for raw_token in raw_tokens:
        if len(raw_token) < 3:
            continue
        if raw_token in SEARCH_STOPWORDS:
            continue
        if raw_token not in feature_tokens:
            feature_tokens.append(raw_token)

    return feature_tokens


def is_likely_unknown_single_drug_query(
    query: str,
    matched_entities: list[EntityMatch],
    matched_drug_documents: list[DrugDocumentMatch],
    section_hints: list[str],
) -> bool:
    """Определяет, похож ли запрос на вопрос про один препарат, который не был распознан lookup-слоем."""

    if matched_entities or matched_drug_documents:
        return False

    query_tokens = tokenize_feature_query(query)
    if not query_tokens:
        return False

    non_section_tokens: list[str] = []

    for query_token in query_tokens:
        token_looks_like_section = any(
            query_section_hint_pattern.search(query_token)
            for query_section_hint_pattern, _ in QUERY_SECTION_HINT_PATTERNS
        )
        if token_looks_like_section:
            continue
        if query_token in {"все", "весь", "всех", "полный", "справочник", "их"}:
            continue
        non_section_tokens.append(query_token)

    if len(non_section_tokens) != 1:
        return False

    main_token = non_section_tokens[0]

    if main_token in FEATURE_QUERY_VARIANTS:
        return False

    category_variants = {
        normalize_search_text(category_variant)
        for feature_query_variant, synonym_variants in FEATURE_QUERY_VARIANTS.items()
        for category_variant in [feature_query_variant, *synonym_variants]
        if normalize_search_text(category_variant)
    }

    if main_token in category_variants:
        return False

    if any(main_token.startswith(category_variant) for category_variant in category_variants):
        return False

    if len(main_token) < 5:
        return False

    if section_hints:
        return True

    normalized_query = normalize_search_text(query)

    return len(normalized_query.split()) <= 3


def build_query_token_variants(query_token: str) -> list[str]:
    """Строит варианты одного токена запроса для более устойчивого лексического совпадения."""

    normalized_token = normalize_search_text(query_token)
    if not normalized_token:
        return []

    token_variants: list[str] = [normalized_token]

    for synonym_variant in FEATURE_QUERY_VARIANTS.get(normalized_token, []):
        if synonym_variant not in token_variants:
            token_variants.append(synonym_variant)

    if len(normalized_token) >= 8:
        prefix_variant = normalized_token[:10]
        if prefix_variant not in token_variants:
            token_variants.append(prefix_variant)

    if len(normalized_token) >= 7:
        trimmed_variant = normalized_token[:-2]
        if trimmed_variant not in token_variants:
            token_variants.append(trimmed_variant)

    return token_variants


def build_drug_catalog_entries(structured_documents_path: Path) -> list[DrugCatalogEntry]:
    """Строит документный каталог препаратов для полнотного поиска по признакам."""

    drug_catalog_entries: list[DrugCatalogEntry] = []

    for document_record in load_jsonl_records(input_path=structured_documents_path):
        doc_id = normalize_scalar_text(document_record.get("doc_id"))

        drug_name_ru = normalize_scalar_text(document_record.get("drug_name_ru"))

        drug_name_lat = normalize_scalar_text(document_record.get("drug_name_lat"))

        normalized_name_ru = normalize_drug_name_lookup_text(drug_name_ru)

        normalized_name_lat = normalize_drug_name_lookup_text(drug_name_lat)

        atc_codes = normalize_string_list(document_record.get("atc_codes"))

        active_substances = normalize_string_list(document_record.get("active_substances"))

        sections = document_record.get("sections") or {}

        searchable_parts = [
            drug_name_ru,
            drug_name_lat,
            normalize_scalar_text(document_record.get("clinical_pharmacological_group")),
            normalize_scalar_text(document_record.get("dosage_form")),
            normalize_scalar_text(document_record.get("active_substance_raw")),
            normalize_scalar_text(document_record.get("composition_and_packaging")),
            " ".join(active_substances),
            " ".join(atc_codes),
        ]

        for section_name, section_text in sections.items():
            searchable_parts.append(normalize_scalar_text(section_name))
            searchable_parts.append(normalize_scalar_text(section_text))

        searchable_text = normalize_search_text(" ".join(part for part in searchable_parts if part))

        if not doc_id:
            continue
        if not searchable_text:
            continue

        drug_catalog_entries.append(
            DrugCatalogEntry(
                doc_id=doc_id,
                drug_name_ru=drug_name_ru,
                drug_name_lat=drug_name_lat,
                normalized_name_ru=normalized_name_ru,
                normalized_name_lat=normalized_name_lat,
                atc_codes=atc_codes,
                active_substances=active_substances,
                searchable_text=searchable_text,
            )
        )

    return drug_catalog_entries


def build_drug_catalog_map(drug_catalog_entries: list[DrugCatalogEntry]) -> dict[str, DrugCatalogEntry]:
    """Строит словарь карточек препаратов по doc_id для быстрого доступа."""

    drug_catalog_map = {
        drug_catalog_entry.doc_id: drug_catalog_entry
        for drug_catalog_entry in drug_catalog_entries
        if drug_catalog_entry.doc_id
    }

    return drug_catalog_map


def match_drug_catalog_entries(
    query: str,
    drug_catalog_entries: list[DrugCatalogEntry],
    matched_entities: list[EntityMatch],
    matched_drug_documents: list[DrugDocumentMatch],
) -> list[DrugCatalogMatch]:
    """Находит все препараты, подходящие по структурным и текстовым признакам запроса."""

    drug_catalog_map = build_drug_catalog_map(drug_catalog_entries)

    candidate_doc_ids = build_search_scope_doc_ids(
        matched_entities=matched_entities,
        matched_drug_documents=matched_drug_documents,
    )

    catalog_matches: list[DrugCatalogMatch] = []

    if candidate_doc_ids:
        for candidate_doc_id in candidate_doc_ids:
            drug_catalog_entry = drug_catalog_map.get(candidate_doc_id)
            if drug_catalog_entry is None:
                continue

            match_reasons = []
            if matched_drug_documents and candidate_doc_id in {item.doc_id for item in matched_drug_documents}:
                match_reasons.append("точное совпадение по торговому названию")
            if matched_entities and candidate_doc_id in {doc_id for item in matched_entities for doc_id in item.candidate_doc_ids}:
                match_reasons.append("совпадение по структурной сущности")

            catalog_matches.append(
                DrugCatalogMatch(
                    doc_id=drug_catalog_entry.doc_id,
                    drug_name_ru=drug_catalog_entry.drug_name_ru,
                    drug_name_lat=drug_catalog_entry.drug_name_lat,
                    score=100.0,
                    match_reasons=match_reasons or ["структурное совпадение"],
                )
            )

        sorted_catalog_matches = sorted(
            catalog_matches,
            key=lambda item: (-item.score, item.drug_name_ru, item.doc_id),
        )
        return sorted_catalog_matches

    query_tokens = tokenize_feature_query(query)

    query_token_variants_map = {
        query_token: build_query_token_variants(query_token)
        for query_token in query_tokens
    }

    normalized_query = normalize_search_text(query)

    for drug_catalog_entry in drug_catalog_entries:
        score = 0.0

        match_reasons: list[str] = []

        if normalized_query and normalized_query in drug_catalog_entry.searchable_text:
            score += 20.0
            match_reasons.append("совпадение по полной фразе")

        matched_all_tokens = True

        for query_token, token_variants in query_token_variants_map.items():
            matched_token = any(
                token_variant and token_variant in drug_catalog_entry.searchable_text
                for token_variant in token_variants
            )

            if matched_token:
                score += 10.0
                match_reasons.append(f"совпадение по признаку '{query_token}'")
            else:
                matched_all_tokens = False
                break

        if query_tokens and not matched_all_tokens:
            continue

        if score <= 0.0:
            continue

        catalog_matches.append(
            DrugCatalogMatch(
                doc_id=drug_catalog_entry.doc_id,
                drug_name_ru=drug_catalog_entry.drug_name_ru,
                drug_name_lat=drug_catalog_entry.drug_name_lat,
                score=score,
                match_reasons=match_reasons,
            )
        )

    sorted_catalog_matches = sorted(
        catalog_matches,
        key=lambda item: (-item.score, item.drug_name_ru, item.doc_id),
    )

    return sorted_catalog_matches


def run_find_all_retrieval(
    query: str,
    entity_relations_path: Path,
    structured_documents_path: Path,
) -> FindAllBundle:
    """Выполняет полнотный поиск препаратов по признакам и возвращает все промежуточные результаты."""

    loaded_entity_matches = load_entity_matches(entity_relations_path)

    drug_document_entries = build_drug_document_entries(structured_documents_path)

    matched_entities = find_entity_matches(
        query=query,
        entity_matches=loaded_entity_matches,
    )

    matched_drug_documents = find_drug_document_matches(
        query=query,
        drug_document_entries=drug_document_entries,
    )

    drug_catalog_entries = build_drug_catalog_entries(structured_documents_path)

    catalog_matches = match_drug_catalog_entries(
        query=query,
        drug_catalog_entries=drug_catalog_entries,
        matched_entities=matched_entities,
        matched_drug_documents=matched_drug_documents,
    )

    find_all_bundle = FindAllBundle(
        matched_entities=matched_entities,
        matched_drug_documents=matched_drug_documents,
        catalog_matches=catalog_matches,
    )

    return find_all_bundle


def infer_section_hints(query: str) -> list[str]:
    """Извлекает из запроса желаемые разделы инструкции по простым эвристикам."""

    normalized_query = normalize_search_text(query)

    section_hints: list[str] = []

    for query_pattern, section_name in QUERY_SECTION_HINT_PATTERNS:
        if query_pattern.search(normalized_query) and section_name not in section_hints:
            section_hints.append(section_name)

    return section_hints


def has_active_substance_entity(matched_entities: list[EntityMatch]) -> bool:
    """Проверяет, была ли в запросе распознана сущность типа active_substance."""

    for matched_entity in matched_entities:
        if matched_entity.entity_type == "active_substance":
            return True

    return False


def is_service_section(section_name: str) -> bool:
    """Определяет, относится ли раздел к служебным и административным блокам."""

    normalized_section_name = normalize_scalar_text(section_name)

    return normalized_section_name in SERVICE_SECTION_NAMES


def is_core_section(section_name: str) -> bool:
    """Определяет, относится ли раздел к базовым содержательным секциям инструкции."""

    normalized_section_name = normalize_scalar_text(section_name)

    return normalized_section_name in CORE_SECTION_NAMES


def count_active_substances(metadata: dict[str, Any]) -> int:
    """Подсчитывает число действующих веществ в metadata текущего чанка."""

    active_substances = normalize_string_list(metadata.get("active_substances"))

    return len(active_substances)


def build_chunk_metadata(chunk_record: dict[str, Any]) -> dict[str, Any]:
    """Строит нормализованные metadata для записи одного чанка в ChromaDB."""

    metadata = {
        "chunk_id": normalize_scalar_text(chunk_record.get("chunk_id")),
        "doc_id": normalize_scalar_text(chunk_record.get("doc_id")),
        "drug_name_ru": normalize_scalar_text(chunk_record.get("drug_name_ru")),
        "drug_name_lat": normalize_scalar_text(chunk_record.get("drug_name_lat")),
        "section_name": normalize_scalar_text(chunk_record.get("section_name")),
        "chunk_type": normalize_scalar_text(chunk_record.get("chunk_type")),
        "dosage_form": normalize_scalar_text(chunk_record.get("dosage_form")),
        "title": normalize_scalar_text(chunk_record.get("title")),
        "source_path": normalize_scalar_text(chunk_record.get("source_path")),
        "clinical_pharmacological_group": normalize_scalar_text(
            chunk_record.get("clinical_pharmacological_group")
        ),
        "registration_number": normalize_scalar_text(chunk_record.get("registration_number")),
        "registration_date_raw": normalize_scalar_text(chunk_record.get("registration_date_raw")),
        "active_substances": normalize_string_list(chunk_record.get("active_substances")),
        "related_active_substance_names_ru": normalize_string_list(
            chunk_record.get("related_active_substance_names_ru")
        ),
        "related_active_substance_names_lat": normalize_string_list(
            chunk_record.get("related_active_substance_names_lat")
        ),
        "atc_codes": normalize_string_list(chunk_record.get("atc_codes")),
        "nosology_codes": normalize_string_list(chunk_record.get("nosology_codes")),
        "nosology_names": normalize_string_list(chunk_record.get("nosology_names")),
        "clinical_group_codes": normalize_string_list(chunk_record.get("clinical_group_codes")),
        "clinical_group_names": normalize_string_list(chunk_record.get("clinical_group_names")),
    }

    return metadata


def remove_empty_metadata_values(metadata: dict[str, Any]) -> dict[str, Any]:
    """Удаляет из metadata пустые строки, пустые списки и пустые словари перед записью в ChromaDB."""

    cleaned_metadata: dict[str, Any] = {}

    for key, value in metadata.items():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        if isinstance(value, list) and len(value) == 0:
            continue
        if isinstance(value, dict) and len(value) == 0:
            continue
        cleaned_metadata[key] = value

    return cleaned_metadata


def iter_indexable_chunks(chunks_path: Path, limit: Optional[int] = None) -> Iterator[dict[str, Any]]:
    """Возвращает только валидные чанки, пригодные для индексации."""

    for chunk_record in load_jsonl_records(input_path=chunks_path, limit=limit):
        chunk_id = normalize_scalar_text(chunk_record.get("chunk_id"))

        retrieval_text = normalize_scalar_text(chunk_record.get("retrieval_text"))

        chunk_text = normalize_scalar_text(chunk_record.get("chunk_text"))

        if not chunk_id or not retrieval_text or not chunk_text:
            continue

        yield chunk_record


def batched(records: Iterable[dict[str, Any]], batch_size: int) -> Iterator[list[dict[str, Any]]]:
    """Разбивает поток чанков на батчи фиксированного размера."""

    batch: list[dict[str, Any]] = []

    for record in records:
        batch.append(record)
        if len(batch) >= batch_size:
            yield batch
            batch = []

    if batch:
        yield batch


def extract_embedding_items(response: Any) -> list[Any]:
    """Извлекает список элементов embeddings из ответа GigaChat SDK."""

    data_items = getattr(response, "data", None)
    if data_items is not None:
        return list(data_items)

    if isinstance(response, dict):
        dict_data_items = response.get("data")
        if isinstance(dict_data_items, list):
            return dict_data_items

    raise RuntimeError("Не удалось извлечь поле 'data' из ответа embeddings API GigaChat.")


def extract_embedding_vector(response_item: Any) -> list[float]:
    """Извлекает один embedding-вектор из элемента ответа GigaChat API."""

    embedding_value = getattr(response_item, "embedding", None)
    if embedding_value is None and isinstance(response_item, dict):
        embedding_value = response_item.get("embedding")

    if not isinstance(embedding_value, list):
        raise RuntimeError("Не удалось извлечь embedding-вектор из ответа GigaChat API.")

    return [float(value) for value in embedding_value]


def extract_chat_message_text(chat_response: Any) -> str:
    """Извлекает текст ответа модели из структуры ChatCompletion SDK."""

    choices = getattr(chat_response, "choices", None)
    if not choices and isinstance(chat_response, dict):
        choices = chat_response.get("choices")

    if not isinstance(choices, list) or not choices:
        raise RuntimeError("Не удалось извлечь choices из ответа chat API GigaChat.")

    first_choice = choices[0]

    message = getattr(first_choice, "message", None)
    if message is None and isinstance(first_choice, dict):
        message = first_choice.get("message")

    content = getattr(message, "content", None)
    if content is None and isinstance(message, dict):
        content = message.get("content")

    normalized_content = normalize_scalar_text(content)
    if not normalized_content:
        raise RuntimeError("Модель вернула пустой ответ.")

    return normalized_content


def create_embeddings_batch(gigachat_client: Any, texts: list[str], model_name: str) -> list[list[float]]:
    """Создает embeddings для батча текстов через GigaChat API."""

    from .clients import retry_on_transient_error

    response = retry_on_transient_error(gigachat_client.embeddings, texts, model=model_name)

    response_items = extract_embedding_items(response)

    if len(response_items) != len(texts):
        raise RuntimeError(
            f"Число embeddings в ответе ({len(response_items)}) не совпадает с числом текстов ({len(texts)})."
        )

    embedding_vectors = [extract_embedding_vector(response_item) for response_item in response_items]

    return embedding_vectors
