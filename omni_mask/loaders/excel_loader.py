from typing import Any, Callable, Optional, Set
import openpyxl

from omni_mask.loaders.base import BaseLoader


def _process_properties(wb: Any, process_fn: Callable[[str], str]) -> None:
    props = getattr(wb, "properties", None)
    if not props:
        return
    prop_names = [
        "creator",
        "lastModifiedBy",
        "title",
        "subject",
        "description",
        "keywords",
        "category",
        "comments",
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


def _process_cell_value(cell: Any, process_fn: Callable[[str], str]) -> None:
    val = cell.value
    if val is None:
        return

    if isinstance(val, str):
        new_val = process_fn(val)
        if new_val != val:
            cell.value = new_val
    elif isinstance(val, int):
        val_str = str(val)
        new_val = process_fn(val_str)
        if new_val != val_str:
            cell.value = new_val
    elif isinstance(val, float) and val.is_integer():
        val_str = str(int(val))
        new_val = process_fn(val_str)
        if new_val != val_str:
            cell.value = new_val


def _process_cell_comment(cell: Any, process_fn: Callable[[str], str]) -> None:
    comment = getattr(cell, "comment", None)
    if not comment:
        return

    if hasattr(comment, "text") and isinstance(comment.text, str) and comment.text:
        new_text = process_fn(comment.text)
        if new_text != comment.text:
            comment.text = new_text

    if (
        hasattr(comment, "author")
        and isinstance(comment.author, str)
        and comment.author
    ):
        new_author = process_fn(comment.author)
        if new_author != comment.author:
            comment.author = new_author


class ExcelLoader(BaseLoader):
    def can_handle(self, filepath: str) -> bool:
        return filepath.lower().endswith((".xlsx", ".xls"))

    def anonymize(
        self,
        filepath: str,
        outpath: str,
        core: Any,
        pii_enabled: Optional[Set[str]] = None,
        enabled_fastmask: Optional[Set[str]] = None,
    ) -> None:
        wb = openpyxl.load_workbook(filepath)
        process_fn = lambda t: core.anonymize_text(
            t, pii_enabled=pii_enabled, enabled_fastmask=enabled_fastmask
        )

        for sheet in wb.worksheets:
            for row in sheet.iter_rows():
                for cell in row:
                    _process_cell_value(cell, process_fn)
                    _process_cell_comment(cell, process_fn)

        _process_properties(wb, process_fn)

        wb.save(outpath)
        wb.close()

    def deanonymize(self, filepath: str, outpath: str, core: Any) -> None:
        wb = openpyxl.load_workbook(filepath)
        process_fn = lambda t: core.deanonymize_text(t)

        for sheet in wb.worksheets:
            for row in sheet.iter_rows():
                for cell in row:
                    _process_cell_value(cell, process_fn)
                    _process_cell_comment(cell, process_fn)

        _process_properties(wb, process_fn)

        wb.save(outpath)
        wb.close()
