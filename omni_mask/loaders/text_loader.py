from typing import Any

from omni_mask.loaders.base import BaseLoader


class TextLoader(BaseLoader):
    def can_handle(self, filepath: str) -> bool:
        return filepath.lower().endswith((".txt", ".csv"))

    def anonymize(self, filepath: str, outpath: str, core: Any) -> None:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        with open(outpath, "w", encoding="utf-8") as f:
            f.write(core.anonymize_text(text))

    def deanonymize(self, filepath: str, outpath: str, core: Any) -> None:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        with open(outpath, "w", encoding="utf-8") as f:
            f.write(core.deanonymize_text(text))
