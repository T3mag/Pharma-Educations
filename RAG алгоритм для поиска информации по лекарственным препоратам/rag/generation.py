"""Генерация ответов и вопросов поверх retrieval-результатов."""

from __future__ import annotations

import re
from typing import Any

from .common import extract_chat_message_text, normalize_drug_name_lookup_text, normalize_search_text
from .models import (
    AnswerValidationResult,
    FindAllBundle,
    RankedChunkResult,
    RetrievalBundle,
    RetrievalSummary,
)
from .search import select_context_chunks


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

    # normalized_text хранит нормализованный текст без различий регистра и лишних пробелов.
    normalized_text = normalize_search_text(text)
    if not normalized_text:
        return []

    # raw_tokens хранит все буквенно-цифровые токены нормализованного текста.
    raw_tokens = re.findall(r"[0-9a-zа-я]+", normalized_text)

    # filtered_tokens хранит токены, пригодные для post-check проверки.
    filtered_tokens = [
        raw_token
        for raw_token in raw_tokens
        if len(raw_token) >= 4 and raw_token not in VALIDATION_STOPWORDS
    ]

    # return_value содержит значимые токены для валидации ответа.
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

    # normalized_answer_text хранит нормализованный ответ модели.
    normalized_answer_text = normalize_search_text(answer_text)
    if not normalized_answer_text or not retrieval_bundle.section_hints:
        return []

    # normalized_requested_sections хранит нормализованные целевые разделы из вопроса.
    normalized_requested_sections = {
        normalize_search_text(section_hint)
        for section_hint in retrieval_bundle.section_hints
        if normalize_search_text(section_hint)
    }

    # mentioned_sections хранит явные маркеры других разделов, найденные прямо в ответе.
    mentioned_sections: list[str] = []

    # section_marker_text и canonical_section_name по очереди перебирают известные названия разделов.
    for section_marker_text, canonical_section_name in SECTION_MARKERS.items():
        # escaped_section_marker_text хранит безопасную regex-форму маркера раздела.
        escaped_section_marker_text = re.escape(section_marker_text)

        # section_pattern хранит regex для поиска маркера раздела по границам слова.
        section_pattern = re.compile(
            rf"(?<![0-9a-zа-я]){escaped_section_marker_text}(?![0-9a-zа-я])"
        )

        if not section_pattern.search(normalized_answer_text):
            continue

        # normalized_canonical_name хранит нормализованное каноническое имя раздела.
        normalized_canonical_name = normalize_search_text(canonical_section_name)
        if normalized_canonical_name in normalized_requested_sections:
            continue

        if canonical_section_name not in mentioned_sections:
            mentioned_sections.append(canonical_section_name)

    # return_value содержит список явно упомянутых сторонних разделов.
    return mentioned_sections


def validate_rag_answer(
    query: str,
    answer_text: str,
    retrieval_bundle: RetrievalBundle,
    retrieval_summary: RetrievalSummary,
    context_chunks: list[RankedChunkResult],
) -> AnswerValidationResult:
    """Выполняет post-check ответа LLM по набору heuristics поверх retrieval-контекста."""

    del query

    # context_blocks хранит отдельные текстовые блоки для грубой оценки groundedness.
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

    # context_text хранит объединенный текст чанков, реально использованных в prompt.
    context_text = "\n".join(context_blocks)

    # context_tokens хранит значимые токены retrieval-контекста.
    context_tokens = extract_validation_tokens(context_text)

    # answer_tokens хранит значимые токены ответа модели.
    answer_tokens = extract_validation_tokens(answer_text)

    # context_token_set хранит множество токенов retrieval-контекста.
    context_token_set = set(context_tokens)

    # answer_token_set хранит множество токенов ответа модели.
    answer_token_set = set(answer_tokens)

    # shared_token_count хранит число значимых токенов ответа, поддержанных retrieval-контекстом.
    shared_token_count = len(answer_token_set & context_token_set)

    # grounding_overlap_ratio хранит долю токенов ответа, встречающихся в контексте.
    grounding_overlap_ratio = (
        shared_token_count / len(answer_token_set)
        if answer_token_set
        else 0.0
    )

    # primary_drug_name хранит основной препарат для focused-ответов.
    primary_drug_name = infer_primary_drug_name(
        retrieval_bundle=retrieval_bundle,
        retrieval_summary=retrieval_summary,
        context_chunks=context_chunks,
    )

    # normalized_answer_text хранит нормализованный ответ модели для поиска имен препаратов.
    normalized_answer_text = normalize_drug_name_lookup_text(answer_text)

    # context_drug_names хранит названия препаратов из реально использованного контекста без дублей.
    context_drug_names = [
        context_drug_name
        for context_drug_name in dict.fromkeys(
            context_chunk.drug_name_ru for context_chunk in context_chunks if context_chunk.drug_name_ru
        )
        if context_drug_name
    ]

    # mentioned_context_drug_names хранит препараты из контекста, явно упомянутые в ответе.
    mentioned_context_drug_names = [
        context_drug_name
        for context_drug_name in context_drug_names
        if normalize_drug_name_lookup_text(context_drug_name)
        and normalize_drug_name_lookup_text(context_drug_name) in normalized_answer_text
    ]

    # issues хранит список потенциальных проблем ответа.
    issues: list[str] = []

    if answer_token_set and grounding_overlap_ratio < 0.35:
        issues.append(
            "Низкая опора на retrieval-контекст: значимая часть терминов ответа не найдена в использованных источниках."
        )

    if (
        primary_drug_name
        and retrieval_summary.answer_mode in {"single_drug", "section_focused"}
    ):
        # non_primary_drug_names хранит препараты из ответа, которые отвлекают от основного препарата.
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

    # leaked_sections хранит сторонние разделы, явно всплывшие в ответе модели.
    leaked_sections = detect_section_leakage(
        answer_text=answer_text,
        retrieval_bundle=retrieval_bundle,
    )
    if leaked_sections:
        issues.append(
            "Ответ, вероятно, вышел за пределы запрошенного раздела и затронул: "
            + ", ".join(leaked_sections[:5])
        )

    # status хранит итоговый статус проверки.
    status = "ok" if not issues else "warning"

    # validation_result хранит итог post-check проверки ответа модели.
    validation_result = AnswerValidationResult(
        status=status,
        issues=issues,
        grounding_overlap_ratio=grounding_overlap_ratio,
        answer_token_count=len(answer_token_set),
        context_token_count=len(context_token_set),
        primary_drug_name=primary_drug_name,
        mentioned_context_drug_names=mentioned_context_drug_names,
    )

    # return_value содержит структурированный результат post-check проверки.
    return validation_result


def infer_answer_mode(
    retrieval_bundle: RetrievalBundle,
) -> str:
    """Определяет режим ответа модели по структуре запроса и найденным retrieval-сигналам."""

    # has_drug_match показывает, найден ли конкретный препарат по торговому названию.
    has_drug_match = bool(retrieval_bundle.matched_drug_documents)

    # has_section_hint показывает, запрошен ли конкретный раздел инструкции.
    has_section_hint = bool(retrieval_bundle.section_hints)

    # has_entity_match показывает, распознана ли структурная сущность справочника.
    has_entity_match = bool(retrieval_bundle.matched_entities)

    if has_drug_match and has_section_hint:
        return "section_focused"

    if has_drug_match:
        return "single_drug"

    if has_entity_match:
        return "entity_list"

    # return_value содержит режим ответа для широких и категориальных запросов.
    return "category_list"


def build_retrieval_summary(
    retrieval_bundle: RetrievalBundle,
) -> RetrievalSummary:
    """Собирает краткую сводку retrieval для prompt и финального объяснения ответа."""

    # answer_mode хранит режим ответа, подходящий для текущего вопроса.
    answer_mode = infer_answer_mode(retrieval_bundle)

    # retrieved_drug_names хранит названия препаратов из сгруппированной выдачи без дублей.
    retrieved_drug_names: list[str] = []

    # retrieved_doc_ids хранит doc_id из сгруппированной выдачи без дублей.
    retrieved_doc_ids: list[str] = []

    # grouped_result по очереди перебирает найденные документы.
    for grouped_result in retrieval_bundle.grouped_results:
        if grouped_result.drug_name_ru and grouped_result.drug_name_ru not in retrieved_drug_names:
            retrieved_drug_names.append(grouped_result.drug_name_ru)
        if grouped_result.doc_id and grouped_result.doc_id not in retrieved_doc_ids:
            retrieved_doc_ids.append(grouped_result.doc_id)

    # matched_entity_types хранит типы найденных структурных сущностей без дублей.
    matched_entity_types = [
        matched_entity_type
        for matched_entity_type in dict.fromkeys(
            matched_entity.entity_type for matched_entity in retrieval_bundle.matched_entities
        )
        if matched_entity_type
    ]

    # retrieval_summary хранит собранную краткую сводку retrieval.
    retrieval_summary = RetrievalSummary(
        answer_mode=answer_mode,
        retrieved_drug_names=retrieved_drug_names,
        retrieved_doc_ids=retrieved_doc_ids,
        section_hints=list(retrieval_bundle.section_hints),
        matched_entity_types=matched_entity_types,
    )

    # return_value содержит краткую сводку retrieval для prompt.
    return retrieval_summary


def build_retrieval_summary_text(
    retrieval_summary: RetrievalSummary,
) -> str:
    """Строит краткий текстовый summary retrieval для передачи в prompt модели."""

    # drug_names_text хранит компактный список найденных препаратов.
    drug_names_text = ", ".join(retrieval_summary.retrieved_drug_names[:10]) or "не указаны"

    # doc_ids_text хранит компактный список найденных doc_id.
    doc_ids_text = ", ".join(retrieval_summary.retrieved_doc_ids[:10]) or "не указаны"

    # entity_types_text хранит список найденных типов сущностей.
    entity_types_text = ", ".join(retrieval_summary.matched_entity_types) or "не найдены"

    # section_hints_text хранит список целевых разделов, если они были найдены в вопросе.
    section_hints_text = ", ".join(retrieval_summary.section_hints) or "не указаны"

    # summary_text хранит текстовую сводку retrieval для prompt.
    summary_text = (
        f"Режим ответа: {retrieval_summary.answer_mode}\n"
        f"Найденные типы сущностей: {entity_types_text}\n"
        f"Найденные препараты: {drug_names_text}\n"
        f"Doc ID найденных документов: {doc_ids_text}\n"
        f"Целевые разделы: {section_hints_text}"
    )

    # return_value содержит краткую retrieval-сводку для модели.
    return summary_text


def build_rag_context_text(
    context_chunks: list[RankedChunkResult],
) -> str:
    """Строит компактный текстовый контекст для генерации ответа модели."""

    # context_blocks хранит текстовые блоки источников, которые будут переданы модели.
    context_blocks: list[str] = []

    # chunk_index и context_chunk по очереди перебирают выбранные чанки контекста.
    for chunk_index, context_chunk in enumerate(context_chunks, start=1):
        # source_block хранит оформленный блок одного источника для prompt-контекста.
        source_block = (
            f"[Источник {chunk_index}]\n"
            f"Препарат: {context_chunk.drug_name_ru or 'Не указан'}\n"
            f"Doc ID: {context_chunk.doc_id or 'Не указан'}\n"
            f"Раздел: {context_chunk.section_name or 'Не указан'}\n"
            f"Текст: {context_chunk.document_text}"
        )
        context_blocks.append(source_block)

    # context_text хранит объединенный текст всех источников для prompt.
    context_text = "\n\n".join(context_blocks)

    # return_value содержит готовый контекст для передачи в модель.
    return context_text


def build_rag_messages(
    query: str,
    retrieval_summary: RetrievalSummary,
    retrieval_summary_text: str,
    context_text: str,
) -> list[dict[str, str]]:
    """Формирует список сообщений для GigaChat на основе вопроса и retrieval-контекста."""

    # system_prompt хранит системную инструкцию для медицинского RAG-ответа.
    system_prompt = (
        "Ты помогаешь отвечать по справочнику лекарственных препаратов. "
        "Используй только предоставленные источники. "
        "Не выдумывай факты, противопоказания, показания, дозировки и иные медицинские сведения. "
        "Если в источниках нет ответа, честно скажи, что данных недостаточно. "
        "Отвечай по-русски, четко и по делу. "
        "Если уместно, упоминай препарат и раздел, из которого взята информация. "
        "Если вопрос относится к группе препаратов или категории, перечисляй несколько найденных препаратов, а не своди ответ к одному. "
        "Если вопрос относится к конкретному препарату и конкретному разделу, отвечай только по нему. "
        "Не добавляй сведения о дозировке, противопоказаниях, побочных действиях или других разделах, если пользователь этого не спрашивал."
    )

    # answer_mode_instructions хранит уточнение формата ответа в зависимости от типа вопроса.
    if retrieval_summary.answer_mode == "section_focused":
        answer_mode_instructions = (
            "Это вопрос про конкретный препарат и конкретный раздел. "
            "Ответь только по этому препарату и только по запрошенному разделу."
        )
    elif retrieval_summary.answer_mode == "single_drug":
        answer_mode_instructions = (
            "Это вопрос про конкретный препарат. "
            "Ответь только по нему и кратко обобщи найденные сведения без перечисления посторонних препаратов."
        )
    elif retrieval_summary.answer_mode == "entity_list":
        answer_mode_instructions = (
            "Это вопрос по сущности справочника, которая может быть связана с несколькими препаратами. "
            "Если источники это подтверждают, перечисли несколько найденных препаратов и кратко опиши различия или общее."
        )
    else:
        answer_mode_instructions = (
            "Это широкий категориальный запрос. "
            "Перечисли несколько наиболее релевантных найденных препаратов и кратко объясни, почему они подходят."
        )

    # user_prompt хранит пользовательский вопрос вместе с retrieval-контекстом.
    user_prompt = (
        f"Вопрос пользователя:\n{query}\n\n"
        f"Сводка retrieval:\n{retrieval_summary_text}\n\n"
        f"Инструкция по формату ответа:\n{answer_mode_instructions}\n\n"
        f"Источники:\n{context_text}\n\n"
        "Сформируй краткий и точный ответ только на основе этих источников."
    )

    # messages хранит список сообщений для chat API GigaChat.
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    # return_value содержит готовые chat messages для модели.
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

    # retrieval_summary хранит краткую сводку retrieval для prompt.
    retrieval_summary = build_retrieval_summary(retrieval_bundle)

    # context_chunks хранит ограниченный набор лучших чанков для генерации ответа.
    context_chunks = select_context_chunks(
        grouped_results=retrieval_bundle.grouped_results,
        context_chunk_limit=context_chunk_limit,
        answer_mode=retrieval_summary.answer_mode,
    )

    if not context_chunks:
        raise RuntimeError("Не удалось отобрать чанки контекста для генерации ответа.")

    # context_text хранит компактное текстовое представление retrieval-контекста.
    context_text = build_rag_context_text(context_chunks)

    # retrieval_summary_text хранит краткое текстовое описание найденных документов и режима ответа.
    retrieval_summary_text = build_retrieval_summary_text(retrieval_summary)

    # chat_messages хранит список сообщений для chat API модели.
    chat_messages = build_rag_messages(
        query=query,
        retrieval_summary=retrieval_summary,
        retrieval_summary_text=retrieval_summary_text,
        context_text=context_text,
    )

    # chat_payload хранит параметры запроса к GigaChat для генерации финального ответа.
    chat_payload = {
        "model": chat_model_name,
        "messages": chat_messages,
        "temperature": 0.1,
        "max_tokens": answer_max_tokens,
    }

    # chat_response хранит ответ модели на RAG-запрос.
    chat_response = gigachat_client.chat(chat_payload)

    # answer_text хранит извлеченный текст итогового ответа модели.
    answer_text = extract_chat_message_text(chat_response)

    # validation_result хранит результат post-check проверки ответа на groundedness и фокус.
    validation_result = validate_rag_answer(
        query=query,
        answer_text=answer_text,
        retrieval_bundle=retrieval_bundle,
        retrieval_summary=retrieval_summary,
        context_chunks=context_chunks,
    )

    # return_value содержит готовый ответ, использованные чанки-источники и результат валидации.
    return answer_text, context_chunks, validation_result


def build_find_all_summary_text(
    query: str,
    find_all_bundle: FindAllBundle,
    summary_limit: int,
) -> str:
    """Строит компактную сводку полнотного поиска для передачи в LLM."""

    # effective_summary_limit хранит безопасное положительное ограничение длины LLM-сводки.
    effective_summary_limit = max(summary_limit, 1)

    # total_matches_count хранит общее число найденных препаратов.
    total_matches_count = len(find_all_bundle.catalog_matches)

    # summary_matches хранит список препаратов, который будет реально передан в модель.
    summary_matches = find_all_bundle.catalog_matches[:effective_summary_limit]

    # entity_types хранит типы найденных структурных сущностей без дублей.
    entity_types = [
        entity_type
        for entity_type in dict.fromkeys(
            matched_entity.entity_type for matched_entity in find_all_bundle.matched_entities
        )
        if entity_type
    ]

    # matched_drug_names хранит названия препаратов, найденных через прямой lookup по торговому названию.
    matched_drug_names = [
        matched_drug_document.drug_name_ru
        for matched_drug_document in find_all_bundle.matched_drug_documents
        if matched_drug_document.drug_name_ru
    ]

    # summary_lines хранит текстовые строки итоговой сводки для модели.
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

    # match_index и catalog_match по очереди перебирают препараты, вошедшие в LLM-сводку.
    for match_index, catalog_match in enumerate(summary_matches, start=1):
        # reasons_text хранит компактное описание причин совпадения препарата с запросом.
        reasons_text = ", ".join(catalog_match.match_reasons) or "причина не указана"

        summary_lines.append(
            f"{match_index}. {catalog_match.drug_name_ru or 'N/A'} "
            f"(Doc ID: {catalog_match.doc_id}, score={catalog_match.score}, причины: {reasons_text})"
        )

    # summary_text хранит готовую текстовую сводку полнотного поиска.
    summary_text = "\n".join(summary_lines)

    # return_value содержит компактную сводку для передачи в LLM.
    return summary_text


def build_find_all_ask_messages(
    query: str,
    summary_text: str,
) -> list[dict[str, str]]:
    """Формирует сообщения для LLM-резюме поверх полного списка найденных препаратов."""

    # system_prompt хранит системную инструкцию для краткого резюме полного списка препаратов.
    system_prompt = (
        "Ты помогаешь объяснять результаты полнотного поиска по справочнику лекарственных препаратов. "
        "Используй только предоставленную сводку. "
        "Не выдумывай новые препараты, свойства или медицинские факты, которых нет во входных данных. "
        "Если список найденных препаратов длинный, кратко опиши его и выдели наиболее заметные группы или примеры, "
        "но явно укажи, что полный список приведен ниже в результатах поиска. "
        "Отвечай по-русски, коротко, структурно и по делу."
    )

    # user_prompt хранит запрос пользователя и сводку полного списка препаратов.
    user_prompt = (
        f"Запрос пользователя:\n{query}\n\n"
        f"Сводка полного списка найденных препаратов:\n{summary_text}\n\n"
        "Сформируй краткое понятное резюме этого полного результата. "
        "Не сокращай полный результат до одного препарата. "
        "Если уместно, укажи, что ниже будет напечатан полный список найденных препаратов."
    )

    # messages хранит список сообщений для chat API GigaChat.
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    # return_value содержит готовые сообщения для генерации LLM-резюме.
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

    # summary_text хранит компактную сводку полного списка препаратов для модели.
    summary_text = build_find_all_summary_text(
        query=query,
        find_all_bundle=find_all_bundle,
        summary_limit=summary_limit,
    )

    # chat_messages хранит сообщения для генерации итогового резюме.
    chat_messages = build_find_all_ask_messages(
        query=query,
        summary_text=summary_text,
    )

    # chat_payload хранит параметры запроса к GigaChat для резюме полного списка.
    chat_payload = {
        "model": chat_model_name,
        "messages": chat_messages,
        "temperature": 0.1,
        "max_tokens": answer_max_tokens,
    }

    # chat_response хранит ответ модели на запрос резюме полного списка.
    chat_response = gigachat_client.chat(chat_payload)

    # answer_text хранит извлеченный текст итогового LLM-резюме.
    answer_text = extract_chat_message_text(chat_response)

    # return_value содержит готовое краткое резюме полного списка препаратов.
    return answer_text


def build_generate_questions_messages(
    query: str,
    question_count: int,
    summary_text: str,
) -> list[dict[str, str]]:
    """Формирует сообщения для генерации списка вопросов по найденной теме."""

    # system_prompt хранит системную инструкцию для генерации вопросов на основе полного результата поиска.
    system_prompt = (
        "Ты помогаешь составлять вопросы по справочнику лекарственных препаратов. "
        "Используй только предоставленную сводку найденных препаратов. "
        "Не выдумывай препараты или факты, которых нет в сводке. "
        "Сформируй вопросы так, чтобы на них можно было отвечать, опираясь на найденный набор препаратов и их признаки. "
        "Отвечай по-русски. "
        "Верни только нумерованный список вопросов без дополнительных пояснений."
    )

    # user_prompt хранит запрос пользователя, требуемое число вопросов и сводку найденных препаратов.
    user_prompt = (
        f"Тема пользователя:\n{query}\n\n"
        f"Нужно сгенерировать вопросов: {question_count}\n\n"
        f"Сводка найденных препаратов:\n{summary_text}\n\n"
        "Сгенерируй ровно указанное число вопросов. "
        "Вопросы должны быть разнообразными, понятными и относиться к найденной теме."
    )

    # messages хранит сообщения для chat API GigaChat.
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    # return_value содержит готовые сообщения для генерации вопросов.
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

    # effective_question_count хранит безопасное положительное число вопросов.
    effective_question_count = max(question_count, 1)

    # summary_text хранит компактную сводку полного списка препаратов для модели.
    summary_text = build_find_all_summary_text(
        query=query,
        find_all_bundle=find_all_bundle,
        summary_limit=summary_limit,
    )

    # chat_messages хранит сообщения для генерации списка вопросов.
    chat_messages = build_generate_questions_messages(
        query=query,
        question_count=effective_question_count,
        summary_text=summary_text,
    )

    # chat_payload хранит параметры запроса к GigaChat для генерации вопросов.
    chat_payload = {
        "model": chat_model_name,
        "messages": chat_messages,
        "temperature": 0.3,
        "max_tokens": answer_max_tokens,
    }

    # chat_response хранит ответ модели со списком вопросов.
    chat_response = gigachat_client.chat(chat_payload)

    # answer_text хранит извлеченный текст списка вопросов.
    answer_text = extract_chat_message_text(chat_response)

    # return_value содержит готовый список вопросов по найденной теме.
    return answer_text
