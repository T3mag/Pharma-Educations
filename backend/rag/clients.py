"""Клиенты и фабрики внешних зависимостей для RAG-системы."""

from __future__ import annotations

import os
import random
import re
import time
from pathlib import Path
from typing import Any, Optional

DEFAULT_RETRY_ATTEMPTS = 5
DEFAULT_RETRY_BASE_DELAY = 2.0


def parse_retry_delay_seconds(error_text: str) -> Optional[float]:
    """Пытается извлечь Retry-After или разумную паузу из текста ошибки."""

    retry_after_match = re.search(r"retry-after['\"]?:\s*['\"]?(\d+)", error_text, flags=re.IGNORECASE)
    if retry_after_match:
        return float(retry_after_match.group(1))
    return None


def is_transient_error_text(error_text: str) -> bool:
    """Определяет, относится ли ошибка к временным сбоям сети или rate limit."""

    transient_markers = (
        "timeout",
        "429",
        "too many requests",
        "rate limit",
        "500",
        "502",
        "503",
        "504",
        "connection",
        "reset",
        "broken pipe",
    )
    return any(marker in error_text for marker in transient_markers)


def retry_on_transient_error(func, *args, max_attempts: int = DEFAULT_RETRY_ATTEMPTS, base_delay: float = DEFAULT_RETRY_BASE_DELAY, **kwargs) -> Any:
    """Повторяет вызов при временных сбоях API с exponential backoff."""
    last_exception: Optional[Exception] = None
    for attempt in range(1, max_attempts + 1):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            last_exception = exc
            exc_text = str(exc).lower()
            if not is_transient_error_text(exc_text) or attempt == max_attempts:
                raise
            retry_after_delay = parse_retry_delay_seconds(str(exc))
            delay = retry_after_delay or (base_delay * (2 ** (attempt - 1)))
            delay += random.uniform(0.0, 0.75)
            time.sleep(delay)
    raise last_exception


def ensure_gigachat_credentials(
    env_name: str = "GIGACHAT_CREDENTIALS",
    fallback_env_names: tuple[str, ...] = (),
    label: str = "GigaChat",
) -> str:
    """Читает токен доступа GigaChat из переменной окружения."""

    credentials = os.environ.get(env_name, "").strip()
    if not credentials:
        for fallback_env_name in fallback_env_names:
            credentials = os.environ.get(fallback_env_name, "").strip()
            if credentials:
                break

    if not credentials:
        env_names_text = ", ".join((env_name, *fallback_env_names))
        raise RuntimeError(
            f"Не найдена переменная окружения для {label}: {env_names_text}. "
            "Секреты не должны храниться в коде."
        )

    return credentials


def ensure_gigachat_embedding_credentials() -> str:
    """Читает отдельный ключ GigaChat для embeddings с fallback на общий ключ."""

    return ensure_gigachat_credentials(
        env_name="GIGACHAT_EMBEDDING_CREDENTIALS",
        fallback_env_names=("GIGACHAT_CREDENTIALS",),
        label="GigaChat embeddings",
    )


def ensure_gigachat_chat_credentials() -> str:
    """Читает отдельный ключ GigaChat для chat/LLM с fallback на общий ключ."""

    return ensure_gigachat_credentials(
        env_name="GIGACHAT_CHAT_CREDENTIALS",
        fallback_env_names=("GIGACHAT_CREDENTIALS",),
        label="GigaChat chat",
    )


def build_gigachat_client(credentials: str, timeout: int, verify_ssl_certs: bool) -> Any:
    """Создает клиент GigaChat через официальный Python SDK."""

    try:
        from gigachat import GigaChat
    except ImportError as import_error:
        raise RuntimeError(
            "Пакет 'gigachat' не установлен. Установите его командой 'pip install gigachat'."
        ) from import_error

    gigachat_client = GigaChat(
        credentials=credentials,
        timeout=timeout,
        verify_ssl_certs=verify_ssl_certs,
    )

    return gigachat_client


def build_chroma_collection(chroma_path: Path, collection_name: str, reset: bool = False) -> Any:
    """Создает или открывает persistent-коллекцию ChromaDB."""

    try:
        import chromadb
    except ImportError as import_error:
        raise RuntimeError(
            "Пакет 'chromadb' не установлен. Установите его командой 'pip install chromadb'."
        ) from import_error

    chroma_path_string = str(chroma_path.resolve())

    chroma_client = chromadb.PersistentClient(path=chroma_path_string)

    if reset:
        try:
            chroma_client.delete_collection(name=collection_name)
        except Exception:
            pass

    collection = chroma_client.get_or_create_collection(name=collection_name)

    return collection
