"""Use case слой для RAG-вопросов."""

from __future__ import annotations

from ..api_models import AskRequest, AskResponse, SourceResponse, ValidationResponse
from ..common import is_likely_unknown_single_drug_query
from ..config import DEFAULT_ENTITY_RELATIONS_PATH, DEFAULT_STRUCTURED_DOCUMENTS_PATH
from ..generation import generate_rag_answer
from ..search import run_hybrid_retrieval
from .aggregate_search_service import try_execute_aggregate_ask
from .runtime import get_runtime


def execute_ask(request: AskRequest) -> AskResponse:
    """Выполняет общий RAG-пайплайн для CLI-подобного ask и chat."""

    aggregate_response = try_execute_aggregate_ask(
        query=request.query,
        limit=request.n_results if request.n_results > 50 else 200,
    )
    if aggregate_response is not None:
        return aggregate_response

    embedding_client, chat_client, collection = get_runtime()
    retrieval_bundle = run_hybrid_retrieval(
        collection=collection,
        gigachat_client=embedding_client,
        query=request.query,
        embedding_model_name=request.embedding_model,
        n_results=request.n_results,
        overfetch_factor=request.overfetch_factor,
        entity_relations_path=DEFAULT_ENTITY_RELATIONS_PATH,
        structured_documents_path=DEFAULT_STRUCTURED_DOCUMENTS_PATH,
    )

    if is_likely_unknown_single_drug_query(
        query=request.query,
        matched_entities=retrieval_bundle.matched_entities,
        matched_drug_documents=retrieval_bundle.matched_drug_documents,
        section_hints=retrieval_bundle.section_hints,
    ):
        return AskResponse(
            query=request.query,
            answer=(
                "Похоже, запрос относится к конкретному препарату, но такой препарат не найден "
                "в справочнике. Проверьте написание названия."
            ),
            matched_entities=[],
            matched_drug_documents=[],
            section_hints=retrieval_bundle.section_hints,
            sources=[],
            validation=None,
        )

    if not retrieval_bundle.grouped_results:
        return AskResponse(
            query=request.query,
            answer="По найденным данным ответ сформировать не удалось: retrieval не вернул релевантных результатов.",
            matched_entities=[],
            matched_drug_documents=[],
            section_hints=retrieval_bundle.section_hints,
            sources=[],
            validation=None,
        )

    answer_text, context_chunks, validation_result = generate_rag_answer(
        gigachat_client=chat_client,
        query=request.query,
        retrieval_bundle=retrieval_bundle,
        chat_model_name=request.chat_model,
        context_chunk_limit=request.context_chunks,
        answer_max_tokens=request.answer_max_tokens,
    )

    return AskResponse(
        query=request.query,
        answer=answer_text,
        matched_entities=[
            {
                "type": item.entity_type,
                "code": item.entity_code,
                "name": item.entity_name,
                "fragment": item.source_query_fragment,
                "candidate_docs": len(item.candidate_doc_ids),
            }
            for item in retrieval_bundle.matched_entities
        ],
        matched_drug_documents=[
            {
                "doc_id": item.doc_id,
                "drug_name_ru": item.drug_name_ru,
                "drug_name_lat": item.drug_name_lat,
                "fragment": item.source_query_fragment,
            }
            for item in retrieval_bundle.matched_drug_documents
        ],
        section_hints=retrieval_bundle.section_hints,
        sources=[
            SourceResponse(
                drug=chunk.drug_name_ru,
                doc_id=chunk.doc_id,
                section=chunk.section_name,
                chunk_id=chunk.chunk_id,
            )
            for chunk in context_chunks
        ],
        validation=ValidationResponse(
            status=validation_result.status,
            grounding_overlap=validation_result.grounding_overlap_ratio,
            primary_drug_focus=validation_result.primary_drug_name,
            mentioned_context_drugs=validation_result.mentioned_context_drug_names,
            potential_issues=validation_result.issues,
        ),
    )
