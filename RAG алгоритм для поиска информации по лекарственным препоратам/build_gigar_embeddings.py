"""Build embeddings for retrieval-ready chunks with Sber EmbeddingsGigaR.

The script solves the next preparation stage for the RAG pipeline:
1. Reads retrieval-ready chunks from chunks.jsonl.
2. Sends retrieval_text values to the GigaChat embeddings API.
3. Stores embeddings together with the original chunk metadata in JSONL.
4. Supports resumable execution by skipping already processed chunk_ids.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional


# DEFAULT_INPUT_FILE хранит путь к входному JSONL-файлу с retrieval-ready чанками.
DEFAULT_INPUT_FILE = Path(__file__).resolve().parent / "chunks.jsonl"

# DEFAULT_OUTPUT_FILE хранит путь к выходному JSONL-файлу с рассчитанными embeddings.
DEFAULT_OUTPUT_FILE = Path(__file__).resolve().parent / "chunk_embeddings_gigar.jsonl"

# DEFAULT_MODEL_NAME хранит имя embedding-модели GigaChat, которое рекомендовано для большого retrieval.
DEFAULT_MODEL_NAME = "EmbeddingsGigaR"

# DEFAULT_BATCH_SIZE хранит размер батча по числу текстов в одном запросе к API.
DEFAULT_BATCH_SIZE = 16

# DEFAULT_TIMEOUT_SECONDS хранит таймаут HTTP-запроса к API GigaChat.
DEFAULT_TIMEOUT_SECONDS = 600


@dataclass
class EmbeddingTask:
    """Хранит входные данные для расчета embedding одного чанка."""

    # chunk_id хранит идентификатор чанка, который будет использоваться как стабильный id результата.
    chunk_id: str

    # retrieval_text хранит строку, которая будет отправлена в embedding model.
    retrieval_text: str

    # chunk_record хранит полную исходную запись чанка для сохранения полезных метаданных рядом с embedding.
    chunk_record: dict[str, Any]


def parse_arguments() -> argparse.Namespace:
    """Разбирает аргументы командной строки и возвращает конфигурацию запуска скрипта."""

    # parser описывает пользовательский интерфейс запуска из терминала.
    parser = argparse.ArgumentParser(
        description="Build embeddings for chunks.jsonl with EmbeddingsGigaR.",
    )

    # input_file_argument указывает путь к chunks.jsonl.
    parser.add_argument(
        "--input-file",
        type=Path,
        default=DEFAULT_INPUT_FILE,
        help="Path to chunks.jsonl.",
    )

    # output_file_argument указывает путь к выходному JSONL-файлу с embeddings.
    parser.add_argument(
        "--output-file",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help="Path to output JSONL with embeddings.",
    )

    # model_argument указывает имя embedding-модели GigaChat.
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL_NAME,
        help="GigaChat embedding model name.",
    )

    # batch_size_argument указывает число текстов в одном запросе к embeddings API.
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="Number of texts per embeddings request.",
    )

    # timeout_argument указывает HTTP-таймаут запросов к API.
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Request timeout in seconds.",
    )

    # limit_argument позволяет ограничить число обрабатываемых чанков при отладке.
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit of chunks to process.",
    )

    # resume_argument включает режим продолжения и пропуска уже обработанных chunk_id.
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip chunk_ids that already exist in the output file.",
    )

    # verify_ssl_argument включает проверку SSL-сертификатов при запросах к GigaChat API.
    parser.add_argument(
        "--verify-ssl-certs",
        action="store_true",
        help="Enable SSL certificate verification for GigaChat requests.",
    )

    # dry_run_argument включает режим без вызова API для проверки входных данных и батчинга.
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not call API, only validate and count pending chunks.",
    )

    # return_value содержит разобранные аргументы командной строки.
    return parser.parse_args()


def load_jsonl_records(input_file: Path, limit: Optional[int] = None) -> Iterator[dict[str, Any]]:
    """Читает JSONL-файл и возвращает записи по одной."""

    with input_file.open("r", encoding="utf-8") as input_stream:
        # line_index хранит номер текущей строки и нужен для поддержки limit.
        for line_index, line in enumerate(input_stream, start=1):
            if limit is not None and line_index > limit:
                break

            # record хранит одну JSON-запись, считанную из файла.
            record = json.loads(line)
            yield record


def load_processed_chunk_ids(output_file: Path) -> set[str]:
    """Читает существующий output JSONL и возвращает множество уже обработанных chunk_id."""

    if not output_file.exists():
        return set()

    # processed_chunk_ids хранит chunk_id, которые уже были сохранены в output-файл.
    processed_chunk_ids: set[str] = set()

    with output_file.open("r", encoding="utf-8") as output_stream:
        # line по очереди перебирает существующие записи embeddings.
        for line in output_stream:
            try:
                # record хранит одну запись embeddings из существующего файла.
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            # chunk_id хранит идентификатор уже обработанного чанка.
            chunk_id = record.get("chunk_id")
            if isinstance(chunk_id, str) and chunk_id:
                processed_chunk_ids.add(chunk_id)

    # return_value содержит множество всех обработанных идентификаторов чанков.
    return processed_chunk_ids


def iter_pending_tasks(
    input_file: Path,
    processed_chunk_ids: set[str],
    limit: Optional[int] = None,
) -> Iterator[EmbeddingTask]:
    """Возвращает только те чанки, для которых embedding еще не был сохранен."""

    # chunk_record по очереди перебирает входные чанки из chunks.jsonl.
    for chunk_record in load_jsonl_records(input_file=input_file, limit=limit):
        # chunk_id хранит идентификатор текущего чанка.
        chunk_id = chunk_record.get("chunk_id", "")

        # retrieval_text хранит строку, которую мы будем кодировать в embedding.
        retrieval_text = chunk_record.get("retrieval_text", "")

        if not isinstance(chunk_id, str) or not chunk_id:
            continue
        if not isinstance(retrieval_text, str) or not retrieval_text.strip():
            continue
        if chunk_id in processed_chunk_ids:
            continue

        yield EmbeddingTask(
            chunk_id=chunk_id,
            retrieval_text=retrieval_text,
            chunk_record=chunk_record,
        )


def batched(items: Iterable[EmbeddingTask], batch_size: int) -> Iterator[list[EmbeddingTask]]:
    """Разбивает поток задач на батчи фиксированного размера."""

    # batch хранит текущий набор задач перед отправкой в API.
    batch: list[EmbeddingTask] = []

    # item по очереди перебирает задачи на расчет embedding.
    for item in items:
        batch.append(item)
        if len(batch) >= batch_size:
            yield batch
            batch = []

    if batch:
        yield batch


def build_gigachat_client(credentials: str, timeout: int, verify_ssl_certs: bool) -> Any:
    """Создает клиента GigaChat через официальный Python SDK."""

    try:
        # GigaChat импортируется локально внутри функции, чтобы сам скрипт можно было читать и проверять
        # даже в окружении, где пакет gigachat еще не установлен.
        from gigachat import GigaChat
    except ImportError as import_error:
        raise RuntimeError(
            "Пакет 'gigachat' не установлен. Установите его командой 'pip install gigachat'."
        ) from import_error

    # client хранит клиент официального SDK GigaChat для вызова embeddings API.
    client = GigaChat(
        credentials=credentials,
        timeout=timeout,
        verify_ssl_certs=verify_ssl_certs,
    )

    # return_value содержит готовый клиент для запросов embeddings.
    return client


def extract_embedding_items(response: Any) -> list[Any]:
    """Извлекает список элементов embeddings из ответа SDK в максимально безопасной форме."""

    # data_items хранит список embedding-элементов, если SDK вернул объект с атрибутом data.
    data_items = getattr(response, "data", None)
    if data_items is not None:
        return list(data_items)

    if isinstance(response, dict):
        # dict_data_items хранит список embeddings, если ответ пришел словарем.
        dict_data_items = response.get("data")
        if isinstance(dict_data_items, list):
            return dict_data_items

    raise RuntimeError("Не удалось извлечь поле 'data' из ответа embeddings API GigaChat.")


def extract_embedding_vector(item: Any) -> list[float]:
    """Извлекает числовой вектор embedding из одного элемента ответа API."""

    # embedding_value хранит вектор embedding, если элемент ответа реализован как объект SDK.
    embedding_value = getattr(item, "embedding", None)
    if embedding_value is None and isinstance(item, dict):
        embedding_value = item.get("embedding")

    if not isinstance(embedding_value, list):
        raise RuntimeError("Не удалось извлечь список чисел из поля 'embedding'.")

    # return_value содержит вектор embedding как список чисел с плавающей точкой.
    return [float(value) for value in embedding_value]


def request_embeddings(client: Any, texts: list[str], model_name: str) -> list[list[float]]:
    """Отправляет батч текстов в embeddings API и возвращает список векторов в исходном порядке."""

    # response хранит ответ от метода embeddings официального SDK GigaChat.
    response = client.embeddings(texts, model=model_name)

    # response_items хранит список embedding-элементов из ответа API.
    response_items = extract_embedding_items(response)

    if len(response_items) != len(texts):
        raise RuntimeError(
            f"Число embeddings в ответе ({len(response_items)}) не совпадает с числом текстов ({len(texts)})."
        )

    # embedding_vectors хранит итоговый список embedding-векторов для батча.
    embedding_vectors = [extract_embedding_vector(item) for item in response_items]

    # return_value содержит embeddings в том же порядке, что и исходные тексты.
    return embedding_vectors


def serialize_embedding_record(
    task: EmbeddingTask,
    embedding_vector: list[float],
    model_name: str,
) -> dict[str, Any]:
    """Собирает одну запись результата для output JSONL."""

    # embedding_record хранит полную JSON-структуру результата для одного чанка.
    embedding_record = {
        "chunk_id": task.chunk_id,
        "model": model_name,
        "vector_size": len(embedding_vector),
        "embedding": embedding_vector,
        "chunk_record": task.chunk_record,
    }

    # return_value содержит сериализуемую запись embeddings.
    return embedding_record


def ensure_credentials() -> str:
    """Читает ключ авторизации GigaChat из переменных окружения."""

    # credentials хранит ключ авторизации GigaChat из переменной окружения.
    credentials = os.environ.get("GIGACHAT_CREDENTIALS", "").strip()

    if not credentials:
        raise RuntimeError(
            "Не найден ключ авторизации GigaChat. Установите переменную окружения GIGACHAT_CREDENTIALS."
        )

    # return_value содержит непустой ключ авторизации.
    return credentials


def write_embeddings(
    output_file: Path,
    records: Iterable[dict[str, Any]],
    append_mode: bool,
) -> int:
    """Записывает embeddings в JSONL и возвращает число сохраненных строк."""

    # output_directory хранит каталог, который должен существовать до записи выходного файла.
    output_directory = output_file.parent
    output_directory.mkdir(parents=True, exist_ok=True)

    # file_mode выбирает режим записи: append для resume или write для нового прогона.
    file_mode = "a" if append_mode else "w"

    # written_rows хранит число реально записанных строк embeddings.
    written_rows = 0

    with output_file.open(file_mode, encoding="utf-8") as output_stream:
        # record по очереди перебирает готовые JSON-структуры embeddings.
        for record in records:
            # serialized_record хранит JSON-представление результата для одного чанка.
            serialized_record = json.dumps(record, ensure_ascii=False)
            output_stream.write(serialized_record + "\n")
            written_rows += 1

    # return_value содержит число сохраненных строк.
    return written_rows


def build_embedding_records(
    tasks: Iterable[EmbeddingTask],
    client: Any,
    model_name: str,
    batch_size: int,
) -> Iterator[dict[str, Any]]:
    """Строит поток записей embeddings, батчами вызывая официальный API GigaChat."""

    # task_batch по очереди перебирает батчи задач на embedding.
    for task_batch in batched(items=tasks, batch_size=batch_size):
        # batch_texts хранит список retrieval_text для текущего батча.
        batch_texts = [task.retrieval_text for task in task_batch]

        # batch_vectors хранит список embedding-векторов, полученных от API для текущего батча.
        batch_vectors = request_embeddings(
            client=client,
            texts=batch_texts,
            model_name=model_name,
        )

        # task и embedding_vector синхронно перебирают задачи и рассчитанные векторы.
        for task, embedding_vector in zip(task_batch, batch_vectors):
            yield serialize_embedding_record(
                task=task,
                embedding_vector=embedding_vector,
                model_name=model_name,
            )


def count_pending_tasks(
    input_file: Path,
    output_file: Path,
    resume: bool,
    limit: Optional[int],
) -> tuple[int, set[str]]:
    """Считает число необработанных задач и возвращает также множество уже готовых chunk_id."""

    # processed_chunk_ids хранит уже сохраненные chunk_id, если включен режим resume.
    processed_chunk_ids = load_processed_chunk_ids(output_file) if resume else set()

    # pending_count хранит число чанков, для которых embeddings еще не рассчитаны.
    pending_count = 0

    # _task по очереди перебирает отфильтрованные задачи без фактического вызова API.
    for _task in iter_pending_tasks(
        input_file=input_file,
        processed_chunk_ids=processed_chunk_ids,
        limit=limit,
    ):
        pending_count += 1

    # return_value содержит число необработанных задач и множество уже обработанных chunk_id.
    return pending_count, processed_chunk_ids


def main() -> None:
    """Запускает полный конвейер расчета embeddings для retrieval-ready чанков."""

    # arguments хранит аргументы командной строки.
    arguments = parse_arguments()

    # input_file хранит абсолютный путь к входному chunks.jsonl.
    input_file = arguments.input_file.resolve()

    # output_file хранит абсолютный путь к выходному JSONL с embeddings.
    output_file = arguments.output_file.resolve()

    # pending_count и processed_chunk_ids позволяют заранее понять объем оставшейся работы.
    pending_count, processed_chunk_ids = count_pending_tasks(
        input_file=input_file,
        output_file=output_file,
        resume=arguments.resume,
        limit=arguments.limit,
    )

    if arguments.dry_run:
        # summary_message хранит итоговое сообщение dry-run без фактических вызовов API.
        summary_message = (
            f"Dry run: pending chunks = {pending_count}, "
            f"already processed chunk_ids = {len(processed_chunk_ids)}."
        )
        print(summary_message)
        return

    if pending_count == 0:
        print("Нет новых чанков для расчета embeddings.")
        return

    # credentials хранит ключ авторизации GigaChat из переменной окружения.
    credentials = ensure_credentials()

    # client хранит клиент официального SDK GigaChat.
    client = build_gigachat_client(
        credentials=credentials,
        timeout=arguments.timeout,
        verify_ssl_certs=arguments.verify_ssl_certs,
    )

    # pending_tasks хранит ленивый поток только тех чанков, которые еще не обработаны.
    pending_tasks = iter_pending_tasks(
        input_file=input_file,
        processed_chunk_ids=processed_chunk_ids,
        limit=arguments.limit,
    )

    # embedding_records хранит ленивый поток JSON-структур результата после вызовов embeddings API.
    embedding_records = build_embedding_records(
        tasks=pending_tasks,
        client=client,
        model_name=arguments.model,
        batch_size=arguments.batch_size,
    )

    # append_mode включает дозапись, если выбран resume и файл уже существует.
    append_mode = arguments.resume and output_file.exists()

    # written_rows хранит число embeddings, записанных за текущий запуск.
    written_rows = write_embeddings(
        output_file=output_file,
        records=embedding_records,
        append_mode=append_mode,
    )

    # summary_message хранит итоговое сообщение по завершении расчета embeddings.
    summary_message = (
        f"Saved {written_rows} embeddings to '{output_file}' "
        f"with model '{arguments.model}'."
    )
    print(summary_message)


if __name__ == "__main__":
    main()
