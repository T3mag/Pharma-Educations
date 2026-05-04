"""Клиенты и фабрики внешних зависимостей для RAG-системы."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def ensure_gigachat_credentials() -> str:
    """Читает токен доступа GigaChat из переменной окружения."""

    # credentials хранит токен или OAuth-ключ для доступа к GigaChat API.
    credentials = os.environ.get("GIGACHAT_CREDENTIALS", "").strip()

    if not credentials:
        raise RuntimeError(
            "Не найдена переменная окружения GIGACHAT_CREDENTIALS. "
            "Секреты не должны храниться в коде."
        )

    # return_value содержит непустой токен доступа GigaChat.
    return credentials


def build_gigachat_client(credentials: str, timeout: int, verify_ssl_certs: bool) -> Any:
    """Создает клиент GigaChat через официальный Python SDK."""

    try:
        # GigaChat импортируется внутри функции, чтобы ошибка установки была явной и понятной.
        from gigachat import GigaChat
    except ImportError as import_error:
        raise RuntimeError(
            "Пакет 'gigachat' не установлен. Установите его командой 'pip install gigachat'."
        ) from import_error

    # gigachat_client хранит объект клиента GigaChat для вызова embeddings API.
    gigachat_client = GigaChat(
        credentials=credentials,
        timeout=timeout,
        verify_ssl_certs=verify_ssl_certs,
    )

    # return_value содержит готовый клиент GigaChat.
    return gigachat_client


def build_chroma_collection(chroma_path: Path, collection_name: str, reset: bool = False) -> Any:
    """Создает или открывает persistent-коллекцию ChromaDB."""

    try:
        # chromadb импортируется внутри функции, чтобы сообщение об отсутствии зависимости было понятнее.
        import chromadb
    except ImportError as import_error:
        raise RuntimeError(
            "Пакет 'chromadb' не установлен. Установите его командой 'pip install chromadb'."
        ) from import_error

    # chroma_path_string хранит путь к каталогу ChromaDB в строковом виде для клиента библиотеки.
    chroma_path_string = str(chroma_path.resolve())

    # chroma_client хранит persistent-клиент ChromaDB.
    chroma_client = chromadb.PersistentClient(path=chroma_path_string)

    if reset:
        try:
            chroma_client.delete_collection(name=collection_name)
        except Exception:
            pass

    # collection хранит открытую или заново созданную коллекцию ChromaDB.
    collection = chroma_client.get_or_create_collection(name=collection_name)

    # return_value содержит коллекцию ChromaDB, готовую к записи и поиску.
    return collection
