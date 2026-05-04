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
        # line_index хранит порядковый номер текущей строки и используется для поддержки limit.
        for line_index, line in enumerate(input_stream, start=1):
            if limit is not None and line_index > limit:
                break

            # record хранит одну JSON-запись из файла chunks.jsonl.
            record = json.loads(line)
            yield record


def normalize_scalar_text(value: Any) -> str:
    """Приводит значение metadata к чистой строке для надежного хранения в ChromaDB."""

    if value is None:
        return ""

    # text_value хранит строковое представление входного значения.
    text_value = str(value).strip()

    # return_value содержит очищенную строку без пробелов по краям.
    return text_value


def normalize_string_list(values: Any) -> list[str]:
    """Приводит входное значение к списку непустых строк без дубликатов."""

    if not isinstance(values, list):
        return []

    # normalized_values хранит очищенные элементы списка в исходном порядке без дубликатов.
    normalized_values: list[str] = []

    # raw_value по очереди перебирает элементы исходного списка.
    for raw_value in values:
        # normalized_value хранит очищенное строковое представление элемента списка.
        normalized_value = normalize_scalar_text(raw_value)
        if not normalized_value:
            continue
        if normalized_value in normalized_values:
            continue
        normalized_values.append(normalized_value)

    # return_value содержит нормализованный список строк.
    return normalized_values


def normalize_search_text(value: Any) -> str:
    """Нормализует текст для поиска: приводит к нижнему регистру, схлопывает пробелы и заменяет ё на е."""

    # raw_text хранит строковое представление входного значения до нормализации.
    raw_text = normalize_scalar_text(value)
    if not raw_text:
        return ""

    # lowered_text хранит строку в нижнем регистре.
    lowered_text = raw_text.lower()

    # normalized_yo_text хранит строку после замены буквы ё на е.
    normalized_yo_text = lowered_text.replace("ё", "е")

    # collapsed_text хранит строку после схлопывания повторяющихся пробелов.
    collapsed_text = " ".join(normalized_yo_text.split())

    # return_value содержит нормализованный текст для entity lookup.
    return collapsed_text


def normalize_drug_name_lookup_text(value: Any) -> str:
    """Нормализует торговое название препарата для устойчивого lookup по названию."""

    # normalized_text хранит базовый нормализованный текст после общей подготовки строки.
    normalized_text = normalize_search_text(value)
    if not normalized_text:
        return ""

    # without_trademark_text хранит строку без символов торговой марки и типографских спецсимволов.
    without_trademark_text = (
        normalized_text
        .replace("®", " ")
        .replace("™", " ")
        .replace("«", " ")
        .replace("»", " ")
    )

    # collapsed_text хранит строку после повторного схлопывания пробелов.
    collapsed_text = " ".join(without_trademark_text.split())

    # return_value содержит форму названия, пригодную для drug-name lookup.
    return collapsed_text


def build_query_fuzzy_fragments(normalized_query: str) -> list[str]:
    """Строит короткие фрагменты запроса для fuzzy-сравнения с названиями препаратов."""

    if not normalized_query:
        return []

    # query_tokens хранит токены нормализованного запроса.
    query_tokens = normalized_query.split()
    if not query_tokens:
        return []

    # max_fragment_length хранит максимальную длину фрагмента в токенах.
    max_fragment_length = min(4, len(query_tokens))

    # fragments хранит все короткие contiguous-фрагменты запроса без дублей.
    fragments: list[str] = []

    # start_index и fragment_length по очереди перебирают окна токенов внутри запроса.
    for start_index in range(len(query_tokens)):
        for fragment_length in range(1, max_fragment_length + 1):
            end_index = start_index + fragment_length
            if end_index > len(query_tokens):
                break

            # fragment_text хранит один короткий фрагмент запроса.
            fragment_text = " ".join(query_tokens[start_index:end_index]).strip()
            if len(fragment_text) < 4:
                continue
            if fragment_text in fragments:
                continue
            fragments.append(fragment_text)

    # return_value содержит набор query-фрагментов для fuzzy drug-name lookup.
    return fragments


def calculate_fuzzy_name_similarity(
    query_fragment: str,
    candidate_variant: str,
) -> float:
    """Считает грубую similarity между фрагментом запроса и названием препарата."""

    # normalized_query_fragment хранит нормализованный фрагмент запроса.
    normalized_query_fragment = normalize_drug_name_lookup_text(query_fragment)

    # normalized_candidate_variant хранит нормализованное название препарата.
    normalized_candidate_variant = normalize_drug_name_lookup_text(candidate_variant)

    if not normalized_query_fragment or not normalized_candidate_variant:
        return 0.0

    # fragment_token_count хранит число токенов во фрагменте запроса.
    fragment_token_count = len(normalized_query_fragment.split())

    # candidate_token_count хранит число токенов в названии препарата.
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

    # similarity_ratio хранит SequenceMatcher-score между фрагментом и названием.
    similarity_ratio = difflib.SequenceMatcher(
        None,
        normalized_query_fragment,
        normalized_candidate_variant,
    ).ratio()

    # return_value содержит similarity-score для fuzzy-сопоставления названия препарата.
    return similarity_ratio


def build_entity_match_pattern(entity_text: str) -> Optional[re.Pattern[str]]:
    """Создает регулярное выражение для безопасного поиска сущности внутри смешанного запроса."""

    # normalized_entity_text хранит нормализованное название сущности.
    normalized_entity_text = normalize_search_text(entity_text)
    if len(normalized_entity_text) < 3:
        return None

    # escaped_entity_text хранит экранированный текст сущности для безопасного использования в regex.
    escaped_entity_text = re.escape(normalized_entity_text)

    # pattern_text хранит выражение для поиска сущности внутри произвольного запроса по границам слова.
    pattern_text = rf"(?<![0-9a-zа-я]){escaped_entity_text}(?![0-9a-zа-я])"

    # entity_pattern хранит готовый regex-объект.
    entity_pattern = re.compile(pattern_text)

    # return_value содержит regex для поиска сущности в запросе.
    return entity_pattern


def build_drug_document_entries(structured_documents_path: Path) -> list[DrugDocumentEntry]:
    """Загружает структурированные карточки препаратов и строит индекс по торговым названиям."""

    # drug_document_entries хранит все документы препаратов, пригодные для точного lookup.
    drug_document_entries: list[DrugDocumentEntry] = []

    # document_record по очереди перебирает записи structured_documents.jsonl.
    for document_record in load_jsonl_records(input_path=structured_documents_path):
        # doc_id хранит идентификатор документа препарата.
        doc_id = normalize_scalar_text(document_record.get("doc_id"))

        # drug_name_ru хранит русскоязычное название препарата.
        drug_name_ru = normalize_scalar_text(document_record.get("drug_name_ru"))

        # drug_name_lat хранит латинское название препарата.
        drug_name_lat = normalize_scalar_text(document_record.get("drug_name_lat"))

        # normalized_name_ru хранит нормализованное русскоязычное название препарата.
        normalized_name_ru = normalize_drug_name_lookup_text(drug_name_ru)

        # normalized_name_lat хранит нормализованное латинское название препарата.
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

    # return_value содержит индекс документов препаратов по торговым названиям.
    return drug_document_entries


def load_entity_matches(entity_relations_path: Path) -> list[EntityMatch]:
    """Агрегирует entity_relations.jsonl в список уникальных сущностей со связанными doc_id."""

    # aggregated_entities хранит промежуточное агрегированное состояние по ключу сущности.
    aggregated_entities: dict[tuple[str, str, str, str], dict[str, Any]] = {}

    # relation_record по очереди перебирает записи файла entity_relations.jsonl.
    for relation_record in load_jsonl_records(input_path=entity_relations_path):
        # entity_key хранит ключ группировки сущности по типу, коду и названиям.
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

        # aggregated_entity хранит агрегированную сущность для текущей relation-записи.
        aggregated_entity = aggregated_entities[entity_key]

        # target_doc_id хранит doc_id документа, связанного с текущей сущностью.
        target_doc_id = normalize_scalar_text(relation_record.get("target_doc_id"))
        if target_doc_id and target_doc_id not in aggregated_entity["candidate_doc_ids"]:
            aggregated_entity["candidate_doc_ids"].append(target_doc_id)

    # entity_matches хранит список агрегированных сущностей для дальнейшего поиска по запросу.
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

    # return_value содержит список уникальных сущностей со связанными документами.
    return entity_matches


def find_entity_matches(query: str, entity_matches: list[EntityMatch]) -> list[EntityMatch]:
    """Ищет в запросе точные и встроенные совпадения с сущностями справочника."""

    # normalized_query хранит нормализованный пользовательский запрос.
    normalized_query = normalize_search_text(query)
    if not normalized_query:
        return []

    # exact_matches хранит сущности, которые полностью совпали с запросом или кодом.
    exact_matches: list[EntityMatch] = []

    # embedded_matches хранит сущности, которые распознаны как часть смешанного запроса.
    embedded_matches: list[EntityMatch] = []

    # entity_match по очереди перебирает все агрегированные сущности справочника.
    for entity_match in entity_matches:
        # candidate_variants хранит все строковые представления сущности, которые можно искать в запросе.
        candidate_variants = [
            normalize_search_text(entity_match.entity_code),
            normalize_search_text(entity_match.entity_name),
            normalize_search_text(entity_match.entity_name_lat),
        ]

        # candidate_variants очищается от пустых строк и дубликатов.
        candidate_variants = [
            candidate_variant
            for candidate_variant in dict.fromkeys(candidate_variants)
            if candidate_variant
        ]

        # exact_variant хранит вариант сущности, который полностью совпал с запросом.
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

        # matched_fragment хранит вариант сущности, который обнаружен внутри смешанного запроса.
        matched_fragment = ""

        # candidate_variant по очереди перебирает текстовые представления сущности.
        for candidate_variant in candidate_variants:
            # entity_pattern хранит regex для безопасного поиска сущности в запросе.
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
        # sorted_exact_matches хранит точные совпадения, отсортированные по длине распознанной сущности.
        sorted_exact_matches = sorted(
            exact_matches,
            key=lambda item: len(item.source_query_fragment),
            reverse=True,
        )
        return sorted_exact_matches

    # sorted_embedded_matches хранит встроенные совпадения, отсортированные по длине распознанной сущности.
    sorted_embedded_matches = sorted(
        embedded_matches,
        key=lambda item: len(item.source_query_fragment),
        reverse=True,
    )

    # return_value содержит найденные сущности в порядке убывания специфичности.
    return sorted_embedded_matches


def find_drug_document_matches(
    query: str,
    drug_document_entries: list[DrugDocumentEntry],
) -> list[DrugDocumentMatch]:
    """Ищет в запросе точные, встроенные и fuzzy-совпадения с торговыми названиями препаратов."""

    # normalized_query хранит нормализованный пользовательский запрос для drug-name lookup.
    normalized_query = normalize_drug_name_lookup_text(query)
    if not normalized_query:
        return []

    # exact_matches хранит карточки препаратов, полностью совпавшие с запросом.
    exact_matches: list[DrugDocumentMatch] = []

    # embedded_matches хранит карточки препаратов, найденные как часть смешанного запроса.
    embedded_matches: list[DrugDocumentMatch] = []

    # fuzzy_candidates хранит кандидатов для typo-tolerant lookup: score и найденную карточку препарата.
    fuzzy_candidates: list[tuple[float, DrugDocumentMatch]] = []

    # query_fuzzy_fragments хранит короткие фрагменты запроса для fuzzy-сравнения.
    query_fuzzy_fragments = build_query_fuzzy_fragments(normalized_query)

    # drug_document_entry по очереди перебирает все карточки препаратов.
    for drug_document_entry in drug_document_entries:
        # candidate_variants хранит доступные варианты торгового названия для текущего документа.
        candidate_variants = [
            drug_document_entry.normalized_name_ru,
            drug_document_entry.normalized_name_lat,
        ]

        # candidate_variants очищается от пустых значений и дублей.
        candidate_variants = [
            candidate_variant
            for candidate_variant in dict.fromkeys(candidate_variants)
            if candidate_variant
        ]

        # exact_variant хранит вариант названия, который полностью совпал с запросом.
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

        # matched_fragment хранит вариант названия, найденный внутри смешанного запроса.
        matched_fragment = ""

        # candidate_variant по очереди перебирает варианты торгового названия.
        for candidate_variant in candidate_variants:
            # drug_pattern хранит безопасное регулярное выражение для поиска названия препарата в запросе.
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

        # best_fuzzy_fragment хранит лучший короткий фрагмент запроса для fuzzy-сравнения с названием препарата.
        best_fuzzy_fragment = ""

        # best_fuzzy_score хранит лучший fuzzy-score для текущего препарата.
        best_fuzzy_score = 0.0

        # candidate_variant по очереди перебирает варианты торгового названия.
        for candidate_variant in candidate_variants:
            # query_fuzzy_fragment по очереди перебирает короткие окна запроса.
            for query_fuzzy_fragment in query_fuzzy_fragments:
                # fuzzy_score хранит similarity между окном запроса и названием препарата.
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
        # sorted_exact_matches хранит точные совпадения, отсортированные по длине совпавшего названия.
        sorted_exact_matches = sorted(
            exact_matches,
            key=lambda item: len(item.source_query_fragment),
            reverse=True,
        )
        return sorted_exact_matches

    # sorted_embedded_matches хранит совпадения внутри смешанного запроса, отсортированные по специфичности.
    sorted_embedded_matches = sorted(
        embedded_matches,
        key=lambda item: len(item.source_query_fragment),
        reverse=True,
    )

    if sorted_embedded_matches:
        return sorted_embedded_matches

    if fuzzy_candidates:
        # best_fuzzy_score хранит лучший найденный similarity-score среди карточек препаратов.
        best_fuzzy_score = max(fuzzy_candidate[0] for fuzzy_candidate in fuzzy_candidates)

        # filtered_fuzzy_matches хранит лучшие fuzzy-кандидаты с близким score.
        filtered_fuzzy_matches = [
            fuzzy_match
            for fuzzy_score, fuzzy_match in fuzzy_candidates
            if fuzzy_score >= best_fuzzy_score - 0.02
        ]

        # sorted_fuzzy_matches хранит typo-tolerant совпадения, отсортированные по длине найденного фрагмента.
        sorted_fuzzy_matches = sorted(
            filtered_fuzzy_matches,
            key=lambda item: len(item.source_query_fragment),
            reverse=True,
        )

        return sorted_fuzzy_matches

    # return_value содержит найденные по названию карточки препаратов.
    return []


def collect_candidate_doc_ids(matched_entities: list[EntityMatch]) -> list[str]:
    """Объединяет doc_id из найденных сущностей в один список без дубликатов."""

    # candidate_doc_ids хранит объединенное множество документов, связанных с найденными сущностями.
    candidate_doc_ids: list[str] = []

    # matched_entity по очереди перебирает найденные сущности.
    for matched_entity in matched_entities:
        # candidate_doc_id по очереди перебирает документы, связанные с текущей сущностью.
        for candidate_doc_id in matched_entity.candidate_doc_ids:
            if candidate_doc_id not in candidate_doc_ids:
                candidate_doc_ids.append(candidate_doc_id)

    # return_value содержит уникальный список документов-кандидатов.
    return candidate_doc_ids


def collect_drug_document_ids(matched_drug_documents: list[DrugDocumentMatch]) -> list[str]:
    """Собирает уникальные doc_id из найденных по названию карточек препаратов."""

    # candidate_doc_ids хранит список уникальных документов, найденных через drug-name lookup.
    candidate_doc_ids: list[str] = []

    # matched_drug_document по очереди перебирает найденные карточки препаратов.
    for matched_drug_document in matched_drug_documents:
        if matched_drug_document.doc_id and matched_drug_document.doc_id not in candidate_doc_ids:
            candidate_doc_ids.append(matched_drug_document.doc_id)

    # return_value содержит уникальные doc_id, найденные по торговому названию.
    return candidate_doc_ids


def build_search_scope_doc_ids(
    matched_entities: list[EntityMatch],
    matched_drug_documents: list[DrugDocumentMatch],
) -> list[str]:
    """Определяет итоговое множество документов для constrained retrieval."""

    # drug_document_ids хранит документы, найденные по торговому названию препарата.
    drug_document_ids = collect_drug_document_ids(matched_drug_documents)
    if drug_document_ids:
        return drug_document_ids

    # entity_document_ids хранит документы, найденные через entity_relations.
    entity_document_ids = collect_candidate_doc_ids(matched_entities)

    # return_value содержит итоговую область поиска по документам.
    return entity_document_ids


def tokenize_feature_query(query: str) -> list[str]:
    """Разбивает запрос на значимые токены для полнотного поиска по признакам."""

    # normalized_query хранит нормализованную строку пользовательского запроса.
    normalized_query = normalize_search_text(query)

    # raw_tokens хранит все буквенно-цифровые токены, найденные в запросе.
    raw_tokens = re.findall(r"[0-9a-zа-я]+", normalized_query)

    # feature_tokens хранит очищенные значимые токены без служебных слов.
    feature_tokens: list[str] = []

    # raw_token по очереди перебирает токены исходного запроса.
    for raw_token in raw_tokens:
        if len(raw_token) < 3:
            continue
        if raw_token in SEARCH_STOPWORDS:
            continue
        if raw_token not in feature_tokens:
            feature_tokens.append(raw_token)

    # return_value содержит список значимых токенов запроса.
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

    # query_tokens хранит значимые токены исходного запроса без служебных слов.
    query_tokens = tokenize_feature_query(query)
    if not query_tokens:
        return False

    # non_section_tokens хранит токены, которые не похожи на названия разделов инструкции.
    non_section_tokens: list[str] = []

    # query_token по очереди перебирает значимые токены запроса.
    for query_token in query_tokens:
        # token_looks_like_section показывает, совпадает ли токен с паттерном раздела инструкции.
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

    # main_token хранит основной содержательный токен запроса.
    main_token = non_section_tokens[0]

    if main_token in FEATURE_QUERY_VARIANTS:
        return False

    # category_variants хранит набор известных категориальных токенов и их словарных вариантов.
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

    # normalized_query хранит нормализованный исходный запрос.
    normalized_query = normalize_search_text(query)

    # return_value показывает, похож ли короткий запрос на обращение к одному препарату.
    return len(normalized_query.split()) <= 3


def build_query_token_variants(query_token: str) -> list[str]:
    """Строит варианты одного токена запроса для более устойчивого лексического совпадения."""

    # normalized_token хранит нормализованную форму токена.
    normalized_token = normalize_search_text(query_token)
    if not normalized_token:
        return []

    # token_variants хранит варианты токена, пригодные для поиска в текстовых признаках.
    token_variants: list[str] = [normalized_token]

    # synonym_variant по очереди перебирает словарные варианты признака.
    for synonym_variant in FEATURE_QUERY_VARIANTS.get(normalized_token, []):
        if synonym_variant not in token_variants:
            token_variants.append(synonym_variant)

    if len(normalized_token) >= 8:
        # prefix_variant хранит длинный префикс токена для грубого учета словоформ.
        prefix_variant = normalized_token[:10]
        if prefix_variant not in token_variants:
            token_variants.append(prefix_variant)

    if len(normalized_token) >= 7:
        # trimmed_variant хранит укороченную основу токена без конечного окончания.
        trimmed_variant = normalized_token[:-2]
        if trimmed_variant not in token_variants:
            token_variants.append(trimmed_variant)

    # return_value содержит варианты токена для полнотного поиска.
    return token_variants


def build_drug_catalog_entries(structured_documents_path: Path) -> list[DrugCatalogEntry]:
    """Строит документный каталог препаратов для полнотного поиска по признакам."""

    # drug_catalog_entries хранит все агрегированные карточки препаратов.
    drug_catalog_entries: list[DrugCatalogEntry] = []

    # document_record по очереди перебирает записи structured_documents.jsonl.
    for document_record in load_jsonl_records(input_path=structured_documents_path):
        # doc_id хранит идентификатор документа препарата.
        doc_id = normalize_scalar_text(document_record.get("doc_id"))

        # drug_name_ru хранит русскоязычное название препарата.
        drug_name_ru = normalize_scalar_text(document_record.get("drug_name_ru"))

        # drug_name_lat хранит латинское название препарата.
        drug_name_lat = normalize_scalar_text(document_record.get("drug_name_lat"))

        # normalized_name_ru хранит нормализованное русскоязычное название препарата.
        normalized_name_ru = normalize_drug_name_lookup_text(drug_name_ru)

        # normalized_name_lat хранит нормализованное латинское название препарата.
        normalized_name_lat = normalize_drug_name_lookup_text(drug_name_lat)

        # atc_codes хранит ATC-коды текущего препарата.
        atc_codes = normalize_string_list(document_record.get("atc_codes"))

        # active_substances хранит действующие вещества препарата.
        active_substances = normalize_string_list(document_record.get("active_substances"))

        # sections хранит текстовые разделы карточки препарата.
        sections = document_record.get("sections") or {}

        # searchable_parts хранит фрагменты текста, из которых будет собран единый полнотный индекс препарата.
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

        # section_name и section_text по очереди перебирают разделы карточки препарата.
        for section_name, section_text in sections.items():
            searchable_parts.append(normalize_scalar_text(section_name))
            searchable_parts.append(normalize_scalar_text(section_text))

        # searchable_text хранит единый нормализованный текст признаков препарата.
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

    # return_value содержит каталог препаратов для полнотного поиска.
    return drug_catalog_entries


def build_drug_catalog_map(drug_catalog_entries: list[DrugCatalogEntry]) -> dict[str, DrugCatalogEntry]:
    """Строит словарь карточек препаратов по doc_id для быстрого доступа."""

    # drug_catalog_map хранит отображение doc_id -> DrugCatalogEntry.
    drug_catalog_map = {
        drug_catalog_entry.doc_id: drug_catalog_entry
        for drug_catalog_entry in drug_catalog_entries
        if drug_catalog_entry.doc_id
    }

    # return_value содержит словарь карточек препаратов.
    return drug_catalog_map


def match_drug_catalog_entries(
    query: str,
    drug_catalog_entries: list[DrugCatalogEntry],
    matched_entities: list[EntityMatch],
    matched_drug_documents: list[DrugDocumentMatch],
) -> list[DrugCatalogMatch]:
    """Находит все препараты, подходящие по структурным и текстовым признакам запроса."""

    # drug_catalog_map хранит быстрый доступ к карточке препарата по doc_id.
    drug_catalog_map = build_drug_catalog_map(drug_catalog_entries)

    # candidate_doc_ids хранит документы, найденные по структурным слоям lookup.
    candidate_doc_ids = build_search_scope_doc_ids(
        matched_entities=matched_entities,
        matched_drug_documents=matched_drug_documents,
    )

    # catalog_matches хранит все найденные препараты с оценкой совпадения.
    catalog_matches: list[DrugCatalogMatch] = []

    if candidate_doc_ids:
        # candidate_doc_id по очереди перебирает структурно найденные документы.
        for candidate_doc_id in candidate_doc_ids:
            # drug_catalog_entry хранит карточку препарата для текущего doc_id.
            drug_catalog_entry = drug_catalog_map.get(candidate_doc_id)
            if drug_catalog_entry is None:
                continue

            # match_reasons хранит причины включения препарата в полнотную выдачу.
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

        # sorted_catalog_matches хранит структурные совпадения, отсортированные по названию препарата.
        sorted_catalog_matches = sorted(
            catalog_matches,
            key=lambda item: (-item.score, item.drug_name_ru, item.doc_id),
        )
        return sorted_catalog_matches

    # query_tokens хранит значимые токены пользовательского запроса.
    query_tokens = tokenize_feature_query(query)

    # query_token_variants_map хранит варианты каждого токена запроса для лексического поиска.
    query_token_variants_map = {
        query_token: build_query_token_variants(query_token)
        for query_token in query_tokens
    }

    # normalized_query хранит полную нормализованную форму запроса.
    normalized_query = normalize_search_text(query)

    # drug_catalog_entry по очереди перебирает все препараты каталога.
    for drug_catalog_entry in drug_catalog_entries:
        # score хранит итоговую оценку совпадения текущего препарата с запросом.
        score = 0.0

        # match_reasons хранит причины совпадения текущего препарата с запросом.
        match_reasons: list[str] = []

        if normalized_query and normalized_query in drug_catalog_entry.searchable_text:
            score += 20.0
            match_reasons.append("совпадение по полной фразе")

        # matched_all_tokens показывает, совпали ли все значимые токены запроса.
        matched_all_tokens = True

        # query_token и token_variants по очереди перебирают токены запроса и их варианты.
        for query_token, token_variants in query_token_variants_map.items():
            # matched_token показывает, найден ли хотя бы один вариант текущего токена.
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

    # sorted_catalog_matches хранит найденные препараты, отсортированные по score и названию.
    sorted_catalog_matches = sorted(
        catalog_matches,
        key=lambda item: (-item.score, item.drug_name_ru, item.doc_id),
    )

    # return_value содержит список всех найденных препаратов по признакам.
    return sorted_catalog_matches


def run_find_all_retrieval(
    query: str,
    entity_relations_path: Path,
    structured_documents_path: Path,
) -> FindAllBundle:
    """Выполняет полнотный поиск препаратов по признакам и возвращает все промежуточные результаты."""

    # loaded_entity_matches хранит агрегированные сущности из entity_relations.
    loaded_entity_matches = load_entity_matches(entity_relations_path)

    # drug_document_entries хранит индекс торговых названий препаратов.
    drug_document_entries = build_drug_document_entries(structured_documents_path)

    # matched_entities хранит найденные структурные сущности.
    matched_entities = find_entity_matches(
        query=query,
        entity_matches=loaded_entity_matches,
    )

    # matched_drug_documents хранит найденные по названию карточки препаратов.
    matched_drug_documents = find_drug_document_matches(
        query=query,
        drug_document_entries=drug_document_entries,
    )

    # drug_catalog_entries хранит каталог препаратов для полнотного поиска по признакам.
    drug_catalog_entries = build_drug_catalog_entries(structured_documents_path)

    # catalog_matches хранит все найденные препараты по структурным или текстовым признакам.
    catalog_matches = match_drug_catalog_entries(
        query=query,
        drug_catalog_entries=drug_catalog_entries,
        matched_entities=matched_entities,
        matched_drug_documents=matched_drug_documents,
    )

    # find_all_bundle хранит весь результат полнотного поиска в одной структуре.
    find_all_bundle = FindAllBundle(
        matched_entities=matched_entities,
        matched_drug_documents=matched_drug_documents,
        catalog_matches=catalog_matches,
    )

    # return_value содержит полный пакет результатов полнотного поиска.
    return find_all_bundle


def infer_section_hints(query: str) -> list[str]:
    """Извлекает из запроса желаемые разделы инструкции по простым эвристикам."""

    # normalized_query хранит нормализованный запрос пользователя.
    normalized_query = normalize_search_text(query)

    # section_hints хранит разделы инструкции, которые следует дополнительно поднять в выдаче.
    section_hints: list[str] = []

    # query_pattern и section_name по очереди перебирают регулярные выражения для section boost.
    for query_pattern, section_name in QUERY_SECTION_HINT_PATTERNS:
        if query_pattern.search(normalized_query) and section_name not in section_hints:
            section_hints.append(section_name)

    # return_value содержит список предпочтительных section_name для reranking.
    return section_hints


def has_active_substance_entity(matched_entities: list[EntityMatch]) -> bool:
    """Проверяет, была ли в запросе распознана сущность типа active_substance."""

    # matched_entity по очереди перебирает найденные сущности.
    for matched_entity in matched_entities:
        if matched_entity.entity_type == "active_substance":
            return True

    # return_value сообщает, найдено ли активное вещество в запросе.
    return False


def is_service_section(section_name: str) -> bool:
    """Определяет, относится ли раздел к служебным и административным блокам."""

    # normalized_section_name хранит очищенное имя раздела.
    normalized_section_name = normalize_scalar_text(section_name)

    # return_value показывает, нужно ли штрафовать раздел в общих запросах.
    return normalized_section_name in SERVICE_SECTION_NAMES


def is_core_section(section_name: str) -> bool:
    """Определяет, относится ли раздел к базовым содержательным секциям инструкции."""

    # normalized_section_name хранит очищенное имя раздела.
    normalized_section_name = normalize_scalar_text(section_name)

    # return_value показывает, нужно ли раздел дополнительно поднимать в общих запросах.
    return normalized_section_name in CORE_SECTION_NAMES


def count_active_substances(metadata: dict[str, Any]) -> int:
    """Подсчитывает число действующих веществ в metadata текущего чанка."""

    # active_substances хранит нормализованный список действующих веществ препарата.
    active_substances = normalize_string_list(metadata.get("active_substances"))

    # return_value содержит число уникальных действующих веществ.
    return len(active_substances)


def build_chunk_metadata(chunk_record: dict[str, Any]) -> dict[str, Any]:
    """Строит нормализованные metadata для записи одного чанка в ChromaDB."""

    # metadata хранит все поля, которые реально пригодятся для поиска и отладки retrieval.
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

    # return_value содержит нормализованный словарь metadata для ChromaDB.
    return metadata


def remove_empty_metadata_values(metadata: dict[str, Any]) -> dict[str, Any]:
    """Удаляет из metadata пустые строки, пустые списки и пустые словари перед записью в ChromaDB."""

    # cleaned_metadata хранит только те metadata-поля, которые безопасно сохранять в ChromaDB.
    cleaned_metadata: dict[str, Any] = {}

    # key и value по очереди перебирают все metadata-поля исходного чанка.
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

    # return_value содержит metadata без пустых значений, которые не принимает ChromaDB.
    return cleaned_metadata


def iter_indexable_chunks(chunks_path: Path, limit: Optional[int] = None) -> Iterator[dict[str, Any]]:
    """Возвращает только валидные чанки, пригодные для индексации."""

    # chunk_record по очереди перебирает все записи из chunks.jsonl.
    for chunk_record in load_jsonl_records(input_path=chunks_path, limit=limit):
        # chunk_id хранит идентификатор текущего чанка.
        chunk_id = normalize_scalar_text(chunk_record.get("chunk_id"))

        # retrieval_text хранит строку, которая будет отправлена в embedding model.
        retrieval_text = normalize_scalar_text(chunk_record.get("retrieval_text"))

        # chunk_text хранит человекочитаемый текст чанка для возврата в поиске.
        chunk_text = normalize_scalar_text(chunk_record.get("chunk_text"))

        if not chunk_id or not retrieval_text or not chunk_text:
            continue

        yield chunk_record


def batched(records: Iterable[dict[str, Any]], batch_size: int) -> Iterator[list[dict[str, Any]]]:
    """Разбивает поток чанков на батчи фиксированного размера."""

    # batch хранит текущий батч чанков перед записью в ChromaDB.
    batch: list[dict[str, Any]] = []

    # record по очереди перебирает чанки для индексации.
    for record in records:
        batch.append(record)
        if len(batch) >= batch_size:
            yield batch
            batch = []

    if batch:
        yield batch


def extract_embedding_items(response: Any) -> list[Any]:
    """Извлекает список элементов embeddings из ответа GigaChat SDK."""

    # data_items хранит embeddings-элементы, если SDK вернул объект с атрибутом data.
    data_items = getattr(response, "data", None)
    if data_items is not None:
        return list(data_items)

    if isinstance(response, dict):
        # dict_data_items хранит embeddings-элементы, если ответ имеет словарную форму.
        dict_data_items = response.get("data")
        if isinstance(dict_data_items, list):
            return dict_data_items

    raise RuntimeError("Не удалось извлечь поле 'data' из ответа embeddings API GigaChat.")


def extract_embedding_vector(response_item: Any) -> list[float]:
    """Извлекает один embedding-вектор из элемента ответа GigaChat API."""

    # embedding_value хранит список чисел embedding из объекта SDK или словаря.
    embedding_value = getattr(response_item, "embedding", None)
    if embedding_value is None and isinstance(response_item, dict):
        embedding_value = response_item.get("embedding")

    if not isinstance(embedding_value, list):
        raise RuntimeError("Не удалось извлечь embedding-вектор из ответа GigaChat API.")

    # return_value содержит embedding в виде списка чисел с плавающей точкой.
    return [float(value) for value in embedding_value]


def extract_chat_message_text(chat_response: Any) -> str:
    """Извлекает текст ответа модели из структуры ChatCompletion SDK."""

    # choices хранит список вариантов ответа модели.
    choices = getattr(chat_response, "choices", None)
    if not choices and isinstance(chat_response, dict):
        choices = chat_response.get("choices")

    if not isinstance(choices, list) or not choices:
        raise RuntimeError("Не удалось извлечь choices из ответа chat API GigaChat.")

    # first_choice хранит первый вариант ответа модели.
    first_choice = choices[0]

    # message хранит сообщение модели из первого варианта ответа.
    message = getattr(first_choice, "message", None)
    if message is None and isinstance(first_choice, dict):
        message = first_choice.get("message")

    # content хранит текстовое содержимое сообщения модели.
    content = getattr(message, "content", None)
    if content is None and isinstance(message, dict):
        content = message.get("content")

    # normalized_content хранит очищенный текст ответа модели.
    normalized_content = normalize_scalar_text(content)
    if not normalized_content:
        raise RuntimeError("Модель вернула пустой ответ.")

    # return_value содержит итоговый текст ответа модели.
    return normalized_content


def create_embeddings_batch(gigachat_client: Any, texts: list[str], model_name: str) -> list[list[float]]:
    """Создает embeddings для батча текстов через GigaChat API."""

    # response хранит ответ GigaChat API на запрос embeddings для списка текстов.
    response = gigachat_client.embeddings(texts, model=model_name)

    # response_items хранит список элементов embeddings из ответа API.
    response_items = extract_embedding_items(response)

    if len(response_items) != len(texts):
        raise RuntimeError(
            f"Число embeddings в ответе ({len(response_items)}) не совпадает с числом текстов ({len(texts)})."
        )

    # embedding_vectors хранит список embedding-векторов для входного батча текстов.
    embedding_vectors = [extract_embedding_vector(response_item) for response_item in response_items]

    # return_value содержит embedding-векторы в исходном порядке текстов.
    return embedding_vectors
