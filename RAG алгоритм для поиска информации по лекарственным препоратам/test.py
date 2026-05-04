"""CLI-скрипт для индексации retrieval-ready чанков, тестового поиска и первого RAG-ответа.

Скрипт решает две задачи:
1. Индексирует чанки из chunks.jsonl в коллекцию ChromaDB.
2. Выполняет тестовый семантический поиск по уже созданной коллекции.
3. Выполняет retrieval + generation и формирует готовый ответ модели.

Примечание:
- Этот файл сохранен как совместимый старый entrypoint.
- Предпочтительная точка запуска CLI теперь находится в app.py.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any, Optional

from rag.clients import build_chroma_collection, build_gigachat_client, ensure_gigachat_credentials
from rag.common import (
    build_chunk_metadata,
    build_drug_catalog_entries,
    build_drug_document_entries,
    batched,
    create_embeddings_batch,
    iter_indexable_chunks,
    is_likely_unknown_single_drug_query,
    load_jsonl_records,
    match_drug_catalog_entries,
    normalize_scalar_text,
    normalize_string_list,
    remove_empty_metadata_values,
    run_find_all_retrieval,
    tokenize_feature_query,
)
from rag.config import (
    DEFAULT_ANSWER_MAX_TOKENS,
    DEFAULT_BATCH_SIZE,
    DEFAULT_CHAT_MODEL,
    DEFAULT_CHROMA_PATH,
    DEFAULT_CHUNKS_PATH,
    DEFAULT_COLLECTION_NAME,
    DEFAULT_CONTEXT_CHUNKS,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_ENTITY_RELATIONS_PATH,
    DEFAULT_FIND_ALL_SUMMARY_LIMIT,
    DEFAULT_QUERY_RESULTS,
    DEFAULT_SEARCH_OVERFETCH_FACTOR,
    DEFAULT_STRUCTURED_DOCUMENTS_PATH,
    DEFAULT_TIMEOUT_SECONDS,
)
from rag.models import (
    AnswerValidationResult,
    DrugCatalogMatch,
    DrugDocumentMatch,
    EntityMatch,
    FindAllBundle,
    GroupedDocumentResult,
    RankedChunkResult,
    RetrievalBundle,
)
from rag.search import run_hybrid_retrieval
from rag.generation import generate_find_all_answer, generate_questions_answer, generate_rag_answer


def parse_arguments() -> argparse.Namespace:
    """Разбирает аргументы командной строки и возвращает конфигурацию запуска."""

    # parser описывает интерфейс запуска скрипта из терминала.
    parser = argparse.ArgumentParser(
        description="Индексация чанков в ChromaDB и тестовый поиск через EmbeddingsGigaR.",
    )

    # common_parent_parser хранит общие аргументы для команд index и search.
    common_parent_parser = argparse.ArgumentParser(add_help=False)

    # chunks_path_argument указывает путь к chunks.jsonl.
    common_parent_parser.add_argument(
        "--chunks-path",
        type=Path,
        default=DEFAULT_CHUNKS_PATH,
        help="Путь к chunks.jsonl.",
    )

    # chroma_path_argument указывает каталог persistent-хранилища ChromaDB.
    common_parent_parser.add_argument(
        "--chroma-path",
        type=Path,
        default=DEFAULT_CHROMA_PATH,
        help="Каталог для persistent-хранилища ChromaDB.",
    )

    # entity_relations_path_argument указывает путь к JSONL-файлу со связями между сущностями и документами.
    common_parent_parser.add_argument(
        "--entity-relations-path",
        type=Path,
        default=DEFAULT_ENTITY_RELATIONS_PATH,
        help="Путь к entity_relations.jsonl.",
    )

    # structured_documents_path_argument указывает путь к JSONL-файлу со структурированными карточками препаратов.
    common_parent_parser.add_argument(
        "--structured-documents-path",
        type=Path,
        default=DEFAULT_STRUCTURED_DOCUMENTS_PATH,
        help="Путь к structured_documents.jsonl.",
    )

    # collection_name_argument указывает имя коллекции ChromaDB.
    common_parent_parser.add_argument(
        "--collection-name",
        type=str,
        default=DEFAULT_COLLECTION_NAME,
        help="Имя коллекции ChromaDB.",
    )

    # model_argument указывает embedding-модель GigaChat.
    common_parent_parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_EMBEDDING_MODEL,
        help="Имя embedding-модели GigaChat.",
    )

    # timeout_argument указывает таймаут запросов к embeddings API.
    common_parent_parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Таймаут запросов к API GigaChat в секундах.",
    )

    # verify_ssl_argument включает проверку SSL-сертификатов для GigaChat API.
    common_parent_parser.add_argument(
        "--verify-ssl-certs",
        action="store_true",
        help="Включить проверку SSL-сертификатов для GigaChat API.",
    )

    # subparsers хранит набор подкоманд CLI.
    subparsers = parser.add_subparsers(dest="command", required=True)

    # index_parser описывает режим индексации чанков в ChromaDB.
    index_parser = subparsers.add_parser(
        "index",
        parents=[common_parent_parser],
        help="Индексировать chunks.jsonl в ChromaDB.",
    )

    # batch_size_argument указывает размер батча для индексации.
    index_parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="Размер батча для расчета embeddings и записи в ChromaDB.",
    )

    # limit_argument ограничивает число обрабатываемых чанков при отладке.
    index_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Ограничить число индексируемых чанков.",
    )

    # reset_argument указывает, что коллекцию нужно удалить и создать заново перед индексацией.
    index_parser.add_argument(
        "--reset",
        action="store_true",
        help="Удалить коллекцию перед новой индексацией.",
    )

    # search_parser описывает режим поиска по уже построенной коллекции.
    search_parser = subparsers.add_parser(
        "search",
        parents=[common_parent_parser],
        help="Выполнить тестовый поиск по коллекции ChromaDB.",
    )

    # query_argument хранит пользовательский поисковый запрос.
    search_parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="Текст поискового запроса.",
    )

    # n_results_argument указывает число результатов поиска.
    search_parser.add_argument(
        "--n-results",
        type=int,
        default=DEFAULT_QUERY_RESULTS,
        help="Число результатов поиска.",
    )

    # overfetch_factor_argument указывает, во сколько раз retrieval должен взять больше чанков до группировки.
    search_parser.add_argument(
        "--overfetch-factor",
        type=int,
        default=DEFAULT_SEARCH_OVERFETCH_FACTOR,
        help="Во сколько раз расширять retrieval до группировки по документам.",
    )

    # ask_parser описывает режим полного RAG-пайплайна: retrieval + generation.
    ask_parser = subparsers.add_parser(
        "ask",
        parents=[common_parent_parser],
        help="Выполнить retrieval и сгенерировать итоговый ответ модели.",
    )

    # ask_query_argument хранит пользовательский вопрос для полного RAG-ответа.
    ask_parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="Вопрос пользователя для retrieval и генерации ответа.",
    )

    # ask_n_results_argument указывает число документов, которое retrieval вернет до сборки контекста.
    ask_parser.add_argument(
        "--n-results",
        type=int,
        default=DEFAULT_QUERY_RESULTS,
        help="Число документов, которые retrieval вернет перед генерацией ответа.",
    )

    # ask_overfetch_factor_argument указывает, насколько расширять vector retrieval до группировки.
    ask_parser.add_argument(
        "--overfetch-factor",
        type=int,
        default=DEFAULT_SEARCH_OVERFETCH_FACTOR,
        help="Во сколько раз расширять retrieval до группировки по документам.",
    )

    # chat_model_argument указывает имя модели GigaChat, которая будет формировать итоговый ответ.
    ask_parser.add_argument(
        "--chat-model",
        type=str,
        default=DEFAULT_CHAT_MODEL,
        help="Имя модели GigaChat для генерации ответа.",
    )

    # context_chunks_argument указывает число чанков, включаемых в контекст модели.
    ask_parser.add_argument(
        "--context-chunks",
        type=int,
        default=DEFAULT_CONTEXT_CHUNKS,
        help="Число лучших чанков, передаваемых в модель как контекст.",
    )

    # answer_max_tokens_argument указывает ограничение на длину финального ответа модели.
    ask_parser.add_argument(
        "--answer-max-tokens",
        type=int,
        default=DEFAULT_ANSWER_MAX_TOKENS,
        help="Максимальное число токенов в финальном ответе модели.",
    )

    # find_all_parser описывает режим полнотного поиска препаратов по признакам.
    find_all_parser = subparsers.add_parser(
        "find-all",
        parents=[common_parent_parser],
        help="Найти все препараты, подходящие по признакам запроса.",
    )

    # find_all_query_argument хранит строку признаков для полнотного поиска.
    find_all_parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="Запрос с признаками для полнотного поиска препаратов.",
    )

    # find_all_limit_argument позволяет ограничить длину печатной выдачи при необходимости.
    find_all_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Ограничить число найденных препаратов в печатной выдаче.",
    )

    # find_all_ask_parser описывает режим полнотного поиска с последующим LLM-резюме.
    find_all_ask_parser = subparsers.add_parser(
        "find-all-ask",
        parents=[common_parent_parser],
        help="Найти все препараты по признакам и попросить модель кратко объяснить результат.",
    )

    # find_all_ask_query_argument хранит строку признаков для полнотного поиска с последующим резюме.
    find_all_ask_parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="Запрос с признаками для полнотного поиска и LLM-резюме.",
    )

    # find_all_ask_limit_argument позволяет ограничить длину печатного списка найденных препаратов.
    find_all_ask_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Ограничить число найденных препаратов в печатной выдаче.",
    )

    # find_all_ask_chat_model_argument указывает модель GigaChat для краткого резюме полного списка.
    find_all_ask_parser.add_argument(
        "--chat-model",
        type=str,
        default=DEFAULT_CHAT_MODEL,
        help="Имя модели GigaChat для краткого резюме полного списка препаратов.",
    )

    # find_all_ask_answer_max_tokens_argument ограничивает размер LLM-резюме.
    find_all_ask_parser.add_argument(
        "--answer-max-tokens",
        type=int,
        default=DEFAULT_ANSWER_MAX_TOKENS,
        help="Максимальное число токенов в кратком резюме полного списка.",
    )

    # find_all_ask_summary_limit_argument ограничивает число препаратов, передаваемых в LLM-контекст.
    find_all_ask_parser.add_argument(
        "--summary-limit",
        type=int,
        default=DEFAULT_FIND_ALL_SUMMARY_LIMIT,
        help="Максимальное число найденных препаратов, включаемых в LLM-сводку.",
    )

    # generate_questions_parser описывает режим генерации списка вопросов по найденным препаратам.
    generate_questions_parser = subparsers.add_parser(
        "generate-questions",
        parents=[common_parent_parser],
        help="Сгенерировать список вопросов по теме на основе полнотного поиска препаратов.",
    )

    # generate_questions_query_argument хранит пользовательский тематический запрос.
    generate_questions_parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="Тематический запрос, по которому нужно сгенерировать вопросы.",
    )

    # generate_questions_count_argument хранит число вопросов, которое должна сгенерировать модель.
    generate_questions_parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="Сколько вопросов нужно сгенерировать.",
    )

    # generate_questions_with_answers_argument включает генерацию ответов на каждый сгенерированный вопрос.
    generate_questions_parser.add_argument(
        "--with-answers",
        action="store_true",
        help="Сразу сгенерировать краткий grounded-ответ на каждый созданный вопрос.",
    )

    # generate_questions_chat_model_argument указывает модель GigaChat для генерации вопросов.
    generate_questions_parser.add_argument(
        "--chat-model",
        type=str,
        default=DEFAULT_CHAT_MODEL,
        help="Имя модели GigaChat для генерации вопросов.",
    )

    # generate_questions_answer_max_tokens_argument ограничивает размер ответа с вопросами.
    generate_questions_parser.add_argument(
        "--answer-max-tokens",
        type=int,
        default=DEFAULT_ANSWER_MAX_TOKENS,
        help="Максимальное число токенов в ответе со списком вопросов.",
    )

    # generate_questions_summary_limit_argument ограничивает число препаратов, включаемых в LLM-сводку.
    generate_questions_parser.add_argument(
        "--summary-limit",
        type=int,
        default=DEFAULT_FIND_ALL_SUMMARY_LIMIT,
        help="Максимальное число найденных препаратов, включаемых в контекст генерации вопросов.",
    )

    # generate_questions_n_results_argument указывает число документов retrieval для ответа на каждый вопрос.
    generate_questions_parser.add_argument(
        "--n-results",
        type=int,
        default=DEFAULT_QUERY_RESULTS,
        help="Число документов retrieval для ответа на каждый сгенерированный вопрос.",
    )

    # generate_questions_overfetch_factor_argument указывает степень расширения retrieval для ответов.
    generate_questions_parser.add_argument(
        "--overfetch-factor",
        type=int,
        default=DEFAULT_SEARCH_OVERFETCH_FACTOR,
        help="Во сколько раз расширять retrieval до группировки при ответе на каждый вопрос.",
    )

    # generate_questions_context_chunks_argument указывает число чанков в контексте ответа на каждый вопрос.
    generate_questions_parser.add_argument(
        "--context-chunks",
        type=int,
        default=DEFAULT_CONTEXT_CHUNKS,
        help="Число чанков, передаваемых в модель для ответа на каждый сгенерированный вопрос.",
    )

    # return_value содержит разобранные аргументы запуска.
    return parser.parse_args()


def index_chunks(
    collection: Any,
    gigachat_client: Any,
    chunks_path: Path,
    model_name: str,
    batch_size: int,
    limit: Optional[int] = None,
) -> None:
    """Индексирует чанки в коллекцию ChromaDB с батчевым расчетом embeddings."""

    print("Loading indexable chunks...")

    # chunk_stream хранит ленивый поток валидных чанков, пригодных для индексации.
    chunk_stream = iter_indexable_chunks(chunks_path=chunks_path, limit=limit)

    # processed_records_count хранит число чанков, успешно обработанных и записанных в коллекцию.
    processed_records_count = 0

    # batch_index хранит номер текущего батча для логирования прогресса.
    batch_index = 0

    # chunk_batch по очереди перебирает чанки батчами фиксированного размера.
    for chunk_batch in batched(records=chunk_stream, batch_size=batch_size):
        batch_index += 1

        # batch_ids хранит идентификаторы чанков текущего батча.
        batch_ids = [normalize_scalar_text(chunk_record["chunk_id"]) for chunk_record in chunk_batch]

        # batch_documents хранит человекочитаемый текст чанков, который будет возвращаться из ChromaDB.
        batch_documents = [
            normalize_scalar_text(chunk_record.get("chunk_text"))
            for chunk_record in chunk_batch
        ]

        # batch_texts хранит retrieval_text, по которому реально считаются embeddings.
        batch_texts = [
            normalize_scalar_text(chunk_record.get("retrieval_text"))
            for chunk_record in chunk_batch
        ]

        # batch_metadatas хранит нормализованные metadata текущего батча без пустых значений.
        batch_metadatas = [
            remove_empty_metadata_values(build_chunk_metadata(chunk_record))
            for chunk_record in chunk_batch
        ]

        # batch_embeddings хранит embedding-векторы, полученные от GigaChat для текущего батча.
        batch_embeddings = create_embeddings_batch(
            gigachat_client=gigachat_client,
            texts=batch_texts,
            model_name=model_name,
        )

        collection.upsert(
            ids=batch_ids,
            embeddings=batch_embeddings,
            documents=batch_documents,
            metadatas=batch_metadatas,
        )

        processed_records_count += len(chunk_batch)
        print(f"Processed batch {batch_index}: total indexed chunks = {processed_records_count}")

    print("Indexing completed.")
    print(f"Stored chunks in collection: {collection.count()}")


def print_search_results(
    query: str,
    matched_entities: list[EntityMatch],
    matched_drug_documents: list[DrugDocumentMatch],
    section_hints: list[str],
    grouped_results: list[GroupedDocumentResult],
) -> None:
    """Печатает результаты hybrid search в понятном виде с учетом найденных сущностей и группировки."""

    if matched_entities:
        print("\nMatched entities:")

        # matched_entity по очереди перебирает найденные сущности справочника.
        for matched_entity in matched_entities[:10]:
            print(
                f"- type={matched_entity.entity_type}, "
                f"code={matched_entity.entity_code or 'N/A'}, "
                f"name={matched_entity.entity_name or 'N/A'}, "
                f"fragment={matched_entity.source_query_fragment}, "
                f"candidate_docs={len(matched_entity.candidate_doc_ids)}"
            )
    else:
        print("\nMatched entities: none")

    if matched_drug_documents:
        print("\nMatched drug documents:")

        # matched_drug_document по очереди перебирает найденные карточки препаратов.
        for matched_drug_document in matched_drug_documents[:10]:
            print(
                f"- doc_id={matched_drug_document.doc_id}, "
                f"drug_name_ru={matched_drug_document.drug_name_ru or 'N/A'}, "
                f"drug_name_lat={matched_drug_document.drug_name_lat or 'N/A'}, "
                f"fragment={matched_drug_document.source_query_fragment}"
            )
    else:
        print("\nMatched drug documents: none")

    print(f"\nSection hints: {section_hints if section_hints else 'none'}")
    print(f"Query: {query}")

    if not grouped_results:
        print("\nNo results found.")
        return

    print("\nGrouped search results:")

    # result_index по очереди перебирает группы документов, вошедшие в финальную выдачу.
    for result_index, grouped_result in enumerate(grouped_results, start=1):
        print("====")
        print(f"Rank: {result_index}")
        print(f"Drug: {grouped_result.drug_name_ru or 'N/A'}")
        print(f"Doc ID: {grouped_result.doc_id}")
        print(f"Best score: {grouped_result.best_score}")
        print(f"Matched sections: {grouped_result.matched_sections if grouped_result.matched_sections else 'N/A'}")

        # chunk_result по очереди перебирает чанки, вошедшие в группу текущего документа.
        for chunk_result in grouped_result.chunks[:3]:
            print("----")
            print(f"Chunk ID: {chunk_result.chunk_id}")
            print(f"Section: {chunk_result.section_name or 'N/A'}")
            print(f"Distance: {chunk_result.distance}")
            print(f"Reranked score: {chunk_result.reranked_score}")
            print("Text:")
            print(chunk_result.document_text)
            print("Metadata:")
            print(chunk_result.metadata)


def print_ask_results(
    query: str,
    retrieval_bundle: RetrievalBundle,
    answer_text: str,
    context_chunks: list[RankedChunkResult],
    validation_result: Optional[AnswerValidationResult] = None,
) -> None:
    """Печатает готовый RAG-ответ вместе с краткой сводкой retrieval и использованными источниками."""

    print(f"\nQuery: {query}")

    if retrieval_bundle.matched_entities:
        print("\nMatched entities:")

        # matched_entity по очереди перебирает найденные структурные сущности.
        for matched_entity in retrieval_bundle.matched_entities[:10]:
            print(
                f"- type={matched_entity.entity_type}, "
                f"code={matched_entity.entity_code or 'N/A'}, "
                f"name={matched_entity.entity_name or 'N/A'}, "
                f"fragment={matched_entity.source_query_fragment}"
            )
    else:
        print("\nMatched entities: none")

    if retrieval_bundle.matched_drug_documents:
        print("\nMatched drug documents:")

        # matched_drug_document по очереди перебирает найденные по названию препараты.
        for matched_drug_document in retrieval_bundle.matched_drug_documents[:10]:
            print(
                f"- doc_id={matched_drug_document.doc_id}, "
                f"drug_name_ru={matched_drug_document.drug_name_ru or 'N/A'}, "
                f"fragment={matched_drug_document.source_query_fragment}"
            )
    else:
        print("\nMatched drug documents: none")

    print(f"\nSection hints: {retrieval_bundle.section_hints if retrieval_bundle.section_hints else 'none'}")

    print("\nAnswer:")
    print(answer_text)

    if validation_result is not None:
        print("\nAnswer validation:")
        print(f"Status: {validation_result.status}")
        print(f"Grounding overlap: {validation_result.grounding_overlap_ratio:.2f}")
        print(
            "Primary drug focus: "
            + (validation_result.primary_drug_name or "not applicable")
        )
        print(
            "Mentioned context drugs: "
            + (
                ", ".join(validation_result.mentioned_context_drug_names)
                if validation_result.mentioned_context_drug_names
                else "none"
            )
        )
        if validation_result.issues:
            print("Potential issues:")
            for validation_issue in validation_result.issues:
                print(f"- {validation_issue}")
        else:
            print("Potential issues: none detected")

    print("\nSources:")

    # context_chunk по очереди перебирает чанки, реально использованные для генерации ответа.
    for context_chunk in context_chunks:
        print("----")
        print(f"Drug: {context_chunk.drug_name_ru or 'N/A'}")
        print(f"Doc ID: {context_chunk.doc_id or 'N/A'}")
        print(f"Section: {context_chunk.section_name or 'N/A'}")
        print(f"Chunk ID: {context_chunk.chunk_id or 'N/A'}")


def print_find_all_results(
    query: str,
    matched_entities: list[EntityMatch],
    matched_drug_documents: list[DrugDocumentMatch],
    catalog_matches: list[DrugCatalogMatch],
    limit: Optional[int],
    show_header: bool = True,
) -> None:
    """Печатает результаты полнотного поиска препаратов по признакам."""

    if show_header:
        print(f"\nQuery: {query}")

        if matched_entities:
            print("\nMatched entities:")

            # matched_entity по очереди перебирает найденные структурные сущности.
            for matched_entity in matched_entities[:10]:
                print(
                    f"- type={matched_entity.entity_type}, "
                    f"code={matched_entity.entity_code or 'N/A'}, "
                    f"name={matched_entity.entity_name or 'N/A'}, "
                    f"fragment={matched_entity.source_query_fragment}, "
                    f"candidate_docs={len(matched_entity.candidate_doc_ids)}"
                )
        else:
            print("\nMatched entities: none")

        if matched_drug_documents:
            print("\nMatched drug documents:")

            # matched_drug_document по очереди перебирает найденные по названию карточки препаратов.
            for matched_drug_document in matched_drug_documents[:10]:
                print(
                    f"- doc_id={matched_drug_document.doc_id}, "
                    f"drug_name_ru={matched_drug_document.drug_name_ru or 'N/A'}, "
                    f"fragment={matched_drug_document.source_query_fragment}"
                )
        else:
            print("\nMatched drug documents: none")

    if not catalog_matches:
        print("\nNo drugs found.")
        return

    # displayed_matches хранит список результатов, который реально будет выведен пользователю.
    displayed_matches = catalog_matches if limit is None else catalog_matches[:limit]

    print(f"\nFound drugs: {len(catalog_matches)}")
    if limit is not None:
        print(f"Displayed drugs: {len(displayed_matches)}")

    print("\nDrug list:")

    # match_index и catalog_match по очереди перебирают найденные препараты.
    for match_index, catalog_match in enumerate(displayed_matches, start=1):
        print("====")
        print(f"Rank: {match_index}")
        print(f"Drug: {catalog_match.drug_name_ru or 'N/A'}")
        print(f"Drug LAT: {catalog_match.drug_name_lat or 'N/A'}")
        print(f"Doc ID: {catalog_match.doc_id}")
        print(f"Score: {catalog_match.score}")
        print(f"Reasons: {catalog_match.match_reasons}")


def print_find_all_ask_results(
    query: str,
    find_all_bundle: FindAllBundle,
    answer_text: str,
    limit: Optional[int],
) -> None:
    """Печатает LLM-резюме полного списка препаратов и сам полный результат поиска."""

    print(f"\nQuery: {query}")

    if find_all_bundle.matched_entities:
        print("\nMatched entities:")

        # matched_entity по очереди перебирает найденные структурные сущности.
        for matched_entity in find_all_bundle.matched_entities[:10]:
            print(
                f"- type={matched_entity.entity_type}, "
                f"code={matched_entity.entity_code or 'N/A'}, "
                f"name={matched_entity.entity_name or 'N/A'}, "
                f"fragment={matched_entity.source_query_fragment}, "
                f"candidate_docs={len(matched_entity.candidate_doc_ids)}"
            )
    else:
        print("\nMatched entities: none")

    if find_all_bundle.matched_drug_documents:
        print("\nMatched drug documents:")

        # matched_drug_document по очереди перебирает найденные по названию карточки препаратов.
        for matched_drug_document in find_all_bundle.matched_drug_documents[:10]:
            print(
                f"- doc_id={matched_drug_document.doc_id}, "
                f"drug_name_ru={matched_drug_document.drug_name_ru or 'N/A'}, "
                f"fragment={matched_drug_document.source_query_fragment}"
            )
    else:
        print("\nMatched drug documents: none")

    print("\nAnswer:")
    print(answer_text)

    print_find_all_results(
        query=query,
        matched_entities=find_all_bundle.matched_entities,
        matched_drug_documents=find_all_bundle.matched_drug_documents,
        catalog_matches=find_all_bundle.catalog_matches,
        limit=limit,
        show_header=False,
    )


def print_generate_questions_results(
    query: str,
    question_count: int,
    find_all_bundle: FindAllBundle,
    answer_text: str,
    qa_pairs: Optional[list[tuple[str, str]]] = None,
) -> None:
    """Печатает список сгенерированных вопросов и краткую сводку полнотного поиска."""

    print(f"\nQuery: {query}")
    print(f"Requested questions: {question_count}")
    print(f"Found drugs: {len(find_all_bundle.catalog_matches)}")

    if find_all_bundle.matched_entities:
        print("\nMatched entities:")

        # matched_entity по очереди перебирает найденные структурные сущности.
        for matched_entity in find_all_bundle.matched_entities[:10]:
            print(
                f"- type={matched_entity.entity_type}, "
                f"code={matched_entity.entity_code or 'N/A'}, "
                f"name={matched_entity.entity_name or 'N/A'}, "
                f"fragment={matched_entity.source_query_fragment}"
            )
    else:
        print("\nMatched entities: none")

    if find_all_bundle.matched_drug_documents:
        print("\nMatched drug documents:")

        # matched_drug_document по очереди перебирает найденные по названию карточки препаратов.
        for matched_drug_document in find_all_bundle.matched_drug_documents[:10]:
            print(
                f"- doc_id={matched_drug_document.doc_id}, "
                f"drug_name_ru={matched_drug_document.drug_name_ru or 'N/A'}, "
                f"fragment={matched_drug_document.source_query_fragment}"
            )
    else:
        print("\nMatched drug documents: none")

    print("\nQuestions:")
    print(answer_text)

    if qa_pairs:
        print("\nQuestions with answers:")

        # qa_index и qa_pair по очереди перебирают пары вопрос-ответ.
        for qa_index, qa_pair in enumerate(qa_pairs, start=1):
            # generated_question хранит один сгенерированный вопрос.
            generated_question = qa_pair[0]

            # generated_answer хранит grounded-ответ на соответствующий вопрос.
            generated_answer = qa_pair[1]

            print("----")
            print(f"{qa_index}. Question: {generated_question}")
            print("Answer:")
            print(generated_answer)


def extract_generated_questions(answer_text: str, expected_count: int) -> list[str]:
    """Извлекает отдельные вопросы из текстового ответа модели со списком вопросов."""

    # extracted_questions хранит итоговый список извлеченных вопросов.
    extracted_questions: list[str] = []

    # answer_lines хранит непустые строки ответа модели.
    answer_lines = [answer_line.strip() for answer_line in answer_text.splitlines() if answer_line.strip()]

    # answer_line по очереди перебирает строки ответа модели.
    for answer_line in answer_lines:
        # normalized_line хранит строку без числового маркера списка в начале.
        normalized_line = re.sub(r"^\d+[\.\)]\s*", "", answer_line).strip()

        # normalized_line_without_bullet хранит строку без префикса-маркера списка.
        normalized_line_without_bullet = re.sub(r"^[-*]\s*", "", normalized_line).strip()

        if not normalized_line_without_bullet:
            continue

        if normalized_line_without_bullet not in extracted_questions:
            extracted_questions.append(normalized_line_without_bullet)

        if len(extracted_questions) >= max(expected_count, 1):
            break

    # return_value содержит список извлеченных вопросов в порядке появления.
    return extracted_questions


def main() -> None:
    """Запускает CLI-команду индексации или поиска."""

    # arguments хранит разобранные аргументы командной строки.
    arguments = parse_arguments()

    # gigachat_client хранит клиент GigaChat для embeddings и chat, если выбранный режим его требует.
    gigachat_client: Any = None

    # collection хранит коллекцию ChromaDB, если выбранный режим работает с vector search.
    collection: Any = None

    if arguments.command in {"index", "search", "ask", "find-all-ask", "generate-questions"}:
        # credentials хранит токен доступа к GigaChat API из переменной окружения.
        credentials = ensure_gigachat_credentials()

        # gigachat_client хранит клиент GigaChat для вызова embeddings API и chat API.
        gigachat_client = build_gigachat_client(
            credentials=credentials,
            timeout=arguments.timeout,
            verify_ssl_certs=arguments.verify_ssl_certs,
        )

    if arguments.command in {"index", "search", "ask"} or (
        arguments.command == "generate-questions" and arguments.with_answers
    ):
        # collection хранит коллекцию ChromaDB, с которой будет работать выбранная команда.
        collection = build_chroma_collection(
            chroma_path=arguments.chroma_path,
            collection_name=arguments.collection_name,
            reset=getattr(arguments, "reset", False),
        )

    if arguments.command == "index":
        index_chunks(
            collection=collection,
            gigachat_client=gigachat_client,
            chunks_path=arguments.chunks_path,
            model_name=arguments.model,
            batch_size=arguments.batch_size,
            limit=arguments.limit,
        )
        return

    if arguments.command == "search":
        # retrieval_bundle хранит полный результат retrieval для диагностического search-режима.
        retrieval_bundle = run_hybrid_retrieval(
            collection=collection,
            gigachat_client=gigachat_client,
            query=arguments.query,
            embedding_model_name=arguments.model,
            n_results=arguments.n_results,
            overfetch_factor=arguments.overfetch_factor,
            entity_relations_path=arguments.entity_relations_path,
            structured_documents_path=arguments.structured_documents_path,
        )

        print_search_results(
            query=arguments.query,
            matched_entities=retrieval_bundle.matched_entities,
            matched_drug_documents=retrieval_bundle.matched_drug_documents,
            section_hints=retrieval_bundle.section_hints,
            grouped_results=retrieval_bundle.grouped_results,
        )
        return

    if arguments.command == "ask":
        # retrieval_bundle хранит полный результат retrieval для последующей генерации ответа.
        retrieval_bundle = run_hybrid_retrieval(
            collection=collection,
            gigachat_client=gigachat_client,
            query=arguments.query,
            embedding_model_name=arguments.model,
            n_results=arguments.n_results,
            overfetch_factor=arguments.overfetch_factor,
            entity_relations_path=arguments.entity_relations_path,
            structured_documents_path=arguments.structured_documents_path,
        )

        # is_unknown_single_drug_query показывает, что запрос похож на конкретный препарат, но lookup его не распознал.
        is_unknown_single_drug_query = is_likely_unknown_single_drug_query(
            query=arguments.query,
            matched_entities=retrieval_bundle.matched_entities,
            matched_drug_documents=retrieval_bundle.matched_drug_documents,
            section_hints=retrieval_bundle.section_hints,
        )

        if is_unknown_single_drug_query:
            unknown_drug_message = (
                "Похоже, запрос относится к конкретному препарату, но такой препарат не найден в справочнике. "
                "Проверьте написание названия."
            )

            print_ask_results(
                query=arguments.query,
                retrieval_bundle=retrieval_bundle,
                answer_text=unknown_drug_message,
                context_chunks=[],
                validation_result=None,
            )
            return

        if not retrieval_bundle.grouped_results:
            print_ask_results(
                query=arguments.query,
                retrieval_bundle=retrieval_bundle,
                answer_text="По найденным данным ответ сформировать не удалось: retrieval не вернул релевантных результатов.",
                context_chunks=[],
                validation_result=None,
            )
            return

        # answer_text хранит итоговый ответ модели, context_chunks - реально использованные источники,
        # а validation_result - post-check проверку groundedness ответа.
        answer_text, context_chunks, validation_result = generate_rag_answer(
            gigachat_client=gigachat_client,
            query=arguments.query,
            retrieval_bundle=retrieval_bundle,
            chat_model_name=arguments.chat_model,
            context_chunk_limit=arguments.context_chunks,
            answer_max_tokens=arguments.answer_max_tokens,
        )

        print_ask_results(
            query=arguments.query,
            retrieval_bundle=retrieval_bundle,
            answer_text=answer_text,
            context_chunks=context_chunks,
            validation_result=validation_result,
        )
        return

    if arguments.command == "find-all":
        # find_all_bundle хранит полный результат полнотного поиска препаратов по признакам.
        find_all_bundle = run_find_all_retrieval(
            query=arguments.query,
            entity_relations_path=arguments.entity_relations_path,
            structured_documents_path=arguments.structured_documents_path,
        )

        print_find_all_results(
            query=arguments.query,
            matched_entities=find_all_bundle.matched_entities,
            matched_drug_documents=find_all_bundle.matched_drug_documents,
            catalog_matches=find_all_bundle.catalog_matches,
            limit=arguments.limit,
        )
        return

    if arguments.command == "find-all-ask":
        # find_all_bundle хранит полный результат полнотного поиска препаратов по признакам.
        find_all_bundle = run_find_all_retrieval(
            query=arguments.query,
            entity_relations_path=arguments.entity_relations_path,
            structured_documents_path=arguments.structured_documents_path,
        )

        if not find_all_bundle.catalog_matches:
            print_find_all_ask_results(
                query=arguments.query,
                find_all_bundle=find_all_bundle,
                answer_text="По найденным данным резюме сформировать не удалось: полнотный поиск не вернул препаратов.",
                limit=arguments.limit,
            )
            return

        # answer_text хранит краткое LLM-резюме полного списка найденных препаратов.
        answer_text = generate_find_all_answer(
            gigachat_client=gigachat_client,
            query=arguments.query,
            find_all_bundle=find_all_bundle,
            chat_model_name=arguments.chat_model,
            answer_max_tokens=arguments.answer_max_tokens,
            summary_limit=arguments.summary_limit,
        )

        print_find_all_ask_results(
            query=arguments.query,
            find_all_bundle=find_all_bundle,
            answer_text=answer_text,
            limit=arguments.limit,
        )
        return

    if arguments.command == "generate-questions":
        # find_all_bundle хранит полный результат полнотного поиска препаратов по теме пользователя.
        find_all_bundle = run_find_all_retrieval(
            query=arguments.query,
            entity_relations_path=arguments.entity_relations_path,
            structured_documents_path=arguments.structured_documents_path,
        )

        if not find_all_bundle.catalog_matches:
            print_generate_questions_results(
                query=arguments.query,
                question_count=arguments.count,
                find_all_bundle=find_all_bundle,
                answer_text="Вопросы не сгенерированы: полнотный поиск не нашел подходящих препаратов по теме.",
            )
            return

        # answer_text хранит список вопросов, сгенерированный по найденной теме.
        answer_text = generate_questions_answer(
            gigachat_client=gigachat_client,
            query=arguments.query,
            find_all_bundle=find_all_bundle,
            question_count=arguments.count,
            chat_model_name=arguments.chat_model,
            answer_max_tokens=arguments.answer_max_tokens,
            summary_limit=arguments.summary_limit,
        )

        # qa_pairs хранит пары "вопрос -> ответ", если пользователь запросил генерацию ответов.
        qa_pairs: Optional[list[tuple[str, str]]] = None

        if arguments.with_answers:
            # generated_questions хранит отдельные вопросы, извлеченные из ответа модели.
            generated_questions = extract_generated_questions(
                answer_text=answer_text,
                expected_count=arguments.count,
            )

            qa_pairs = []

            # generated_question по очереди перебирает сгенерированные вопросы.
            for generated_question in generated_questions:
                # retrieval_bundle хранит retrieval-результат для одного сгенерированного вопроса.
                retrieval_bundle = run_hybrid_retrieval(
                    collection=collection,
                    gigachat_client=gigachat_client,
                    query=generated_question,
                    embedding_model_name=arguments.model,
                    n_results=arguments.n_results,
                    overfetch_factor=arguments.overfetch_factor,
                    entity_relations_path=arguments.entity_relations_path,
                    structured_documents_path=arguments.structured_documents_path,
                )

                # generated_answer хранит grounded-ответ на один сгенерированный вопрос.
                if not retrieval_bundle.grouped_results:
                    generated_answer = (
                        "Ответ не сформирован: retrieval не нашел достаточно релевантных результатов."
                    )
                else:
                    generated_answer, _, _ = generate_rag_answer(
                        gigachat_client=gigachat_client,
                        query=generated_question,
                        retrieval_bundle=retrieval_bundle,
                        chat_model_name=arguments.chat_model,
                        context_chunk_limit=arguments.context_chunks,
                        answer_max_tokens=arguments.answer_max_tokens,
                    )

                qa_pairs.append((generated_question, generated_answer))

        print_generate_questions_results(
            query=arguments.query,
            question_count=arguments.count,
            find_all_bundle=find_all_bundle,
            answer_text=answer_text,
            qa_pairs=qa_pairs,
        )
        return

    raise RuntimeError(f"Неизвестная команда: {arguments.command}")


if __name__ == "__main__":
    main()
