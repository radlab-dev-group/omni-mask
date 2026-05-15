import fitz
from typing import Any

from omni_mask.loaders.base import BaseLoader


class PDFLoader(BaseLoader):
    def can_handle(self, filepath: str) -> bool:
        return filepath.lower().endswith(".pdf")

    def anonymize(self, filepath: str, outpath: str, core: Any) -> None:
        doc = fitz.open(filepath)

        # Collect all text from all pages
        page_texts = []
        for page in doc:
            page_texts.append(page.get_text("text"))

        # Single mask() call — get consistent pseudonyms
        combined = "\n".join(page_texts)
        _, mappings = core._masker.mask(combined)

        # Build {original: pseudonym} for PDF redaction
        orig_to_pseudo = {}
        for pseudo, orig in mappings.items():
            if orig not in orig_to_pseudo:
                orig_to_pseudo[orig] = "{" + pseudo + "}"

        for page in doc:
            for original, pseudonym in orig_to_pseudo.items():
                for rect in page.search_for(original):
                    page.add_redact_annot(
                        rect,
                        text=pseudonym,
                        align=1,
                        fill=(0, 0, 0),
                        text_color=(1, 1, 1),
                    )
            if orig_to_pseudo:
                page.apply_redactions()
        doc.save(outpath, deflate=True, garbage=4)
        doc.close()

    def deanonymize(self, filepath: str, outpath: str, core: Any) -> None:
        # PDFy nie obsługują przywracania danych w tej wersji
        raise NotImplementedError("Pliki PDF nie obsługują odwracania.")


from typing import Any
