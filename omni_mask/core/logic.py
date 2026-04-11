import re
import pandas as pd

from omni_mask.utils.validators import (
    PESEL_RE,
    NIP_RE,
    PHONE_RE,
    ADDRESS_RE,
    NAME_RE,
    EMAIL_RE,
    IBAN_RE,
    IDCARD_RE,
    is_valid_pesel,
    is_valid_nip,
    is_likely_person_name,
    load_exclusions,
    ANON_TYPE_LABELS,
)


class AnonymizerCore:
    def __init__(self):
        self.mapping = {}
        self.counters = {k: 1 for k in ANON_TYPE_LABELS}
        self.enabled = {k: True for k in ANON_TYPE_LABELS}
        self.records = []
        self.exclusions = load_exclusions()

    def get_pseudo(self, text: str, type_name: str, context: str = "") -> str:
        txt_norm = text.strip()
        if txt_norm in self.mapping:
            return self.mapping[txt_norm]

        pseudo = f"[{type_name}_{self.counters[type_name]}]"
        self.counters[type_name] += 1
        self.mapping[txt_norm] = pseudo
        self.records.append(
            {
                "Oryginalna wartość": txt_norm,
                "Typ danych": type_name,
                "Wygenerowany pseudonim": pseudo,
                "Kontekst": f"...{context}..." if context else "",
            }
        )
        return pseudo

    def get_context(self, full_text: str, match_obj) -> str:
        start = max(0, match_obj.start() - 40)
        end = min(len(full_text), match_obj.end() + 40)
        return full_text[start:end].replace("\n", " ")

    def extract_matches(self, text: str):
        matches = []
        if not isinstance(text, str):
            return matches
        en = self.enabled

        if en.get("PESEL", True):
            for m in PESEL_RE.finditer(text):
                if is_valid_pesel(m.group(0)):
                    matches.append(("PESEL", m.group(0)))
        if en.get("NIP", True):
            for m in NIP_RE.finditer(text):
                if is_valid_nip(m.group(0)):
                    matches.append(("NIP", m.group(0)))
        if en.get("TELEFON", True):
            for m in PHONE_RE.finditer(text):
                matches.append(("TELEFON", m.group(0)))
        if en.get("ADRES", True):
            for m in ADDRESS_RE.finditer(text):
                matches.append(("ADRES", m.group(0)))
        if en.get("NAZWISKO", True):
            for m in NAME_RE.finditer(text):
                if is_likely_person_name(m.group(0), self.exclusions):
                    matches.append(("NAZWISKO", m.group(0)))
        if en.get("EMAIL", True):
            for m in EMAIL_RE.finditer(text):
                matches.append(("EMAIL", m.group(0)))
        if en.get("KONTO_BANKOWE", True):
            for m in IBAN_RE.finditer(text):
                matches.append(("KONTO_BANKOWE", m.group(0)))
        if en.get("DOKUMENT_TOZSAMOSCI", True):
            for m in IDCARD_RE.finditer(text):
                matches.append(("DOKUMENT_TOZSAMOSCI", m.group(0)))

        return matches

    def anonymize_text(self, text: str) -> str:
        if not isinstance(text, str):
            return text
        en = self.enabled

        if en.get("PESEL", True):
            text = PESEL_RE.sub(
                lambda m: (
                    self.get_pseudo(m.group(0), "PESEL", self.get_context(text, m))
                    if is_valid_pesel(m.group(0))
                    else m.group(0)
                ),
                text,
            )
        if en.get("NIP", True):
            text = NIP_RE.sub(
                lambda m: (
                    self.get_pseudo(m.group(0), "NIP", self.get_context(text, m))
                    if is_valid_nip(m.group(0))
                    else m.group(0)
                ),
                text,
            )
        if en.get("TELEFON", True):
            text = PHONE_RE.sub(
                lambda m: self.get_pseudo(
                    m.group(0), "TELEFON", self.get_context(text, m)
                ),
                text,
            )
        if en.get("ADRES", True):
            text = ADDRESS_RE.sub(
                lambda m: self.get_pseudo(
                    m.group(0), "ADRES", self.get_context(text, m)
                ),
                text,
            )
        if en.get("EMAIL", True):
            text = EMAIL_RE.sub(
                lambda m: self.get_pseudo(
                    m.group(0), "EMAIL", self.get_context(text, m)
                ),
                text,
            )
        if en.get("KONTO_BANKOWE", True):
            text = IBAN_RE.sub(
                lambda m: self.get_pseudo(
                    m.group(0), "KONTO_BANKOWE", self.get_context(text, m)
                ),
                text,
            )
        if en.get("DOKUMENT_TOZSAMOSCI", True):
            text = IDCARD_RE.sub(
                lambda m: self.get_pseudo(
                    m.group(0), "DOKUMENT_TOZSAMOSCI", self.get_context(text, m)
                ),
                text,
            )
        if en.get("NAZWISKO", True):

            def repl_name(m):
                val = m.group(0)
                if val.startswith("[") and val.endswith("]"):
                    return val
                if not is_likely_person_name(val, self.exclusions):
                    return val
                return self.get_pseudo(val, "NAZWISKO", self.get_context(text, m))

            text = NAME_RE.sub(repl_name, text)

        return text


class DeanonymizerCore:
    def __init__(self):
        self.reverse_map = {}
        self.pattern = None

    def load_key(self, key_path: str):
        try:
            df = pd.read_excel(key_path)
            self.reverse_map = {
                str(row["Wygenerowany pseudonim"]): str(row["Oryginalna wartość"])
                for _, row in df.iterrows()
            }
            if not self.reverse_map:
                return False, "Klucz mapowania jest pusty."
            keys = sorted(self.reverse_map.keys(), key=len, reverse=True)
            self.pattern = re.compile("|".join([re.escape(str(k)) for k in keys]))
            return True, f"Wczytano {len(self.reverse_map)} par z klucza."
        except Exception as e:
            return False, f"Błąd wczytywania klucza: {str(e)}"

    def deanonymize_text(self, text: str) -> str:
        if not isinstance(text, str) or not self.pattern:
            return text
        return self.pattern.sub(lambda m: self.reverse_map[m.group(0)], text)
