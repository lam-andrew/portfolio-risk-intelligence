"""Versioned, deterministic HTML-to-text and passage extraction. No I/O."""

import re
from dataclasses import dataclass
from html.parser import HTMLParser
from itertools import pairwise

PARSER_VERSION = "html-text-v1"


class FilingTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        style = (attributes.get("style") or "").replace(" ", "").lower()
        if self.hidden:
            if tag not in {"br", "hr", "img", "meta", "link", "input"}:
                self.hidden.append(tag)
            return
        if tag in {"script", "style", "noscript", "ix:hidden", "head"} or (
            "hidden" in attributes or "display:none" in style or "visibility:hidden" in style
        ):
            self.hidden.append(tag)
        elif tag in {"p", "div", "br", "tr", "h1", "h2", "h3", "h4", "li"}:
            self.parts.append("\n")
        elif tag in {"td", "th"}:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if self.hidden:
            if tag in self.hidden:
                self.hidden = self.hidden[: len(self.hidden) - 1 - self.hidden[::-1].index(tag)]
        elif tag in {"p", "div", "tr", "h1", "h2", "h3", "h4", "li"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.hidden:
            self.parts.append(data)


@dataclass(frozen=True)
class Passage:
    ordinal: int
    section: str
    start: int
    end: int
    text: str


def extract_passages(html: str) -> tuple[str, list[Passage]]:
    parser = FilingTextParser()
    parser.feed(html)
    parser.close()
    lines = (re.sub(r"\s+", " ", line).strip() for line in "".join(parser.parts).splitlines())
    text = "\n".join(line for line in lines if line)
    if len(text) < 80:
        raise ValueError("The document has too little readable text to index.")
    headings = list(re.finditer(r"(?im)^item\s+\d+[a-z]?[. :\-][^\n]{0,150}", text))
    passages: list[Passage] = []
    boundaries = sorted({0, len(text), *(heading.start() for heading in headings)})
    for region_start, region_end in pairwise(boundaries):
        section = next(
            (m.group().strip() for m in reversed(headings) if m.start() <= region_start),
            "Document",
        )
        start = region_start
        while start < region_end:
            end = min(start + 1800, region_end)
            if end < region_end:
                boundary = text.rfind(" ", start + 1200, end)
                if boundary > start:
                    end = boundary
            if text[start:end].strip():
                passages.append(Passage(len(passages), section, start, end, text[start:end]))
            if end == region_end:
                break
            start = end - 200
            boundary = text.find(" ", start, end)
            if boundary != -1:
                start = boundary + 1
    return text, passages
