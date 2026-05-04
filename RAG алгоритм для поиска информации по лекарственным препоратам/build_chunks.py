"""Build retrieval-ready chunks from structured Vidal documents.

The script solves the third preparation stage for the future RAG pipeline:
1. Reads structured drug documents and entity relations.
2. Enriches each drug document with related entities.
3. Builds meaningful chunks from overview, composition, and instruction sections.
4. Saves chunk records into a JSONL file for embedding and retrieval.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Iterator, Optional


# DEFAULT_DOCUMENTS_FILE хранит путь к JSONL-файлу со структурированными карточками препаратов.
DEFAULT_DOCUMENTS_FILE = Path(__file__).resolve().parent / "structured_documents.jsonl"

# DEFAULT_RELATIONS_FILE хранит путь к JSONL-файлу со связями между сущностями и карточками препаратов.
DEFAULT_RELATIONS_FILE = Path(__file__).resolve().parent / "entity_relations.jsonl"

# DEFAULT_OUTPUT_FILE хранит путь к выходному JSONL-файлу с retrieval-ready чанками.
DEFAULT_OUTPUT_FILE = Path(__file__).resolve().parent / "chunks.jsonl"

# WHITESPACE_PATTERN схлопывает последовательности пробелов и переводов строк в один пробел.
WHITESPACE_PATTERN = re.compile(r"\s+")

# SENTENCE_SPLIT_PATTERN приближенно делит русский и латинский текст на предложения по знакам конца фразы.
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+(?=[A-ZА-ЯЁ0-9])")

# DEFAULT_TARGET_CHUNK_LENGTH задает желаемую длину chunk_text в символах.
DEFAULT_TARGET_CHUNK_LENGTH = 1400

# DEFAULT_MAX_CHUNK_LENGTH задает верхнюю границу длины chunk_text в символах.
DEFAULT_MAX_CHUNK_LENGTH = 1800

# DEFAULT_OVERLAP_SENTENCES задает число предложений, переносимых в следующий чанк.
DEFAULT_OVERLAP_SENTENCES = 1


@dataclass
class ChunkRecord:
    """Хранит один retrieval-ready чанк с текстом и метаданными."""

    # chunk_id хранит уникальный идентификатор чанка для отладки, индексации и трассировки ответа.
    chunk_id: str

    # doc_id хранит идентификатор карточки препарата, из которой построен чанк.
    doc_id: str

    # chunk_type хранит тип чанка: overview, composition или section.
    chunk_type: str

    # section_name хранит название раздела, если чанк создан из конкретного раздела инструкции.
    section_name: str

    # chunk_index хранит порядковый номер чанка внутри одного раздела или блока.
    chunk_index: int

    # source_path хранит путь к исходной HTML-карточке препарата.
    source_path: str

    # title хранит заголовок HTML-страницы карточки препарата.
    title: str

    # drug_name_ru хранит торговое название препарата на русском языке.
    drug_name_ru: str

    # drug_name_lat хранит латинское или международное торговое название препарата.
    drug_name_lat: str

    # dosage_form хранит лекарственную форму препарата.
    dosage_form: str

    # clinical_pharmacological_group хранит клинико-фармакологическую группу из карточки препарата.
    clinical_pharmacological_group: str

    # active_substances хранит вещества, извлеченные из шапки карточки препарата.
    active_substances: list[str]

    # related_active_substance_names_ru хранит русские названия действующих веществ из индексных страниц.
    related_active_substance_names_ru: list[str]

    # related_active_substance_names_lat хранит латинские названия действующих веществ из индексных страниц.
    related_active_substance_names_lat: list[str]

    # atc_codes хранит все ATX-коды, связанные с карточкой препарата.
    atc_codes: list[str]

    # nosology_codes хранит коды нозологий, связанных с карточкой препарата.
    nosology_codes: list[str]

    # nosology_names хранит названия нозологий, связанных с карточкой препарата.
    nosology_names: list[str]

    # clinical_group_codes хранит коды клинико-фармакологических групп, связанных с карточкой препарата.
    clinical_group_codes: list[str]

    # clinical_group_names хранит названия клинико-фармакологических групп, связанных с карточкой препарата.
    clinical_group_names: list[str]

    # registration_number хранит регистрационный номер, если он в карточке один и был извлечен однозначно.
    registration_number: str

    # registration_date_raw хранит дату регистрации, если она извлечена однозначно.
    registration_date_raw: str

    # chunk_text хранит чистый текст chunk'а без дополнительного контекста.
    chunk_text: str

    # retrieval_text хранит текст, обогащенный контекстом и готовый к построению эмбеддингов.
    retrieval_text: str


def parse_arguments() -> argparse.Namespace:
    """Разбирает аргументы командной строки и возвращает конфигурацию запуска."""

    # parser описывает интерфейс запуска скрипта из терминала.
    parser = argparse.ArgumentParser(
        description="Build retrieval-ready chunks from structured Vidal documents.",
    )

    # documents_file_argument указывает путь к JSONL-файлу со структурированными карточками препаратов.
    parser.add_argument(
        "--documents-file",
        type=Path,
        default=DEFAULT_DOCUMENTS_FILE,
        help="Path to structured_documents.jsonl.",
    )

    # relations_file_argument указывает путь к JSONL-файлу со связями между сущностями и препаратами.
    parser.add_argument(
        "--relations-file",
        type=Path,
        default=DEFAULT_RELATIONS_FILE,
        help="Path to entity_relations.jsonl.",
    )

    # output_file_argument указывает путь к выходному JSONL-файлу с чанками.
    parser.add_argument(
        "--output-file",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help="Path to chunks.jsonl.",
    )

    # target_length_argument задает желаемую длину чанка в символах.
    parser.add_argument(
        "--target-length",
        type=int,
        default=DEFAULT_TARGET_CHUNK_LENGTH,
        help="Desired chunk length in characters.",
    )

    # max_length_argument задает жесткий верхний предел длины чанка в символах.
    parser.add_argument(
        "--max-length",
        type=int,
        default=DEFAULT_MAX_CHUNK_LENGTH,
        help="Maximum chunk length in characters.",
    )

    # overlap_argument задает число предложений перекрытия между соседними чанками.
    parser.add_argument(
        "--overlap-sentences",
        type=int,
        default=DEFAULT_OVERLAP_SENTENCES,
        help="Number of overlapping sentences between neighboring chunks.",
    )

    # limit_argument позволяет ограничить число обработанных документов при отладке.
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit of processed structured documents.",
    )

    # return_value содержит разобранные аргументы командной строки.
    return parser.parse_args()


def normalize_text(raw_text: str) -> str:
    """Очищает строку от лишних пробелов и переводов строк."""

    # stripped_text удаляет пробелы по краям строки.
    stripped_text = raw_text.strip()

    # normalized_text схлопывает повторяющиеся пробельные символы.
    normalized_text = WHITESPACE_PATTERN.sub(" ", stripped_text)

    # return_value содержит чистый однострочный текст.
    return normalized_text


def load_jsonl_records(input_file: Path, limit: Optional[int] = None) -> Iterator[dict]:
    """Читает JSONL-файл и возвращает записи по одной."""

    with input_file.open("r", encoding="utf-8") as input_stream:
        # line_index хранит порядковый номер текущей строки и используется для поддержки limit.
        for line_index, line in enumerate(input_stream, start=1):
            if limit is not None and line_index > limit:
                break

            # record хранит одну JSON-запись, считанную из файла.
            record = json.loads(line)
            yield record


def append_unique(target_list: list[str], value: str) -> None:
    """Добавляет значение в список только если оно непустое и еще не встречалось."""

    # normalized_value хранит очищенное значение для безопасного добавления в список.
    normalized_value = normalize_text(value)
    if not normalized_value:
        return
    if normalized_value in target_list:
        return
    target_list.append(normalized_value)


def append_labeled_value(target_list: list[str], label: str, value: str) -> None:
    """Добавляет строку вида 'label: value' только если value непустое."""

    # normalized_label хранит очищенную подпись поля.
    normalized_label = normalize_text(label)

    # normalized_value хранит очищенное значение поля.
    normalized_value = normalize_text(value)

    if not normalized_label or not normalized_value:
        return
    if normalized_value.rstrip(":") == normalized_label.rstrip(":"):
        return

    # labeled_value хранит итоговую строку с подписью и значением.
    labeled_value = f"{normalized_label}: {normalized_value}"
    append_unique(target_list, labeled_value)


def build_relation_index(relations_file: Path) -> dict[str, dict[str, list[str]]]:
    """Строит индекс метаданных по doc_id на основе файла entity_relations.jsonl."""

    # relation_index хранит агрегированные метаданные по каждому doc_id.
    relation_index: dict[str, dict[str, list[str]]] = {}

    # relation_record по очереди перебирает все записи о связях между сущностями и препаратами.
    for relation_record in load_jsonl_records(input_file=relations_file):
        # doc_id хранит идентификатор карточки препарата, к которой относится текущая связь.
        doc_id = relation_record["target_doc_id"]

        if doc_id not in relation_index:
            relation_index[doc_id] = {
                "active_substance_names_ru": [],
                "active_substance_names_lat": [],
                "atc_codes": [],
                "nosology_codes": [],
                "nosology_names": [],
                "clinical_group_codes": [],
                "clinical_group_names": [],
            }

        # relation_bucket хранит агрегированные списки метаданных для текущего doc_id.
        relation_bucket = relation_index[doc_id]

        # entity_type хранит тип сущности текущей связи.
        entity_type = relation_record["entity_type"]

        if entity_type == "active_substance":
            append_unique(relation_bucket["active_substance_names_ru"], relation_record["entity_name"])
            append_unique(relation_bucket["active_substance_names_lat"], relation_record["entity_name_lat"])
        elif entity_type == "atc":
            append_unique(relation_bucket["atc_codes"], relation_record["entity_code"])
        elif entity_type == "nosology":
            append_unique(relation_bucket["nosology_codes"], relation_record["entity_code"])
            append_unique(relation_bucket["nosology_names"], relation_record["entity_name"])
        elif entity_type == "clinical_pharmacology_group":
            append_unique(relation_bucket["clinical_group_codes"], relation_record["entity_code"])
            append_unique(relation_bucket["clinical_group_names"], relation_record["entity_name"])

    # return_value содержит агрегированные метаданные по всем карточкам препаратов.
    return relation_index


def merge_document_metadata(document_record: dict, relation_index: dict[str, dict[str, list[str]]]) -> dict:
    """Объединяет данные карточки препарата с агрегированными связями из index-страниц."""

    # doc_id хранит идентификатор текущей карточки препарата.
    doc_id = document_record["doc_id"]

    # relation_metadata хранит связанные сущности для текущей карточки препарата.
    relation_metadata = relation_index.get(doc_id, {})

    # merged_metadata хранит объединенный набор метаданных, который будет добавлен в каждый чанк.
    merged_metadata = {
        "doc_id": doc_id,
        "title": document_record["title"],
        "source_path": document_record["source_path"],
        "drug_name_ru": document_record["drug_name_ru"],
        "drug_name_lat": document_record["drug_name_lat"],
        "dosage_form": document_record["dosage_form"],
        "clinical_pharmacological_group": document_record["clinical_pharmacological_group"],
        "active_substances": list(document_record.get("active_substances", [])),
        "related_active_substance_names_ru": list(relation_metadata.get("active_substance_names_ru", [])),
        "related_active_substance_names_lat": list(relation_metadata.get("active_substance_names_lat", [])),
        "atc_codes": [],
        "nosology_codes": list(relation_metadata.get("nosology_codes", [])),
        "nosology_names": list(relation_metadata.get("nosology_names", [])),
        "clinical_group_codes": list(relation_metadata.get("clinical_group_codes", [])),
        "clinical_group_names": list(relation_metadata.get("clinical_group_names", [])),
        "registration_number": document_record.get("registration_number", ""),
        "registration_date_raw": document_record.get("registration_date_raw", ""),
    }

    # atc_code добавляет коды ATX как из карточки, так и из relation_index без дублирования.
    for atc_code in document_record.get("atc_codes", []):
        append_unique(merged_metadata["atc_codes"], atc_code)
    for atc_code in relation_metadata.get("atc_codes", []):
        append_unique(merged_metadata["atc_codes"], atc_code)

    # return_value содержит объединенные метаданные документа.
    return merged_metadata


def split_text_into_sentences(section_text: str) -> list[str]:
    """Приближенно разбивает текст на предложения для более аккуратного chunking'а."""

    # normalized_section_text хранит очищенный текст раздела.
    normalized_section_text = normalize_text(section_text)
    if not normalized_section_text:
        return []

    # raw_sentences хранит список строк после регулярного разбиения по предполагаемым границам предложений.
    raw_sentences = SENTENCE_SPLIT_PATTERN.split(normalized_section_text)

    # sentences хранит очищенные непустые предложения.
    sentences = [normalize_text(raw_sentence) for raw_sentence in raw_sentences if normalize_text(raw_sentence)]

    # return_value содержит итоговый список предложений.
    return sentences


def chunk_text_by_sentences(
    section_text: str,
    target_length: int,
    max_length: int,
    overlap_sentences: int,
) -> list[str]:
    """Разбивает текст на чанки, стараясь сохранять смысловые границы по предложениям."""

    # sentences хранит предложения, извлеченные из текста текущего блока.
    sentences = split_text_into_sentences(section_text)
    if not sentences:
        return []

    # short_text хранит исходный текст, если он достаточно короткий и не требует разбиения.
    short_text = normalize_text(section_text)
    if len(short_text) <= target_length:
        return [short_text]

    # chunks хранит итоговые текстовые чанки для текущего блока.
    chunks: list[str] = []

    # start_index хранит позицию первого предложения текущего чанка.
    start_index = 0

    while start_index < len(sentences):
        # current_sentences хранит предложения, накопленные в текущий чанк.
        current_sentences: list[str] = []

        # end_index хранит позицию предложения, которое сейчас пытаемся добавить в чанк.
        end_index = start_index

        while end_index < len(sentences):
            # candidate_sentences хранит текущие предложения плюс следующее тестовое предложение.
            candidate_sentences = current_sentences + [sentences[end_index]]

            # candidate_text хранит текст чанка, который получится после добавления предложения.
            candidate_text = normalize_text(" ".join(candidate_sentences))

            if len(candidate_text) > max_length and current_sentences:
                break

            current_sentences.append(sentences[end_index])
            end_index += 1

            # current_text_after_append хранит текущую длину чанка после успешного добавления предложения.
            current_text_after_append = normalize_text(" ".join(current_sentences))
            if len(current_text_after_append) >= target_length:
                break

        # chunk_text хранит финальный текст одного чанка.
        chunk_text = normalize_text(" ".join(current_sentences))
        if chunk_text:
            chunks.append(chunk_text)

        if end_index >= len(sentences):
            break

        # overlap_start_index хранит позицию старта следующего чанка с учетом перекрытия предложений.
        overlap_start_index = max(start_index + 1, end_index - overlap_sentences)
        start_index = overlap_start_index

    # return_value содержит список текстов готовых чанков.
    return chunks


def build_overview_text(document_record: dict) -> str:
    """Строит обзорный текст карточки препарата из кратких метаданных."""

    # overview_parts хранит отдельные текстовые строки, из которых будет собран overview-чанк.
    overview_parts: list[str] = []

    append_labeled_value(overview_parts, "Препарат", document_record.get("drug_name_ru", ""))
    append_labeled_value(overview_parts, "Латинское название", document_record.get("drug_name_lat", ""))
    append_labeled_value(overview_parts, "Действующее вещество", document_record.get("active_substance_raw", ""))
    append_labeled_value(overview_parts, "Лекарственная форма", document_record.get("dosage_form", ""))
    append_labeled_value(
        overview_parts,
        "Клинико-фармакологическая группа",
        document_record.get("clinical_pharmacological_group", ""),
    )
    append_labeled_value(
        overview_parts,
        "Регистрационная информация",
        document_record.get("registration_info_raw", ""),
    )
    append_labeled_value(
        overview_parts,
        "Владелец регистрационного удостоверения",
        document_record.get("holder_information", ""),
    )
    append_labeled_value(
        overview_parts,
        "Представительство",
        document_record.get("representative_information", ""),
    )

    # overview_text хранит итоговый обзорный текст карточки препарата.
    overview_text = normalize_text(" ".join(overview_parts))

    # return_value содержит обзорный текст для будущего overview-чанка.
    return overview_text


def build_retrieval_text(
    chunk_type: str,
    section_name: str,
    chunk_text: str,
    document_metadata: dict,
) -> str:
    """Строит текст для эмбеддингов, добавляя к содержимому chunk'а важный контекст."""

    # retrieval_parts хранит текстовые фрагменты, которые будут склеены в итоговый retrieval_text.
    retrieval_parts: list[str] = []

    append_labeled_value(retrieval_parts, "Препарат", document_metadata["drug_name_ru"])
    append_labeled_value(retrieval_parts, "Латинское название", document_metadata["drug_name_lat"])
    append_labeled_value(retrieval_parts, "Тип чанка", chunk_type)
    append_labeled_value(retrieval_parts, "Раздел", section_name)
    append_labeled_value(retrieval_parts, "Лекарственная форма", document_metadata["dosage_form"])
    append_labeled_value(
        retrieval_parts,
        "Клинико-фармакологическая группа",
        document_metadata["clinical_pharmacological_group"],
    )
    append_labeled_value(
        retrieval_parts,
        "Действующие вещества",
        ", ".join(document_metadata["active_substances"]),
    )
    append_labeled_value(
        retrieval_parts,
        "Названия по индексу действующих веществ",
        ", ".join(document_metadata["related_active_substance_names_ru"]),
    )
    append_labeled_value(
        retrieval_parts,
        "ATX коды",
        ", ".join(document_metadata["atc_codes"]),
    )
    append_labeled_value(
        retrieval_parts,
        "Нозологии",
        ", ".join(document_metadata["nosology_names"]),
    )
    append_labeled_value(
        retrieval_parts,
        "Клинико-фармакологические группы",
        ", ".join(document_metadata["clinical_group_names"]),
    )
    append_labeled_value(retrieval_parts, "Текст", chunk_text)

    # retrieval_text хранит итоговый текст, который будет лучше работать для embedding-модели.
    retrieval_text = normalize_text(" ".join(retrieval_parts))

    # return_value содержит готовый retrieval_text.
    return retrieval_text


def create_chunk_record(
    doc_id: str,
    chunk_type: str,
    section_name: str,
    chunk_index: int,
    chunk_text: str,
    document_metadata: dict,
) -> ChunkRecord:
    """Создает один объект ChunkRecord из текста и метаданных документа."""

    # normalized_section_name хранит очищенное имя раздела и используется в идентификаторе chunk'а.
    normalized_section_name = normalize_text(section_name) if section_name else chunk_type

    # section_slug хранит безопасное текстовое имя раздела для chunk_id.
    section_slug = (
        normalized_section_name
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace("(", "")
        .replace(")", "")
        .replace(",", "")
    )

    # chunk_id хранит уникальный идентификатор chunk'а.
    chunk_id = f"{doc_id}__{section_slug}__{chunk_index:03d}"

    # retrieval_text хранит текст chunk'а, расширенный метаданными для embedding retrieval.
    retrieval_text = build_retrieval_text(
        chunk_type=chunk_type,
        section_name=normalized_section_name,
        chunk_text=chunk_text,
        document_metadata=document_metadata,
    )

    # chunk_record хранит итоговый объект чанка.
    chunk_record = ChunkRecord(
        chunk_id=chunk_id,
        doc_id=doc_id,
        chunk_type=chunk_type,
        section_name=normalized_section_name,
        chunk_index=chunk_index,
        source_path=document_metadata["source_path"],
        title=document_metadata["title"],
        drug_name_ru=document_metadata["drug_name_ru"],
        drug_name_lat=document_metadata["drug_name_lat"],
        dosage_form=document_metadata["dosage_form"],
        clinical_pharmacological_group=document_metadata["clinical_pharmacological_group"],
        active_substances=document_metadata["active_substances"],
        related_active_substance_names_ru=document_metadata["related_active_substance_names_ru"],
        related_active_substance_names_lat=document_metadata["related_active_substance_names_lat"],
        atc_codes=document_metadata["atc_codes"],
        nosology_codes=document_metadata["nosology_codes"],
        nosology_names=document_metadata["nosology_names"],
        clinical_group_codes=document_metadata["clinical_group_codes"],
        clinical_group_names=document_metadata["clinical_group_names"],
        registration_number=document_metadata["registration_number"],
        registration_date_raw=document_metadata["registration_date_raw"],
        chunk_text=chunk_text,
        retrieval_text=retrieval_text,
    )

    # return_value содержит полностью подготовленный ChunkRecord.
    return chunk_record


def build_chunks_for_document(
    document_record: dict,
    relation_index: dict[str, dict[str, list[str]]],
    target_length: int,
    max_length: int,
    overlap_sentences: int,
) -> list[ChunkRecord]:
    """Строит все чанки для одной структурированной карточки препарата."""

    # document_metadata хранит объединенные метаданные документа и связанных сущностей.
    document_metadata = merge_document_metadata(
        document_record=document_record,
        relation_index=relation_index,
    )

    # chunks хранит итоговый список chunk'ов, построенных для текущей карточки препарата.
    chunks: list[ChunkRecord] = []

    # overview_text хранит краткое summary-описание карточки препарата.
    overview_text = build_overview_text(document_record)
    if overview_text:
        chunks.append(
            create_chunk_record(
                doc_id=document_record["doc_id"],
                chunk_type="overview",
                section_name="Общая информация",
                chunk_index=1,
                chunk_text=overview_text,
                document_metadata=document_metadata,
            )
        )

    # composition_text хранит текст блока "Форма выпуска, состав и упаковка".
    composition_text = normalize_text(document_record.get("composition_and_packaging", ""))
    if composition_text:
        # composition_chunks хранит текстовые чанки для раздела состава и упаковки.
        composition_chunks = chunk_text_by_sentences(
            section_text=composition_text,
            target_length=target_length,
            max_length=max_length,
            overlap_sentences=overlap_sentences,
        )
        for chunk_index, chunk_text in enumerate(composition_chunks, start=1):
            chunks.append(
                create_chunk_record(
                    doc_id=document_record["doc_id"],
                    chunk_type="composition",
                    section_name="Форма выпуска, состав и упаковка",
                    chunk_index=chunk_index,
                    chunk_text=chunk_text,
                    document_metadata=document_metadata,
                )
            )

    # section_name и section_text по очереди перебирают все структурированные разделы инструкции.
    for section_name, section_text in document_record.get("sections", {}).items():
        # section_chunks хранит список чанков, построенных из текста одного раздела инструкции.
        section_chunks = chunk_text_by_sentences(
            section_text=section_text,
            target_length=target_length,
            max_length=max_length,
            overlap_sentences=overlap_sentences,
        )

        for chunk_index, chunk_text in enumerate(section_chunks, start=1):
            chunks.append(
                create_chunk_record(
                    doc_id=document_record["doc_id"],
                    chunk_type="section",
                    section_name=section_name,
                    chunk_index=chunk_index,
                    chunk_text=chunk_text,
                    document_metadata=document_metadata,
                )
            )

    # return_value содержит все чанки, построенные для текущего документа.
    return chunks


def write_jsonl(records: Iterable[ChunkRecord], output_file: Path) -> int:
    """Записывает чанки в JSONL и возвращает число записанных строк."""

    # output_directory хранит каталог, который должен существовать до записи выходного файла.
    output_directory = output_file.parent
    output_directory.mkdir(parents=True, exist_ok=True)

    # written_rows хранит число успешно записанных chunk'ов.
    written_rows = 0

    with output_file.open("w", encoding="utf-8") as output_stream:
        # record по очереди перебирает все chunk'и, подготовленные к сериализации.
        for record in records:
            # serialized_record хранит JSON-представление текущего chunk'а.
            serialized_record = json.dumps(asdict(record), ensure_ascii=False)
            output_stream.write(serialized_record + "\n")
            written_rows += 1

    # return_value содержит число записанных строк.
    return written_rows


def iter_chunks(
    documents_file: Path,
    relations_file: Path,
    target_length: int,
    max_length: int,
    overlap_sentences: int,
    limit: Optional[int] = None,
) -> Iterator[ChunkRecord]:
    """Лениво строит чанки по всем структурированным карточкам препаратов."""

    # relation_index хранит агрегированные метаданные по каждому doc_id.
    relation_index = build_relation_index(relations_file=relations_file)

    # document_record по очереди перебирает структурированные карточки препаратов.
    for document_record in load_jsonl_records(input_file=documents_file, limit=limit):
        # document_chunks хранит чанки, построенные для текущего документа.
        document_chunks = build_chunks_for_document(
            document_record=document_record,
            relation_index=relation_index,
            target_length=target_length,
            max_length=max_length,
            overlap_sentences=overlap_sentences,
        )

        # chunk_record по очереди отдает чанки наружу без удержания всего набора в памяти.
        for chunk_record in document_chunks:
            yield chunk_record


def main() -> None:
    """Запускает полный конвейер построения retrieval-ready чанков."""

    # arguments хранит аргументы командной строки, разобранные argparse.
    arguments = parse_arguments()

    # documents_file хранит абсолютный путь к файлу structured_documents.jsonl.
    documents_file = arguments.documents_file.resolve()

    # relations_file хранит абсолютный путь к файлу entity_relations.jsonl.
    relations_file = arguments.relations_file.resolve()

    # output_file хранит абсолютный путь к файлу chunks.jsonl.
    output_file = arguments.output_file.resolve()

    # chunk_records хранит ленивый итератор по всем chunk'ам, создаваемым из документов.
    chunk_records = iter_chunks(
        documents_file=documents_file,
        relations_file=relations_file,
        target_length=arguments.target_length,
        max_length=arguments.max_length,
        overlap_sentences=arguments.overlap_sentences,
        limit=arguments.limit,
    )

    # written_rows хранит число chunk'ов, записанных в выходной JSONL-файл.
    written_rows = write_jsonl(records=chunk_records, output_file=output_file)

    # summary_message хранит итоговое сообщение, выводимое после завершения скрипта.
    summary_message = (
        f"Saved {written_rows} retrieval-ready chunks to '{output_file}'."
    )
    print(summary_message)


if __name__ == "__main__":
    main()
