# Spec: Soporte de `.txt` y `.json` como submissions en modo batch y single-file

**Fecha:** 2026-05-25  
**Alcance:** Grader Agent — modo "Calificar carpeta de entregas" (batch Moodle) + entregable individual  
**Estado:** Aprobado por usuario

---

## Contexto

El pipeline de calificación admite actualmente cuatro tipos de entregable:

| Extensión | Servicio | DeliveryType |
|-----------|----------|--------------|
| `.pdf` | `PDFExtractionService` | `PDF_DELIVERABLE` |
| `.docx` | `PDFExtractionService` | `PDF_DELIVERABLE` |
| `.py` | `CodeNotebookExtractionService` | `CODE_DELIVERABLE` |
| `.ipynb` | `CodeNotebookExtractionService` | `CODE_DELIVERABLE` |

Los archivos `.txt` y `.json` (como submissions de alumno) no están soportados:

- `.txt` — ninguna capa lo maneja.
- `.json` — existe `extraer_texto_json()` en `grading/pdf.py` como función standalone, pero no está integrada en ningún servicio ni en el pipeline.

---

## Objetivo

Agregar `.txt` y `.json` como tipos de entregable válidos en:

1. El modo batch (`/calificar-carpeta-entregables`).
2. El modo single-file (`/calificar-entregable`).
3. El filtrado de archivos en el frontend (JS + `accept` attrs + textos de UI).

Ambas extensiones producen texto plano que el pipeline evalúa con la rúbrica multi-criterio, igual que PDF/DOCX.

---

## Diseño

### Nuevo `DeliveryType`

```python
# src/grader_agent/models.py
class DeliveryType(str, Enum):
    TEXT = "text"
    AUDIO = "audio"
    PDF_DELIVERABLE = "pdf_deliverable"
    CODE_DELIVERABLE = "code_deliverable"
    PLAIN_TEXT_DELIVERABLE = "plain_text_deliverable"  # nuevo
```

### Nuevo servicio: `PlainTextExtractionService`

Archivo: `src/grader_agent/services/plain_text_extraction.py`

Responsabilidad única: dado un path de archivo `.txt` o `.json`, devuelve `str` (texto plano) o `ErrorResult` (validación).

**Flujo `.txt`:**
1. Valida existencia del archivo (`Path.is_file()`).
2. Valida tamaño (`GRADER_CODE_MAX_BYTES`, default 200 KB).
3. Lee con `utf-8-sig` (maneja BOM de Windows).
4. Valida que no esté vacío.
5. Aplica límite de caracteres (`GRADER_CODE_MAX_CHARS`, default 80 000).
6. Devuelve texto.

**Flujo `.json`:**
1. Mismas validaciones de existencia y tamaño.
2. Lee bytes y decodifica `utf-8-sig`.
3. `json.loads()` — en `JSONDecodeError` devuelve `ErrorResult` con mensaje amigable.
4. Valida que el dato no sea falsy (`{}`, `[]`, `""`, `null`).
5. `json.dumps(data, ensure_ascii=False, indent=2)` como texto plano.
6. Aplica límite de caracteres.
7. Devuelve texto.

**Extensión desconocida:** devuelve `ErrorResult(ERROR_TYPE_VALIDATION, "Solo se aceptan .txt o .json para este tipo de entrega.")`.

**Env vars reutilizados** (mismos que código):
- `GRADER_CODE_MAX_BYTES` (default 200 000 bytes)
- `GRADER_CODE_MAX_CHARS` (default 80 000 chars)

No se agregan nuevas variables de entorno.

### Cambios en `pipeline.py`

#### `GradingPipeline.__init__`

Recibe nuevo parámetro:
```python
plain_text_extraction_service: PlainTextExtractionService
```

#### `_step1_acquire_text`

Nueva rama:
```python
if delivery == DeliveryType.PLAIN_TEXT_DELIVERABLE:
    out = self._plain_text.extract(request.content.strip(), request_id=request_id)
    if isinstance(out, ErrorResult):
        return out
    path = request.content.strip()
    return out, "", path
```

#### `_submission_body_heading`

Nueva rama para el heading que se inyecta al modelo:
```python
if delivery == DeliveryType.PLAIN_TEXT_DELIVERABLE:
    low = artifact_path.lower()
    if low.endswith(".json"):
        return "CONTENIDO JSON DEL ENTREGABLE"
    return "TEXTO PLANO DEL ENTREGABLE (TXT)"
```

El resto del pipeline (`_step4_grade_with_json_retries`, `_build_success_result`) ya cubre todos los tipos no-TEXT/AUDIO con `grade_pdf_submission_text` sin cambios.

### Cambios en `grading_http.py`

Nueva función:
```python
def build_plain_text_grading_request(
    *,
    rubric: str,
    student_name: str,
    file_path: str,
) -> GradingRequest:
    return GradingRequest(
        delivery_type=DeliveryType.PLAIN_TEXT_DELIVERABLE,
        content=file_path.strip(),
        student_name=student_name.strip() or "Alumno",
        rubric_content=rubric,
    )
```

### Cambios en `routes.py`

#### `_suffix_entregable_multimodal`

```python
for suf in (".pdf", ".docx", ".py", ".ipynb", ".txt", ".json"):
```

#### Rama de ruteo en `calificar_entregable` y batch loop

```python
if suf in (".pdf", ".docx"):
    pipe_req = build_pdf_grading_request(...)
elif suf in (".txt", ".json"):
    pipe_req = build_plain_text_grading_request(...)
else:
    pipe_req = build_code_deliverable_grading_request(...)
```

Los mensajes de error de extensión no permitida en batch se actualizan para mencionar `.txt` y `.json`.

### Cambios en `index.html`

1. `esExtensionEntregableMultimodal`:
   ```js
   return n.endsWith(".pdf") || n.endsWith(".docx") || n.endsWith(".py") || n.endsWith(".ipynb") || n.endsWith(".txt") || n.endsWith(".json");
   ```

2. Input de entregable individual:
   ```html
   accept=".pdf,.docx,.py,.ipynb,.txt,.json,..."
   ```

3. Textos descriptivos del modo batch y single-file: agregar `.txt` y `.json` junto a las otras extensiones.

4. Mensaje de error de validación JS: `"Solo se aceptan archivos .pdf, .docx, .py, .ipynb, .txt o .json"`.

5. Mensaje de error en batch sin entregables admitidos: actualizar para incluir `.txt` y `.json`.

### Cambios en `grading_pipeline_factory.py`

```python
from grader_agent.services.plain_text_extraction import PlainTextExtractionService

return GradingPipeline(
    ...
    plain_text_extraction_service=PlainTextExtractionService(),
)
```

---

## Manejo de errores

| Caso | Capa | Respuesta HTTP |
|------|------|----------------|
| `.txt` vacío | `PlainTextExtractionService` | 400 |
| `.txt` no UTF-8 | `PlainTextExtractionService` | 400 |
| `.json` malformado | `PlainTextExtractionService` | 400 (mensaje amigable) |
| `.json` vacío (`{}`, `[]`) | `PlainTextExtractionService` | 400 |
| Archivo > `GRADER_CODE_MAX_BYTES` | `PlainTextExtractionService` | 400 |
| Texto > `GRADER_CODE_MAX_CHARS` | `PlainTextExtractionService` | 400 |
| Extensión no permitida (batch) | `routes.py` | entrada en `errores[]` |
| Extensión no permitida (single) | `routes.py` | 400 |

---

## Tests

### `tests/test_plain_text_extraction.py`

Unitarios sin API key (mock de filesystem con `tmp_path`):

- **`.txt` happy path** — archivo válido devuelve el texto.
- **`.txt` vacío** — devuelve `ErrorResult`.
- **`.txt` no UTF-8** — bytes inválidos devuelven `ErrorResult`.
- **`.txt` demasiado grande** — supera `GRADER_CODE_MAX_BYTES` → `ErrorResult`.
- **`.txt` texto > `GRADER_CODE_MAX_CHARS`** — `ErrorResult`.
- **`.json` happy path** — JSON válido devuelve texto indentado.
- **`.json` inválido** — `JSONDecodeError` → `ErrorResult` con mensaje amigable.
- **`.json` vacío** (`{}`, `[]`, `""`, `null`) — `ErrorResult`.
- **`.json` demasiado grande** — `ErrorResult`.
- **Extensión desconocida** (`.csv`) — `ErrorResult`.

### `tests/test_routes_txt_json.py`

Flask test client con pipeline mockeado:

- `POST /calificar-entregable` con `.txt` → llama `build_plain_text_grading_request`.
- `POST /calificar-entregable` con `.json` → llama `build_plain_text_grading_request`.
- `POST /calificar-entregable` con `.csv` → 400.
- `POST /calificar-carpeta-entregables` con `.txt` en batch → resultado en `resultados`.
- `POST /calificar-carpeta-entregables` con `.json` en batch → resultado en `resultados`.
- Extensión no permitida en batch → entrada en `errores`.

---

## Puntos de toque (resumen)

```
src/grader_agent/models.py                          (+1 línea)
src/grader_agent/services/plain_text_extraction.py  (nuevo, ~90 líneas)
src/grader_agent/pipeline.py                        (+~15 líneas)
app/grading_http.py                                 (+~12 líneas)
app/routes.py                                       (+~8 líneas)
app/templates/index.html                            (+~8 líneas)
app/grading_pipeline_factory.py                     (+~3 líneas)
tests/test_plain_text_extraction.py                 (nuevo, ~120 líneas)
tests/test_routes_txt_json.py                       (nuevo, ~80 líneas)
```

**Total estimado:** ~340 líneas netas.

---

## Fuera de alcance

- `.json` como rúbrica (ya soportado en el input de rubric).
- Límites de tamaño dedicados para `.txt`/`.json` (se reutilizan `GRADER_CODE_MAX_*`).
- Soporte de encodings distintos de UTF-8 (`.txt` en latin-1, etc.).
- Preview/diff de contenido extraído en la UI.
