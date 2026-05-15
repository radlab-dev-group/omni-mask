import logging
import pandas as pd

from llm_router_plugins.maskers.fast_masker.core.masker import (
    FastMasker,
    FastDeanonymizer,
)
from llm_router_plugins.maskers.fast_masker.rules import (
    EmailRule,
    PhoneRule,
    PhoneInternationalRule,
    BankAccountRule,
    PassportRule,
    IdCardRule,
    PeselRule,
    NipRule,
)

logger = logging.getLogger(__name__)

# Try lazy import of AnonPredictor
_anon_predictor_class = None
_pii_import_error = None
try:
    from pii_classification.inference.inference import AnonPredictor
    _anon_predictor_class = AnonPredictor
except Exception as exc:
    _pii_import_error = str(exc)

if _pii_import_error:
    logger.warning("PII AnonPredictor unavailable: %s", _pii_import_error)

# Labels for the PII checkbox section — from anonymizer-model config
PII_TYPE_LABELS = {
    "LOCATION": "Lokalizacja",
    "PERSON": "Osoba",
    "FACILITY": "Obiekt",
    "ORGANIZATION": "Organizacja",
    "PRODUCT": "Produkt",
    "EVENT": "Wydarzenie",
    "CONTACT/NUM": "Kontakt / Numer",
    "OTHER": "Inne",
}

# Labels for the FastMasker checkbox section
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

# Map FastMasker type names to rule classes
_FASTMASKER_RULES = {
    "PESEL": PeselRule,
    "NIP": NipRule,
    "TELEFON": PhoneRule,
    "EMAIL": EmailRule,
    "KONTO_BANKOWE": BankAccountRule,
    "DOKUMENT_TOZSAMOSCI": PassportRule,
    "NAZWISKO": None,
    "ADRES": None,
}

_pii_predictor = None


def _get_pii_predictor():
    global _pii_predictor
    if _pii_import_error:
        raise RuntimeError(
            "AnonPredictor import failed: {}".format(_pii_import_error)
        )
    if _pii_predictor is None:
        _pii_predictor = _anon_predictor_class("radlab/pii-pl-v1.0")
    return _pii_predictor


class AnonymizerCore:
    """Wrapper around FastMasker that exposes the original omni-mask API with PII support."""

    def __init__(self):
        self._masker = FastMasker()
        self.mapping = self._masker.mapping
        self.enabled = {k: True for k in ANON_TYPE_LABELS}
        self.pii_enabled = set(PII_TYPE_LABELS.keys())
        self._accumulated_records = []

    def _build_fastmask_rules(self, enabled_fastmask: set) -> list:
        rules = []
        for fm_type in enabled_fastmask:
            rule_cls = _FASTMASKER_RULES.get(fm_type)
            if rule_cls:
                rules.append(rule_cls())
        return rules

    def pii_anonymize_text(self, text: str, pii_enabled_labels: set) -> tuple:
        """Return (masked_text, pii_mappings) without accumulating."""
        predictor = _get_pii_predictor()
        if not pii_enabled_labels:
            return text, {}

        target_labels = [l for l in PII_TYPE_LABELS.keys() if l in pii_enabled_labels]
        result = predictor.predict_and_anonymize(text=text, labels=target_labels)
        return result["text"], result["mappings"]

    def accumulate_pii_mappings(self, mappings: dict):
        for tag, orig in mappings.items():
            tag_type = tag.split("_")[0]
            self._accumulated_records.append({
                "Oryginalna wartość": orig,
                "Typ danych": tag_type,
                "Wygenerowany pseudonim": "{" + tag + "}",
                "Kontekst": "",
            })

    def accumulate_fastmask_mappings(self, mappings: dict):
        for pseudo, orig in mappings.items():
            tag_type = pseudo.split("_")[0]
            self._accumulated_records.append({
                "Oryginalna wartość": orig,
                "Typ danych": tag_type,
                "Wygenerowany pseudonim": "{" + pseudo + "}",
                "Kontekst": "",
            })

    def reset_records(self):
        self._accumulated_records = []

    @property
    def records(self):
        all_records = list(self._accumulated_records)
        all_records.extend([
            {
                "Oryginalna wartość": orig,
                "Typ danych": pseud.split("_")[0],
                "Wygenerowany pseudonim": "{" + pseud + "}",
                "Kontekst": "",
            }
            for orig, pseud in self.mapping.items()
        ])
        return all_records

    @property
    def pii_records(self):
        return self._accumulated_records

    def get_pseudo(self, text: str, type_name: str) -> str:
        pseudo = self._masker._get_pseudo(text, type_name)
        return "{" + pseudo + "}"

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
