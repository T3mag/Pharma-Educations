"""Pydantic-схемы HTTP API."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from .config import (
    DEFAULT_ANSWER_MAX_TOKENS,
    DEFAULT_CHAT_MODEL,
    DEFAULT_CONTEXT_CHUNKS,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_FIND_ALL_SUMMARY_LIMIT,
    DEFAULT_QUERY_RESULTS,
    DEFAULT_SEARCH_OVERFETCH_FACTOR,
)


class AskRequest(BaseModel):
    """Запрос к RAG-эндпоинту ask."""

    query: str = Field(..., min_length=1, description="Вопрос пользователя.")
    n_results: int = Field(DEFAULT_QUERY_RESULTS, ge=1, le=50)
    overfetch_factor: int = Field(DEFAULT_SEARCH_OVERFETCH_FACTOR, ge=1, le=20)
    context_chunks: int = Field(DEFAULT_CONTEXT_CHUNKS, ge=1, le=30)
    answer_max_tokens: int = Field(DEFAULT_ANSWER_MAX_TOKENS, ge=64, le=8000)
    embedding_model: str = Field(DEFAULT_EMBEDDING_MODEL)
    chat_model: str = Field(DEFAULT_CHAT_MODEL)


class SourceResponse(BaseModel):
    """Источник, использованный для генерации ответа."""

    drug: str
    doc_id: str
    section: str
    chunk_id: str


class ValidationResponse(BaseModel):
    """Результат post-check проверки ответа."""

    status: str
    grounding_overlap: float
    primary_drug_focus: str
    mentioned_context_drugs: list[str]
    potential_issues: list[str]


class AskResponse(BaseModel):
    """Ответ RAG-системы на пользовательский вопрос."""

    query: str
    answer: str
    matched_entities: list[dict[str, Any]]
    matched_drug_documents: list[dict[str, Any]]
    section_hints: list[str]
    sources: list[SourceResponse]
    validation: Optional[ValidationResponse]


class AggregateSearchRequest(BaseModel):
    """Запрос полнотного структурного поиска по всем карточкам препаратов."""

    query: str = Field("", description="Естественно-языковой запрос пользователя.")
    active_substance: str = Field("", description="Действующее вещество для фильтрации.")
    indication: str = Field("", description="Показание или заболевание для фильтрации.")
    exclude_contraindication: str = Field("", description="Противопоказание, которого не должно быть у препарата.")
    limit: int = Field(200, ge=1, le=1000)


class AggregateDrugResult(BaseModel):
    """Один препарат в результате полнотного структурного поиска."""

    doc_id: str
    drug_name_ru: str
    drug_name_lat: str = ""
    dosage_form: str = ""
    clinical_pharmacological_group: str = ""
    active_substances: list[str] = Field(default_factory=list)
    atc_codes: list[str] = Field(default_factory=list)
    indications: str = ""
    contraindications: str = ""
    matched_reasons: list[str] = Field(default_factory=list)


class AggregateSearchResponse(BaseModel):
    """Ответ полнотного структурного поиска."""

    query: str
    search_type: str = "aggregate_structured_search"
    filters: dict[str, str]
    total_found: int
    results: list[AggregateDrugResult]


class ChatMessage(BaseModel):
    """Одно сообщение из истории чата."""

    role: str
    content: str


class ChatRequest(BaseModel):
    """Запрос к conversational RAG-эндпоинту."""

    message: str = Field(..., min_length=1, description="Сообщение пользователя.")
    session_id: Optional[str] = Field(None, description="Идентификатор сессии чата.")
    n_results: int = Field(DEFAULT_QUERY_RESULTS, ge=1, le=50)
    overfetch_factor: int = Field(DEFAULT_SEARCH_OVERFETCH_FACTOR, ge=1, le=20)
    context_chunks: int = Field(DEFAULT_CONTEXT_CHUNKS, ge=1, le=30)
    answer_max_tokens: int = Field(DEFAULT_ANSWER_MAX_TOKENS, ge=64, le=8000)
    embedding_model: str = Field(DEFAULT_EMBEDDING_MODEL)
    chat_model: str = Field(DEFAULT_CHAT_MODEL)


class ChatResponse(BaseModel):
    """Ответ conversational RAG-эндпоинта."""

    session_id: str
    message: str
    answer: str
    history: list[ChatMessage]
    ask_result: AskResponse


class TopicResponse(BaseModel):
    """Тема, которую можно выбрать для генерации учебной мини-игры."""

    id: str = ""
    catalog: str = ""
    type: str
    title: str
    parent_id: str = ""
    level: int = 0
    path: list[str] = Field(default_factory=list)
    source_page_path: str = ""
    code: str = ""
    doc_count: int = 0
    has_children: bool = False


class TopicsResponse(BaseModel):
    """Список тем, найденных в данных справочника."""

    topics: list[TopicResponse]


class TopicTreeNodeResponse(BaseModel):
    """Узел полного дерева тем с вложенными дочерними элементами."""

    id: str = ""
    catalog: str = ""
    type: str
    title: str
    parent_id: str = ""
    level: int = 0
    path: list[str] = Field(default_factory=list)
    source_page_path: str = ""
    code: str = ""
    doc_count: int = 0
    has_children: bool = False
    children: list["TopicTreeNodeResponse"] = Field(default_factory=list)


class TopicTreeResponse(BaseModel):
    """Полное дерево тем для выбора учебной темы одним запросом."""

    topics: list[TopicTreeNodeResponse]


class TopicCatalogResponse(BaseModel):
    """Один верхнеуровневый указатель тем."""

    id: str
    title: str
    description: str


class TopicCatalogsResponse(BaseModel):
    """Список доступных указателей тем."""

    catalogs: list[TopicCatalogResponse]


class FoundDrugResponse(BaseModel):
    """Препарат, найденный для выбранной игровой темы."""

    doc_id: str
    drug_name_ru: str
    drug_name_lat: str = ""
    score: float = 0.0
    match_reasons: list[str] = Field(default_factory=list)


class QuizRequest(BaseModel):
    """Запрос на генерацию викторины по теме из справочника."""

    topic: str = Field("", description="Свободная текстовая тема, если topic_id не выбран.")
    topic_id: Optional[str] = Field(None, description="ID темы из иерархического дерева /topics.")
    topic_ids: list[str] = Field(default_factory=list, description="Список ID тем из каталога для общей викторины.")
    question_count: int = Field(5, ge=1, le=10)
    options_per_question: int = Field(4, ge=2, le=6)
    summary_limit: int = Field(DEFAULT_FIND_ALL_SUMMARY_LIMIT, ge=1, le=300)
    context_chunks: int = Field(DEFAULT_CONTEXT_CHUNKS, ge=1, le=30)
    answer_max_tokens: int = Field(DEFAULT_ANSWER_MAX_TOKENS, ge=256, le=8000)
    embedding_model: str = Field(DEFAULT_EMBEDDING_MODEL)
    chat_model: str = Field(DEFAULT_CHAT_MODEL)


class QuizQuestionResponse(BaseModel):
    """Один вопрос викторины."""

    question: str
    options: list[str]
    correct_answer: str
    explanation: str


class QuizResponse(BaseModel):
    """Сгенерированная викторина по данным справочника."""

    game_type: str
    topic: str
    title: str
    questions: list[QuizQuestionResponse]


class FlashcardsRequest(BaseModel):
    """Запрос на генерацию карточек для запоминания по теме из справочника."""

    topic: str = Field("", description="Свободная текстовая тема, если topic_id не выбран.")
    topic_id: Optional[str] = Field(None, description="ID темы из иерархического дерева /topics.")
    topic_ids: list[str] = Field(default_factory=list, description="Список ID тем или каталогов для набора карточек.")
    card_count: int = Field(6, ge=1, le=20)
    summary_limit: int = Field(DEFAULT_FIND_ALL_SUMMARY_LIMIT, ge=1, le=300)
    context_chunks: int = Field(DEFAULT_CONTEXT_CHUNKS, ge=1, le=30)
    answer_max_tokens: int = Field(DEFAULT_ANSWER_MAX_TOKENS, ge=256, le=8000)
    embedding_model: str = Field(DEFAULT_EMBEDDING_MODEL)
    chat_model: str = Field(DEFAULT_CHAT_MODEL)


class FlashcardResponse(BaseModel):
    """Одна учебная карточка."""

    front_title: str = "Лекарство"
    front: str
    back_title: str = "Ответ"
    back: str
    explanation: str


class FlashcardsResponse(BaseModel):
    """Сгенерированный набор карточек по данным справочника."""

    game_type: str
    topic: str
    title: str
    cards: list[FlashcardResponse]


class MatchRequest(BaseModel):
    """Запрос на генерацию игры на сопоставление по теме из справочника."""

    topic: str = Field("", description="Свободная текстовая тема, если topic_id или topic_ids не выбраны.")
    topic_id: Optional[str] = Field(None, description="ID темы из иерархического дерева /topics.")
    topic_ids: list[str] = Field(default_factory=list, description="Список ID тем или каталогов для общей Match-игры.")
    task_count: int = Field(
        1,
        ge=1,
        le=10,
        description="Количество заданий для Match-игры. Одно задание = один набор карточек.",
    )
    pair_count: int = Field(4, ge=2, le=10, description="Количество пар левая карточка -> правая карточка внутри одного задания.")
    match_type: Optional[str] = Field(
        None,
        description=(
            "Тип сопоставления: drug_to_active_substance, drug_to_contraindication, "
            "drug_to_indication, drug_to_dosage_form, drug_to_clinical_group, drug_to_feature. "
            "Если не передан, сервер выберет случайный поддерживаемый тип."
        ),
    )
    feature_name: str = Field("", description="Произвольное название признака, если match_type=drug_to_feature.")
    summary_limit: int = Field(DEFAULT_FIND_ALL_SUMMARY_LIMIT, ge=1, le=300)
    context_chunks: int = Field(DEFAULT_CONTEXT_CHUNKS, ge=1, le=30)
    answer_max_tokens: int = Field(DEFAULT_ANSWER_MAX_TOKENS, ge=256, le=8000)
    embedding_model: str = Field(DEFAULT_EMBEDDING_MODEL)
    chat_model: str = Field(DEFAULT_CHAT_MODEL)


class MatchPairResponse(BaseModel):
    """Одна пара для игры на сопоставление."""

    pair_id: str
    left: str
    right: str
    explanation: str = ""


class MatchTaskResponse(BaseModel):
    """Один набор карточек для Match-игры."""

    task_id: str
    pairs: list[MatchPairResponse]


class MatchResponse(BaseModel):
    """Сгенерированный набор пар для Match-игры."""

    game_type: str
    topic: str
    title: str
    match_type: str
    left_label: str
    right_label: str
    task_count: int
    pair_count: int
    tasks: list[MatchTaskResponse]


class SimulatorCustomerRequest(BaseModel):
    """Запрос на генерацию клиента для симулятора аптекаря."""

    customer_count: int = Field(1, ge=1, le=10, description="Сколько покупателей нужно сгенерировать.")


class SimulatorCustomerResponse(BaseModel):
    """Клиент и запрос, которые видит студент в режиме симулятора аптекаря."""

    scenario_id: str
    mode: str = "pharmacy_simulator"
    customer_profile: dict[str, Any]
    customer_request: str
    visible_facts: list[str] = Field(default_factory=list)
    task: str


class SimulatorCustomersResponse(BaseModel):
    """Набор клиентов для режима симулятора аптекаря."""

    mode: str = "pharmacy_simulator"
    customer_count: int
    customers: list[SimulatorCustomerResponse]


class SimulatorEvaluateRequest(BaseModel):
    """Запрос на оценку ответа студента в симуляторе аптекаря."""

    scenario_id: str = Field(..., min_length=1)
    student_answer: str = Field(..., min_length=1, description="Какой препарат и объяснение выбрал студент.")
    answer_max_tokens: int = Field(DEFAULT_ANSWER_MAX_TOKENS, ge=256, le=8000)
    chat_model: str = Field(DEFAULT_CHAT_MODEL)


class SimulatorEvaluationResponse(BaseModel):
    """Оценка качества подбора препарата студентом."""

    scenario_id: str
    score: int = Field(..., ge=0, le=100)
    verdict: str
    feedback: str
    strengths: list[str] = Field(default_factory=list)
    mistakes: list[str] = Field(default_factory=list)
    safety_warnings: list[str] = Field(default_factory=list)
    recommended_answer: str
    referenced_drugs: list[str] = Field(default_factory=list)


TopicTreeNodeResponse.model_rebuild()
