"""Use case слой conversational RAG-чата."""

from __future__ import annotations

import re
from uuid import uuid4
from typing import Optional

from ..api_models import AskRequest, AskResponse, ChatMessage, ChatRequest, ChatResponse
from .rag_service import execute_ask


MAX_CHAT_HISTORY_MESSAGES = 12

chat_sessions: dict[str, list[dict[str, str]]] = {}

GREETING_PATTERNS = [
    re.compile(
        r"^\s*(привет|здравствуй|здравствуйте|добрый день|доброе утро|добрый вечер|hello|hi)\s*[!.?]*\s*$",
        re.IGNORECASE,
    ),
]


def build_contextual_chat_query(message: str, history: list[dict[str, str]]) -> str:
    """Собирает текущий вопрос с короткой историей, чтобы follow-up вопросы были понятны retrieval."""

    recent_history = history[-6:]
    if not recent_history:
        return message

    history_lines = [
        f"{item['role']}: {item['content']}"
        for item in recent_history
        if item.get("content")
    ]
    if not history_lines:
        return message

    return (
        "История диалога:\n"
        + "\n".join(history_lines)
        + "\n\nТекущий вопрос пользователя:\n"
        + message
    )


def build_plain_chat_answer(message: str) -> Optional[str]:
    """Возвращает обычный conversational-ответ без RAG, если поиск по справочнику не нужен."""

    if any(pattern.match(message) for pattern in GREETING_PATTERNS):
        return (
            "Привет. Я могу помочь найти информацию по лекарственным препаратам. "
            "Например: \"Авамис противопоказания\" или \"Антигриппин побочные действия\"."
        )

    return None


def execute_chat(request: ChatRequest) -> ChatResponse:
    """Выполняет вопрос-ответ в рамках сессии чата с короткой историей."""

    session_id = request.session_id or str(uuid4())
    history = chat_sessions.setdefault(session_id, [])

    plain_answer = build_plain_chat_answer(request.message)
    if plain_answer is not None:
        history.append({"role": "user", "content": request.message})
        history.append({"role": "assistant", "content": plain_answer})
        del history[:-MAX_CHAT_HISTORY_MESSAGES]

        ask_result = AskResponse(
            query=request.message,
            answer=plain_answer,
            matched_entities=[],
            matched_drug_documents=[],
            section_hints=[],
            sources=[],
            validation=None,
        )

        return ChatResponse(
            session_id=session_id,
            message=request.message,
            answer=plain_answer,
            history=[ChatMessage(**item) for item in history],
            ask_result=ask_result,
        )

    contextual_query = build_contextual_chat_query(
        message=request.message,
        history=history,
    )
    ask_result = execute_ask(
        AskRequest(
            query=contextual_query,
            n_results=request.n_results,
            overfetch_factor=request.overfetch_factor,
            context_chunks=request.context_chunks,
            answer_max_tokens=request.answer_max_tokens,
            embedding_model=request.embedding_model,
            chat_model=request.chat_model,
        )
    )

    history.append({"role": "user", "content": request.message})
    history.append({"role": "assistant", "content": ask_result.answer})
    del history[:-MAX_CHAT_HISTORY_MESSAGES]

    return ChatResponse(
        session_id=session_id,
        message=request.message,
        answer=ask_result.answer,
        history=[ChatMessage(**item) for item in history],
        ask_result=ask_result,
    )


def clear_chat_session(session_id: str) -> dict[str, str]:
    """Удаляет историю указанной сессии чата из памяти сервера."""

    chat_sessions.pop(session_id, None)
    return {"status": "ok", "session_id": session_id}
