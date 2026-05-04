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


# DEFAULT_SOURCE_ROOT stores the default directory with the raw Vidal HTML pages.
DEFAULT_SOURCE_ROOT = (
    Path(__file__).resolve().parents[1]
    / "Данные для rag"
    / "vidal_cd1823"
    / "vidal_2018-2023"
    / "data"
)

# DEFAULT_OUTPUT_FILE stores the default location of the normalized JSONL dataset.
DEFAULT_OUTPUT_FILE = Path(__file__).resolve().parent / "normalized_pages.jsonl"

# HTML_FILE_EXTENSIONS stores the file suffixes that should be treated as HTML pages.
HTML_FILE_EXTENSIONS = {".htm", ".html"}

# ENCODING_CANDIDATES stores the fallback encodings used when the page has no clear charset.
ENCODING_CANDIDATES = ("utf-8-sig", "utf-8", "cp1251", "windows-1251", "latin-1")

# WHITESPACE_PATTERN collapses repeated spaces and line breaks into a readable single-space form.
WHITESPACE_PATTERN = re.compile(r"\s+")

# META_CHARSET_PATTERN extracts charset values from legacy meta tags when needed.
META_CHARSET_PATTERN = re.compile(br"charset\s*=\s*['\"]?([A-Za-z0-9._-]+)", re.IGNORECASE)

# PAGE_TYPE_PATTERNS maps handbook folders to a stable page type label.
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

    # page_id keeps the file stem and later can be reused as a stable local identifier.
    page_id: str

    # page_type describes the logical section of the handbook for downstream processing.
    page_type: str

    # title keeps the HTML page title after normalization.
    title: str

    # source_path keeps the page path relative to the raw source root.
    source_path: str

    # encoding stores the final text encoding used to decode the source file.
    encoding: str

    # content_html stores cleaned HTML for cases where later parsing needs preserved markup.
    content_html: str

    # content_text stores the plain normalized text used for retrieval and chunking.
    content_text: str

    # headings stores the main headings found inside the kept content block.
    headings: list[str]

    # links stores relative hyperlinks extracted from the main content block.
    links: list[str]


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments and return runtime configuration."""

    # parser defines the command-line interface of the normalizer script.
    parser = argparse.ArgumentParser(
        description="Normalize Vidal HTML pages into a JSONL dataset.",
    )

    # source_root_argument configures where the script should read raw HTML files.
    parser.add_argument(
        "--source-root",
        type=Path,
        default=DEFAULT_SOURCE_ROOT,
        help="Directory with raw HTML pages.",
    )

    # output_file_argument configures where the script should write the JSONL result.
    parser.add_argument(
        "--output-file",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help="Path to the output JSONL file.",
    )

    # limit_argument makes debugging easier because it can restrict the number of processed pages.
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit for the number of processed pages.",
    )

    # return_value contains all parsed argument values.
    return parser.parse_args()


def collect_html_files(source_root: Path) -> list[Path]:
    """Return a sorted list of HTML files found under the source directory."""

    # all_files_iterator walks through every file under the source directory.
    all_files_iterator = source_root.rglob("*")

    # html_files keeps only files with supported HTML suffixes.
    html_files = [
        file_path
        for file_path in all_files_iterator
        if file_path.is_file() and file_path.suffix.lower() in HTML_FILE_EXTENSIONS
    ]

    # return_value is sorted to guarantee deterministic output.
    return sorted(html_files)


def detect_encoding(raw_bytes: bytes) -> str:
    """Detect the most likely encoding for one HTML file."""

    # bom indicates whether the document starts with the UTF-8 BOM marker.
    bom = raw_bytes.startswith(b"\xef\xbb\xbf")
    if bom:
        return "utf-8-sig"

    # meta_match keeps the first charset declaration found in the raw HTML header.
    meta_match = META_CHARSET_PATTERN.search(raw_bytes[:2048])
    if meta_match:
        # declared_encoding stores the charset taken from the HTML meta tag.
        declared_encoding = meta_match.group(1).decode("ascii", errors="ignore").lower()
        return declared_encoding

    # candidate_encoding iterates through known encodings used in the handbook.
    for candidate_encoding in ENCODING_CANDIDATES:
        try:
            raw_bytes.decode(candidate_encoding)
            return candidate_encoding
        except UnicodeDecodeError:
            continue

    # return_value falls back to latin-1 because it never crashes on byte decoding.
    return "latin-1"


def read_html_file(file_path: Path) -> tuple[str, str]:
    """Read one HTML file and return decoded text together with the used encoding."""

    # raw_bytes stores the original file content without any text decoding.
    raw_bytes = file_path.read_bytes()

    # detected_encoding stores the selected encoding for this specific file.
    detected_encoding = detect_encoding(raw_bytes)

    # html_text stores the decoded HTML string that BeautifulSoup will parse next.
    html_text = raw_bytes.decode(detected_encoding, errors="replace")

    # return_value contains both the decoded HTML and the encoding metadata.
    return html_text, detected_encoding


def determine_page_type(relative_path: Path) -> str:
    """Map a relative file path to a stable logical page type."""

    # path_parts stores each folder and file name of the relative path.
    path_parts = relative_path.parts

    # path_part iterates over folders to find the handbook section name.
    for path_part in path_parts:
        if path_part in PAGE_TYPE_PATTERNS:
            return PAGE_TYPE_PATTERNS[path_part]

    # return_value is used for pages outside the known handbook sections.
    return "unknown"


def remove_service_nodes(content_root: Tag) -> None:
    """Delete script, style, navigation, and empty nodes from the main content block."""

    # removable_node iterates over tags that do not carry semantic handbook content.
    for removable_node in content_root.find_all(["script", "style", "noscript"]):
        removable_node.decompose()

    # removable_break keeps duplicate horizontal separators from polluting plain text.
    for removable_break in content_root.find_all("hr"):
        removable_break.decompose()

    # removable_anchor removes purely navigational anchors without visible text.
    for removable_anchor in content_root.find_all("a"):
        # anchor_text stores the visible text of the hyperlink.
        anchor_text = removable_anchor.get_text(" ", strip=True)
        if not anchor_text:
            removable_anchor.decompose()

    # empty_tag iterates over tags that became empty after node cleanup.
    for empty_tag in list(content_root.find_all(True)):
        # tag_text stores the normalized visible text of the current tag.
        tag_text = empty_tag.get_text(" ", strip=True)
        if not tag_text and not empty_tag.find(["img", "table", "tr", "td"]):
            empty_tag.decompose()


def extract_main_content(soup: BeautifulSoup) -> Tag:
    """Return the tag that contains the main readable page content."""

    # info_block stores the main Vidal content table present on most handbook pages.
    info_block = soup.find(id="info")
    if isinstance(info_block, Tag):
        return info_block

    # body_block is the fallback content root for pages without the standard info table.
    body_block = soup.body
    if isinstance(body_block, Tag):
        return body_block

    # html_block is the final fallback that prevents parser failures on malformed pages.
    html_block = soup.find("html")
    if isinstance(html_block, Tag):
        return html_block

    # fallback_container is a synthetic wrapper used only if the parsed page is very broken.
    fallback_container = soup.new_tag("div")
    fallback_container.string = soup.get_text(" ", strip=True)
    return fallback_container


def normalize_whitespace(raw_text: str) -> str:
    """Collapse repeated whitespace and return a clean single-line text string."""

    # stripped_text removes leading and trailing whitespace from the text fragment.
    stripped_text = raw_text.strip()

    # normalized_text collapses repeated spaces, tabs, and line breaks into one space.
    normalized_text = WHITESPACE_PATTERN.sub(" ", stripped_text)

    # return_value contains the final clean text representation.
    return normalized_text


def extract_headings(content_root: Tag) -> list[str]:
    """Extract readable heading texts from the main content block."""

    # heading_tags stores the HTML tag names that may represent section titles.
    heading_tags = ["h1", "h2", "h3", "h4", "b", "strong"]

    # headings keeps unique heading strings in the order they appear on the page.
    headings: list[str] = []

    # seen_headings prevents duplicated heading text from being appended multiple times.
    seen_headings: set[str] = set()

    # heading_node iterates through every candidate heading in the content block.
    for heading_node in content_root.find_all(heading_tags):
        # heading_text stores the readable normalized heading content.
        heading_text = normalize_whitespace(heading_node.get_text(" ", strip=True))
        if len(heading_text) < 3:
            continue
        if heading_text in seen_headings:
            continue
        seen_headings.add(heading_text)
        headings.append(heading_text)

    # return_value contains the ordered list of extracted headings.
    return headings


def extract_links(content_root: Tag) -> list[str]:
    """Extract unique relative links from the main content block."""

    # links keeps unique href values from the meaningful content region.
    links: list[str] = []

    # seen_links prevents duplicates when the same href appears multiple times.
    seen_links: set[str] = set()

    # link_node iterates over every anchor with an href attribute.
    for link_node in content_root.find_all("a", href=True):
        # href_value stores the target of the current anchor tag.
        href_value = link_node["href"].strip()
        if not href_value:
            continue
        if href_value in seen_links:
            continue
        seen_links.add(href_value)
        links.append(href_value)

    # return_value contains the unique relative links found in the content.
    return links


def build_normalized_page(file_path: Path, source_root: Path) -> NormalizedPage:
    """Convert one raw HTML file into a normalized page record."""

    # relative_path keeps the file path relative to the source directory.
    relative_path = file_path.relative_to(source_root)

    # html_text stores the decoded HTML markup for the current file.
    # encoding stores the selected text encoding used for this file.
    html_text, encoding = read_html_file(file_path)

    # soup stores the parsed BeautifulSoup tree used for HTML traversal and cleanup.
    soup = BeautifulSoup(html_text, "html.parser")

    # content_root stores the main semantic part of the page.
    content_root = extract_main_content(soup)

    # content_copy prevents accidental changes to the original parse tree outside the main block.
    content_copy = BeautifulSoup(str(content_root), "html.parser")

    # normalized_root stores the actual root node used for cleanup and extraction.
    normalized_root = extract_main_content(content_copy)

    remove_service_nodes(normalized_root)

    # page_title stores the normalized HTML title for the current page.
    page_title = normalize_whitespace(soup.title.get_text(" ", strip=True) if soup.title else "")

    # content_text stores the final clean text extracted from the kept content block.
    content_text = normalize_whitespace(normalized_root.get_text(" ", strip=True))

    # content_html stores cleaned HTML markup for later structured parsing stages.
    content_html = str(normalized_root)

    # headings stores the main section labels that can later help chunking logic.
    headings = extract_headings(normalized_root)

    # links stores the local relations that can later become graph edges.
    links = extract_links(normalized_root)

    # normalized_page contains all cleaned fields for the current HTML page.
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

    # return_value is the fully prepared page record.
    return normalized_page


def iter_normalized_pages(file_paths: Iterable[Path], source_root: Path) -> Iterator[NormalizedPage]:
    """Yield normalized page records one by one."""

    # file_path iterates over each raw HTML file selected for processing.
    for file_path in file_paths:
        yield build_normalized_page(file_path=file_path, source_root=source_root)


def write_jsonl(records: Iterable[NormalizedPage], output_file: Path) -> int:
    """Write normalized records to a JSONL file and return the number of written rows."""

    # parent_directory stores the output folder that must exist before file writing.
    parent_directory = output_file.parent
    parent_directory.mkdir(parents=True, exist_ok=True)

    # written_rows counts how many records were successfully saved to disk.
    written_rows = 0

    with output_file.open("w", encoding="utf-8") as jsonl_stream:
        # record iterates over every normalized page ready for serialization.
        for record in records:
            # serialized_record stores the JSON representation of one page.
            serialized_record = json.dumps(asdict(record), ensure_ascii=False)
            jsonl_stream.write(serialized_record + "\n")
            written_rows += 1

    # return_value contains the number of JSONL rows written to the output file.
    return written_rows


def main() -> None:
    """Run the full normalization pipeline from raw HTML pages to JSONL output."""

    # arguments stores user-provided command-line values.
    arguments = parse_arguments()

    # source_root stores the resolved root directory with raw HTML pages.
    source_root = arguments.source_root.resolve()

    # output_file stores the resolved destination JSONL file path.
    output_file = arguments.output_file.resolve()

    # html_files stores all candidate HTML files found under the source directory.
    html_files = collect_html_files(source_root)

    # limited_html_files optionally restricts the number of pages processed during debugging.
    limited_html_files = html_files[: arguments.limit] if arguments.limit else html_files

    # normalized_records lazily yields normalized page objects.
    normalized_records = iter_normalized_pages(
        file_paths=limited_html_files,
        source_root=source_root,
    )

    # written_rows stores how many normalized pages were written to the JSONL file.
    written_rows = write_jsonl(records=normalized_records, output_file=output_file)

    # summary_message stores the human-readable completion message shown in the terminal.
    summary_message = (
        f"Normalized {written_rows} HTML pages from '{source_root}' "
        f"into '{output_file}'."
    )
    print(summary_message)


if __name__ == "__main__":
    main()
