"""Use case слой симулятора аптекаря."""

from __future__ import annotations

import random
import uuid
from typing import Any

from ..api_models import (
    SimulatorCustomerRequest,
    SimulatorCustomerResponse,
    SimulatorCustomersResponse,
    SimulatorEvaluateRequest,
    SimulatorEvaluationResponse,
)
from ..common import normalize_drug_name_lookup_text
from ..config import DEFAULT_ANSWER_MAX_TOKENS, DEFAULT_CHAT_MODEL
from .errors import NotFoundError
from .game_service import call_gigachat_json, truncate_text
from .runtime import get_runtime, load_structured_documents_index


simulator_scenarios: dict[str, dict[str, Any]] = {}
SIMULATOR_CONTEXT_DOCUMENT_LIMIT = 8


def document_has_learning_data(document_record: dict[str, Any]) -> bool:
    """Оставляет карточки, по которым можно составить аптечный сценарий."""

    sections = document_record.get("sections") or {}
    return bool(
        document_record.get("drug_name_ru")
        and sections.get("Показания")
        and sections.get("Противопоказания")
    )


def select_simulator_documents() -> list[dict[str, Any]]:
    """Выбирает случайные препараты, на основе которых LLM создаст клиента."""

    documents_by_id = load_structured_documents_index()
    candidate_documents = [
        document_record
        for document_record in documents_by_id.values()
        if document_has_learning_data(document_record)
    ]
    if not candidate_documents:
        raise NotFoundError("Не найдено подходящих карточек препаратов для сценария.")

    random.shuffle(candidate_documents)
    return candidate_documents[:SIMULATOR_CONTEXT_DOCUMENT_LIMIT]


def format_simulator_context(documents: list[dict[str, Any]]) -> str:
    """Формирует компактный grounded-контекст для генерации и оценки сценария."""

    context_lines = ["Проверенные данные лекарственного справочника:"]
    for index, document_record in enumerate(documents, start=1):
        sections = document_record.get("sections") or {}
        active_substances = document_record.get("active_substances") or []
        atc_codes = document_record.get("atc_codes") or []
        context_lines.extend(
            [
                f"{index}. Препарат: {document_record.get('drug_name_ru') or 'Не указан'}",
                f"   Doc ID: {document_record.get('doc_id') or 'Не указан'}",
                f"   Латинское название: {document_record.get('drug_name_lat') or 'не указано'}",
                f"   Действующие вещества: {', '.join(active_substances) if active_substances else 'не указаны'}",
                f"   ATC: {', '.join(atc_codes) if atc_codes else 'не указаны'}",
                f"   КФГ: {document_record.get('clinical_pharmacological_group') or 'не указана'}",
                f"   Лекарственная форма: {document_record.get('dosage_form') or 'не указана'}",
                f"   Показания: {truncate_text(sections.get('Показания'), limit=700)}",
                f"   Противопоказания: {truncate_text(sections.get('Противопоказания'), limit=700)}",
                f"   Побочное действие: {truncate_text(sections.get('Побочное действие'), limit=350)}",
                f"   Особые указания: {truncate_text(sections.get('Особые указания'), limit=350)}",
            ]
        )
    return "\n".join(context_lines)


def create_simulator_customer(request: SimulatorCustomerRequest) -> SimulatorCustomerResponse:
    """Создает клиента аптеки и сохраняет скрытый эталонный контекст сценария."""

    selected_documents = select_simulator_documents()
    context_text = format_simulator_context(selected_documents)
    _embedding_client, chat_client, _collection = get_runtime()

    game_json = call_gigachat_json(
        gigachat_client=chat_client,
        chat_model_name=DEFAULT_CHAT_MODEL,
        answer_max_tokens=DEFAULT_ANSWER_MAX_TOKENS,
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты создаешь учебный сценарий для симулятора аптекаря. "
                    "Используй только предоставленный лекарственный контекст. "
                    "Не раскрывай студенту правильный препарат напрямую. "
                    "Сценарий должен выглядеть как реальный покупатель, который пришел в аптеку за лекарством. "
                    "Верни только валидный JSON без markdown."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"{context_text}\n\n"
                    "Сформируй одного клиента аптеки. "
                    "Клиент должен попросить помощь так, как это было бы в реальной аптеке. "
                    "Не называй препарат в запросе клиента. "
                    "В visible_facts включи только то, что клиент сам сообщает студенту. "
                    "В reference оставь скрытую информацию для проверки. "
                    "Если контекст позволяет, подбери 2-4 возможных подходящих препарата, а не один. "
                    "Подходящие препараты должны решать запрос клиента и не иметь явного конфликта с видимыми фактами. "
                    "Если есть только один безопасный вариант, укажи один.\n\n"
                    "JSON строго такого вида:\n"
                    "{\n"
                    '  "customer_profile": {"age": "примерный возраст", "gender": "пол", "context": "кто пришел"},\n'
                    '  "customer_request": "реплика клиента в аптеке",\n'
                    '  "visible_facts": ["факт 1", "факт 2"],\n'
                    '  "reference": {\n'
                    '    "suitable_drugs": ["2-4 названия подходящих препаратов из контекста, если это возможно"],\n'
                    '    "unsafe_drugs": ["названия препаратов, которые опасны или нежелательны"],\n'
                    '    "must_check": ["что студент должен уточнить"],\n'
                    '    "ideal_pharmacist_logic": "краткая логика правильного подбора и критерии выбора между вариантами"\n'
                    "  }\n"
                    "}"
                ),
            },
        ],
    )

    scenario_id = str(uuid.uuid4())
    simulator_scenarios[scenario_id] = {
        "context_text": context_text,
        "customer_profile": game_json.get("customer_profile") or {},
        "customer_request": str(game_json.get("customer_request") or "").strip(),
        "visible_facts": [str(item) for item in game_json.get("visible_facts") or []],
        "reference": game_json.get("reference") or {},
    }

    return SimulatorCustomerResponse(
        scenario_id=scenario_id,
        customer_profile=simulator_scenarios[scenario_id]["customer_profile"],
        customer_request=simulator_scenarios[scenario_id]["customer_request"],
        visible_facts=simulator_scenarios[scenario_id]["visible_facts"],
        task="Подберите препарат, который студент готов выдать покупателю, и кратко объясните выбор.",
    )


def create_simulator_customers(request: SimulatorCustomerRequest) -> SimulatorCustomersResponse:
    """Создает несколько независимых клиентов аптеки одним HTTP-запросом."""

    customers = [
        create_simulator_customer(SimulatorCustomerRequest())
        for _ in range(request.customer_count)
    ]
    return SimulatorCustomersResponse(
        customer_count=len(customers),
        customers=customers,
    )


def find_student_drug_documents(student_answer: str, limit: int = 5) -> list[dict[str, Any]]:
    """Находит карточки препаратов, названия которых студент упомянул в ответе."""

    normalized_answer = normalize_drug_name_lookup_text(student_answer)
    if not normalized_answer:
        return []

    matched_documents: list[dict[str, Any]] = []
    for document_record in load_structured_documents_index().values():
        drug_name_ru = str(document_record.get("drug_name_ru") or "")
        drug_name_lat = str(document_record.get("drug_name_lat") or "")
        name_variants = [
            normalize_drug_name_lookup_text(drug_name_ru),
            normalize_drug_name_lookup_text(drug_name_lat),
        ]
        if any(name_variant and name_variant in normalized_answer for name_variant in name_variants):
            matched_documents.append(document_record)
        if len(matched_documents) >= limit:
            break
    return matched_documents


def clamp_score(value: Any) -> int:
    """Приводит score модели к диапазону 0-100."""

    try:
        score = int(round(float(value)))
    except (TypeError, ValueError):
        score = 0
    return min(max(score, 0), 100)


def evaluate_simulator_answer(request: SimulatorEvaluateRequest) -> SimulatorEvaluationResponse:
    """Оценивает ответ студента по сохраненному сценарию и карточкам препаратов."""

    scenario = simulator_scenarios.get(request.scenario_id)
    if scenario is None:
        raise NotFoundError("Сценарий не найден. Сначала создайте клиента через /simulator/customer.")

    student_documents = find_student_drug_documents(request.student_answer)
    student_context = format_simulator_context(student_documents) if student_documents else "Упомянутые студентом препараты в справочнике не найдены."
    _embedding_client, chat_client, _collection = get_runtime()

    evaluation_json = call_gigachat_json(
        gigachat_client=chat_client,
        chat_model_name=request.chat_model,
        answer_max_tokens=request.answer_max_tokens,
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты строгий, но справедливый преподаватель фармацевтического консультирования. "
                    "Оценивай ответ студента только на основе предоставленного контекста. "
                    "Безопасность пациента важнее угадывания препарата. "
                    "Верни только валидный JSON без markdown."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Сценарий клиента:\n"
                    f"Профиль: {scenario['customer_profile']}\n"
                    f"Запрос клиента: {scenario['customer_request']}\n"
                    f"Факты от клиента: {scenario['visible_facts']}\n\n"
                    f"Скрытый эталон сценария:\n{scenario['reference']}\n\n"
                    f"Контекст препаратов, на основе которых создан сценарий:\n{scenario['context_text']}\n\n"
                    f"Карточки препаратов, которые упомянул студент:\n{student_context}\n\n"
                    f"Ответ студента:\n{request.student_answer}\n\n"
                    "Оцени качество подбора препарата по шкале 0-100. "
                    "Учитывай: подходит ли препарат по показаниям, нет ли явного противопоказания, "
                    "уточнил ли студент важные риски, не выдал ли потенциально опасную рекомендацию. "
                    "Если студент выбрал любой препарат из suitable_drugs и дал осознанное безопасное объяснение, "
                    "не снижай оценку только за то, что он не выбрал первый или самый очевидный вариант. "
                    "Смягчай оценку для ответов, где студент: задает важные уточняющие вопросы, проверяет противопоказания, "
                    "предлагает обратиться к врачу при рисках, честно ограничивает рекомендацию рамками инструкции. "
                    "Такие ответы могут получать среднюю или высокую оценку даже при неполном подборе препарата. "
                    "Ужесточай оценку для несуразных ответов: случайный препарат без связи с запросом, игнорирование явных рисков, "
                    "уверенная рекомендация препарата, не найденного в справочнике, опасный совет, отказ от уточнений при очевидной необходимости. "
                    "Если студент не указал препарат, но дал безопасный алгоритм уточнений и направления к врачу, не ставь ноль автоматически. "
                    "Если студент не указал препарат и ответ не содержит полезной безопасной логики, оценка должна быть низкой.\n\n"
                    "Ориентиры оценки:\n"
                    "90-100: безопасный осознанный ответ, подходящий препарат или корректный выбор из нескольких вариантов, важные уточнения учтены.\n"
                    "70-89: в целом верная рекомендация, но часть уточнений или объяснений неполная.\n"
                    "40-69: есть полезная логика безопасности, но препарат выбран слабо, не назван или обоснование неполное.\n"
                    "0-39: несуразный, случайный, опасный или не связанный со сценарием ответ.\n\n"
                    "JSON строго такого вида:\n"
                    "{\n"
                    '  "score": 0,\n'
                    '  "verdict": "короткий вердикт",\n'
                    '  "feedback": "понятный фидбек студенту",\n'
                    '  "strengths": ["что сделано хорошо"],\n'
                    '  "mistakes": ["ошибка или недочет"],\n'
                    '  "safety_warnings": ["важные предупреждения"],\n'
                    '  "recommended_answer": "как можно было ответить лучше",\n'
                    '  "referenced_drugs": ["названия препаратов, на которые опиралась оценка"]\n'
                    "}"
                ),
            },
        ],
    )

    return SimulatorEvaluationResponse(
        scenario_id=request.scenario_id,
        score=clamp_score(evaluation_json.get("score")),
        verdict=str(evaluation_json.get("verdict") or "").strip(),
        feedback=str(evaluation_json.get("feedback") or "").strip(),
        strengths=[str(item) for item in evaluation_json.get("strengths") or []],
        mistakes=[str(item) for item in evaluation_json.get("mistakes") or []],
        safety_warnings=[str(item) for item in evaluation_json.get("safety_warnings") or []],
        recommended_answer=str(evaluation_json.get("recommended_answer") or "").strip(),
        referenced_drugs=[str(item) for item in evaluation_json.get("referenced_drugs") or []],
    )
