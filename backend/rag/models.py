"""Структуры данных, используемые в RAG-системе."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class EntityMatch:
    """Хранит результат распознавания сущности в пользовательском запросе."""

    entity_type: str

    entity_code: str

    entity_name: str

    entity_name_lat: str

    source_query_fragment: str

    candidate_doc_ids: list[str]


@dataclass
class RankedChunkResult:
    """Хранит один найденный чанк после retrieval и дополнительного rule-based reranking."""

    chunk_id: str

    doc_id: str

    drug_name_ru: str

    section_name: str

    document_text: str

    metadata: dict[str, Any]

    distance: float

    reranked_score: float


@dataclass
class GroupedDocumentResult:
    """Хранит сгруппированные результаты поиска по одному документу или препарату."""

    doc_id: str

    drug_name_ru: str

    best_score: float

    matched_sections: list[str]

    chunks: list[RankedChunkResult]


@dataclass
class DrugDocumentEntry:
    """Хранит карточку препарата для точного lookup по торговому названию."""

    doc_id: str

    drug_name_ru: str

    drug_name_lat: str

    normalized_name_ru: str

    normalized_name_lat: str


@dataclass
class DrugDocumentMatch:
    """Хранит найденное совпадение пользовательского запроса с карточкой препарата."""

    doc_id: str

    drug_name_ru: str

    drug_name_lat: str

    source_query_fragment: str


@dataclass
class RetrievalBundle:
    """Хранит полный результат retrieval, пригодный и для search, и для ask."""

    matched_entities: list[EntityMatch]

    matched_drug_documents: list[DrugDocumentMatch]

    candidate_doc_ids: list[str]

    section_hints: list[str]

    raw_results: dict[str, Any]

    flat_chunk_results: list[RankedChunkResult]

    reranked_chunk_results: list[RankedChunkResult]

    grouped_results: list[GroupedDocumentResult]


@dataclass
class RetrievalSummary:
    """Хранит краткую сводку retrieval для построения prompt и финального ответа."""

    answer_mode: str

    retrieved_drug_names: list[str]

    retrieved_doc_ids: list[str]

    section_hints: list[str]

    matched_entity_types: list[str]


@dataclass
class AnswerValidationResult:
    """Хранит результат post-check проверки ответа LLM на опору в retrieval-контекст."""

    status: str

    issues: list[str]

    grounding_overlap_ratio: float

    answer_token_count: int

    context_token_count: int

    primary_drug_name: str

    mentioned_context_drug_names: list[str]


@dataclass
class DrugCatalogEntry:
    """Хранит агрегированную карточку препарата для полнотного поиска по признакам."""

    doc_id: str

    drug_name_ru: str

    drug_name_lat: str

    normalized_name_ru: str

    normalized_name_lat: str

    atc_codes: list[str]

    active_substances: list[str]

    searchable_text: str


@dataclass
class DrugCatalogMatch:
    """Хранит результат полнотного поиска препарата по признакам."""

    doc_id: str

    drug_name_ru: str

    drug_name_lat: str

    score: float

    match_reasons: list[str]


@dataclass
class FindAllBundle:
    """Хранит полный результат полнотного поиска препаратов по признакам."""

    matched_entities: list[EntityMatch]

    matched_drug_documents: list[DrugDocumentMatch]

    catalog_matches: list[DrugCatalogMatch]
