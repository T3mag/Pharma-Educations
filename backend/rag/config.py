"""Конфигурация путей, констант и эвристик для RAG-системы."""

from __future__ import annotations

import re
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent

PROJECT_ROOT = PACKAGE_ROOT.parent

DATA_ROOT = PROJECT_ROOT / "data"

DEFAULT_CHUNKS_PATH = DATA_ROOT / "chunks.jsonl"

DEFAULT_ENTITY_RELATIONS_PATH = DATA_ROOT / "entity_relations.jsonl"

DEFAULT_NORMALIZED_PAGES_PATH = DATA_ROOT / "normalized_pages.jsonl"

DEFAULT_STRUCTURED_DOCUMENTS_PATH = DATA_ROOT / "structured_documents.jsonl"

DEFAULT_CHROMA_PATH = PROJECT_ROOT / "chroma_data"

DEFAULT_COLLECTION_NAME = "drug_handbook_chunks"

DEFAULT_EMBEDDING_MODEL = "EmbeddingsGigaR"

DEFAULT_CHAT_MODEL = "GigaChat"

DEFAULT_BATCH_SIZE = 16

DEFAULT_QUERY_RESULTS = 8

DEFAULT_SEARCH_OVERFETCH_FACTOR = 8

DEFAULT_TIMEOUT_SECONDS = 600

DEFAULT_CONTEXT_CHUNKS = 10

DEFAULT_ANSWER_MAX_TOKENS = 2000

DEFAULT_FIND_ALL_SUMMARY_LIMIT = 200

FEATURE_QUERY_VARIANTS = {
    "жаропонижающие": ["жаропонижа", "антипирет", "лихорад"],
    "жаропонижающее": ["жаропонижа", "антипирет", "лихорад"],
    "жаропонижающий": ["жаропонижа", "антипирет", "лихорад"],
    "седативные": ["седатив", "успокаива"],
    "седативное": ["седатив", "успокаива"],
    "седативный": ["седатив", "успокаива"],
}

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

SERVICE_SECTION_NAMES = {
    "Условия реализации",
    "Условия хранения и сроки годности",
}

CORE_SECTION_NAMES = {
    "Общая информация",
    "Форма выпуска, состав и упаковка",
    "Показания",
    "Фармакологическое действие",
}

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
