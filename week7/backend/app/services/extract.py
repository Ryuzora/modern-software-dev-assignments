from __future__ import annotations

import re
from dataclasses import dataclass

# Removes common bullet/index/checkbox prefixes:
#   "- ", "* ", "1. ", "(2) ", "[ ] ", "[x] "
_LEADING_MARKUP_RE = re.compile(
    r"^\s*(?:[-*+]\s+|\d+[.)]\s+|\(\d+\)\s+|\[[xX ]\]\s+)+",
    re.IGNORECASE,
)

# Strong signal for explicit action lines.
_EXPLICIT_PREFIX_RE = re.compile(
    r"^(?:todo|to-do|action(?:\s*item)?|next\s*step|follow[- ]?up|owner)\s*[:\-]\s*",
    re.IGNORECASE,
)

# Imperative and obligation cue verbs. We intentionally keep this list compact to avoid
# expensive over-matching while still covering common team-note phrasing.
_VERB_CUE_RE = re.compile(
    r"\b(?:please|must|should|need(?:s)?\s+to|have\s+to|required\s+to|let'?s|assign)\b",
    re.IGNORECASE,
)

# Explicit deadlines/time urgency usually indicate higher-priority actionable work.
_TIME_CUE_RE = re.compile(
    r"\b(?:asap|urgent|today|tomorrow|eod|by\s+\w+day|before\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b",
    re.IGNORECASE,
)

# Domain hints for lightweight categorization.
_CATEGORY_PATTERNS: dict[str, re.Pattern[str]] = {
    "testing": re.compile(r"\b(?:test|qa|regression|bug|fix)\b", re.IGNORECASE),
    "documentation": re.compile(r"\b(?:docs?|documentation|readme|writeup)\b", re.IGNORECASE),
    "review": re.compile(r"\b(?:review|approve|pr|merge)\b", re.IGNORECASE),
    "delivery": re.compile(r"\b(?:deploy|release|ship|publish)\b", re.IGNORECASE),
    "communication": re.compile(r"\b(?:email|notify|inform|sync|meeting)\b", re.IGNORECASE),
}

_NON_ACTIONABLE_RE = re.compile(
    r"\b(?:not actionable|fyi|for reference|just noting|discussion only|no action)\b",
    re.IGNORECASE,
)

_SPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True, slots=True)
class ExtractedActionItem:
    text: str
    category: str
    priority: str
    score: int


def _clean_line(line: str) -> str:
    line = _LEADING_MARKUP_RE.sub("", line).strip()
    line = line.strip(" \t-")
    return _SPACE_RE.sub(" ", line)


def _categorize(text: str) -> str:
    for category, pattern in _CATEGORY_PATTERNS.items():
        if pattern.search(text):
            return category
    return "general"


def _score_actionability(text: str) -> int:
    score = 0
    if _EXPLICIT_PREFIX_RE.search(text):
        score += 4
    if _VERB_CUE_RE.search(text):
        score += 2
    if _TIME_CUE_RE.search(text):
        score += 2
    if text.endswith("!"):
        score += 1
    return score


def _priority_from_score(score: int) -> str:
    if score >= 6:
        return "high"
    if score >= 3:
        return "medium"
    return "low"


def extract_action_items_detailed(text: str) -> list[ExtractedActionItem]:
    # O(n) scan over lines with precompiled regexes keeps performance stable on long notes.
    lines = (line for line in text.splitlines() if line.strip())
    seen: set[str] = set()
    items: list[ExtractedActionItem] = []

    for raw_line in lines:
        line = _clean_line(raw_line)
        if not line:
            continue
        if _NON_ACTIONABLE_RE.search(line):
            continue

        score = _score_actionability(line)
        if score <= 0:
            continue

        normalized_key = line.lower()
        if normalized_key in seen:
            continue
        seen.add(normalized_key)

        items.append(
            ExtractedActionItem(
                text=line,
                category=_categorize(line),
                priority=_priority_from_score(score),
                score=score,
            )
        )

    # Sort by importance first, then keep deterministic text ordering for stable tests.
    return sorted(items, key=lambda item: (-item.score, item.text.lower()))


def extract_action_items(text: str) -> list[str]:
    return [item.text for item in extract_action_items_detailed(text)]


