"""Структуры данных, используемые в RAG-системе."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class EntityMatch:
    """Хранит результат распознавания сущности в пользовательском запросе."""

    # entity_type хранит тип найденной сущности: active_substance, atc, nosology или clinical_pharmacology_group.
    entity_type: str

    # entity_code хранит код сущности, если он есть в entity_relations.
    entity_code: str

    # entity_name хранит основное русскоязычное название сущности.
    entity_name: str

    # entity_name_lat хранит латинское название сущности, если оно есть.
    entity_name_lat: str

    # source_query_fragment хранит фрагмент запроса, по которому сущность была распознана.
    source_query_fragment: str

    # candidate_doc_ids хранит набор документов, связанных с найденной сущностью.
    candidate_doc_ids: list[str]


@dataclass
class RankedChunkResult:
    """Хранит один найденный чанк после retrieval и дополнительного rule-based reranking."""

    # chunk_id хранит идентификатор чанка из индекса.
    chunk_id: str

    # doc_id хранит идентификатор документа, которому принадлежит чанк.
    doc_id: str

    # drug_name_ru хранит название препарата для текущего чанка.
    drug_name_ru: str

    # section_name хранит название раздела, из которого получен чанк.
    section_name: str

    # document_text хранит текст чанка, возвращенный ChromaDB.
    document_text: str

    # metadata хранит metadata чанка, пришедшие из ChromaDB.
    metadata: dict[str, Any]

    # distance хранит исходное расстояние из vector search.
    distance: float

    # reranked_score хранит значение, по которому результаты будут дополнительно сортироваться.
    reranked_score: float


@dataclass
class GroupedDocumentResult:
    """Хранит сгруппированные результаты поиска по одному документу или препарату."""

    # doc_id хранит идентификатор документа.
    doc_id: str

    # drug_name_ru хранит название препарата для группы чанков.
    drug_name_ru: str

    # best_score хранит лучший reranked_score среди чанков документа.
    best_score: float

    # matched_sections хранит список разделов, которые были найдены в рамках данного документа.
    matched_sections: list[str]

    # chunks хранит ранжированные чанки, относящиеся к одному документу.
    chunks: list[RankedChunkResult]


@dataclass
class DrugDocumentEntry:
    """Хранит карточку препарата для точного lookup по торговому названию."""

    # doc_id хранит идентификатор документа препарата.
    doc_id: str

    # drug_name_ru хранит русскоязычное торговое название препарата.
    drug_name_ru: str

    # drug_name_lat хранит латинское торговое название препарата.
    drug_name_lat: str

    # normalized_name_ru хранит нормализованную русскоязычную форму названия для lookup.
    normalized_name_ru: str

    # normalized_name_lat хранит нормализованную латинскую форму названия для lookup.
    normalized_name_lat: str


@dataclass
class DrugDocumentMatch:
    """Хранит найденное совпадение пользовательского запроса с карточкой препарата."""

    # doc_id хранит идентификатор найденного документа препарата.
    doc_id: str

    # drug_name_ru хранит русскоязычное название найденного препарата.
    drug_name_ru: str

    # drug_name_lat хранит латинское название найденного препарата.
    drug_name_lat: str

    # source_query_fragment хранит фрагмент запроса, по которому был найден препарат.
    source_query_fragment: str


@dataclass
class RetrievalBundle:
    """Хранит полный результат retrieval, пригодный и для search, и для ask."""

    # matched_entities хранит сущности, найденные через entity_relations.
    matched_entities: list[EntityMatch]

    # matched_drug_documents хранит карточки препаратов, найденные по торговому названию.
    matched_drug_documents: list[DrugDocumentMatch]

    # candidate_doc_ids хранит итоговую область поиска по документам.
    candidate_doc_ids: list[str]

    # section_hints хранит подсказки по разделам инструкции.
    section_hints: list[str]

    # raw_results хранит сырой ответ ChromaDB.
    raw_results: dict[str, Any]

    # flat_chunk_results хранит найденные чанки до reranking.
    flat_chunk_results: list[RankedChunkResult]

    # reranked_chunk_results хранит чанки после rule-based reranking.
    reranked_chunk_results: list[RankedChunkResult]

    # grouped_results хранит финальную выдачу, сгруппированную по документам.
    grouped_results: list[GroupedDocumentResult]


@dataclass
class RetrievalSummary:
    """Хранит краткую сводку retrieval для построения prompt и финального ответа."""

    # answer_mode хранит режим ответа: single_drug, section_focused, entity_list или category_list.
    answer_mode: str

    # retrieved_drug_names хранит названия препаратов, вошедших в финальную retrieval-выдачу.
    retrieved_drug_names: list[str]

    # retrieved_doc_ids хранит doc_id документов, вошедших в финальную retrieval-выдачу.
    retrieved_doc_ids: list[str]

    # section_hints хранит целевые разделы, извлеченные из формулировки вопроса.
    section_hints: list[str]

    # matched_entity_types хранит типы сущностей, найденных через entity_relations.
    matched_entity_types: list[str]


@dataclass
class AnswerValidationResult:
    """Хранит результат post-check проверки ответа LLM на опору в retrieval-контекст."""

    # status хранит итоговый статус проверки: ok или warning.
    status: str

    # issues хранит список потенциальных проблем, найденных в ответе.
    issues: list[str]

    # grounding_overlap_ratio хранит долю значимых токенов ответа, найденных в retrieval-контексте.
    grounding_overlap_ratio: float

    # answer_token_count хранит число значимых токенов в ответе после нормализации.
    answer_token_count: int

    # context_token_count хранит число значимых токенов в выбранных чанках контекста.
    context_token_count: int

    # primary_drug_name хранит основной препарат, если ответ ожидался про один препарат.
    primary_drug_name: str

    # mentioned_context_drug_names хранит найденные в ответе названия препаратов из использованного контекста.
    mentioned_context_drug_names: list[str]


@dataclass
class DrugCatalogEntry:
    """Хранит агрегированную карточку препарата для полнотного поиска по признакам."""

    # doc_id хранит идентификатор документа препарата.
    doc_id: str

    # drug_name_ru хранит русскоязычное торговое название препарата.
    drug_name_ru: str

    # drug_name_lat хранит латинское торговое название препарата.
    drug_name_lat: str

    # normalized_name_ru хранит нормализованное русскоязычное название для поиска.
    normalized_name_ru: str

    # normalized_name_lat хранит нормализованное латинское название для поиска.
    normalized_name_lat: str

    # atc_codes хранит ATC-коды препарата.
    atc_codes: list[str]

    # active_substances хранит действующие вещества препарата.
    active_substances: list[str]

    # searchable_text хранит объединенный нормализованный текст признаков препарата.
    searchable_text: str


@dataclass
class DrugCatalogMatch:
    """Хранит результат полнотного поиска препарата по признакам."""

    # doc_id хранит идентификатор найденного документа.
    doc_id: str

    # drug_name_ru хранит русскоязычное название найденного препарата.
    drug_name_ru: str

    # drug_name_lat хранит латинское название найденного препарата.
    drug_name_lat: str

    # score хранит итоговый rule-based score совпадения.
    score: float

    # match_reasons хранит причины, по которым препарат был включен в выдачу.
    match_reasons: list[str]


@dataclass
class FindAllBundle:
    """Хранит полный результат полнотного поиска препаратов по признакам."""

    # matched_entities хранит найденные структурные сущности запроса.
    matched_entities: list[EntityMatch]

    # matched_drug_documents хранит найденные карточки препаратов по торговому названию.
    matched_drug_documents: list[DrugDocumentMatch]

    # catalog_matches хранит полный список найденных препаратов по признакам.
    catalog_matches: list[DrugCatalogMatch]
