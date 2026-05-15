from typing import Any, Set
from abc import ABC, abstractmethod


class BaseLoader(ABC):
    @abstractmethod
    def can_handle(self, filepath: str) -> bool:
        """Sprawdza czy loader obsługuje dany plik."""
        pass

    @abstractmethod
    def anonymize(self, filepath: str, outpath: str, core: Any, pii_enabled: Set = None, enabled_fastmask: Set = None) -> None:
        """Przeprowadza anonimizację pliku."""
        pass

    @abstractmethod
    def deanonymize(self, filepath: str, outpath: str, core: Any) -> None:
        """Przeprowadza de-anonimizację."""
        pass
