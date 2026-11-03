import difflib
from typing import Any, Callable, List, Optional, Set
from docx import Document

from omni_mask.loaders.base import BaseLoader


def _apply_text_to_runs(runs_text: List[str], new_text: str) -> List[str]:
    """Applies changed paragraph text back to individual runs while preserving run boundaries."""
    if not runs_text:
        return []
    orig_text = "".join(runs_text)
    if orig_text == new_text:
        return runs_text

    run_spans = []
    curr = 0
    for r in runs_text:
        run_spans.append((curr, curr + len(r)))
        curr += len(r)

    matcher = difflib.SequenceMatcher(None, orig_text, new_text)
    opcodes = matcher.get_opcodes()

    new_runs = [[] for _ in runs_text]

    for tag, i1, i2, j1, j2 in opcodes:
        if tag == "equal":
            for r_idx, (r_start, r_end) in enumerate(run_spans):
                overlap_start = max(i1, r_start)
                overlap_end = min(i2, r_end)
                if overlap_start < overlap_end:
                    new_runs[r_idx].append(orig_text[overlap_start:overlap_end])
        elif tag in ("replace", "delete", "insert"):
            repl = new_text[j1:j2]
            placed = False
            for r_idx, (r_start, r_end) in enumerate(run_spans):
                if r_start <= i1 < r_end or (
                    i1 == i2 and r_start <= i1 <= r_end and not placed
                ):
                    new_runs[r_idx].append(repl)
                    placed = True
                    break
                elif r_start < i2 and r_end > i1:
                    if not placed:
                        new_runs[r_idx].append(repl)
                        placed = True
                        break
            if not placed and run_spans:
                new_runs[-1].append(repl)

    res = ["".join(parts) for parts in new_runs]
    return res


def _process_paragraph(para: Any, process_fn: Callable[[str], str]) -> None:
    if not para.text:
        return
    old_text = para.text
    new_text = process_fn(old_text)
    if new_text == old_text:
        return

    if not para.runs:
        para.text = new_text
        return

    runs_texts = [r.text for r in para.runs]
    if "".join(runs_texts) != old_text:
        para.text = new_text
        return

    new_runs_texts = _apply_text_to_runs(runs_texts, new_text)
    for run, r_text in zip(para.runs, new_runs_texts):
        run.text = r_text


def _process_table(table: Any, process_fn: Callable[[str], str]) -> None:
    for row in table.rows:
        for cell in row.cells:
            for para in cell.paragraphs:
                _process_paragraph(para, process_fn)
            for nested_table in cell.tables:
                _process_table(nested_table, process_fn)


def _process_sections(doc: Any, process_fn: Callable[[str], str]) -> None:
    seen_elements = set()
    for section in doc.sections:
        headers_footers = [
            getattr(section, "header", None),
            getattr(section, "first_page_header", None),
            getattr(section, "even_page_header", None),
            getattr(section, "footer", None),
            getattr(section, "first_page_footer", None),
            getattr(section, "even_page_footer", None),
        ]
        for hf in headers_footers:
            if hf is None:
                continue
            elem_id = id(getattr(hf, "_element", None))
            if elem_id in seen_elements:
                continue
            seen_elements.add(elem_id)

            for para in hf.paragraphs:
                _process_paragraph(para, process_fn)
            for table in hf.tables:
                _process_table(table, process_fn)


def _process_core_properties(doc: Any, process_fn: Callable[[str], str]) -> None:
    props = getattr(doc, "core_properties", None)
    if not props:
        return
    prop_names = [
        "author",
        "last_modified_by",
        "title",
        "subject",
        "keywords",
        "comments",
        "category",
    ]
    for prop in prop_names:
        try:
            val = getattr(props, prop, None)
            if val and isinstance(val, str) and val.strip():
                new_val = process_fn(val)
                if new_val != val:
                    setattr(props, prop, new_val)
        except Exception:
            pass


class DocxLoader(BaseLoader):
    def can_handle(self, filepath: str) -> bool:
        return filepath.lower().endswith((".docx", ".doc"))

    def anonymize(
        self,
        filepath: str,
        outpath: str,
        core: Any,
        pii_enabled: Optional[Set[str]] = None,
        enabled_fastmask: Optional[Set[str]] = None,
    ) -> None:
        doc = Document(filepath)

        process_fn = lambda t: core.anonymize_text(
            t, pii_enabled=pii_enabled, enabled_fastmask=enabled_fastmask
        )

        for para in doc.paragraphs:
            _process_paragraph(para, process_fn)

        for table in doc.tables:
            _process_table(table, process_fn)

        _process_sections(doc, process_fn)
        _process_core_properties(doc, process_fn)

        doc.save(outpath)

    def deanonymize(self, filepath: str, outpath: str, core: Any) -> None:
        doc = Document(filepath)

        process_fn = lambda t: core.deanonymize_text(t)

        for para in doc.paragraphs:
            _process_paragraph(para, process_fn)

        for table in doc.tables:
            _process_table(table, process_fn)

        _process_sections(doc, process_fn)
        _process_core_properties(doc, process_fn)

        doc.save(outpath)
