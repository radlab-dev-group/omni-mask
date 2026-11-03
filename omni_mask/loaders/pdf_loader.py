import fitz
from typing import Any, Set

from omni_mask.loaders.base import BaseLoader


class PDFLoader(BaseLoader):
    def can_handle(self, filepath: str) -> bool:
        return filepath.lower().endswith(".pdf")

    def anonymize(
        self,
        filepath: str,
        outpath: str,
        core: Any,
        pii_enabled: Set = None,
        enabled_fastmask: Set = None,
    ) -> None:
        doc = fitz.open(filepath)

        # Collect all text from all pages
        page_texts = []
        for page in doc:
            page_texts.append(page.get_text("text"))

        combined = "\n".join(page_texts)

        # Anonymize using central core pipeline
        core.anonymize_text(
            combined, pii_enabled=pii_enabled, enabled_fastmask=enabled_fastmask
        )

        for page in doc:
            for original, pseudonym in core.registry.val_to_tag.items():
                for rect in page.search_for(original):
                    page.add_redact_annot(
                        rect,
                        text=pseudonym,
                        align=1,
                        fill=(0, 0, 0),
                        text_color=(1, 1, 1),
                    )
            if core.registry.val_to_tag:
                page.apply_redactions()
        doc.save(outpath, deflate=True, garbage=4)
        doc.close()

    def deanonymize(self, filepath: str, outpath: str, core: Any) -> None:
        raise NotImplementedError("Pliki PDF nie obsługują odwracania.")
