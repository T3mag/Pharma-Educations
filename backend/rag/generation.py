"""Генерация ответов и вопросов поверх retrieval-результатов."""

from __future__ import annotations

import re
from typing import Any

from .clients import retry_on_transient_error
from .common import extract_chat_message_text, normalize_drug_name_lookup_text, normalize_search_text
from .models import (
    AnswerValidationResult,
    FindAllBundle,
    RankedChunkResult,
    RetrievalBundle,
    RetrievalSummary,
)
from .search import select_context_chunks


def expand_query(
    gigachat_client: Any,
    query: str,
    chat_model_name: str,
) -> list[str]:
    """Генерирует 2-3 альтернативные формулировки запроса для улучшения recall retrieval."""

    system_prompt = (
        "Ты помогаешь перефразировать вопросы для поиска по медицинскому справочнику лекарств. "
        "Верни 2-3 альтернативные формулировки вопроса, каждую на отдельной строке. "
        "Формулировки должны использовать синонимы, медицинские термины, латинские/русские названия. "
        "Не добавляй ничего кроме формулировок. Не нумеруй их."
    )

    user_prompt = f"Перефразируй для поиска в справочнике:\n{query}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    payload = {
        "model": chat_model_name,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 300,
    }

    try:
        response = retry_on_transient_error(gigachat_client.chat, payload)
        answer = extract_chat_message_text(response)
        variants = [line.strip() for line in answer.splitlines() if line.strip() and len(line.strip()) > 5]
        return variants[:3]
    except Exception:
        return []


def generate_hypothetical_document(
    gigachat_client: Any,
    query: str,
    chat_model_name: str,
) -> str:
    """HyDE: генерирует короткий гипотетический ответ, чей embedding ближе к релевантным документам."""

    system_prompt = (
        "Ты — медицинский справочник. Напиши короткий параграф (3-5 предложений), "
        "который мог бы быть в инструкции к лекарственному препарату и содержал бы ответ на вопрос пользователя. "
        "Используй медицинскую терминологию. Пиши так, как пишут в справочниках лекарств. "
        "Не уточняй, что это гипотетический текст — пиши как реальный справочный текст."
    )

    user_prompt = f"Вопрос: {query}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    payload = {
        "model": chat_model_name,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 400,
    }

    try:
        response = retry_on_transient_error(gigachat_client.chat, payload)
        return extract_chat_message_text(response)
    except Exception:
        return ""


VALIDATION_STOPWORDS = {
    "если",
    "или",
    "для",
    "при",
    "как",
    "что",
    "это",
    "этого",
    "этой",
    "этом",
    "этим",
    "также",
    "между",
    "после",
    "перед",
    "только",
    "который",
    "которая",
    "которые",
    "пользователя",
    "источник",
    "источники",
    "препарат",
    "раздел",
    "данные",
    "ответ",
}

SECTION_MARKERS = {
    "противопоказания": "Противопоказания",
    "показания": "Показания",
    "побочное действие": "Побочное действие",
    "побочные действия": "Побочное действие",
    "режим дозирования": "Режим дозирования",
    "дозировка": "Режим дозирования",
    "способ применения": "Режим дозирования",
    "фармакологическое действие": "Фармакологическое действие",
    "применение при беременности": "Применение при беременности и кормлении грудью",
    "кормлении грудью": "Применение при беременности и кормлении грудью",
}


def extract_validation_tokens(text: str) -> list[str]:
    """Извлекает значимые токены для грубой оценки groundedness ответа."""

    normalized_text = normalize_search_text(text)
    if not normalized_text:
        return []

    raw_tokens = re.findall(r"[0-9a-zа-я]+", normalized_text)

    filtered_tokens = [
        raw_token
        for raw_token in raw_tokens
        if len(raw_token) >= 4 and raw_token not in VALIDATION_STOPWORDS
    ]

    return filtered_tokens


def infer_primary_drug_name(
    retrieval_bundle: RetrievalBundle,
    retrieval_summary: RetrievalSummary,
    context_chunks: list[RankedChunkResult],
) -> str:
    """Определяет основной препарат для focused-ответов, если такой ожидается."""

    if retrieval_bundle.matched_drug_documents:
        return retrieval_bundle.matched_drug_documents[0].drug_name_ru

    if retrieval_summary.answer_mode in {"single_drug", "section_focused"}:
        if retrieval_summary.retrieved_drug_names:
            return retrieval_summary.retrieved_drug_names[0]
        if context_chunks and context_chunks[0].drug_name_ru:
            return context_chunks[0].drug_name_ru

    return ""


def detect_section_leakage(
    answer_text: str,
    retrieval_bundle: RetrievalBundle,
) -> list[str]:
    """Ищет явные признаки выхода ответа за пределы запрошенного раздела."""

    normalized_answer_text = normalize_search_text(answer_text)
    if not normalized_answer_text or not retrieval_bundle.section_hints:
        return []

    normalized_requested_sections = {
        normalize_search_text(section_hint)
        for section_hint in retrieval_bundle.section_hints
        if normalize_search_text(section_hint)
    }

    mentioned_sections: list[str] = []

    for section_marker_text, canonical_section_name in SECTION_MARKERS.items():
        escaped_section_marker_text = re.escape(section_marker_text)

        section_pattern = re.compile(
            rf"(?<![0-9a-zа-я]){escaped_section_marker_text}(?![0-9a-zа-я])"
        )

        if not section_pattern.search(normalized_answer_text):
            continue

        normalized_canonical_name = normalize_search_text(canonical_section_name)
        if normalized_canonical_name in normalized_requested_sections:
            continue

        if canonical_section_name not in mentioned_sections:
            mentioned_sections.append(canonical_section_name)

    return mentioned_sections


def validate_rag_answer(
    query: str,
    answer_text: str,
    retrieval_bundle: RetrievalBundle,
    retrieval_summary: RetrievalSummary,
    context_chunks: list[RankedChunkResult],
) -> AnswerValidationResult:
    """Выполняет post-check ответа LLM по набору heuristics поверх retrieval-контекста."""

    context_blocks = [
        "\n".join(
            [
                context_chunk.document_text,
                context_chunk.section_name,
                context_chunk.drug_name_ru,
            ]
        )
        for context_chunk in context_chunks
    ]

    context_text = "\n".join(context_blocks)

    context_tokens = extract_validation_tokens(context_text)
    answer_tokens = extract_validation_tokens(answer_text)
    query_tokens = extract_validation_tokens(query)

    context_token_set = set(context_tokens)
    answer_token_set = set(answer_tokens)
    query_token_set = set(query_tokens)

    shared_token_count = len(answer_token_set & context_token_set)

    grounding_overlap_ratio = (
        shared_token_count / len(answer_token_set)
        if answer_token_set
        else 0.0
    )

    primary_drug_name = infer_primary_drug_name(
        retrieval_bundle=retrieval_bundle,
        retrieval_summary=retrieval_summary,
        context_chunks=context_chunks,
    )

    normalized_answer_text = normalize_drug_name_lookup_text(answer_text)

    context_drug_names = [
        context_drug_name
        for context_drug_name in dict.fromkeys(
            context_chunk.drug_name_ru for context_chunk in context_chunks if context_chunk.drug_name_ru
        )
        if context_drug_name
    ]

    mentioned_context_drug_names = [
        context_drug_name
        for context_drug_name in context_drug_names
        if normalize_drug_name_lookup_text(context_drug_name)
        and normalize_drug_name_lookup_text(context_drug_name) in normalized_answer_text
    ]

    issues: list[str] = []

    if answer_token_set and grounding_overlap_ratio < 0.30:
        issues.append(
            "Низкая опора на retrieval-контекст: значимая часть терминов ответа не найдена в использованных источниках."
        )

    query_coverage = len(answer_token_set & query_token_set) / len(query_token_set) if query_token_set else 1.0
    if query_token_set and query_coverage < 0.2:
        issues.append(
            "Ответ, возможно, не отвечает на заданный вопрос: мало пересечений с ключевыми словами запроса."
        )

    if (
        primary_drug_name
        and retrieval_summary.answer_mode in {"single_drug", "section_focused"}
    ):
        non_primary_drug_names = [
            mentioned_context_drug_name
            for mentioned_context_drug_name in mentioned_context_drug_names
            if normalize_drug_name_lookup_text(mentioned_context_drug_name)
            != normalize_drug_name_lookup_text(primary_drug_name)
        ]
        if non_primary_drug_names:
            issues.append(
                "Ответ смешивает основной препарат с другими препаратами из retrieval-контекста: "
                + ", ".join(non_primary_drug_names[:5])
            )

    leaked_sections = detect_section_leakage(
        answer_text=answer_text,
        retrieval_bundle=retrieval_bundle,
    )
    if leaked_sections:
        issues.append(
            "Ответ, вероятно, вышел за пределы запрошенного раздела и затронул: "
            + ", ".join(leaked_sections[:5])
        )

    status = "ok" if not issues else "warning"

    validation_result = AnswerValidationResult(
        status=status,
        issues=issues,
        grounding_overlap_ratio=grounding_overlap_ratio,
        answer_token_count=len(answer_token_set),
        context_token_count=len(context_token_set),
        primary_drug_name=primary_drug_name,
        mentioned_context_drug_names=mentioned_context_drug_names,
    )

    return validation_result


def infer_answer_mode(
    retrieval_bundle: RetrievalBundle,
) -> str:
    """Определяет режим ответа модели по структуре запроса и найденным retrieval-сигналам."""

    has_drug_match = bool(retrieval_bundle.matched_drug_documents)

    has_section_hint = bool(retrieval_bundle.section_hints)

    has_entity_match = bool(retrieval_bundle.matched_entities)

    if has_drug_match and has_section_hint:
        return "section_focused"

    if has_drug_match:
        return "single_drug"

    if has_entity_match:
        return "entity_list"

    return "category_list"


def build_retrieval_summary(
    retrieval_bundle: RetrievalBundle,
) -> RetrievalSummary:
    """Собирает краткую сводку retrieval для prompt и финального объяснения ответа."""

    answer_mode = infer_answer_mode(retrieval_bundle)

    retrieved_drug_names: list[str] = []

    retrieved_doc_ids: list[str] = []

    for grouped_result in retrieval_bundle.grouped_results:
        if grouped_result.drug_name_ru and grouped_result.drug_name_ru not in retrieved_drug_names:
            retrieved_drug_names.append(grouped_result.drug_name_ru)
        if grouped_result.doc_id and grouped_result.doc_id not in retrieved_doc_ids:
            retrieved_doc_ids.append(grouped_result.doc_id)

    matched_entity_types = [
        matched_entity_type
        for matched_entity_type in dict.fromkeys(
            matched_entity.entity_type for matched_entity in retrieval_bundle.matched_entities
        )
        if matched_entity_type
    ]

    retrieval_summary = RetrievalSummary(
        answer_mode=answer_mode,
        retrieved_drug_names=retrieved_drug_names,
        retrieved_doc_ids=retrieved_doc_ids,
        section_hints=list(retrieval_bundle.section_hints),
        matched_entity_types=matched_entity_types,
    )

    return retrieval_summary


def build_retrieval_summary_text(
    retrieval_summary: RetrievalSummary,
) -> str:
    """Строит краткий текстовый summary retrieval для передачи в prompt модели."""

    drug_names_text = ", ".join(retrieval_summary.retrieved_drug_names[:10]) or "не указаны"

    doc_ids_text = ", ".join(retrieval_summary.retrieved_doc_ids[:10]) or "не указаны"

    entity_types_text = ", ".join(retrieval_summary.matched_entity_types) or "не найдены"

    section_hints_text = ", ".join(retrieval_summary.section_hints) or "не указаны"

    summary_text = (
        f"Режим ответа: {retrieval_summary.answer_mode}\n"
        f"Найденные типы сущностей: {entity_types_text}\n"
        f"Найденные препараты: {drug_names_text}\n"
        f"Doc ID найденных документов: {doc_ids_text}\n"
        f"Целевые разделы: {section_hints_text}"
    )

    return summary_text


def build_rag_context_text(
    context_chunks: list[RankedChunkResult],
) -> str:
    """Строит компактный текстовый контекст для генерации ответа модели."""

    context_blocks: list[str] = []

    for chunk_index, context_chunk in enumerate(context_chunks, start=1):
        source_block = (
            f"[Контекст {chunk_index}]\n"
            f"Препарат: {context_chunk.drug_name_ru or 'Не указан'}\n"
            f"Doc ID: {context_chunk.doc_id or 'Не указан'}\n"
            f"Раздел: {context_chunk.section_name or 'Не указан'}\n"
            f"Текст: {context_chunk.document_text}"
        )
        context_blocks.append(source_block)

    context_text = "\n\n".join(context_blocks)

    return context_text


def clean_user_visible_answer(answer_text: str) -> str:
    """Убирает markdown и текстовые ссылки на источники из ответа для UI."""

    cleaned_lines: list[str] = []
    for raw_line in answer_text.splitlines():
        line = raw_line.strip()
        if not line:
            cleaned_lines.append("")
            continue

        line = re.sub(r"^#{1,6}\s*", "", line)
        line = re.sub(r"\[(?:Источник|Контекст)\s+\d+\]", "", line, flags=re.IGNORECASE)
        line = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
        line = re.sub(r"__(.*?)__", r"\1", line)
        line = re.sub(r"(?<!\w)\*(?!\s)(.*?)(?<!\s)\*(?!\w)", r"\1", line)
        line = re.sub(r"(?<!\w)_(?!\s)(.*?)(?<!\s)_(?!\w)", r"\1", line)
        line = re.sub(r"\s{2,}", " ", line).strip()
        line = re.sub(r"\s+([,.;:!?])", r"\1", line)
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


def build_rag_messages(
    query: str,
    retrieval_summary: RetrievalSummary,
    retrieval_summary_text: str,
    context_text: str,
) -> list[dict[str, str]]:
    """Формирует список сообщений для GigaChat на основе вопроса и retrieval-контекста."""

    system_prompt = (
        "Ты — медицинский справочный ассистент. Твоя задача — давать точные, структурированные ответы "
        "по лекарственным препаратам, опираясь ИСКЛЮЧИТЕЛЬНО на предоставленные источники.\n\n"
        "СТРОГИЕ ПРАВИЛА:\n"
        "1. Используй ТОЛЬКО информацию из предоставленных источников. Если информации недостаточно — "
        "честно скажи об этом. Никогда не придумывай медицинские факты.\n"
        "2. Не добавляй текстовые ссылки на источники в answer: не пиши [Источник 1], [Контекст 1] и похожие пометки. "
        "Источники будут переданы приложению отдельным JSON-полем sources.\n"
        "3. Отвечай по-русски, структурированно. Используй обычный текст, короткие абзацы и нумерованные списки, где это уместно.\n"
        "4. НЕ добавляй информацию из разделов, о которых пользователь не спрашивал "
        "(не примешивай дозировки к вопросу о противопоказаниях, и наоборот).\n"
        "5. В конце ответа добавь краткую пометку: "
        "'Информация приведена на основе справочных данных и не заменяет консультацию врача.'\n\n"
        "ФОРМАТ ОТВЕТА:\n"
        "- Не используй markdown-разметку: символы # для заголовков, **жирный текст**, *курсив*.\n"
        "- Сначала кратко определи суть вопроса.\n"
        "- Затем дай структурированный ответ без текстового указания источников.\n"
        "- Если уместно, укажи название препарата и раздел инструкции."
    )

    if retrieval_summary.answer_mode == "section_focused":
        answer_mode_instructions = (
            "Вопрос про конкретный препарат и конкретный раздел инструкции. "
            "Ответь ТОЛЬКО по этому препарату и ТОЛЬКО по запрошенному разделу. "
            "Не упоминай другие разделы и не переключайся на другие препараты. "
            "Приведи информацию максимально полно из доступных источников."
        )
    elif retrieval_summary.answer_mode == "single_drug":
        answer_mode_instructions = (
            "Вопрос про конкретный препарат. "
            "Ответь только по нему. Обобщи найденные сведения, структурируй по разделам, если это уместно. "
            "Не упоминай другие препараты, если пользователь не просил сравнения."
        )
    elif retrieval_summary.answer_mode == "entity_list":
        answer_mode_instructions = (
            "Вопрос связан с медицинской сущностью (действующее вещество, ATC-группа, нозология), "
            "которая может относиться к нескольким препаратам. "
            "Перечисли найденные препараты, кратко опиши каждый и выдели общее и различия."
        )
    else:
        answer_mode_instructions = (
            "Это широкий категориальный запрос. "
            "Перечисли наиболее релевантные найденные препараты (не один!). "
            "Для каждого кратко поясни, почему он подходит под запрос. "
            "Если препаратов много, сгруппируй их по общим признакам."
        )

    drug_names_text = ", ".join(retrieval_summary.retrieved_drug_names[:10]) or "не определены"
    section_hints_text = ", ".join(retrieval_summary.section_hints) or "не указаны"

    user_prompt = (
        f"Вопрос пользователя:\n{query}\n\n"
        f"Найденные препараты: {drug_names_text}\n"
        f"Целевые разделы: {section_hints_text}\n\n"
        f"Инструкция по формату ответа:\n{answer_mode_instructions}\n\n"
        f"Контексты:\n{context_text}\n\n"
        "Сформируй точный и структурированный ответ только на основе этих контекстов. "
        "Не добавляй markdown-разметку и не вставляй ссылки вида [Источник N] или [Контекст N]."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    return messages


def generate_rag_answer(
    gigachat_client: Any,
    query: str,
    retrieval_bundle: RetrievalBundle,
    chat_model_name: str,
    context_chunk_limit: int,
    answer_max_tokens: int,
) -> tuple[str, list[RankedChunkResult], AnswerValidationResult]:
    """Собирает контекст retrieval, вызывает модель и возвращает итоговый ответ вместе с источниками."""

    if not retrieval_bundle.grouped_results:
        raise RuntimeError("Невозможно сгенерировать ответ без retrieval-результатов.")

    retrieval_summary = build_retrieval_summary(retrieval_bundle)

    context_chunks = select_context_chunks(
        grouped_results=retrieval_bundle.grouped_results,
        context_chunk_limit=context_chunk_limit,
        answer_mode=retrieval_summary.answer_mode,
    )

    if not context_chunks:
        raise RuntimeError("Не удалось отобрать чанки контекста для генерации ответа.")

    context_text = build_rag_context_text(context_chunks)

    retrieval_summary_text = build_retrieval_summary_text(retrieval_summary)

    chat_messages = build_rag_messages(
        query=query,
        retrieval_summary=retrieval_summary,
        retrieval_summary_text=retrieval_summary_text,
        context_text=context_text,
    )

    chat_payload = {
        "model": chat_model_name,
        "messages": chat_messages,
        "temperature": 0.1,
        "max_tokens": answer_max_tokens,
    }

    chat_response = retry_on_transient_error(gigachat_client.chat, chat_payload)

    answer_text = clean_user_visible_answer(extract_chat_message_text(chat_response))

    validation_result = validate_rag_answer(
        query=query,
        answer_text=answer_text,
        retrieval_bundle=retrieval_bundle,
        retrieval_summary=retrieval_summary,
        context_chunks=context_chunks,
    )

    return answer_text, context_chunks, validation_result


def build_find_all_summary_text(
    query: str,
    find_all_bundle: FindAllBundle,
    summary_limit: int,
) -> str:
    """Строит компактную сводку полнотного поиска для передачи в LLM."""

    effective_summary_limit = max(summary_limit, 1)

    total_matches_count = len(find_all_bundle.catalog_matches)

    summary_matches = find_all_bundle.catalog_matches[:effective_summary_limit]

    entity_types = [
        entity_type
        for entity_type in dict.fromkeys(
            matched_entity.entity_type for matched_entity in find_all_bundle.matched_entities
        )
        if entity_type
    ]

    matched_drug_names = [
        matched_drug_document.drug_name_ru
        for matched_drug_document in find_all_bundle.matched_drug_documents
        if matched_drug_document.drug_name_ru
    ]

    summary_lines = [
        f"Запрос: {query}",
        f"Всего найдено препаратов: {total_matches_count}",
        (
            "Типы найденных структурных сущностей: "
            + (", ".join(entity_types) if entity_types else "не найдены")
        ),
        (
            "Прямые совпадения по названию препарата: "
            + (", ".join(matched_drug_names) if matched_drug_names else "не найдены")
        ),
        f"В сводку для модели включено препаратов: {len(summary_matches)}",
    ]

    if total_matches_count > len(summary_matches):
        summary_lines.append(
            "Список в контексте усечен для компактности, "
            "но количество найденных препаратов отражает полный результат поиска."
        )

    summary_lines.append("Найденные препараты:")

    for match_index, catalog_match in enumerate(summary_matches, start=1):
        reasons_text = ", ".join(catalog_match.match_reasons) or "причина не указана"

        summary_lines.append(
            f"{match_index}. {catalog_match.drug_name_ru or 'N/A'} "
            f"(Doc ID: {catalog_match.doc_id}, score={catalog_match.score}, причины: {reasons_text})"
        )

    summary_text = "\n".join(summary_lines)

    return summary_text


def build_find_all_ask_messages(
    query: str,
    summary_text: str,
) -> list[dict[str, str]]:
    """Формирует сообщения для LLM-резюме поверх полного списка найденных препаратов."""

    system_prompt = (
        "Ты помогаешь объяснять результаты полнотного поиска по справочнику лекарственных препаратов. "
        "Используй только предоставленную сводку. "
        "Не выдумывай новые препараты, свойства или медицинские факты, которых нет во входных данных. "
        "Если список найденных препаратов длинный, кратко опиши его и выдели наиболее заметные группы или примеры, "
        "но явно укажи, что полный список приведен ниже в результатах поиска. "
        "Отвечай по-русски, коротко, структурно и по делу."
    )

    user_prompt = (
        f"Запрос пользователя:\n{query}\n\n"
        f"Сводка полного списка найденных препаратов:\n{summary_text}\n\n"
        "Сформируй краткое понятное резюме этого полного результата. "
        "Не сокращай полный результат до одного препарата. "
        "Если уместно, укажи, что ниже будет напечатан полный список найденных препаратов."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    return messages


def generate_find_all_answer(
    gigachat_client: Any,
    query: str,
    find_all_bundle: FindAllBundle,
    chat_model_name: str,
    answer_max_tokens: int,
    summary_limit: int,
) -> str:
    """Генерирует краткое LLM-резюме поверх полного списка найденных препаратов."""

    if not find_all_bundle.catalog_matches:
        raise RuntimeError("Невозможно сгенерировать резюме без найденных препаратов.")

    summary_text = build_find_all_summary_text(
        query=query,
        find_all_bundle=find_all_bundle,
        summary_limit=summary_limit,
    )

    chat_messages = build_find_all_ask_messages(
        query=query,
        summary_text=summary_text,
    )

    chat_payload = {
        "model": chat_model_name,
        "messages": chat_messages,
        "temperature": 0.1,
        "max_tokens": answer_max_tokens,
    }

    chat_response = retry_on_transient_error(gigachat_client.chat, chat_payload)

    answer_text = extract_chat_message_text(chat_response)

    return answer_text


def build_generate_questions_messages(
    query: str,
    question_count: int,
    summary_text: str,
) -> list[dict[str, str]]:
    """Формирует сообщения для генерации списка вопросов по найденной теме."""

    system_prompt = (
        "Ты помогаешь составлять вопросы по справочнику лекарственных препаратов. "
        "Используй только предоставленную сводку найденных препаратов. "
        "Не выдумывай препараты или факты, которых нет в сводке. "
        "Сформируй вопросы так, чтобы на них можно было отвечать, опираясь на найденный набор препаратов и их признаки. "
        "Отвечай по-русски. "
        "Верни только нумерованный список вопросов без дополнительных пояснений."
    )

    user_prompt = (
        f"Тема пользователя:\n{query}\n\n"
        f"Нужно сгенерировать вопросов: {question_count}\n\n"
        f"Сводка найденных препаратов:\n{summary_text}\n\n"
        "Сгенерируй ровно указанное число вопросов. "
        "Вопросы должны быть разнообразными, понятными и относиться к найденной теме."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    return messages


def generate_questions_answer(
    gigachat_client: Any,
    query: str,
    find_all_bundle: FindAllBundle,
    question_count: int,
    chat_model_name: str,
    answer_max_tokens: int,
    summary_limit: int,
) -> str:
    """Генерирует список вопросов по теме на основе полного результата полнотного поиска."""

    if not find_all_bundle.catalog_matches:
        raise RuntimeError("Невозможно сгенерировать вопросы без найденных препаратов.")

    effective_question_count = max(question_count, 1)

    summary_text = build_find_all_summary_text(
        query=query,
        find_all_bundle=find_all_bundle,
        summary_limit=summary_limit,
    )

    chat_messages = build_generate_questions_messages(
        query=query,
        question_count=effective_question_count,
        summary_text=summary_text,
    )

    chat_payload = {
        "model": chat_model_name,
        "messages": chat_messages,
        "temperature": 0.3,
        "max_tokens": answer_max_tokens,
    }

    chat_response = retry_on_transient_error(gigachat_client.chat, chat_payload)

    answer_text = extract_chat_message_text(chat_response)

    return answer_text
