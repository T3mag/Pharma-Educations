"""HTTP API для RAG-системы лекарственного справочника."""

from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException, Query

from rag.api_models import (
    AggregateSearchRequest,
    AggregateSearchResponse,
    AskRequest,
    AskResponse,
    ChatRequest,
    ChatResponse,
    FlashcardsRequest,
    FlashcardsResponse,
    MatchRequest,
    MatchResponse,
    QuizRequest,
    QuizResponse,
    SimulatorCustomerRequest,
    SimulatorCustomerResponse,
    SimulatorCustomersResponse,
    SimulatorEvaluateRequest,
    SimulatorEvaluationResponse,
    TopicCatalogsResponse,
    TopicTreeResponse,
    TopicsResponse,
)
from rag.services.chat_service import clear_chat_session, execute_chat
from rag.services.errors import BadRequestError, NotFoundError
from rag.services.aggregate_search_service import execute_aggregate_search
from rag.services.game_service import generate_flashcards, generate_match_game, generate_quiz
from rag.services.rag_service import execute_ask
from rag.services.runtime import get_runtime
from rag.services.simulator_service import create_simulator_customer, create_simulator_customers, evaluate_simulator_answer
from rag.services.topic_service import get_topic_catalogs, get_topics, get_topics_tree


app = FastAPI(
    title="Pharma Education RAG API",
    version="1.0.0",
    description="API для поиска информации по лекарственным препаратам и генерации grounded-ответов.",
)


@app.on_event("startup")
async def warm_up_runtime() -> None:
    """Инициализирует shared runtime в основном event loop потоке до первых запросов."""

    get_runtime()


def map_service_error(error: Exception, fallback_prefix: str) -> HTTPException:
    """Преобразует service layer ошибки в HTTPException."""

    if isinstance(error, BadRequestError):
        return HTTPException(status_code=400, detail=str(error))
    if isinstance(error, NotFoundError):
        return HTTPException(status_code=404, detail=str(error))
    if isinstance(error, RuntimeError):
        return HTTPException(status_code=500, detail=str(error))
    return HTTPException(status_code=500, detail=f"{fallback_prefix}: {error}")


@app.get("/health")
def health() -> dict[str, str]:
    """Проверяет, что API-сервер запущен."""

    return {"status": "ok"}


@app.get("/topic-catalogs", response_model=TopicCatalogsResponse)
def topic_catalogs() -> TopicCatalogsResponse:
    """Возвращает четыре основных указателя для выбора темы мини-игры."""

    return get_topic_catalogs()


@app.get("/topics", response_model=TopicsResponse)
def topics(
    catalog: Optional[str] = Query(None, description="ID указателя: kfu, noz, atc или active_substance."),
    parent_id: Optional[str] = Query(None, description="ID родительской темы, детей которой нужно вернуть."),
    q: Optional[str] = Query(None, description="Фильтр по названию, коду или пути темы."),
    limit: int = Query(100, ge=1, le=500),
) -> TopicsResponse:
    """Возвращает темы из иерархического дерева указателей Vidal."""

    return get_topics(
        catalog=catalog,
        parent_id=parent_id,
        q=q,
        limit=limit,
    )


@app.get("/topics/tree", response_model=TopicTreeResponse)
def topics_tree(
    catalog: Optional[str] = Query(None, description="Опционально ограничить дерево одним каталогом: kfu, noz, atc или active_substance."),
) -> TopicTreeResponse:
    """Возвращает полное дерево тем одним запросом."""

    return get_topics_tree(catalog=catalog)


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    """Выполняет hybrid retrieval, генерацию ответа и возвращает JSON-результат."""

    try:
        return execute_ask(request)
    except Exception as error:
        raise map_service_error(error, "Ошибка выполнения RAG-запроса") from error


@app.post("/catalog/search", response_model=AggregateSearchResponse)
def catalog_search(request: AggregateSearchRequest) -> AggregateSearchResponse:
    """Выполняет полнотный структурный поиск по всем карточкам препаратов."""

    try:
        return execute_aggregate_search(request)
    except Exception as error:
        raise map_service_error(error, "Ошибка структурного поиска") from error


@app.post("/games/quiz", response_model=QuizResponse)
def quiz(request: QuizRequest) -> QuizResponse:
    """Генерирует викторину по выбранной теме из справочника."""

    try:
        return generate_quiz(request)
    except Exception as error:
        raise map_service_error(error, "Ошибка генерации викторины") from error


@app.post("/games/flashcards", response_model=FlashcardsResponse)
def flashcards(request: FlashcardsRequest) -> FlashcardsResponse:
    """Генерирует карточки для запоминания по выбранной теме из справочника."""

    try:
        return generate_flashcards(request)
    except Exception as error:
        raise map_service_error(error, "Ошибка генерации карточек") from error


@app.post("/games/match", response_model=MatchResponse)
def match_game(request: MatchRequest) -> MatchResponse:
    """Генерирует Match-игру по выбранным темам из справочника."""

    try:
        return generate_match_game(request)
    except Exception as error:
        raise map_service_error(error, "Ошибка генерации Match-игры") from error


@app.post("/simulator/customer", response_model=SimulatorCustomerResponse)
def simulator_customer(request: Optional[SimulatorCustomerRequest] = None) -> SimulatorCustomerResponse:
    """Генерирует клиента для режима симулятора аптекаря."""

    try:
        return create_simulator_customer(request or SimulatorCustomerRequest())
    except Exception as error:
        raise map_service_error(error, "Ошибка генерации клиента симулятора") from error


@app.post("/simulator/customers", response_model=SimulatorCustomersResponse)
def simulator_customers(request: SimulatorCustomerRequest) -> SimulatorCustomersResponse:
    """Генерирует несколько клиентов для режима симулятора аптекаря."""

    try:
        return create_simulator_customers(request)
    except Exception as error:
        raise map_service_error(error, "Ошибка генерации клиентов симулятора") from error


@app.post("/simulator/evaluate", response_model=SimulatorEvaluationResponse)
def simulator_evaluate(request: SimulatorEvaluateRequest) -> SimulatorEvaluationResponse:
    """Оценивает ответ студента в режиме симулятора аптекаря."""

    try:
        return evaluate_simulator_answer(request)
    except Exception as error:
        raise map_service_error(error, "Ошибка оценки ответа студента") from error


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Выполняет вопрос-ответ в рамках сессии чата с короткой историей."""

    try:
        return execute_chat(request)
    except Exception as error:
        raise map_service_error(error, "Ошибка выполнения chat-запроса") from error


@app.delete("/chat/{session_id}")
def clear_chat(session_id: str) -> dict[str, str]:
    """Удаляет историю указанной сессии чата из памяти сервера."""

    return clear_chat_session(session_id)
