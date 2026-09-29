"""Text representation of small run clues; -1 denotes a question mark."""
import re


def parse_run_clue(text: str) -> list[int]:
    tokens = re.split(r"[\s,]+", text.strip())
    if not tokens or any(not re.fullmatch(r"\?|[0-8]", token) for token in tokens):
        raise ValueError(f"Invalid run clue {text!r}; use 0..8 or ?, separated by spaces")
    values = [-1 if token == "?" else int(token) for token in tokens]
    if len(values) > 4 or (0 in values and len(values) != 1):
        raise ValueError("Run clues allow up to four entries; 0 must stand alone")
    return values
