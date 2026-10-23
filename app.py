"""
Spam Message Detector — Flask Backend
======================================
Analyses a submitted text message and returns a spam probability score
together with a list of human-readable improvement suggestions.

Scoring model (rule-based, no ML dependency):
  Each rule contributes a fixed number of "spam points".  The raw total is
  normalised to a 0-100 score and mapped to a LOW / MEDIUM / HIGH risk level.

Privacy guarantee: no message text is stored, logged to disk, or transmitted
to any external service.  All analysis happens in memory, per request.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

app = Flask(__name__)
CORS(app)          # allow same-origin XHR from the bundled front-end


# ---------------------------------------------------------------------------
# Spam-scoring engine
# ---------------------------------------------------------------------------

# Maximum possible raw points (sum of all rule weights below).
# Used to normalise the raw score to 0-100.
_MAX_RAW_POINTS = 100


@dataclass
class _Rule:
    """A single spam-indicator rule."""
    name: str
    weight: int           # raw points added when the rule fires
    description: str      # shown to the user as an improvement hint


# ---- Rule definitions -------------------------------------------------------
# Each rule targets a well-known spam signal.  Weights are calibrated so that
# a message hitting every rule reaches exactly _MAX_RAW_POINTS.

_RULES: List[_Rule] = [
    _Rule(
        name="excessive_caps",
        weight=15,
        description="Reduce ALL-CAPS words — they are a strong spam signal.",
    ),
    _Rule(
        name="excessive_exclamation",
        weight=10,
        description="Use fewer exclamation marks (!! or more detected).",
    ),
    _Rule(
        name="money_keywords",
        weight=15,
        description="Remove or rephrase money-related bait words (free, win, cash, prize …).",
    ),
    _Rule(
        name="urgency_keywords",
        weight=10,
        description="Avoid urgency phrases like 'act now', 'limited time', 'expires today'.",
    ),
    _Rule(
        name="url_present",
        weight=10,
        description="Avoid embedding bare URLs; use descriptive anchor text instead.",
    ),
    _Rule(
        name="phone_present",
        weight=8,
        description="Avoid including phone numbers in promotional messages.",
    ),
    _Rule(
        name="short_message",
        weight=7,
        description="Very short messages lack context — add a clear subject or greeting.",
    ),
    _Rule(
        name="repeated_punctuation",
        weight=5,
        description="Avoid sequences of repeated punctuation (???, !!!, ...).",
    ),
    _Rule(
        name="no_greeting",
        weight=5,
        description="Start with a personal greeting (Hi, Dear …) to appear legitimate.",
    ),
    _Rule(
        name="excessive_numbers",
        weight=5,
        description="Excessive digit sequences (prices, codes) inflate the spam score.",
    ),
    _Rule(
        name="html_tags",
        weight=5,
        description="Plain-text messages should not contain raw HTML tags.",
    ),
    _Rule(
        name="click_here_phrase",
        weight=5,
        description="Replace 'click here' with descriptive link text.",
    ),
]

# Sanity-check at import time — keeps _MAX_RAW_POINTS in sync.
assert sum(r.weight for r in _RULES) == _MAX_RAW_POINTS, (
    "Rule weights must sum to _MAX_RAW_POINTS"
)


@dataclass
class AnalysisResult:
    score: int                          # 0 – 100
    risk_level: str                     # LOW | MEDIUM | HIGH
    fired_rules: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


def _check_rules(text: str) -> dict[str, bool]:
    """Return a mapping of rule name → True when the rule fires."""
    t = text                          # original (case-preserved)
    tl = text.lower()                 # lower-case copy

    words = re.findall(r"[A-Za-z]+", t)
    caps_ratio = (
        sum(1 for w in words if w.isupper() and len(w) > 1) / max(len(words), 1)
    )

    money_kw = [
        "free", "win", "winner", "cash", "prize", "reward", "bonus",
        "discount", "offer", "cheap", "buy now", "order now", "claim",
        "congratulations", "selected", "lucky",
    ]
    urgency_kw = [
        "act now", "limited time", "expires", "today only", "hurry",
        "urgent", "immediately", "don't miss", "last chance", "deadline",
    ]
    greeting_kw = ["hi", "hello", "hey", "dear", "greetings", "good morning",
                   "good afternoon", "good evening"]

    return {
        "excessive_caps":        caps_ratio > 0.3,
        "excessive_exclamation": t.count("!") >= 2,
        "money_keywords":        any(kw in tl for kw in money_kw),
        "urgency_keywords":      any(kw in tl for kw in urgency_kw),
        "url_present":           bool(re.search(r"https?://\S+|www\.\S+", tl)),
        "phone_present":         bool(re.search(r"\b\d[\d\s\-().]{7,}\d\b", t)),
        "short_message":         len(t.strip()) < 30,
        "repeated_punctuation":  bool(re.search(r"[!?.]{3,}", t)),
        "no_greeting":           not any(tl.startswith(kw) for kw in greeting_kw),
        "excessive_numbers":     len(re.findall(r"\d{4,}", t)) >= 2,
        "html_tags":             bool(re.search(r"<[a-z][^>]*>", tl)),
        "click_here_phrase":     "click here" in tl,
    }


def analyse(text: str) -> AnalysisResult:
    """Score *text* and return an :class:`AnalysisResult`."""
    fired = _check_rules(text)

    raw = sum(r.weight for r in _RULES if fired.get(r.name))
    score = min(100, int(raw))          # already capped at 100 by design

    if score < 35:
        risk = "LOW"
    elif score < 65:
        risk = "MEDIUM"
    else:
        risk = "HIGH"

    fired_names = [r.name for r in _RULES if fired.get(r.name)]
    suggestions = [r.description for r in _RULES if fired.get(r.name)]

    return AnalysisResult(
        score=score,
        risk_level=risk,
        fired_rules=fired_names,
        suggestions=suggestions,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Serve the single-page front-end."""
    return render_template("index.html")


@app.route("/api/analyse", methods=["POST"])
def api_analyse():
    """
    POST /api/analyse
    Body (JSON): { "message": "<text to check>" }
    Response:    { "score": int, "risk_level": str, "suggestions": [str] }

    The message is analysed in memory only — never stored or forwarded.
    """
    body = request.get_json(silent=True) or {}
    message: str = body.get("message", "")

    if not isinstance(message, str):
        return jsonify({"error": "message must be a string"}), 400

    message = message[:5000]           # hard cap — no need to process novels

    result = analyse(message)

    return jsonify(
        {
            "score":       result.score,
            "risk_level":  result.risk_level,
            "suggestions": result.suggestions,
            # fired_rules intentionally omitted from the public API payload
        }
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5000)
