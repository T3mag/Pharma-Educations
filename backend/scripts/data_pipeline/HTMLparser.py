"""Normalize Vidal HTML pages into a clean JSONL dataset.

The script solves the first preparation stage for a RAG pipeline:
1. Reads raw HTML files from the handbook directory.
2. Detects the correct text encoding for each page.
3. Keeps only the main content block.
4. Produces normalized text and cleaned HTML.
5. Saves one JSON object per page to a JSONL file.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Iterator

from bs4 import BeautifulSoup, Tag


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_SOURCE_ROOT = (
    PROJECT_ROOT.parent
    / "Данные для rag"
    / "vidal_cd1823"
    / "vidal_2018-2023"
    / "data"
)

DEFAULT_OUTPUT_FILE = PROJECT_ROOT / "data" / "normalized_pages.jsonl"

HTML_FILE_EXTENSIONS = {".htm", ".html"}

ENCODING_CANDIDATES = ("utf-8-sig", "utf-8", "cp1251", "windows-1251", "latin-1")

WHITESPACE_PATTERN = re.compile(r"\s+")

META_CHARSET_PATTERN = re.compile(br"charset\s*=\s*['\"]?([A-Za-z0-9._-]+)", re.IGNORECASE)

PAGE_TYPE_PATTERNS = {
    "docs": "drug_document",
    "find": "active_substance_index",
    "atc": "atc_index",
    "noz": "nosology_index",
    "kfu": "clinical_pharmacology_index",
    "alf_drug": "drug_alphabetical_index",
    "alf_comp": "company_index",
    "alf_suppl": "supplement_index",
}


@dataclass
class NormalizedPage:
    """Store one normalized page ready for the next RAG preparation steps."""

    page_id: str

    page_type: str

    title: str

    source_path: str

    encoding: str

    content_html: str

    content_text: str

    headings: list[str]

    links: list[str]


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments and return runtime configuration."""

    parser = argparse.ArgumentParser(
        description="Normalize Vidal HTML pages into a JSONL dataset.",
    )

    parser.add_argument(
        "--source-root",
        type=Path,
        default=DEFAULT_SOURCE_ROOT,
        help="Directory with raw HTML pages.",
    )

    parser.add_argument(
        "--output-file",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help="Path to the output JSONL file.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit for the number of processed pages.",
    )

    return parser.parse_args()


def collect_html_files(source_root: Path) -> list[Path]:
    """Return a sorted list of HTML files found under the source directory."""

    all_files_iterator = source_root.rglob("*")

    html_files = [
        file_path
        for file_path in all_files_iterator
        if file_path.is_file() and file_path.suffix.lower() in HTML_FILE_EXTENSIONS
    ]

    return sorted(html_files)


def detect_encoding(raw_bytes: bytes) -> str:
    """Detect the most likely encoding for one HTML file."""

    bom = raw_bytes.startswith(b"\xef\xbb\xbf")
    if bom:
        return "utf-8-sig"

    meta_match = META_CHARSET_PATTERN.search(raw_bytes[:2048])
    if meta_match:
        declared_encoding = meta_match.group(1).decode("ascii", errors="ignore").lower()
        return declared_encoding

    for candidate_encoding in ENCODING_CANDIDATES:
        try:
            raw_bytes.decode(candidate_encoding)
            return candidate_encoding
        except UnicodeDecodeError:
            continue

    return "latin-1"


def read_html_file(file_path: Path) -> tuple[str, str]:
    """Read one HTML file and return decoded text together with the used encoding."""

    raw_bytes = file_path.read_bytes()

    detected_encoding = detect_encoding(raw_bytes)

    html_text = raw_bytes.decode(detected_encoding, errors="replace")

    return html_text, detected_encoding


def determine_page_type(relative_path: Path) -> str:
    """Map a relative file path to a stable logical page type."""

    path_parts = relative_path.parts

    for path_part in path_parts:
        if path_part in PAGE_TYPE_PATTERNS:
            return PAGE_TYPE_PATTERNS[path_part]

    return "unknown"


def remove_service_nodes(content_root: Tag) -> None:
    """Delete script, style, navigation, and empty nodes from the main content block."""

    for removable_node in content_root.find_all(["script", "style", "noscript"]):
        removable_node.decompose()

    for removable_break in content_root.find_all("hr"):
        removable_break.decompose()

    for removable_anchor in content_root.find_all("a"):
        anchor_text = removable_anchor.get_text(" ", strip=True)
        if not anchor_text:
            removable_anchor.decompose()

    for empty_tag in list(content_root.find_all(True)):
        tag_text = empty_tag.get_text(" ", strip=True)
        if not tag_text and not empty_tag.find(["img", "table", "tr", "td"]):
            empty_tag.decompose()


def extract_main_content(soup: BeautifulSoup) -> Tag:
    """Return the tag that contains the main readable page content."""

    info_block = soup.find(id="info")
    if isinstance(info_block, Tag):
        return info_block

    body_block = soup.body
    if isinstance(body_block, Tag):
        return body_block

    html_block = soup.find("html")
    if isinstance(html_block, Tag):
        return html_block

    fallback_container = soup.new_tag("div")
    fallback_container.string = soup.get_text(" ", strip=True)
    return fallback_container


def normalize_whitespace(raw_text: str) -> str:
    """Collapse repeated whitespace and return a clean single-line text string."""

    stripped_text = raw_text.strip()

    normalized_text = WHITESPACE_PATTERN.sub(" ", stripped_text)

    return normalized_text


def extract_headings(content_root: Tag) -> list[str]:
    """Extract readable heading texts from the main content block."""

    heading_tags = ["h1", "h2", "h3", "h4", "b", "strong"]

    headings: list[str] = []

    seen_headings: set[str] = set()

    for heading_node in content_root.find_all(heading_tags):
        heading_text = normalize_whitespace(heading_node.get_text(" ", strip=True))
        if len(heading_text) < 3:
            continue
        if heading_text in seen_headings:
            continue
        seen_headings.add(heading_text)
        headings.append(heading_text)

    return headings


def extract_links(content_root: Tag) -> list[str]:
    """Extract unique relative links from the main content block."""

    links: list[str] = []

    seen_links: set[str] = set()

    for link_node in content_root.find_all("a", href=True):
        href_value = link_node["href"].strip()
        if not href_value:
            continue
        if href_value in seen_links:
            continue
        seen_links.add(href_value)
        links.append(href_value)

    return links


def build_normalized_page(file_path: Path, source_root: Path) -> NormalizedPage:
    """Convert one raw HTML file into a normalized page record."""

    relative_path = file_path.relative_to(source_root)

    html_text, encoding = read_html_file(file_path)

    soup = BeautifulSoup(html_text, "html.parser")

    content_root = extract_main_content(soup)

    content_copy = BeautifulSoup(str(content_root), "html.parser")

    normalized_root = extract_main_content(content_copy)

    remove_service_nodes(normalized_root)

    page_title = normalize_whitespace(soup.title.get_text(" ", strip=True) if soup.title else "")

    content_text = normalize_whitespace(normalized_root.get_text(" ", strip=True))

    content_html = str(normalized_root)

    headings = extract_headings(normalized_root)

    links = extract_links(normalized_root)

    normalized_page = NormalizedPage(
        page_id=file_path.stem,
        page_type=determine_page_type(relative_path),
        title=page_title,
        source_path=relative_path.as_posix(),
        encoding=encoding,
        content_html=content_html,
        content_text=content_text,
        headings=headings,
        links=links,
    )

    return normalized_page


def iter_normalized_pages(file_paths: Iterable[Path], source_root: Path) -> Iterator[NormalizedPage]:
    """Yield normalized page records one by one."""

    for file_path in file_paths:
        yield build_normalized_page(file_path=file_path, source_root=source_root)


def write_jsonl(records: Iterable[NormalizedPage], output_file: Path) -> int:
    """Write normalized records to a JSONL file and return the number of written rows."""

    parent_directory = output_file.parent
    parent_directory.mkdir(parents=True, exist_ok=True)

    written_rows = 0

    with output_file.open("w", encoding="utf-8") as jsonl_stream:
        for record in records:
            serialized_record = json.dumps(asdict(record), ensure_ascii=False)
            jsonl_stream.write(serialized_record + "\n")
            written_rows += 1

    return written_rows


def main() -> None:
    """Run the full normalization pipeline from raw HTML pages to JSONL output."""

    arguments = parse_arguments()

    source_root = arguments.source_root.resolve()

    output_file = arguments.output_file.resolve()

    html_files = collect_html_files(source_root)

    limited_html_files = html_files[: arguments.limit] if arguments.limit else html_files

    normalized_records = iter_normalized_pages(
        file_paths=limited_html_files,
        source_root=source_root,
    )

    written_rows = write_jsonl(records=normalized_records, output_file=output_file)

    summary_message = (
        f"Normalized {written_rows} HTML pages from '{source_root}' "
        f"into '{output_file}'."
    )
    print(summary_message)


if __name__ == "__main__":
    main()
