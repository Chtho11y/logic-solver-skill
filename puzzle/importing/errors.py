"""Errors raised while decoding a Penpa+ or puzz.link URL."""


class PuzzleImportError(ValueError):
    """A puzzle URL could not be parsed or bound to a spec."""
