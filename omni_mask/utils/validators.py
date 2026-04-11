import re
import os
import json
from typing import Set, List, FrozenSet

# Globalne wyrażenia regularne
PESEL_RE = re.compile(r"\b\d{11}\b")
NIP_RE = re.compile(
    r"\b\d{10}\b|\b\d{3}[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}\b|\b\d{3}[-\s]?\d{2}[-\s]?\d{2}[-\s]?\d{3}\b"
)
PHONE_RE = re.compile(r"\b(?:\+48\s*|0048\s*)?[1-9]\d{2}[\s-]?\d{3}[\s-]?\d{3}\b")
ADDRESS_RE = re.compile(
    r"\b(?:ul\.\s*|al\.\s*|pl\.\s*)?[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+(?: [A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+)?\s+\d+[a-zA-Z]?(?:[/\\]\d+)?(?:,\s*|\s+)\d{2}-\d{3}\s+[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+(?: [A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+)?\b"
)
NAME_RE = re.compile(
    r"\b[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]{2,}\s+[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]{2,}\b"
)
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
IBAN_RE = re.compile(r"\b(?:PL)?[\s-]?\d{2}(?:[\s-]?\d{4}){6}\b")
IDCARD_RE = re.compile(r"\b[A-ZĄĆĘŁŃÓŚŹŻ]{3}[\s-]?\d{6}\b")


class Config:
    def __init__(self):
        self.non_name_words: Set[str] = set()
        self.blocked_name_bigrams: Set[FrozenSet[str]] = set()
        self.non_name_suffixes: tuple = ()
        self.default_exclusions: Set[str] = set()
        self.load_from_json()

    def load_from_json(self):
        config_path = os.path.join(
            os.path.dirname(__file__), "..", "resources", "config.json"
        )
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.non_name_words = set(data.get("non_name_words", []))
                self.blocked_name_bigrams = {
                    frozenset(b) for b in data.get("blocked_name_bigrams", [])
                }
                self.non_name_suffixes = tuple(data.get("non_name_suffixes", []))
                self.default_exclusions = set(data.get("default_exclusions", []))
        except Exception as e:
            print(f"Error loading config: {e}")


config = Config()


def is_valid_pesel(text: str) -> bool:
    pesel = re.sub(r"\D", "", text)
    if len(pesel) != 11:
        return False
    weights = (1, 3, 7, 9, 1, 3, 7, 9, 1, 3)
    checksum = sum(int(pesel[i]) * weights[i] for i in range(10))
    return (10 - (checksum % 10)) % 10 == int(pesel[10])


def is_valid_nip(text: str) -> bool:
    nip = re.sub(r"\D", "", text)
    if len(nip) != 10:
        return False
    weights = (6, 5, 7, 2, 3, 4, 5, 6, 7)
    checksum = sum(int(nip[i]) * weights[i] for i in range(9))
    return (checksum % 11) == int(nip[9])


def is_likely_person_name(text: str, exclusions_lower: Set[str]) -> bool:
    words = text.strip().split()
    if len(words) != 2:
        return False
    w1, w2 = words
    if frozenset({w1.lower(), w2.lower()}) in config.blocked_name_bigrams:
        return False
    for w in (w1, w2):
        if w in config.non_name_words:
            return False
        if w.lower() in exclusions_lower:
            return False
        wl = w.lower()
        if any(wl.endswith(suf) for suf in config.non_name_suffixes):
            return False
    return True


def load_exclusions() -> Set[str]:
    words = config.default_exclusions.copy()
    try:
        if os.path.exists("nie_koduj.txt"):
            with open("nie_koduj.txt", "r", encoding="utf-8") as f:
                for line in f:
                    w = line.strip().lower()
                    if w:
                        words.add(w)
    except Exception:
        pass
    return words


ANON_TYPE_LABELS: dict[str, str] = {
    "PESEL": "PESEL",
    "NIP": "NIP",
    "TELEFON": "Numer telefonu",
    "ADRES": "Adres",
    "EMAIL": "Adres e-mail",
    "KONTO_BANKOWE": "Numer konta (IBAN)",
    "DOKUMENT_TOZSAMOSCI": "Seria i numer dowodu tożsamości",
    "NAZWISKO": "Imię i nazwisko (dwa wyrazy)",
}
