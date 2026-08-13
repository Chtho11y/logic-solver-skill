"""In-memory text-document cache (full document sync)."""

from __future__ import annotations

from dataclasses import dataclass, field

from .convert import normalize_uri


@dataclass
class Document:
    uri: str
    language_id: str
    version: int
    text: str

    @property
    def lines(self) -> list[str]:
        return self.text.split("\n")


@dataclass
class Workspace:
    documents: dict[str, Document] = field(default_factory=dict)

    def get(self, uri: str) -> Document | None:
        return self.documents.get(normalize_uri(uri))

    def open(self, uri: str, language_id: str, version: int, text: str) -> Document:
        doc = Document(normalize_uri(uri), language_id, version, text)
        self.documents[doc.uri] = doc
        return doc

    def change(self, uri: str, version: int, text: str) -> Document | None:
        key = normalize_uri(uri)
        doc = self.documents.get(key)
        if doc is None:
            doc = Document(key, "puzzle-dsl", version, text)
        else:
            doc.version = version
            doc.text = text
        self.documents[key] = doc
        return doc

    def close(self, uri: str) -> None:
        self.documents.pop(normalize_uri(uri), None)

    def text(self, uri: str) -> str | None:
        doc = self.get(uri)
        return None if doc is None else doc.text
