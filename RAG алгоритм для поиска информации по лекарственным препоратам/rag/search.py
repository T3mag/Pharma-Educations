"""Логика hybrid retrieval и подготовки контекста для RAG."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from .common import (
    build_drug_document_entries,
    build_search_scope_doc_ids,
    count_active_substances,
    create_embeddings_batch,
    find_drug_document_matches,
    find_entity_matches,
    has_active_substance_entity,
    infer_section_hints,
    is_core_section,
    is_service_section,
    load_entity_matches,
    normalize_scalar_text,
    normalize_search_text,
)
from .config import DEFAULT_SEARCH_OVERFETCH_FACTOR
from .models import EntityMatch, GroupedDocumentResult, RankedChunkResult, RetrievalBundle


def build_doc_id_filter(candidate_doc_ids: list[str]) -> Optional[dict[str, Any]]:
    """Строит metadata-filter ChromaDB по списку candidate doc_id."""

    if not candidate_doc_ids:
        return None

    # unique_doc_ids хранит doc_id без дубликатов и пустых значений.
    unique_doc_ids = [
        candidate_doc_id
        for candidate_doc_id in dict.fromkeys(candidate_doc_ids)
        if normalize_scalar_text(candidate_doc_id)
    ]

    if not unique_doc_ids:
        return None

    if len(unique_doc_ids) == 1:
        # where_filter хранит точный фильтр для одного документа.
        where_filter = {"doc_id": unique_doc_ids[0]}
        return where_filter

    # where_filter хранит фильтр по нескольким doc_id с использованием оператора $in.
    where_filter = {"doc_id": {"$in": unique_doc_ids}}

    # return_value содержит готовый metadata-filter ChromaDB.
    return where_filter


def search_collection(
    collection: Any,
    gigachat_client: Any,
    query: str,
    model_name: str,
    n_results: int,
    candidate_doc_ids: Optional[list[str]] = None,
    overfetch_factor: int = DEFAULT_SEARCH_OVERFETCH_FACTOR,
) -> dict[str, Any]:
    """Выполняет семантический поиск по коллекции ChromaDB с optional-фильтрацией по doc_id."""

    # normalized_query хранит очищенный поисковый запрос пользователя.
    normalized_query = normalize_scalar_text(query)
    if not normalized_query:
        raise RuntimeError("Поисковый запрос не должен быть пустым.")

    # query_embedding_batch хранит embedding для одного поискового запроса.
    query_embedding_batch = create_embeddings_batch(
        gigachat_client=gigachat_client,
        texts=[normalized_query],
        model_name=model_name,
    )

    # query_embedding хранит embedding-вектор единственного поискового запроса.
    query_embedding = query_embedding_batch[0]

    # where_filter хранит metadata-filter ChromaDB по candidate_doc_ids, если они найдены через entity_relations.
    where_filter = build_doc_id_filter(candidate_doc_ids or [])

    # retrieval_limit хранит число чанков, которое нужно запросить до reranking и grouping.
    retrieval_limit = max(n_results * overfetch_factor, n_results)

    # results хранит результаты векторного поиска по коллекции.
    if where_filter is None:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=retrieval_limit,
        )
    else:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=retrieval_limit,
            where=where_filter,
        )

    # return_value содержит сырой ответ ChromaDB на поисковый запрос.
    return results


def run_hybrid_retrieval(
    collection: Any,
    gigachat_client: Any,
    query: str,
    embedding_model_name: str,
    n_results: int,
    overfetch_factor: int,
    entity_relations_path: Path,
    structured_documents_path: Path,
) -> RetrievalBundle:
    """Выполняет полный retrieval-пайплайн и возвращает все промежуточные и финальные результаты."""

    # loaded_entity_matches хранит агрегированные сущности из entity_relations для entity-aware retrieval.
    loaded_entity_matches = load_entity_matches(entity_relations_path)

    # drug_document_entries хранит индекс торговых названий препаратов из structured_documents.
    drug_document_entries = build_drug_document_entries(structured_documents_path)

    # matched_entities хранит сущности, найденные в пользовательском запросе.
    matched_entities = find_entity_matches(
        query=query,
        entity_matches=loaded_entity_matches,
    )

    # matched_drug_documents хранит найденные по торговому названию карточки препаратов.
    matched_drug_documents = find_drug_document_matches(
        query=query,
        drug_document_entries=drug_document_entries,
    )

    # candidate_doc_ids хранит итоговую область поиска по документам для constrained retrieval.
    candidate_doc_ids = build_search_scope_doc_ids(
        matched_entities=matched_entities,
        matched_drug_documents=matched_drug_documents,
    )

    # section_hints хранит предпочтительные разделы инструкции, извлеченные из формулировки запроса.
    section_hints = infer_section_hints(query)

    # raw_results хранит сырой ответ ChromaDB на constrained или global vector search.
    raw_results = search_collection(
        collection=collection,
        gigachat_client=gigachat_client,
        query=query,
        model_name=embedding_model_name,
        n_results=n_results,
        candidate_doc_ids=candidate_doc_ids,
        overfetch_factor=overfetch_factor,
    )

    # flat_chunk_results хранит плоский список найденных чанков до rule-based reranking.
    flat_chunk_results = flatten_search_results(raw_results)

    # reranked_chunk_results хранит чанки после пересортировки с учетом section hints и candidate docs.
    reranked_chunk_results = rerank_chunk_results(
        query=query,
        chunk_results=flat_chunk_results,
        section_hints=section_hints,
        candidate_doc_ids=candidate_doc_ids,
        matched_entities=matched_entities,
    )

    # grouped_results хранит финальную сгруппированную выдачу по документам.
    grouped_results = group_chunk_results(
        chunk_results=reranked_chunk_results,
        n_results=n_results,
    )

    # retrieval_bundle хранит все результаты retrieval в одной структуре.
    retrieval_bundle = RetrievalBundle(
        matched_entities=matched_entities,
        matched_drug_documents=matched_drug_documents,
        candidate_doc_ids=candidate_doc_ids,
        section_hints=section_hints,
        raw_results=raw_results,
        flat_chunk_results=flat_chunk_results,
        reranked_chunk_results=reranked_chunk_results,
        grouped_results=grouped_results,
    )

    # return_value содержит полный пакет retrieval-данных.
    return retrieval_bundle


def flatten_search_results(results: dict[str, Any]) -> list[RankedChunkResult]:
    """Приводит сырой ответ ChromaDB к плоскому списку чанков для дальнейшего reranking."""

    # result_documents хранит список найденных документов первого поискового запроса.
    result_documents = results.get("documents", [[]])[0]

    # result_metadatas хранит metadata найденных документов первого поискового запроса.
    result_metadatas = results.get("metadatas", [[]])[0]

    # result_distances хранит расстояния или similarity-метрики для найденных документов.
    result_distances = results.get("distances", [[]])[0] if results.get("distances") else []

    # ranked_chunk_results хранит плоский список найденных чанков со score и metadata.
    ranked_chunk_results: list[RankedChunkResult] = []

    # result_index по очереди перебирает позиции результатов поиска.
    for result_index, document_text in enumerate(result_documents):
        # result_metadata хранит metadata текущего найденного результата.
        result_metadata = result_metadatas[result_index] if result_index < len(result_metadatas) else {}

        # result_distance хранит расстояние текущего результата, если ChromaDB его вернул.
        result_distance = result_distances[result_index] if result_index < len(result_distances) else 0.0

        # ranked_chunk_result хранит один найденный чанк в нормализованном виде.
        ranked_chunk_result = RankedChunkResult(
            chunk_id=normalize_scalar_text(result_metadata.get("chunk_id")),
            doc_id=normalize_scalar_text(result_metadata.get("doc_id")),
            drug_name_ru=normalize_scalar_text(result_metadata.get("drug_name_ru")),
            section_name=normalize_scalar_text(result_metadata.get("section_name")),
            document_text=normalize_scalar_text(document_text),
            metadata=result_metadata if isinstance(result_metadata, dict) else {},
            distance=float(result_distance),
            reranked_score=float(result_distance),
        )
        ranked_chunk_results.append(ranked_chunk_result)

    # return_value содержит плоский список чанков для reranking и grouping.
    return ranked_chunk_results


def rerank_chunk_results(
    query: str,
    chunk_results: list[RankedChunkResult],
    section_hints: list[str],
    candidate_doc_ids: list[str],
    matched_entities: list[EntityMatch],
) -> list[RankedChunkResult]:
    """Применяет простой rule-based reranking поверх результатов vector search."""

    # normalized_query хранит нормализованный текст запроса для дополнительных текстовых эвристик.
    normalized_query = normalize_search_text(query)

    # active_substance_query_found показывает, что запрос распознан как поиск по действующему веществу.
    active_substance_query_found = has_active_substance_entity(matched_entities)

    # reranked_results хранит чанки после вычисления окончательного score.
    reranked_results: list[RankedChunkResult] = []

    # chunk_result по очереди перебирает найденные чанки.
    for chunk_result in chunk_results:
        # reranked_score хранит score, где меньшее значение означает более релевантный результат.
        reranked_score = chunk_result.distance

        if candidate_doc_ids and chunk_result.doc_id in candidate_doc_ids:
            reranked_score -= 0.40

        if section_hints and chunk_result.section_name in section_hints:
            reranked_score -= 1.20

        if not section_hints and is_service_section(chunk_result.section_name):
            reranked_score += 0.80

        if not section_hints and is_core_section(chunk_result.section_name):
            reranked_score -= 0.35

        # normalized_drug_name хранит нормализованное название препарата текущего чанка.
        normalized_drug_name = normalize_search_text(chunk_result.drug_name_ru)
        if normalized_drug_name and normalized_drug_name in normalized_query:
            reranked_score -= 0.20

        # normalized_section_name хранит нормализованное название раздела чанка.
        normalized_section_name = normalize_search_text(chunk_result.section_name)
        if normalized_section_name and normalized_section_name in normalized_query:
            reranked_score -= 0.10

        # active_substance_count хранит число действующих веществ в препарате текущего чанка.
        active_substance_count = count_active_substances(chunk_result.metadata)
        if active_substance_query_found and active_substance_count == 1:
            reranked_score -= 0.45
        if active_substance_query_found and active_substance_count > 1:
            reranked_score += 0.20

        reranked_results.append(
            RankedChunkResult(
                chunk_id=chunk_result.chunk_id,
                doc_id=chunk_result.doc_id,
                drug_name_ru=chunk_result.drug_name_ru,
                section_name=chunk_result.section_name,
                document_text=chunk_result.document_text,
                metadata=chunk_result.metadata,
                distance=chunk_result.distance,
                reranked_score=reranked_score,
            )
        )

    # sorted_results хранит чанки, отсортированные по новому score и затем по исходному расстоянию.
    sorted_results = sorted(
        reranked_results,
        key=lambda item: (item.reranked_score, item.distance, item.chunk_id),
    )

    # return_value содержит пересортированные результаты поиска.
    return sorted_results


def group_chunk_results(chunk_results: list[RankedChunkResult], n_results: int) -> list[GroupedDocumentResult]:
    """Группирует чанки по doc_id и оставляет top-n документов с лучшими score."""

    # grouped_documents_by_id хранит промежуточные группы чанков по одному doc_id.
    grouped_documents_by_id: dict[str, GroupedDocumentResult] = {}

    # chunk_result по очереди перебирает ранжированные чанки.
    for chunk_result in chunk_results:
        if not chunk_result.doc_id:
            continue

        if chunk_result.doc_id not in grouped_documents_by_id:
            grouped_documents_by_id[chunk_result.doc_id] = GroupedDocumentResult(
                doc_id=chunk_result.doc_id,
                drug_name_ru=chunk_result.drug_name_ru,
                best_score=chunk_result.reranked_score,
                matched_sections=[],
                chunks=[],
            )

        # grouped_document_result хранит текущую группу документа, в которую добавляется чанк.
        grouped_document_result = grouped_documents_by_id[chunk_result.doc_id]

        # existing_section_chunks_count хранит число уже добавленных чанков из того же раздела.
        existing_section_chunks_count = sum(
            1
            for existing_chunk in grouped_document_result.chunks
            if existing_chunk.section_name == chunk_result.section_name
        )
        if existing_section_chunks_count >= 2:
            continue

        grouped_document_result.chunks.append(chunk_result)
        grouped_document_result.best_score = min(grouped_document_result.best_score, chunk_result.reranked_score)

        if chunk_result.section_name and chunk_result.section_name not in grouped_document_result.matched_sections:
            grouped_document_result.matched_sections.append(chunk_result.section_name)

    # grouped_document_result по очереди перебирает все собранные группы документов.
    for grouped_document_result in grouped_documents_by_id.values():
        grouped_document_result.chunks = sorted(
            grouped_document_result.chunks,
            key=lambda item: (item.reranked_score, item.distance, item.chunk_id),
        )

    # grouped_document_results хранит список групп, отсортированных по лучшему score документа.
    grouped_document_results = sorted(
        grouped_documents_by_id.values(),
        key=lambda item: (item.best_score, item.doc_id),
    )

    # limited_grouped_results хранит только top-n документов для финального ответа.
    limited_grouped_results = grouped_document_results[:n_results]

    # return_value содержит сгруппированные результаты поиска по документам.
    return limited_grouped_results


def select_context_chunks(
    grouped_results: list[GroupedDocumentResult],
    context_chunk_limit: int,
    answer_mode: str,
) -> list[RankedChunkResult]:
    """Отбирает ограниченное число лучших чанков для передачи в модель как контекст."""

    # selected_chunks хранит чанки, которые войдут в контекст модели.
    selected_chunks: list[RankedChunkResult] = []

    # multi_document_mode показывает, что вопрос требует охватить несколько документов, а не один.
    multi_document_mode = answer_mode in {"entity_list", "category_list"}

    if multi_document_mode:
        # grouped_result по очереди перебирает документы из финальной выдачи.
        for grouped_result in grouped_results:
            if len(selected_chunks) >= context_chunk_limit:
                break

            if not grouped_result.chunks:
                continue

            # first_chunk хранит лучший чанк текущего документа.
            first_chunk = grouped_result.chunks[0]
            selected_chunks.append(first_chunk)

        if len(selected_chunks) < context_chunk_limit:
            # grouped_result по очереди перебирает документы повторно, чтобы добрать второй лучший чанк при необходимости.
            for grouped_result in grouped_results:
                if len(selected_chunks) >= context_chunk_limit:
                    break

                # grouped_chunk по очереди перебирает дополнительные чанки документа, начиная со второго.
                for grouped_chunk in grouped_result.chunks[1:]:
                    if len(selected_chunks) >= context_chunk_limit:
                        break
                    selected_chunks.append(grouped_chunk)
    else:
        # grouped_result по очереди перебирает документы из финальной выдачи.
        for grouped_result in grouped_results:
            # grouped_chunk по очереди перебирает чанки текущего документа в порядке релевантности.
            for grouped_chunk in grouped_result.chunks:
                if len(selected_chunks) >= context_chunk_limit:
                    break
                selected_chunks.append(grouped_chunk)

            if len(selected_chunks) >= context_chunk_limit:
                break

    # return_value содержит ограниченный список лучших чанков для контекста модели.
    return selected_chunks
