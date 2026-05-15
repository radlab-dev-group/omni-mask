import pandas as pd

from llm_router_plugins.maskers.fast_masker.core.masker import FastMasker, FastDeanonymizer


# Labels for the type checkboxes in the UI — matches omni-mask's original 8 types
ANON_TYPE_LABELS = {
    "PESEL": "PESEL",
    "NIP": "NIP (ID podatkowy)",
    "TELEFON": "Numer telefonu",
    "EMAIL": "Adres e-mail",
    "KONTO_BANKOWE": "Konto bankowe (IBAN)",
    "DOKUMENT_TOZSAMOSCI": "Dokument tożsamości",
    "NAZWISKO": "Nazwisko (imię + nazwisko)",
    "ADRES": "Adres",
}


class AnonymizerCore:
    """Wrapper around FastMasker that exposes the original omni-mask API."""

    def __init__(self):
        self._masker = FastMasker()
        self.mapping = self._masker.mapping
        self.enabled = {k: True for k in ANON_TYPE_LABELS}

    @property
    def records(self):
        """Expose mapping as list of dicts compatible with the original export format."""
        return [
            {
                "Oryginalna wartość": orig,
                "Typ danych": pseud.split("_")[0],
                "Wygenerowany pseudonim": "{" + pseud + "}",
                "Kontekst": "",
            }
            for orig, pseud in self.mapping.items()
        ]

    def get_pseudo(self, text: str, type_name: str) -> str:
        """Generate a pseudonym for *text*, caching it in the masker."""
        pseudo = self._masker._get_pseudo(text, type_name)
        return "{" + pseudo + "}"

    def extract_matches(self, text: str):
        """Return a list of (type, value) tuples found in *text*."""
        _, mappings = self._masker.mask(text)
        return [(p.split("_")[0], v) for p, v in mappings.items()]

    def anonymize_text(self, text: str) -> str:
        masked, _ = self._masker.mask(text)
        return masked

    def save_mapping(self, path: str):
        self._masker.save_mapping(path)

    def get_mapping_df(self) -> pd.DataFrame:
        return self._masker.get_mapping_df()


class DeanonymizerCore:
    def __init__(self):
        self._deanonymizer = FastDeanonymizer()

    def load_key(self, key_path: str):
        success = self._deanonymizer.load_mapping(key_path)
        if not success:
            return False, "Klucz mapowania jest pusty lub nie udało się go wczytać."
        return True, f"Wczytano {len(self._deanonymizer.reverse_map)} par z klucza."

    def deanonymize_text(self, text: str) -> str:
        return self._deanonymizer.deanonymize(text)
