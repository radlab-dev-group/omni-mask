from typing import Any, Set

from omni_mask.loaders.base import BaseLoader


class TextLoader(BaseLoader):
    def can_handle(self, filepath: str) -> bool:
        return filepath.lower().endswith((".txt", ".csv"))

    def anonymize(self, filepath: str, outpath: str, core: Any, pii_enabled: Set = None, enabled_fastmask: Set = None) -> None:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        core.reset_records()

        # PII first
        if pii_enabled:
            text, pii_mappings = core.pii_anonymize_text(text, pii_enabled)
            core.accumulate_pii_mappings(pii_mappings)

        # Then FastMasker
        if enabled_fastmask:
            rules = core._build_fastmask_rules(enabled_fastmask)
            if rules:
                fm_masker = __import__('llm_router_plugins.maskers.fast_masker.core.masker', fromlist=['FastMasker']).FastMasker(rules)
                text, fm_mappings = fm_masker.mask(text)
                core.accumulate_fastmask_mappings(fm_mappings)

        with open(outpath, "w", encoding="utf-8") as f:
            f.write(text)

    def deanonymize(self, filepath: str, outpath: str, core: Any) -> None:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        with open(outpath, "w", encoding="utf-8") as f:
            f.write(core.deanonymize_text(text))
