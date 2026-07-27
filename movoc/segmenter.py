"""
segmenter.py

segmenter.py

Rule-based prefix/root/suffix morphological segmenter for four Geʿez-script
languages: Amharic, Tigrinya, Tigre, and Geʿez.

For Amharic and Tigrinya, initial morphological analyses are obtained using
HornMorpho (https://github.com/hltdi/HornMorpho) and then manually
post-edited for consistency and quality.

For Tigre and Geʿez, HornMorpho is not used. The segmentation resources are
created from manually collected and annotated morphological examples.

The rule-based segmenter uses longest-match prefix and suffix rules defined
in:

../rules/{lang}_rules.json

It provides a transparent lightweight segmentation approach and does not fully
handle multi-affix stacking, root-and-pattern morphology, or irregular forms.
See README.md Limitations for details.
"""

import json
from pathlib import Path
from typing import NamedTuple

RULES_DIR = Path(__file__).resolve().parent.parent / "rules"
SUPPORTED_LANGUAGES = {"amharic", "tigrinya", "tigre", "geez"}


class Segmentation(NamedTuple):
    prefix: str
    root: str
    suffix: str

    def morphemes(self):
        return [m for m in (self.prefix, self.root, self.suffix) if m]


class MorphemeSegmenter:
    """Longest-match prefix/suffix stripper, parameterized by a per-language
    rules/{lang}_rules.json file (see RULES_DIR).
    """

    def __init__(self, language: str):
        if language not in SUPPORTED_LANGUAGES:
            raise ValueError(
                f"Unsupported language {language!r}; expected one of {SUPPORTED_LANGUAGES}"
            )
        self.language = language
        rules_path = RULES_DIR / f"{language}_rules.json"
        with open(rules_path, encoding="utf-8") as f:
            rules = json.load(f)
        self.source = rules["source"]
        # Longest-first so e.g. "እያለች" matches before the shorter "እ".
        self.prefixes = sorted(set(rules["prefixes"]), key=len, reverse=True)
        self.suffixes = sorted(set(rules["suffixes"]), key=len, reverse=True)

    def segment_word(self, word: str) -> Segmentation:
        remainder = word
        prefix = ""
        for p in self.prefixes:
            if remainder.startswith(p) and len(remainder) > len(p):
                prefix = p
                remainder = remainder[len(p):]
                break

        suffix = ""
        for s in self.suffixes:
            if remainder.endswith(s) and len(remainder) > len(s):
                suffix = s
                remainder = remainder[: -len(s)]
                break

        return Segmentation(prefix=prefix, root=remainder, suffix=suffix)

    def segment_sentence(self, sentence: str) -> list:
        return [self.segment_word(w) for w in sentence.strip().split()]
