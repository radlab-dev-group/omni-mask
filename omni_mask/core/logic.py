import logging
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple
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
    NrbRule,
    PassportRule,
    IdCardRule,
    PeselRule,
    NipRule,
    EuVatRule,
    KrsRule,
    RegonRule,
    PostalCodeRule,
    UrlRule,
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
    # "CONTACT/NUM": "Kontakt / Numer",
    # "OTHER": "Inne",
}

# Labels for the FastMasker checkbox section
ANON_TYPE_LABELS = {
    "PESEL": "PESEL",
    "NIP": "NIP (ID podatkowy / VAT-UE)",
    "REGON": "REGON",
    "KRS": "KRS",
    "TELEFON": "Numer telefonu",
    "EMAIL": "Adres e-mail",
    "URL": "Adres URL / Link",
    "KONTO_BANKOWE": "Konto bankowe (IBAN / NRB)",
    "DOKUMENT_TOZSAMOSCI": "Dokument tożsamości (Dowód / Paszport)",
    "ADRES": "Adres (kod pocztowy)",
}

# Mapping of technical / English entity names to canonical Polish labels
ENTITY_TYPE_MAP = {
    # PII model categories
    "PERSON": "OSOBA",
    "ORGANIZATION": "ORGANIZACJA",
    "LOCATION": "LOKALIZACJA",
    "FACILITY": "OBIEKT",
    "PRODUCT": "PRODUKT",
    "EVENT": "WYDARZENIE",
    "CONTACT/NUM": "TELEFON",
    # FastMasker rule tag types
    "PHONE": "TELEFON",
    "PHONE_INTERNATIONAL": "TELEFON",
    "TELEFON": "TELEFON",
    "EMAIL": "EMAIL",
    "PESEL": "PESEL",
    "NIP": "NIP",
    "EU_VAT": "NIP",
    "REGON": "REGON",
    "KRS": "KRS",
    "BANK_ACCOUNT": "KONTO_BANKOWE",
    "NRB": "KONTO_BANKOWE",
    "KONTO_BANKOWE": "KONTO_BANKOWE",
    "PASSPORT": "DOKUMENT_TOZSAMOSCI",
    "ID_CARD": "DOKUMENT_TOZSAMOSCI",
    "DOKUMENT_TOZSAMOSCI": "DOKUMENT_TOZSAMOSCI",
    "POSTAL_CODE": "ADRES",
    "ADRES": "ADRES",
    "URL": "URL",
}

# Map FastMasker type names to rule classes
_FASTMASKER_RULES = {
    "PESEL": [PeselRule],
    "NIP": [NipRule, EuVatRule],
    "REGON": [RegonRule],
    "KRS": [KrsRule],
    "TELEFON": [PhoneInternationalRule, PhoneRule],
    "EMAIL": [EmailRule],
    "URL": [UrlRule],
    "KONTO_BANKOWE": [BankAccountRule, NrbRule],
    "DOKUMENT_TOZSAMOSCI": [PassportRule, IdCardRule],
    "ADRES": [PostalCodeRule],
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


class EntityRegistry:
    """Central registry for managing consistent entity tags across a session/document."""

    def __init__(self):
        self.val_to_tag: Dict[str, str] = {}
        self.tag_to_val: Dict[str, str] = {}
        self.type_counters: Dict[str, int] = defaultdict(int)
        self.records: List[Dict[str, str]] = []

    def get_or_create(self, value: str, entity_type: str) -> str:
        """Get existing tag for value or create a new sequential tag."""
        norm_val = value.strip()
        if not norm_val:
            return value

        # Normalize canonical type name
        canon_type = ENTITY_TYPE_MAP.get(entity_type.upper(), entity_type.upper())

        if norm_val in self.val_to_tag:
            return self.val_to_tag[norm_val]

        self.type_counters[canon_type] += 1
        idx = self.type_counters[canon_type]
        tag = f"[{canon_type}_{idx}]"

        self.val_to_tag[norm_val] = tag
        self.tag_to_val[tag] = norm_val
        self.records.append(
            {
                "Oryginalna wartość": norm_val,
                "Typ danych": canon_type,
                "Wygenerowany pseudonim": tag,
                "Kontekst": "",
            }
        )
        return tag

    def reset(self):
        self.val_to_tag.clear()
        self.tag_to_val.clear()
        self.type_counters.clear()
        self.records.clear()

    def get_mapping_dataframe(self) -> pd.DataFrame:
        if not self.records:
            return pd.DataFrame(
                columns=[
                    "Oryginalna wartość",
                    "Typ danych",
                    "Wygenerowany pseudonim",
                    "Kontekst",
                ]
            )
        return pd.DataFrame(self.records)

    def save_mapping(self, path: str):
        df = self.get_mapping_dataframe()
        df.to_excel(path, index=False)


class AnonymizerCore:
    """Coordinates deterministic rules and ML model with a unified EntityRegistry."""

    def __init__(self):
        self.registry = EntityRegistry()
        self.enabled = {k: True for k in ANON_TYPE_LABELS}
        self.pii_enabled = set(PII_TYPE_LABELS.keys())
        self._fastmask_instances = []

    @property
    def mapping(self) -> Dict[str, str]:
        return self.registry.val_to_tag

    def _build_fastmask_rules(self, enabled_fastmask: Set[str]) -> list:
        rules = []
        for fm_type in enabled_fastmask:
            rule_entry = _FASTMASKER_RULES.get(fm_type)
            if not rule_entry:
                continue
            if isinstance(rule_entry, (list, tuple)):
                for rule_cls in rule_entry:
                    if rule_cls:
                        rules.append(rule_cls())
            else:
                rules.append(rule_entry())
        return rules

    def _apply_pii_with_registry(
        self, text: str, pii_enabled_labels: Set[str]
    ) -> str:
        if not pii_enabled_labels:
            return text

        predictor = _get_pii_predictor()
        target_labels = [
            l for l in PII_TYPE_LABELS.keys() if l in pii_enabled_labels
        ]
        try:
            predictions = predictor.predict(text=text)
        except Exception as exc:
            logger.warning("PII prediction failed: %s", exc)
            return text

        result_parts = []
        for item in predictions:
            word = item.get("word", "")
            label = item.get("label", "O")
            trimmed = word.strip()

            # Skip if label is not enabled, or if it's "O", or if it's already a tag
            is_tag = (trimmed.startswith("[") and trimmed.endswith("]")) or (
                trimmed.startswith("{") and trimmed.endswith("}")
            )

            if label in target_labels and label != "O" and trimmed and not is_tag:
                l_ws = word[: len(word) - len(word.lstrip())]
                r_ws = word[len(word.rstrip()) :]
                tag = self.registry.get_or_create(trimmed, label)
                result_parts.append(l_ws + tag + r_ws)
            else:
                result_parts.append(word)

        return "".join(result_parts)

    def anonymize_text(
        self,
        text: str,
        pii_enabled: Optional[Set[str]] = None,
        enabled_fastmask: Optional[Set[str]] = None,
    ) -> str:
        """Anonymizes text with deterministic rules first, then PII model using EntityRegistry."""
        if not text:
            return text

        # 1. Apply FastMasker deterministic rules first
        if enabled_fastmask:
            rules = self._build_fastmask_rules(enabled_fastmask)
            for rule in rules:
                text, _ = rule.apply(
                    text,
                    anonymizer_fn=lambda val, tag_type: self.registry.get_or_create(
                        val, tag_type
                    ),
                )

        # 2. Apply PII classification model on the remaining text
        if pii_enabled:
            text = self._apply_pii_with_registry(text, pii_enabled)

        return text

    def pii_anonymize_text(self, text: str, pii_enabled_labels: Set[str]) -> Tuple[str, dict]:
        """Backwards compatibility helper."""
        masked_text = self._apply_pii_with_registry(text, pii_enabled_labels)
        return masked_text, {}

    def accumulate_pii_mappings(self, mappings: dict):
        pass

    def accumulate_fastmask_mappings(self, mappings: dict):
        pass

    def reset_records(self):
        self.registry.reset()
        self._fastmask_instances = []

    @property
    def pii_records(self) -> List[Dict[str, str]]:
        return self.registry.records

    @property
    def records(self) -> List[Dict[str, str]]:
        return self.registry.records

    def get_pseudo(self, text: str, type_name: str) -> str:
        return self.registry.get_or_create(text, type_name)

    def save_mapping(self, path: str):
        self.registry.save_mapping(path)

    def get_mapping_df(self) -> pd.DataFrame:
        return self.registry.get_mapping_dataframe()


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
