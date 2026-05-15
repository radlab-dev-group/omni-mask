import fitz
from typing import Any, Set

from omni_mask.loaders.base import BaseLoader


class PDFLoader(BaseLoader):
    def can_handle(self, filepath: str) -> bool:
        return filepath.lower().endswith(".pdf")

    def anonymize(self, filepath: str, outpath: str, core: Any, pii_enabled: Set = None, enabled_fastmask: Set = None) -> None:
        doc = fitz.open(filepath)

        # Collect all text from all pages
        page_texts = []
        for page in doc:
            page_texts.append(page.get_text("text"))

        combined = "\n".join(page_texts)
        orig_to_pseudo = {}

        # PII first
        if pii_enabled:
            masked, pii_mappings = core.pii_anonymize_text(combined, pii_enabled)
            for tag, orig in pii_mappings.items():
                if orig not in orig_to_pseudo:
                    orig_to_pseudo[orig] = "{" + tag + "}"
            combined = masked

        # Then FastMasker
        if enabled_fastmask:
            rules = core._build_fastmask_rules(enabled_fastmask)
            if rules:
                fm_masker = __import__('llm_router_plugins.maskers.fast_masker.core.masker', fromlist=['FastMasker']).FastMasker(rules)
                masked2, fm_mappings = fm_masker.mask(combined)
                for pseudo, orig in fm_mappings.items():
                    if orig not in orig_to_pseudo:
                        orig_to_pseudo[orig] = "{" + pseudo + "}"
                combined = masked2

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
        raise NotImplementedError("Pliki PDF nie obsługują odwracania.")
