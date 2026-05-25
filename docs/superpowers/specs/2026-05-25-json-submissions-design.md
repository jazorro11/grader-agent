# JSON Submissions Support

**Date:** 2026-05-25  
**Status:** Approved  

## Summary

Add `.json` as a valid student submission format alongside `.pdf`. JSON files are serialized to plain text and graded through the existing criteria-based (PDF) pipeline. No new grading logic is introduced — only a new extractor and a dispatch step.

---

## Architecture

The change follows the existing two-layer split:

- **`src/grader_agent/grading/pdf.py`** — gains `extraer_texto_json`, a peer to `extraer_texto_pdf`
- **`app/routes.py`** — dispatch by file extension before calling the grading pipeline; text extraction is done in the route, not inside `calificar_entregable_pdf`
- **`app/templates/index.html`** — minimal UI changes: extended `accept` attribute and updated copy

`calificar_entregable_pdf` is refactored to accept pre-extracted `texto: str` instead of `ruta_pdf: str`, so extraction and grading are independently testable.

---

## Components

### `extraer_texto_json(ruta_json: str) -> str`

Location: `src/grader_agent/grading/pdf.py`

- Opens and parses the file with `json.load()`
- Serializes result with `json.dumps(data, ensure_ascii=False, indent=2)`
- Raises `ValueError` if the file is not valid JSON or if the serialized output is empty

### `calificar_entregable_pdf` — signature change

```python
# Before
def calificar_entregable_pdf(rubrica_md, ruta_pdf, nombre_alumno, *, criterios=None, metadatos_criterios=None)

# After
def calificar_entregable_pdf(rubrica_md, texto, nombre_alumno, *, criterios=None, metadatos_criterios=None)
```

The `finally` block that deletes `ruta_pdf` is removed from the function; callers (routes) are responsible for temp file cleanup, which they already do.

### Route `/calificar-entregable`

```
1. Save uploaded file to tempfile
2. Detect extension from filename
   - .pdf  → extraer_texto_pdf(ruta_tmp)
   - .json → extraer_texto_json(ruta_tmp)
   - other → 400 "Tipo de archivo no soportado. Usá .pdf o .json"
3. Call calificar_entregable_pdf(rubrica, texto, alumno)
4. Cleanup temp file (finally block, already present)
```

### Route `/calificar-carpeta-entregables`

Same dispatch logic per file. The `archivo_pdf` form field is renamed `archivo_entregable` in both JS and the route to avoid confusion.

### Frontend (`index.html`)

| Element | Before | After |
|---|---|---|
| `accept` on entregable input | `.pdf` | `.pdf,.json` |
| Hint paragraph | "PDF del estudiante (máx. 4 páginas)…" | "PDF (máx. 4 págs.) o JSON del estudiante." |
| JS filter in `construirLoteDesdeCarpeta` | `endsWith(".pdf")` | `endsWith(".pdf") \|\| endsWith(".json")` |
| Error messages in batch JS | "No hay ningún PDF…" | "No hay ningún PDF ni JSON…" |
| Form field name | `archivo_pdf` | `archivo_entregable` |
| `tipo` in JSON response | `"entregable_pdf"` | `"entregable"` (genérico para PDF y JSON) |
| `esResultadoPorCriterios` JS check | `r.tipo === "entregable_pdf" \|\| r.tipo === "informe_pdf"` | agrega `\|\| r.tipo === "entregable"` |

---

## Data Flow

```
Upload .json file
      │
      ▼
Route saves to tempfile
      │
      ▼
Detect extension → extraer_texto_json()
      │  serializes to indented JSON string
      ▼
calificar_entregable_pdf(rubrica, texto, alumno)
      │  (same pipeline as PDF: list criteria → score each → aggregate)
      ▼
JSON response: { alumno, tipo: "entregable", criterios[], total_obtenido, total_maximo }
```

---

## Error Handling

| Scenario | Response |
|---|---|
| Invalid JSON content | `ValueError` from extractor → caught by route → 400 |
| Empty JSON `{}` or `[]` | `ValueError("El JSON no contiene contenido evaluable")` → 400 |
| Unsupported extension | Explicit 400 "Tipo de archivo no soportado. Usá .pdf o .json" |
| OpenAI error | Existing `_api_error_response` handler → 502 |

---

## Testing

### New unit tests

**`tests/test_json_extractor.py`** (new file)

- `extraer_texto_json` with valid JSON dict → returns non-empty string containing serialized content
- `extraer_texto_json` with valid JSON array → same
- `extraer_texto_json` with invalid JSON bytes → raises `ValueError`
- `extraer_texto_json` with empty JSON `{}` → raises `ValueError`

### Updated tests

**`tests/test_pdf_grader.py`**

- Update calls to `calificar_entregable_pdf` to pass `texto` instead of `ruta_pdf`

**`tests/test_app_routes.py`**

- POST `/calificar-entregable` with `.json` file → calls `extraer_texto_json` and grading pipeline
- POST `/calificar-entregable` with `.txt` file → returns 400
- POST `/calificar-carpeta-entregables` with mixed `.pdf` + `.json` files → processes both

---

## Out of Scope

- Schema validation of the JSON (field names, nesting depth) — format is free-form
- Per-field grading (each JSON key mapped to a rubric criterion)
- Size limit beyond the existing 16 MB Flask cap
- Batch Moodle flow for JSON-only submissions (handled generically by the same dispatch)
