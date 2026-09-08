#!/usr/bin/env python3
"""
_scaffold_common.py — naming, substitution, and file helpers shared by
create_slice.py and init_shared.py. Not a CLI; import only.
"""
from __future__ import annotations

import re
from pathlib import Path


# ---------------------------------------------------------------------------
# Naming helpers
# ---------------------------------------------------------------------------

def to_pascal(name: str) -> str:
    """notification -> Notification ; user-profile -> UserProfile ; userProfile -> UserProfile."""
    parts = re.split(r"[-_\s]+", name.strip())
    result = []
    for part in parts:
        # Split on inner capital letters too so "userProfile" becomes ["user","Profile"].
        for sub in re.findall(r"[A-Z]?[a-z0-9]+|[A-Z]+(?=[A-Z]|$)", part):
            if sub:
                result.append(sub[0].upper() + sub[1:].lower())
    return "".join(result)


def to_camel(name: str) -> str:
    pascal = to_pascal(name)
    return pascal[0].lower() + pascal[1:] if pascal else ""


def to_upper_snake(name: str) -> str:
    camel = to_camel(name)
    # Insert underscore before each uppercase letter, then uppercase the whole string.
    return re.sub(r"(?<!^)(?=[A-Z])", "_", camel).upper()


# Vowel-LETTER words with a consonant SOUND (take "a"): user, unit, unique,
# uniform, university, union, usage, usual, utility, European, one-time, UK...
_A_BEFORE_VOWEL_LETTER = ("uni", "use", "usu", "uti", "eu", "one", "uk")
# Consonant-LETTER words with a vowel SOUND (take "an"): hour, honest, heir...
_AN_BEFORE_CONSONANT_LETTER = ("hour", "honest", "heir", "honor")


def indefinite_article(word: str) -> str:
    """Pragmatic English article for generated OpenAPI prose. Handles the common
    vowel-letter/consonant-sound cases (a user, a unit) and silent-h (an hour);
    feature names are plain nouns, so a small exception set covers them."""
    w = word.strip().lower()
    if w.startswith(_A_BEFORE_VOWEL_LETTER):
        return "a"
    if w.startswith(_AN_BEFORE_CONSONANT_LETTER):
        return "an"
    return "an" if w[:1] in "aeiou" else "a"


# ---------------------------------------------------------------------------
# Placeholder substitution
# ---------------------------------------------------------------------------

def substitute(text: str, mapping: dict[str, str]) -> str:
    """Replace {{Key}} placeholders. Plain str.replace — templates never nest."""
    for key, value in mapping.items():
        text = text.replace("{{" + key + "}}", value)
    return text


# ---------------------------------------------------------------------------
# File writing
# ---------------------------------------------------------------------------

def write_file(path: Path, content: str, overwrite: bool) -> bool:
    """Return True if the file was written, False if it was skipped."""
    if path.exists() and not overwrite:
        print(f"  SKIP   {path} (already exists, pass --overwrite to replace)")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  WRITE  {path}")
    return True
