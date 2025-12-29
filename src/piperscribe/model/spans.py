from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True, slots=True)
class Span:
    # A half-open character range [start, end) into a document's plain text.
    start: int
    end: int
    reason: str = ""

    def normalized(self) -> "Span":
        s, e = self.start, self.end
        if e < s:
            s, e = e, s
        return Span(max(0, s), max(0, e), self.reason)

    def is_empty(self) -> bool:
        return self.end <= self.start


def normalize_spans(spans: Iterable[Span], text_len: int) -> List[Span]:
    # Clamp, sort, and merge overlapping spans. Keeps the first span's reason.
    items = []
    for sp in spans:
        n = sp.normalized()
        s = min(max(0, n.start), text_len)
        e = min(max(0, n.end), text_len)
        if e > s:
            items.append(Span(s, e, n.reason))

    items.sort(key=lambda x: (x.start, x.end))
    merged: List[Span] = []
    for sp in items:
        if not merged:
            merged.append(sp)
            continue
        last = merged[-1]
        if sp.start <= last.end:  # overlap/touch
            merged[-1] = Span(last.start, max(last.end, sp.end), last.reason)
        else:
            merged.append(sp)
    return merged


def subtract_spans(text: str, exclusions: Iterable[Span]) -> str:
    # Return text with excluded spans removed.
    spans = normalize_spans(exclusions, len(text))
    if not spans:
        return text
    out_parts = []
    i = 0
    for sp in spans:
        if sp.start > i:
            out_parts.append(text[i:sp.start])
        i = max(i, sp.end)
    if i < len(text):
        out_parts.append(text[i:])
    return "".join(out_parts)


def invert_spans(text_len: int, exclusions: Iterable[Span]) -> List[Span]:
    # Convert exclusions to included spans.
    spans = normalize_spans(exclusions, text_len)
    included: List[Span] = []
    i = 0
    for sp in spans:
        if sp.start > i:
            included.append(Span(i, sp.start))
        i = max(i, sp.end)
    if i < text_len:
        included.append(Span(i, text_len))
    return included
