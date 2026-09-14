"""Map puzz.link / pzprjs pids onto this repo's ``impls/`` keys.

``rules.txt`` uses pzplus names. A few differ from the pid in a puzz.link URL
(``mashu`` vs ``masyu``, ``lightup`` vs ``akari``). Genre tags on a Penpa+
link use yet another set of labels.
"""

from __future__ import annotations

from functools import lru_cache

from puzzle.spec import implemented_keys

# puzz.link / pzprjs pid -> our impls key
PID_ALIASES: dict[str, str] = {
    "mashu": "masyu",
    "masyu": "masyu",
    "pearl": "masyu",
    "lightup": "akari",
    "akari": "akari",
    "bijutsukan": "akari",
    "yajirin": "yajilin",
    "yajilin": "yajilin",
    "building": "skyscrapers",
    "skyscraper": "skyscrapers",
    "skyscrapers": "skyscrapers",
    "bag": "cave",
    "hashikake": "hashi",
    "loopsp": "simpleloop",
    "kurotto": "kurotto",
    "domino": "domino-search",
    "dominosearch": "domino-search",
    "takuzu": "binairo",
    "binairo": "binairo",
    "hidoku": "hidato",
    "numpath": "hidato",
}

# Penpa+ genre tags (rtext[17] / title words) -> our key
PENPA_TAGS: dict[str, str] = {
    "classic": "sudoku",
    "sudoku": "sudoku",
    "slitherlink": "slither",
    "slither": "slither",
    "nurikabe": "nurikabe",
    "masyu": "masyu",
    "mashu": "masyu",
    "heyawake": "heyawake",
    "yajilin": "yajilin",
    "akari": "akari",
    "lightup": "akari",
    "light up": "akari",
    "hitori": "hitori",
    "shikaku": "shikaku",
    "fillomino": "fillomino",
    "norinori": "norinori",
    "starbattle": "starbattle",
    "star battle": "starbattle",
    "skyscrapers": "skyscrapers",
    "skyscraper": "skyscrapers",
    "kurodoko": "kurodoko",
    "cave": "cave",
    "tapa": "tapa",
    "lits": "lits",
    "country road": "country",
    "countryroad": "country",
    "araf": "araf",
    "kropki": "kropki",
    "binairo": "binairo",
    "takuzu": "binairo",
    "hidato": "hidato",
    "hidoku": "hidato",
}


def canonical_pid(pid: str) -> str:
    """Lowercase pid with known aliases applied (may still be unimplemented)."""

    key = (pid or "").strip().lower().replace("_", "-").replace(" ", "")
    return PID_ALIASES.get(key, key)


@lru_cache(maxsize=1)
def _implemented() -> set[str]:
    return set(implemented_keys())


def resolve_puzzle_key(name: str | None) -> str | None:
    """Return an implemented ``impls/`` key, or None."""

    if not name:
        return None
    key = canonical_pid(name)
    tagged = PENPA_TAGS.get((name or "").strip().lower())
    if tagged:
        key = tagged
    implemented = _implemented()
    if key in implemented:
        return key
    if tagged and tagged in implemented:
        return tagged
    return None


def guess_from_tags(tags: list[str], title: str = "") -> str | None:
    """Pick an implemented key from Penpa genre tags or a title string."""

    for tag in tags:
        key = resolve_puzzle_key(tag)
        if key:
            return key
        mapped = PENPA_TAGS.get(str(tag).strip().lower())
        if mapped and mapped in _implemented():
            return mapped
    words = (title or "").lower()
    for label, key in PENPA_TAGS.items():
        if label in words and key in _implemented():
            return key
    return None
