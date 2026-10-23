# Spam Message Detector

A rule-based web application that analyses any text message and returns a **spam-risk score (0–100)**, a risk level (LOW / MEDIUM / HIGH), and actionable improvement suggestions — all processed locally with no data stored or transmitted externally.

---

## Problem Statement

Unsolicited bulk messages impose a significant burden on recipients and are routinely quarantined by server-side spam filters. Users who compose promotional or bulk messages have no reliable, privacy-respecting tool to check whether their content will trigger those filters before sending. Existing online checkers either require account registration, store submitted text on remote servers, or produce opaque scores without explaining what to fix.

This project solves both problems: it provides a **transparent, explainable scorer** and **per-rule improvement suggestions**, running entirely on the user's own machine.

---

## Features

- **Instant spam scoring** — 0–100 normalised score based on 12 documented spam-signal rules
- **Three risk levels** — LOW (< 35), MEDIUM (35–64), HIGH (≥ 65)
- **Per-rule suggestions** — each fired rule returns a concrete improvement tip
- **Animated visualisation** — SVG score ring, linear progress bar, colour-coded risk badge
- **Privacy-first** — no message text is stored, logged, or sent to any external service
- **No ML dependency** — fully explainable rule-based engine; no model files or training data required
- **30 automated tests** — unit tests for every rule + HTTP integration tests for every API contract
- **Responsive UI** — works on desktop and mobile browsers; no JavaScript framework required

---

## Technologies Used

| Layer | Technology | Version |
|---|---|---|
| Backend | Python | 3.8+ |
| Web framework | Flask | 3.0.3 |
| CORS support | flask-cors | 4.0.1 |
| Test runner | pytest | 8.2.2 |
| Frontend | HTML5 / CSS3 / JavaScript (ES2022) | Browser-native |
| Regex engine | re (Python stdlib) | Built-in |

---

## Folder Structure

```
Spam_message/
├── app.py                  # Flask app + rule-based scoring engine
├── requirements.txt        # Pinned Python dependencies
├── README.md               # This file
├── templates/
│   └── index.html          # Single-page HTML UI (served by Flask/Jinja2)
├── static/
│   ├── css/
│   │   └── style.css       # All visual styling — no CSS framework
│   └── js/
│       └── main.js         # Browser interactions — no JS framework
└── tests/
    └── test_app.py         # 30 automated tests (unit + HTTP integration)
```

---

## Installation

### Prerequisites

- Python **3.8 or later** — download from [python.org](https://www.python.org/downloads/)
- `pip` 21.0 or later (bundled with Python)
- Any modern browser (Chrome 104+, Firefox 103+, Safari 15.4+, Edge 104+)

### 1 — Clone or download the project

```bash
# If you have Git:
git clone <your-repo-url>
cd Spam_message

# Or simply unzip the project folder and open a terminal inside it.
```

### 2 — Create a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` prepended to your terminal prompt.

### 3 — Install dependencies

```bash
pip install -r requirements.txt
```

Expected output (versions may vary slightly):

```
Successfully installed Flask-3.0.3 flask-cors-4.0.1 pytest-8.2.2 ...
```

---

## Running the Application

```bash
python app.py
```

The development server starts on **http://127.0.0.1:5000**.  
Open that URL in your browser to use the application.

To stop the server press `Ctrl + C`.

---

## Usage

1. Open **http://127.0.0.1:5000** in your browser.
2. Type or paste a text message (up to 5,000 characters) into the textarea.
3. Click **Analyse message** (or press **Ctrl + Enter** / **Cmd + Enter**).
4. The results panel shows:
   - An animated **score ring** and **progress bar** coloured green / amber / red.
   - A **risk badge**: LOW, MEDIUM, or HIGH.
   - A **suggestions list** — one improvement tip per fired rule — or a green "clean" notice if no rules fired.
5. Edit the message based on the suggestions and re-analyse to track improvements.
6. Click **Clear** to reset the form.

### Example messages

| Message | Expected risk |
|---|---|
| `Hi Sarah, just checking we're still on for Friday's meeting.` | LOW |
| `Exclusive offer — 20% discount this week only! Visit our site.` | MEDIUM |
| `WIN FREE CASH PRIZE NOW!!! ACT NOW! http://win.example.com CLICK HERE` | HIGH |

---

## Running the Tests

With the virtual environment active:

```bash
python -m pytest tests/ -v
```

Expected output:

```
collected 30 items

tests/test_app.py::TestAnalyseScore::test_clean_message_scores_low PASSED
tests/test_app.py::TestAnalyseScore::test_all_caps_raises_score PASSED
...
======================== 30 passed in 0.95s ========================
```

All 30 tests should pass. The single `PytestCacheWarning` that may appear on Windows/OneDrive is a file-permission advisory and does not affect test correctness.

### Test coverage

| Suite | Count | What is tested |
|---|---|---|
| `TestAnalyseScore` | 19 | Every rule fires correctly; score bounds; clean vs spam messages |
| `TestIndexRoute` | 2 | GET / returns HTTP 200 and valid HTML |
| `TestAnalyseRoute` | 9 | API schema, status codes, edge cases, privacy (no `fired_rules` in response) |

---

## Scoring Method

The engine evaluates 12 rules against the submitted text. Each rule that fires adds a fixed number of **penalty points**. The raw total is capped at 100.

| Rule | Points | Signal |
|---|---|---|
| `excessive_caps` | 15 | > 30 % of multi-character words are ALL-CAPS |
| `money_keywords` | 15 | Bait words: free, win, cash, prize, bonus, discount … |
| `excessive_exclamation` | 10 | Two or more exclamation marks |
| `urgency_keywords` | 10 | "act now", "limited time", "expires today" … |
| `url_present` | 10 | Bare HTTP/HTTPS URL or www. prefix |
| `phone_present` | 8 | Digit sequence matching a phone-number pattern |
| `short_message` | 7 | Message shorter than 30 characters |
| `repeated_punctuation` | 5 | `!!!`, `???`, `...` (3+ consecutive) |
| `no_greeting` | 5 | Does not start with Hi, Hello, Dear … |
| `excessive_numbers` | 5 | Two or more runs of 4+ consecutive digits |
| `html_tags` | 5 | Raw HTML tags present in plain-text message |
| `click_here_phrase` | 5 | Exact phrase "click here" |

**Risk thresholds:** score < 35 → LOW · 35–64 → MEDIUM · ≥ 65 → HIGH

---

## Dataset Information

This project **does not use an external dataset**. No training data is required and no model files are bundled.

The scoring engine is a deterministic rule-based classifier: rules are defined in code (`app.py`) with manually calibrated weights based on well-documented spam-signal research. The automated tests in `tests/test_app.py` use **synthetic test cases** — hand-crafted messages that are designed to trigger specific rules in isolation or in combination.

If you wish to extend the project with a machine-learning classifier in the future, the [UCI SMS Spam Collection dataset](https://archive.ics.uci.edu/dataset/228/sms+spam+collection) is a widely used public benchmark (5,574 labelled SMS messages).

---

## API Reference

### `POST /api/analyse`

Analyse a text message for spam indicators.

**Request body (JSON):**

```json
{ "message": "Your message text here" }
```

**Response (JSON):**

```json
{
  "score": 75,
  "risk_level": "HIGH",
  "suggestions": [
    "Reduce ALL-CAPS words — they are a strong spam signal.",
    "Remove or rephrase money-related bait words (free, win, cash, prize …)."
  ]
}
```

| Field | Type | Description |
|---|---|---|
| `score` | integer | Spam score 0–100 |
| `risk_level` | string | `"LOW"`, `"MEDIUM"`, or `"HIGH"` |
| `suggestions` | array of strings | One improvement tip per fired rule; empty array if no rules fired |

**Error responses:**

| Status | Condition |
|---|---|
| `400 Bad Request` | `message` field is present but not a string |

Messages longer than 5,000 characters are silently truncated before analysis.

---

## Security Considerations

- **No data persistence.** Message text is processed in memory only and is never written to disk, a database, or a log file.
- **No external calls.** The application makes zero outbound network requests. All communication is between your browser and `127.0.0.1:5000`.
- **XSS protection.** The front end uses a `escapeHtml()` function before inserting any server-returned text into the DOM, preventing cross-site scripting via crafted suggestion strings.
- **Input cap.** The API enforces a hard 5,000-character limit to prevent resource exhaustion.
- **Development server only.** Flask's built-in server (`app.run(debug=True)`) is not intended for production. Do not expose port 5000 to the public internet. For production deployment, use a WSGI server such as Gunicorn behind a reverse proxy.

---

## Limitations

- **English only** — keyword rules are English-language; results are unreliable for other languages.
- **No semantic understanding** — the word "free" in "feel free to call" still triggers `money_keywords`.
- **Fixed weights** — calibrated manually, not trained on labelled data; may need tuning for specific message domains.
- **No history** — results are not stored between page loads.
- **Text only** — images, attachments, and HTML email structure are not analysed.
- **Single-user local server** — not designed for concurrent multi-user access.

---

## License

This project was created for academic purposes. No licence file is included; all rights are reserved by the author.
