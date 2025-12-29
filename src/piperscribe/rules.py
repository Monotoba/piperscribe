from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Tuple

from piperscribe.model.spans import Span, normalize_spans


@dataclass(slots=True)
class RegexRule:
    name: str
    pattern: str
    action: str = "exclude"  # "exclude" | "include"
    enabled: bool = True
    ignore_case: bool = True
    multiline: bool = True
    dotall: bool = False

    def flags(self) -> int:
        f = 0
        if self.ignore_case:
            f |= re.IGNORECASE
        if self.multiline:
            f |= re.MULTILINE
        if self.dotall:
            f |= re.DOTALL
        return f

    def compile(self) -> re.Pattern[str]:
        return re.compile(self.pattern, self.flags())


def canned_rules() -> List[RegexRule]:
    return [
        RegexRule(name="URLs (http/https)", pattern=r"https?://\S+", action="exclude", enabled=True, ignore_case=True, multiline=False),
        RegexRule(name="Repeated URL line (header/footer)", pattern=r"(?mi)^\s*https?://\S+\s*$", action="exclude", enabled=True, ignore_case=True, multiline=True),
        RegexRule(name="Emails", pattern=r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", action="exclude", enabled=False, ignore_case=True, multiline=False),
        RegexRule(name="Page numbers (Page X of Y)", pattern=r"(?mi)^\s*page\s+\d+\s*(of\s+\d+)?\s*$", action="exclude", enabled=False, ignore_case=True, multiline=True),
        RegexRule(name="Table of Contents block (heuristic)", pattern=r"(?is)^\s*(table\s+of\s+contents|contents)\s*$.*?(?=^\S|\Z)", action="exclude", enabled=False, ignore_case=True, multiline=True, dotall=True),
        RegexRule(name="Appendix headings (heuristic)", pattern=r"(?im)^\s*appendix\s+[a-z0-9]+\b.*$", action="exclude", enabled=False, ignore_case=True, multiline=True),
    ]


def _subtract(exclusions: List[Span], keep: Span) -> List[Span]:
    out: List[Span] = []
    for ex in exclusions:
        if ex.end <= keep.start or ex.start >= keep.end:
            out.append(ex)
        else:
            if ex.start < keep.start:
                out.append(Span(ex.start, keep.start, ex.reason))
            if ex.end > keep.end:
                out.append(Span(keep.end, ex.end, ex.reason))
    return out


def apply_rules(text: str, base_exclusions: Iterable[Span], rules: Iterable[RegexRule]) -> List[Span]:
    exclusions = normalize_spans(list(base_exclusions), len(text))
    for rule in rules:
        if not rule.enabled:
            continue
        try:
            rx = rule.compile()
        except re.error:
            continue

        if rule.action == "exclude":
            for m in rx.finditer(text):
                s, e = m.span()
                if e > s:
                    exclusions.append(Span(s, e, f"rule:{rule.name}"))
            exclusions = normalize_spans(exclusions, len(text))
        elif rule.action == "include":
            for m in rx.finditer(text):
                s, e = m.span()
                if e > s:
                    exclusions = _subtract(exclusions, Span(s, e, f"rule:{rule.name}"))
            exclusions = normalize_spans(exclusions, len(text))
    return exclusions


def test_rule(text: str, rule: RegexRule) -> Tuple[int, List[str]]:
    rx = rule.compile()
    previews: List[str] = []
    n = 0
    for m in rx.finditer(text):
        n += 1
        if len(previews) < 10:
            snippet = text[m.start():m.end()].replace("\n", "\\n")
            if len(snippet) > 120:
                snippet = snippet[:117] + "…"
            previews.append(snippet)
    return n, previews
