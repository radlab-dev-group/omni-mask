import openpyxl
from typing import Any

from omni_mask.loaders.base import BaseLoader


class ExcelLoader(BaseLoader):
    def can_handle(self, filepath: str) -> bool:
        return filepath.lower().endswith((".xlsx", ".xls"))

    def anonymize(self, filepath: str, outpath: str, core: Any) -> None:
        wb = openpyxl.load_workbook(filepath)
        for sheet in wb.worksheets:
            for row in sheet.iter_rows():
                for cell in row:
                    if cell.value and isinstance(cell.value, str):
                        cell.value = core.anonymize_text(cell.value)
        wb.save(outpath)
        wb.close()

    def deanonymize(self, filepath: str, outpath: str, core: Any) -> None:
        wb = openpyxl.load_workbook(filepath)
        for sheet in wb.worksheets:
            for row in sheet.iter_rows():
                for cell in row:
                    if cell.value and isinstance(cell.value, str):
                        cell.value = core.deanonymize_text(cell.value)
        wb.save(outpath)
        wb.close()
