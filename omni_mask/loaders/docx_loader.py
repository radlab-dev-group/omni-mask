from typing import Any
from docx import Document

from omni_mask.loaders.base import BaseLoader


class DocxLoader(BaseLoader):
    def can_handle(self, filepath: str) -> bool:
        return filepath.lower().endswith((".docx", ".doc"))

    def anonymize(self, filepath: str, outpath: str, core: Any) -> None:
        doc = Document(filepath)
        for para in doc.paragraphs:
            for run in para.runs:
                if run.text:
                    run.text = core.anonymize_text(run.text)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        for run in para.runs:
                            if run.text:
                                run.text = core.anonymize_text(run.text)
        doc.save(outpath)

    def deanonymize(self, filepath: str, outpath: str, core: Any) -> None:
        doc = Document(filepath)
        for para in doc.paragraphs:
            for run in para.runs:
                if run.text:
                    run.text = core.deanonymize_text(run.text)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        for run in para.runs:
                            if run.text:
                                run.text = core.deanonymize_text(run.text)
        doc.save(outpath)
