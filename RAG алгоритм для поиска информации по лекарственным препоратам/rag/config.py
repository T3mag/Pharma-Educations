"""Конфигурация путей, констант и эвристик для RAG-системы."""

from __future__ import annotations

import re
from pathlib import Path


# PACKAGE_ROOT хранит путь к каталогу пакета rag/.
PACKAGE_ROOT = Path(__file__).resolve().parent

# PROJECT_ROOT хранит путь к корню каталога RAG/.
PROJECT_ROOT = PACKAGE_ROOT.parent

# DEFAULT_CHUNKS_PATH хранит путь к основному JSONL-файлу с retrieval-ready чанками.
DEFAULT_CHUNKS_PATH = PROJECT_ROOT / "chunks.jsonl"

# DEFAULT_ENTITY_RELATIONS_PATH хранит путь к JSONL-файлу со связями между сущностями и документами.
DEFAULT_ENTITY_RELATIONS_PATH = PROJECT_ROOT / "Data" / "entity_relations.jsonl"

# DEFAULT_STRUCTURED_DOCUMENTS_PATH хранит путь к JSONL-файлу со структурированными карточками препаратов.
DEFAULT_STRUCTURED_DOCUMENTS_PATH = PROJECT_ROOT / "Data" / "structured_documents.jsonl"

# DEFAULT_CHROMA_PATH хранит каталог persistent-данных ChromaDB.
DEFAULT_CHROMA_PATH = PROJECT_ROOT / "chroma_data"

# DEFAULT_COLLECTION_NAME хранит имя коллекции ChromaDB для индекса лекарственного справочника.
DEFAULT_COLLECTION_NAME = "drug_handbook_chunks"

# DEFAULT_EMBEDDING_MODEL хранит имя embedding-модели GigaChat.
DEFAULT_EMBEDDING_MODEL = "EmbeddingsGigaR"

# DEFAULT_CHAT_MODEL хранит имя модели GigaChat для финальной генерации ответа.
DEFAULT_CHAT_MODEL = "GigaChat"

# DEFAULT_BATCH_SIZE хранит число чанков, отправляемых одним батчем в embedding API и ChromaDB.
DEFAULT_BATCH_SIZE = 16

# DEFAULT_QUERY_RESULTS хранит число результатов поиска по умолчанию.
DEFAULT_QUERY_RESULTS = 5

# DEFAULT_SEARCH_OVERFETCH_FACTOR хранит коэффициент расширения retrieval перед группировкой по doc_id.
DEFAULT_SEARCH_OVERFETCH_FACTOR = 6

# DEFAULT_TIMEOUT_SECONDS хранит таймаут HTTP-запросов к GigaChat API.
DEFAULT_TIMEOUT_SECONDS = 600

# DEFAULT_CONTEXT_CHUNKS хранит число чанков, которое нужно передавать в модель для генерации ответа.
DEFAULT_CONTEXT_CHUNKS = 6

# DEFAULT_ANSWER_MAX_TOKENS хранит ограничение на длину генерируемого ответа.
DEFAULT_ANSWER_MAX_TOKENS = 1200

# DEFAULT_FIND_ALL_SUMMARY_LIMIT хранит число найденных препаратов, которое безопасно передавать в LLM-сводку.
DEFAULT_FIND_ALL_SUMMARY_LIMIT = 200

# FEATURE_QUERY_VARIANTS хранит небольшой словарь синонимичных и стем-подобных вариантов признаков.
FEATURE_QUERY_VARIANTS = {
    "жаропонижающие": ["жаропонижа", "антипирет", "лихорад"],
    "жаропонижающее": ["жаропонижа", "антипирет", "лихорад"],
    "жаропонижающий": ["жаропонижа", "антипирет", "лихорад"],
    "седативные": ["седатив", "успокаива"],
    "седативное": ["седатив", "успокаива"],
    "седативный": ["седатив", "успокаива"],
}

# SEARCH_STOPWORDS хранит служебные слова, которые не стоит считать самостоятельными признаками поиска.
SEARCH_STOPWORDS = {
    "и",
    "или",
    "с",
    "со",
    "по",
    "для",
    "при",
    "в",
    "во",
    "на",
    "к",
    "от",
    "из",
    "под",
    "над",
    "до",
    "после",
    "как",
    "какие",
    "какой",
    "какая",
    "какое",
    "препарат",
    "препараты",
    "средство",
    "средства",
    "лекарство",
    "лекарства",
}

# SERVICE_SECTION_NAMES хранит разделы, которые обычно мало полезны для общих поисковых запросов.
SERVICE_SECTION_NAMES = {
    "Условия реализации",
    "Условия хранения и сроки годности",
}

# CORE_SECTION_NAMES хранит базовые содержательные разделы, которые стоит поднимать для общих запросов.
CORE_SECTION_NAMES = {
    "Общая информация",
    "Форма выпуска, состав и упаковка",
    "Показания",
    "Фармакологическое действие",
}

# QUERY_SECTION_HINT_PATTERNS хранит регулярные выражения, указывающие на нужный раздел инструкции.
QUERY_SECTION_HINT_PATTERNS = [
    (re.compile(r"\bпротивопоказ"), "Противопоказания"),
    (re.compile(r"\bпобоч"), "Побочное действие"),
    (re.compile(r"\bпоказани"), "Показания"),
    (re.compile(r"\bдозиров"), "Режим дозирования"),
    (re.compile(r"\bдозировк"), "Режим дозирования"),
    (re.compile(r"\bдоза\b"), "Режим дозирования"),
    (re.compile(r"\bпередоз"), "Передозировка"),
    (re.compile(r"\bвзаимодейств"), "Лекарственное взаимодействие"),
    (re.compile(r"\bберемен"), "Применение при беременности и кормлении грудью"),
    (re.compile(r"\bлактац"), "Применение при беременности и кормлении грудью"),
    (re.compile(r"\bхранен"), "Условия хранения и сроки годности"),
]
