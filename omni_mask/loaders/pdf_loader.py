import fitz
from typing import Any

from omni_mask.loaders.base import BaseLoader


class PDFLoader(BaseLoader):
    def can_handle(self, filepath: str) -> bool:
        return filepath.lower().endswith(".pdf")

    def anonymize(self, filepath: str, outpath: str, core: Any) -> None:
        doc = fitz.open(filepath)
        for page in doc:
            text = page.get_text("text")
            matches = core.extract_matches(text)
            unique_matches = {val: typ for typ, val in matches}

            for val, typ in unique_matches.items():
                pseudo = core.get_pseudo(val, typ)
                for rect in page.search_for(val):
                    page.add_redact_annot(
                        rect,
                        text=pseudo,
                        align=1,
                        fill=(0, 0, 0),
                        text_color=(1, 1, 1),
                    )

            if unique_matches:
                page.apply_redactions()
        doc.save(outpath, deflate=True, garbage=4)
        doc.close()

    def deanonymize(self, filepath: str, outpath: str, core: Any) -> None:
        # PDFy nie obsługują przywracania danych w tej wersji
        raise NotImplementedError("Pliki PDF nie obsługują odwracania.")


from typing import Any
