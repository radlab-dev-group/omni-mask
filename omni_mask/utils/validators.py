import json
import os
from typing import Set, FrozenSet


class Config:
    """Loads name-detection exclusions from config.json."""

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
