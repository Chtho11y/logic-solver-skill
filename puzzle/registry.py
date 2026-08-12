"""The catalogue of every puzzle rule listed in ``rules.txt``.

``rules.txt`` is a tab-separated table exported from pzplus:

``key | included | english | chinese | week | category | subcategory | rule``

This module turns it into :class:`RuleEntry` records, merges in whichever rules
already have a DSL implementation under ``impls/`` and offers the lookup used by
the ``puzzle-rules`` agent tool: name (any language) -> rule, and rule text ->
candidate names.

Pure data; no z3 and no UI imports.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path

from .spec import IMPLS_DIR, ROOT, implemented_keys

RULES_FILE = ROOT / "rules.txt"


@dataclass(frozen=True)
class RuleEntry:
    key: str
    en: str
    zh: str
    category: str
    subcategory: str
    rule: str
    week: str = ""
    included: str = ""
    implemented: bool = False

    def to_json(self) -> dict:
        return asdict(self)

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(n for n in (self.key, self.en, self.zh) if n)


def _split_row(line: str) -> list[str]:
    parts = line.rstrip("\n").split("\t")
    while len(parts) < 8:
        parts.append("")
    return [p.strip() for p in parts[:8]]


@lru_cache(maxsize=1)
def load_rules() -> tuple[RuleEntry, ...]:
    """Parse ``rules.txt`` (skipping its header) into rule entries."""

    if not RULES_FILE.is_file():
        return ()
    done = set(implemented_keys())
    entries: list[RuleEntry] = []
    for lineno, line in enumerate(RULES_FILE.read_text(encoding="utf-8").splitlines()):
        if not line.strip():
            continue
        key, included, en, zh, week, category, subcategory, rule = _split_row(line)
        if lineno == 0 and key.startswith("pzplus"):
            continue
        if not key:
            continue
        entries.append(
            RuleEntry(
                key=key,
                en=en,
                zh=zh,
                category=category,
                subcategory=subcategory,
                rule=rule,
                week=week,
                included=included,
                implemented=key in done,
            )
        )
    return tuple(entries)


@lru_cache(maxsize=1)
def rules_by_key() -> dict[str, RuleEntry]:
    return {entry.key: entry for entry in load_rules()}


def get_rule(key: str) -> RuleEntry | None:
    return rules_by_key().get(key)


# -- searching ----------------------------------------------------------------


def _normalise(text: str) -> str:
    text = unicodedata.normalize("NFKC", str(text)).lower()
    return re.sub(r"[\s\-_/·’'\"()（）]+", "", text)


def _score(entry: RuleEntry, needle: str) -> float:
    """How well ``needle`` identifies ``entry`` (0 = no match)."""

    target_fields = ((entry.key, 1.0), (entry.en, 0.98), (entry.zh, 0.96))
    best = 0.0
    for value, weight in target_fields:
        if not value:
            continue
        norm = _normalise(value)
        if norm == needle:
            best = max(best, 100.0 * weight)
        elif norm.startswith(needle):
            best = max(best, 70.0 * weight)
        elif needle in norm:
            best = max(best, 55.0 * weight)
        elif norm in needle:
            best = max(best, 45.0 * weight)
    if best:
        return best
    haystack = _normalise(f"{entry.category}{entry.subcategory}{entry.rule}")
    if needle and needle in haystack:
        # Rule-text hits rank below any name hit, longer needles rank higher.
        return 10.0 + min(len(needle), 20) * 0.5
    return 0.0


def search_rules(query: str, limit: int = 10) -> list[tuple[RuleEntry, float]]:
    """Rank rules against a free-form query (key / English / Chinese / text)."""

    needle = _normalise(query)
    if not needle:
        return []
    scored = [(entry, _score(entry, needle)) for entry in load_rules()]
    hits = [pair for pair in scored if pair[1] > 0]
    hits.sort(key=lambda pair: (-pair[1], pair[0].key))
    return hits[:limit]


def search_by_description(text: str, limit: int = 10) -> list[tuple[RuleEntry, float]]:
    """Reverse lookup: given rule wording, find which puzzles it could be.

    Scores by how many distinctive fragments of ``text`` appear in each rule
    description, so a paraphrased rule still finds its puzzle.
    """

    norm = _normalise(text)
    if not norm:
        return []
    fragments = [frag for frag in _fragments(norm) if len(frag) >= 3]
    if not fragments:
        return []
    results: list[tuple[RuleEntry, float]] = []
    for entry in load_rules():
        haystack = _normalise(entry.rule)
        if not haystack:
            continue
        hit = sum(len(frag) for frag in fragments if frag in haystack)
        if hit:
            results.append((entry, hit / max(len(norm), 1) * 100))
    results.sort(key=lambda pair: (-pair[1], pair[0].key))
    return results[:limit]


def _fragments(norm: str, size: int = 6) -> list[str]:
    """Overlapping shingles used for fuzzy rule-text matching."""

    if len(norm) <= size:
        return [norm]
    return [norm[i : i + size] for i in range(0, len(norm) - size + 1, 2)]


def categories() -> dict[str, list[RuleEntry]]:
    out: dict[str, list[RuleEntry]] = {}
    for entry in load_rules():
        out.setdefault(entry.category or "未分类", []).append(entry)
    return out


def catalogue() -> list[dict]:
    """Every rule as JSON, marked with whether a solver exists."""

    return [entry.to_json() for entry in load_rules()]


def missing_keys() -> list[str]:
    return [entry.key for entry in load_rules() if not entry.implemented]


def impl_paths(key: str) -> dict[str, Path]:
    return {
        "spec": IMPLS_DIR / f"{key}.json",
        "dsl": IMPLS_DIR / f"{key}.dsl",
        "sample": IMPLS_DIR / "samples" / f"{key}.json",
    }
