# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -e ".[dev]"
cp .env.example .env            # fill in OPENAI_API_KEY at minimum
```

## Commands

```bash
# Run the dev server
python -m app
# or
flask --app app:create_app run

# Run all unit tests (no API key needed)
pytest

# Run a single test file
pytest tests/test_text_grader.py

# Run integration tests (requires real OPENAI_API_KEY + network)
pytest -m integration
```

## Architecture

The project has two layers:

**`app/`** — Flask HTTP layer (`create_app`, routes, one HTML template). Routes validate inputs, call domain functions, and append JSON results to the data dir. `GraderPaths` (from `settings.py`) is stored on `app.config["GRADER_PATHS"]` and accessed in routes via `current_app.config`.

**`src/grader_agent/`** — Domain logic package:

| Module | Role |
|--------|------|
| `settings.py` | Env-backed config: paths, model names, API key validation |
| `grading_config.py` | Temperature and token-limit helpers; `CompletionKind` type |
| `llm/client_calls.py` | Single shared function `chat_completion_json_content` used by all grading paths |
| `prompts_loader.py` | Reads/caches `.md` prompts; some prompts are merged from base fragments at load time (lru_cache — restart server to reload edited prompts) |
| `grading/text.py` | Three-step text grading: locate rubric item → score → feedback |
| `grading/pdf.py` | PDF text extraction (PyMuPDF, max 4 pages) → list criteria → score each → aggregate |
| `grading/score_utils.py` | Snaps raw float scores to discrete rubric levels |
| `grading/rubric_blocks.py` | Formats the optional "levels" block injected into prompts |
| `transcription.py` | Audio → transcript via Whisper |
| `export_csv.py` | Converts batch PDF results to CSV |
| `moodle_paths.py` | Parses Moodle-style folder names into student metadata |
| `openai_retry.py` | Retry wrapper for 429 rate-limit errors |

**Prompts** live in `src/grader_agent/prompts/*.md`. Files prefixed `_base_*` and `_retro_*` are merged fragments; the rest are standalone system prompts. Override the whole directory with `GRADER_AGENT_PROMPTS_DIR`.

**Data** is written to `./data/` by default (`GRADER_DATA_DIR`): `rubrics/rubrica_activa.md` (active rubric) and `resultados.json` (grading log).

## Grading flows

**Text / Audio:** `calificar_respuesta` runs 3 sequential LLM calls — (1) locate rubric item + max score, (2) score, (3) feedback. Audio adds a Whisper transcription step before this.

**PDF:** `calificar_entregable_pdf` first extracts plain text, then calls `metadatos_criterios_desde_rubrica` to list all evaluable criteria, then calls `calificar_criterio_entregable` once per criterion. The batch endpoint pre-fetches criteria once and reuses them across all PDFs.

## Quality gate (from Cursor rules)

For any feature or bugfix:
1. **UI features** — spec with `experto-web-design` first.
2. **Implement** the change.
3. **QA (`experto-qa`)** — add/update tests covering happy path, edge cases, errors; run suite; summarize.
4. **Code review (`revisor-codigo`)** — structured report (executive summary, findings by severity, actionable improvements without behavior change).

A task is not closed until both QA and review are done with no unresolved critical/high findings.

## Test conventions

Tests mock the OpenAI client (`unittest.mock.patch`) so no live API calls are made. `conftest.py` sets `TESTING=true` and injects a fake API key. Integration tests (real API) are gated with `@pytest.mark.integration`.
