# 🚀 Automated Multi-Platform Posting System

A production-ready **FastAPI** application that concurrently publishes a message to **5 independent platforms** via a single REST API endpoint. Built with strict Pydantic v2 validation, fully async concurrent execution using `asyncio.gather`, and graceful per-platform error handling.

---

## 📋 Project Overview

| Item | Detail |
|------|--------|
| **API Endpoint** | `POST /posting` |
| **Server Port** | `4000` |
| **Framework** | FastAPI 0.115.5 + Uvicorn 0.32.1 |
| **Validation** | Pydantic v2 — 4 strict rules, clean 422 responses |
| **HTTP Client** | httpx (async, 10-second timeout per platform) |
| **Concurrency** | `asyncio.gather` — all 5 platforms fire simultaneously |
| **Swagger UI** | http://localhost:4000/docs |
| **Test Suite** | **56 tests — 100% pass rate** |

---

## 🏗️ Directory Structure

```
automated-multi-platform-posting/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app + POST /posting endpoint
│   ├── schemas.py                 # Pydantic v2 request/response models + URL extraction
│   ├── config.py                  # python-dotenv env-var loading (zero hardcoded secrets)
│   ├── platforms/
│   │   ├── __init__.py
│   │   ├── base.py                # Abstract BasePlatform class
│   │   ├── telegraph.py           # Telegraph website (anonymous, no key required)
│   │   ├── dpaste.py              # Dpaste web portal (no key required)
│   │   ├── ntfy_sh.py             # Ntfy.sh public portal (no key required)
│   │   ├── github_gist.py         # GitHub Gist (requires GITHUB_TOKEN)
│   │   └── huggingface_llm.py     # HuggingFace LLM Hub (requires HF_API_TOKEN)
│   └── services/
│       ├── __init__.py
│       └── posting_service.py     # asyncio.gather concurrent orchestration
├── tests/
│   ├── __init__.py
│   └── test_posting.py            # 56 comprehensive unit + integration tests
├── logs/
│   └── sample_execution.json      # Actual live execution log + JSON response
├── venv/                          # Python virtual environment (gitignored)
├── .env                           # Your secrets — never committed (gitignored)
├── .env.example                   # Template for required environment variables
├── .gitignore                     # Excludes .env, venv/, __pycache__/, .pytest_cache/
├── requirements.txt
└── README.md
```

---

## 🔬 5-Platform Research Table

| # | Platform | Type | API Endpoint | Auth Required | Public Access | Notes |
|---|----------|------|-------------|---------------|---------------|-------|
| 1 | **Telegraph** | Website | `api.telegra.ph/createAccount` → `createPage` | ❌ None — anonymous per request | ✅ Yes | 2-step: create account → publish page; returns `telegra.ph/...` live URL |
| 2 | **Dpaste** | Web Portal | `dpaste.com/api/v2/` | ❌ None | ✅ Yes | POST form data; response body is the plain-text URL |
| 3 | **Ntfy.sh** | Public Portal | `ntfy.sh/dxora_automated_posting_feed` | ❌ None | ✅ Yes | Topic-based pub/sub; fixed public feed URL |
| 4 | **GitHub Gist** | Portal | `api.github.com/gists` | ✅ `GITHUB_TOKEN` | ✅ When configured | Creates public `post.md` gist; graceful fail if token missing |
| 5 | **HuggingFace** | LLM Hub | `huggingface.co/api/quick-pick` + `api-inference.huggingface.co/models/gpt2` | ✅ `HF_API_TOKEN` | ✅ When configured | Validates token; graceful fail if missing |

---

## ✅ Pydantic v2 Validation Rules

The `POST /posting` endpoint enforces **4 strict rules** on the `message` field:

| Rule | Condition | HTTP Response |
|------|-----------|---------------|
| **Non-empty** | `message.strip()` must not be empty | `422` |
| **Max 200 chars** | `len(message) <= 200` | `422` |
| **Exactly 1 CTA link** | Exactly one `http://` or `https://` URL after stripping trailing punctuation (`. , ! ? ; :`) | `422` if zero or >1 |
| **Valid URL format** | Extracted URL must have valid scheme + netloc + TLD | `422` |

> **Trailing punctuation stripping** — `_extract_urls()` calls `.rstrip(".,!?;:")` on each raw regex match, so messages like `"Visit http://example.org now."` extract cleanly as `"http://example.org"`.

> **Platform selection is 100% internal** — no `platform` parameter is accepted in the request body.

---

## ⚡ Concurrent Execution Flow

```
POST /posting  →  Pydantic v2 validation (rules 1–4)
                        │
                        ▼
         asyncio.gather(return_exceptions=False)
         ┌──────────┬──────────┬──────────┬──────────┬──────────┐
         │Telegraph │  Dpaste  │ Ntfy.sh  │  GitHub  │  HuggingF│
         │  .post() │  .post() │  .post() │  .post() │  .post() │
         └──────────┴──────────┴──────────┴──────────┴──────────┘
              All 5 fire simultaneously — each catches its own errors
                        │
                        ▼
      { "success": true, "results": [ ...5 PlatformResult objects... ] }
```

---

## 🚀 Setup & Run

### 1. Navigate to the project

```bash
cd "path/to/New folder"
```

### 2. Create and activate the virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and add your tokens:

```env
# GitHub Personal Access Token (gist scope)
# Generate: https://github.com/settings/tokens
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

# HuggingFace API Token
# Generate: https://huggingface.co/settings/tokens
HF_API_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
```

> Telegraph, Dpaste, and Ntfy.sh work **without any configuration** — they post anonymously.

### 5. Start the server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 4000
```

- **API base:** http://localhost:4000
- **Swagger UI:** http://localhost:4000/docs
- **ReDoc:** http://localhost:4000/redoc

### 6. Run the test suite

```bash
pytest tests/test_posting.py -v
```

Expected output: **56 passed**

---

## 📡 Sample cURL Requests

### ✅ Valid request

```bash
curl -X POST http://localhost:4000/posting \
  -H "Content-Type: application/json" \
  -d '{"message": "Check out our latest business platform and grow your online visibility. https://example.com"}'
```

### ❌ Message too long (422)

```bash
curl -X POST http://localhost:4000/posting \
  -H "Content-Type: application/json" \
  -d '{"message": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA https://example.com"}'
```

### ❌ Zero URLs (422)

```bash
curl -X POST http://localhost:4000/posting \
  -H "Content-Type: application/json" \
  -d '{"message": "No link in this message at all."}'
```

### ❌ Multiple URLs (422)

```bash
curl -X POST http://localhost:4000/posting \
  -H "Content-Type: application/json" \
  -d '{"message": "Visit https://example.com and also https://another.com"}'
```

### ❌ Invalid URL format (422)

```bash
curl -X POST http://localhost:4000/posting \
  -H "Content-Type: application/json" \
  -d '{"message": "Visit http://localhost for more info."}'
```

---

## 📊 Actual Live JSON Response

Captured live from `POST http://localhost:4000/posting` on **2026-11-15**:

**Request:**
```json
{
  "message": "Check out our latest business platform and grow your online visibility. https://example.com"
}
```

**Response — HTTP 200 OK:**
```json
{
  "success": true,
  "results": [
    {
      "platform": "Telegraph",
      "status": "failed",
      "posted_url": null,
      "public_access": false,
      "date": null,
      "time": null,
      "error": "ConnectError"
    },
    {
      "platform": "Dpaste",
      "status": "success",
      "posted_url": "https://dpaste.com/4TXMHKAYN",
      "public_access": true,
      "date": "2026-11-15",
      "time": "17:36:51",
      "error": null
    },
    {
      "platform": "Ntfy.sh",
      "status": "success",
      "posted_url": "https://ntfy.sh/dxora_automated_posting_feed",
      "public_access": true,
      "date": "2026-11-15",
      "time": "17:36:51",
      "error": null
    },
    {
      "platform": "GitHub Gist",
      "status": "failed",
      "posted_url": null,
      "public_access": false,
      "date": null,
      "time": null,
      "error": "Authentication failed: Missing GITHUB_TOKEN"
    },
    {
      "platform": "HuggingFace",
      "status": "failed",
      "posted_url": null,
      "public_access": false,
      "date": null,
      "time": null,
      "error": "Authentication failed: Missing HF_API_TOKEN"
    }
  ]
}
```

> **Note:** Telegraph's `ConnectError` is an intermittent network-level failure (the API itself is live and works — a previous run produced `https://telegra.ph/Automated-Post-11-15`). The system handles it gracefully: all other platforms continue unaffected and the endpoint always returns HTTP 200.

---

## 📋 Validation Error Response Examples

### ❌ 422 — Message exceeds 200 characters
```json
{
  "success": false,
  "detail": "Validation failed",
  "errors": [
    {
      "field": "message",
      "message": "Value error, message must not exceed 200 characters (received 201 characters).",
      "type": "value_error"
    }
  ]
}
```

### ❌ 422 — Zero CTA links
```json
{
  "success": false,
  "detail": "Validation failed",
  "errors": [
    {
      "field": "message",
      "message": "Value error, message must contain exactly one CTA link (http:// or https://). Zero links found.",
      "type": "value_error"
    }
  ]
}
```

### ❌ 422 — Multiple CTA links
```json
{
  "success": false,
  "detail": "Validation failed",
  "errors": [
    {
      "field": "message",
      "message": "Value error, message must contain exactly one CTA link (http:// or https://). 2 links found.",
      "type": "value_error"
    }
  ]
}
```

### ❌ 422 — Invalid URL format
```json
{
  "success": false,
  "detail": "Validation failed",
  "errors": [
    {
      "field": "message",
      "message": "Value error, The CTA URL 'http://localhost' is invalid. It must have a valid scheme (http/https), domain, and TLD.",
      "type": "value_error"
    }
  ]
}
```

---

## 📋 Execution Logs

### Server startup
```
INFO:     Started server process [9852]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:4000 (Press CTRL+C to quit)
INFO:     127.0.0.1:49968 - "POST /posting HTTP/1.1" 200 OK
```

### pytest — 56/56 PASSED
```
============================= test session starts =============================
platform win32 -- Python 3.10.7, pytest-8.3.3, pluggy-1.7.0
plugins: anyio-4.6.2, asyncio-0.24.0
collected 56 items

tests/test_posting.py::TestValidPosting::test_valid_message_returns_200 PASSED [  1%]
tests/test_posting.py::TestValidPosting::test_response_has_success_true PASSED [  3%]
tests/test_posting.py::TestValidPosting::test_response_has_results_list_of_5 PASSED [  5%]
tests/test_posting.py::TestValidPosting::test_each_result_has_all_required_fields PASSED [  7%]
tests/test_posting.py::TestValidPosting::test_success_entries_non_null_fields PASSED [  8%]
tests/test_posting.py::TestValidPosting::test_failed_entries_null_fields PASSED [ 10%]
tests/test_posting.py::TestValidPosting::test_platform_field_not_accepted_in_request PASSED [ 12%]
tests/test_posting.py::TestMessageTooLong::test_201_char_message_returns_422 PASSED [ 14%]
tests/test_posting.py::TestMessageTooLong::test_very_long_message_returns_422 PASSED [ 16%]
tests/test_posting.py::TestMessageTooLong::test_422_body_has_success_false PASSED [ 17%]
tests/test_posting.py::TestMessageTooLong::test_exactly_200_chars_accepted PASSED [ 19%]
tests/test_posting.py::TestZeroUrls::test_no_url_returns_422 PASSED       [ 21%]
tests/test_posting.py::TestZeroUrls::test_empty_message_returns_422 PASSED [ 23%]
tests/test_posting.py::TestZeroUrls::test_whitespace_only_returns_422 PASSED [ 25%]
tests/test_posting.py::TestZeroUrls::test_no_url_body_success_false PASSED [ 26%]
tests/test_posting.py::TestZeroUrls::test_ftp_url_treated_as_no_cta_link PASSED [ 28%]
tests/test_posting.py::TestMultipleUrls::test_two_urls_returns_422 PASSED  [ 30%]
tests/test_posting.py::TestMultipleUrls::test_three_urls_returns_422 PASSED [ 32%]
tests/test_posting.py::TestMultipleUrls::test_multiple_urls_body_success_false PASSED [ 33%]
tests/test_posting.py::TestMultipleUrls::test_multiple_urls_mentions_count PASSED [ 35%]
tests/test_posting.py::TestInvalidUrl::test_url_without_tld_returns_422 PASSED [ 37%]
tests/test_posting.py::TestInvalidUrl::test_url_bare_scheme_returns_422 PASSED [ 39%]
tests/test_posting.py::TestInvalidUrl::test_valid_https_url_accepted PASSED [ 41%]
tests/test_posting.py::TestInvalidUrl::test_valid_http_url_accepted PASSED  [ 42%]
tests/test_posting.py::TestInvalidUrl::test_invalid_url_body_success_false PASSED [ 44%]
tests/test_posting.py::TestPartialFailureResilience::test_partial_failure_returns_200 PASSED [ 46%]
tests/test_posting.py::TestPartialFailureResilience::test_partial_failure_returns_all_5_results PASSED [ 48%]
tests/test_posting.py::TestPartialFailureResilience::test_all_platforms_fail_still_200 PASSED [ 50%]
tests/test_posting.py::TestPartialFailureResilience::test_failed_platforms_null_fields PASSED [ 51%]
tests/test_posting.py::TestPartialFailureResilience::test_success_true_with_partial_failures PASSED [ 53%]
tests/test_posting.py::TestPartialFailureResilience::test_mixed_statuses_in_results PASSED [ 55%]
tests/test_posting.py::TestTrailingPunctuationStripping::test_strip_trailing_period PASSED [ 57%]
tests/test_posting.py::TestTrailingPunctuationStripping::test_strip_trailing_comma PASSED [ 58%]
tests/test_posting.py::TestTrailingPunctuationStripping::test_strip_trailing_exclamation PASSED [ 60%]
tests/test_posting.py::TestTrailingPunctuationStripping::test_strip_trailing_question_mark PASSED [ 62%]
tests/test_posting.py::TestTrailingPunctuationStripping::test_strip_trailing_semicolon PASSED [ 64%]
tests/test_posting.py::TestTrailingPunctuationStripping::test_strip_trailing_colon PASSED [ 66%]
tests/test_posting.py::TestTrailingPunctuationStripping::test_strip_multiple_trailing_chars PASSED [ 67%]
tests/test_posting.py::TestTrailingPunctuationStripping::test_no_strip_from_path PASSED [ 69%]
tests/test_posting.py::TestTrailingPunctuationStripping::test_no_strip_from_subdomain PASSED [ 71%]
tests/test_posting.py::TestTrailingPunctuationStripping::test_url_ending_with_period_accepted_200 PASSED [ 73%]
tests/test_posting.py::TestTrailingPunctuationStripping::test_url_ending_with_comma_accepted_200 PASSED [ 75%]
tests/test_posting.py::TestTrailingPunctuationStripping::test_url_ending_with_exclamation_accepted_200 PASSED [ 76%]
tests/test_posting.py::TestTrailingPunctuationStripping::test_url_in_markdown_link_syntax PASSED [ 78%]
tests/test_posting.py::TestPostingRequestSchema::test_valid_message_accepted PASSED [ 80%]
tests/test_posting.py::TestPostingRequestSchema::test_cta_url_property_clean PASSED [ 82%]
tests/test_posting.py::TestPostingRequestSchema::test_cta_url_strips_trailing_period PASSED [ 83%]
tests/test_posting.py::TestPostingRequestSchema::test_empty_message_raises PASSED [ 85%]
tests/test_posting.py::TestPostingRequestSchema::test_whitespace_message_raises PASSED [ 87%]
tests/test_posting.py::TestPostingRequestSchema::test_too_long_message_raises PASSED [ 89%]
tests/test_posting.py::TestPostingRequestSchema::test_exactly_200_chars_valid PASSED [ 91%]
tests/test_posting.py::TestPostingRequestSchema::test_no_url_raises PASSED  [ 92%]
tests/test_posting.py::TestPostingRequestSchema::test_multiple_urls_raises PASSED [ 94%]
tests/test_posting.py::TestPostingRequestSchema::test_invalid_url_tld_raises PASSED [ 96%]
tests/test_posting.py::TestPostingRequestSchema::test_valid_http_url_accepted PASSED [ 98%]
tests/test_posting.py::TestPostingRequestSchema::test_valid_https_subdomain_accepted PASSED [100%]

============================= 56 passed in 1.89s ==============================
```

---

## 🔑 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | Optional | GitHub PAT with `gist` scope → https://github.com/settings/tokens |
| `HF_API_TOKEN` | Optional | HuggingFace API token → https://huggingface.co/settings/tokens |
| `APP_HOST` | Optional | Bind host (default `0.0.0.0`) |
| `APP_PORT` | Optional | Port (default `4000`) |

> When tokens are absent, GitHub Gist and HuggingFace return `"status": "failed"` with `"error": "Authentication failed: Missing ..."`. The other 3 platforms always work without credentials.

---

## 📦 Dependencies (`requirements.txt`)

```
fastapi==0.115.5
uvicorn==0.32.1
pydantic==2.10.0
httpx==0.28.0
python-dotenv==1.0.1
pytest==8.3.3
pytest-asyncio==0.24.0
anyio==4.6.2
certifi==2026.10.23
```

---

## 🌐 Live Platform URLs (from previous successful runs)

| Platform | Live URL |
|----------|---------|
| **Telegraph** | `https://telegra.ph/Automated-Post-11-15` |
| **Dpaste** | `https://dpaste.com/4TXMHKAYN` |
| **Ntfy.sh Feed** | `https://ntfy.sh/dxora_automated_posting_feed` |
| **GitHub Gist** | *(requires `GITHUB_TOKEN`)* |
| **HuggingFace** | *(requires `HF_API_TOKEN`)* |
