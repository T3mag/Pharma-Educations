"""Фабрики и кэш shared runtime-зависимостей."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from ..clients import (
    build_chroma_collection,
    build_gigachat_client,
    ensure_gigachat_chat_credentials,
    ensure_gigachat_embedding_credentials,
)
from ..common import load_jsonl_records
from ..config import (
    DEFAULT_CHROMA_PATH,
    DEFAULT_COLLECTION_NAME,
    DEFAULT_ENTITY_RELATIONS_PATH,
    DEFAULT_NORMALIZED_PAGES_PATH,
    DEFAULT_STRUCTURED_DOCUMENTS_PATH,
    DEFAULT_TIMEOUT_SECONDS,
)
from ..topics import TopicTree, build_topic_tree


@lru_cache(maxsize=1)
def get_runtime() -> tuple[Any, Any, Any]:
    """Лениво создает embedding/chat клиентов GigaChat и ChromaDB для повторного использования."""

    embedding_credentials = ensure_gigachat_embedding_credentials()
    chat_credentials = ensure_gigachat_chat_credentials()
    embedding_client = build_gigachat_client(
        credentials=embedding_credentials,
        timeout=DEFAULT_TIMEOUT_SECONDS,
        verify_ssl_certs=False,
    )
    chat_client = build_gigachat_client(
        credentials=chat_credentials,
        timeout=DEFAULT_TIMEOUT_SECONDS,
        verify_ssl_certs=False,
    )
    collection = build_chroma_collection(
        chroma_path=DEFAULT_CHROMA_PATH,
        collection_name=DEFAULT_COLLECTION_NAME,
        reset=False,
    )
    return embedding_client, chat_client, collection


@lru_cache(maxsize=1)
def get_topic_tree() -> TopicTree:
    """Лениво строит дерево тем по четырем указателям Vidal."""

    return build_topic_tree(
        normalized_pages_path=DEFAULT_NORMALIZED_PAGES_PATH,
        entity_relations_path=DEFAULT_ENTITY_RELATIONS_PATH,
    )


@lru_cache(maxsize=1)
def load_structured_documents_index() -> dict[str, dict[str, Any]]:
    """Загружает structured_documents.jsonl в индекс по doc_id."""

    documents_by_id: dict[str, dict[str, Any]] = {}
    for document_record in load_jsonl_records(DEFAULT_STRUCTURED_DOCUMENTS_PATH):
        doc_id = str(document_record.get("doc_id", "")).strip()
        if doc_id:
            documents_by_id[doc_id] = document_record
    return documents_by_id
