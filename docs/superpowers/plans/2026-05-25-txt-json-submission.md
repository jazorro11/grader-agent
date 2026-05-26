# Soporte de .txt y .json como submissions — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Agregar `.txt` y `.json` como tipos de entregable válidos en el modo batch de Moodle y el modo single-file, usando un nuevo `DeliveryType.PLAIN_TEXT_DELIVERABLE` y un `PlainTextExtractionService` dedicado.

**Architecture:** Se crea `PlainTextExtractionService` (análogo a `CodeNotebookExtractionService`) que lee `.txt` (UTF-8) y `.json` (parse + dump indentado). Se agrega `PLAIN_TEXT_DELIVERABLE` al enum `DeliveryType`, se cablea en el pipeline, se agrega un builder en `grading_http.py`, se actualizan las rutas Flask y el frontend.

**Tech Stack:** Python 3.11+, Flask, pytest, stdlib (`json`, `pathlib`)

---

## Mapa de archivos

| Acción | Archivo |
|--------|---------|
| Modificar | `src/grader_agent/models.py` |
| Crear | `src/grader_agent/services/plain_text_extraction.py` |
| Modificar | `src/grader_agent/pipeline.py` |
| Modificar | `app/grading_http.py` |
| Modificar | `app/routes.py` |
| Modificar | `app/grading_pipeline_factory.py` |
| Modificar | `app/templates/index.html` |
| Crear | `tests/test_plain_text_extraction.py` |
| Crear | `tests/test_routes_txt_json.py` |

---

## Task 1: Agregar `PLAIN_TEXT_DELIVERABLE` al enum

**Files:**
- Modify: `src/grader_agent/models.py`

- [ ] **Step 1: Agregar el nuevo valor al enum**

En `src/grader_agent/models.py`, el bloque `DeliveryType` actualmente termina en `CODE_DELIVERABLE`. Agregar la línea nueva:

```python
class DeliveryType(str, Enum):
    TEXT = "text"
    AUDIO = "audio"
    PDF_DELIVERABLE = "pdf_deliverable"
    CODE_DELIVERABLE = "code_deliverable"
    PLAIN_TEXT_DELIVERABLE = "plain_text_deliverable"   # ← nueva línea
```

- [ ] **Step 2: Verificar que el módulo carga sin errores**

```bash
python -c "from grader_agent.models import DeliveryType; print(DeliveryType.PLAIN_TEXT_DELIVERABLE.value)"
```

Salida esperada: `plain_text_deliverable`

- [ ] **Step 3: Commit**

```bash
git add src/grader_agent/models.py
git -c skill.commit=true commit -m "feat(models): add PLAIN_TEXT_DELIVERABLE delivery type"
```

---

## Task 2: Implementar `PlainTextExtractionService` (TDD)

**Files:**
- Create: `src/grader_agent/services/plain_text_extraction.py`
- Create: `tests/test_plain_text_extraction.py`

- [ ] **Step 1: Escribir los tests primero**

Crear `tests/test_plain_text_extraction.py` con el siguiente contenido completo:

```python
"""Tests para PlainTextExtractionService (sin API)."""
from __future__ import annotations

import json

import pytest

from grader_agent.models import ERROR_TYPE_VALIDATION, ErrorResult
from grader_agent.services.plain_text_extraction import PlainTextExtractionService


@pytest.fixture
def svc():
    return PlainTextExtractionService()


# ---------------------------------------------------------------------------
# .txt — caminos felices
# ---------------------------------------------------------------------------


def test_txt_happy_path(svc, tmp_path):
    p = tmp_path / "ensayo.txt"
    p.write_text("Hola mundo\nSegunda línea.\n", encoding="utf-8")
    out = svc.extract(str(p))
    assert isinstance(out, str)
    assert "Hola mundo" in out
    assert "Segunda línea" in out


def test_txt_bom_utf8_se_procesa(svc, tmp_path):
    # UTF-8 con BOM (common en Windows Notepad)
    p = tmp_path / "bom.txt"
    p.write_bytes(b"\xef\xbb\xbfContenido con BOM")
    out = svc.extract(str(p))
    assert isinstance(out, str)
    assert out.startswith("Contenido con BOM")


# ---------------------------------------------------------------------------
# .txt — errores
# ---------------------------------------------------------------------------


def test_txt_vacio_devuelve_error(svc, tmp_path):
    p = tmp_path / "empty.txt"
    p.write_text("   \n\t\n", encoding="utf-8")
    out = svc.extract(str(p))
    assert isinstance(out, ErrorResult)
    assert out.error_type == ERROR_TYPE_VALIDATION


def test_txt_no_utf8_devuelve_error(svc, tmp_path):
    p = tmp_path / "latin.txt"
    # bytes inválidos para UTF-8 (y para utf-8-sig)
    p.write_bytes(b"\x80\x81\x82")
    out = svc.extract(str(p))
    assert isinstance(out, ErrorResult)
    assert out.error_type == ERROR_TYPE_VALIDATION
    assert "utf" in out.message.lower() or "válido" in out.message.lower()


def test_txt_supera_max_bytes_devuelve_error(svc, monkeypatch, tmp_path):
    monkeypatch.setenv("GRADER_CODE_MAX_BYTES", "2048")
    p = tmp_path / "big.txt"
    p.write_bytes(b"x" * 3000)
    out = svc.extract(str(p))
    assert isinstance(out, ErrorResult)
    assert out.error_type == ERROR_TYPE_VALIDATION
    assert "bytes" in out.message.lower()


def test_txt_supera_max_chars_devuelve_error(svc, monkeypatch, tmp_path):
    monkeypatch.setenv("GRADER_CODE_MAX_CHARS", "5000")
    p = tmp_path / "long.txt"
    p.write_text("x" * 6000, encoding="utf-8")
    out = svc.extract(str(p))
    assert isinstance(out, ErrorResult)
    assert out.error_type == ERROR_TYPE_VALIDATION
    assert "caracteres" in out.message.lower()


# ---------------------------------------------------------------------------
# .json — caminos felices
# ---------------------------------------------------------------------------


def test_json_happy_path(svc, tmp_path):
    payload = {"respuesta": "hola", "criterio": "ortografía"}
    p = tmp_path / "sub.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    out = svc.extract(str(p))
    assert isinstance(out, str)
    assert '"respuesta"' in out
    assert '"ortografía"' in out


def test_json_lista_no_vacia(svc, tmp_path):
    p = tmp_path / "lista.json"
    p.write_text(json.dumps([{"a": 1}, {"b": 2}]), encoding="utf-8")
    out = svc.extract(str(p))
    assert isinstance(out, str)
    assert '"a"' in out


def test_json_bom_utf8(svc, tmp_path):
    p = tmp_path / "bom.json"
    content = b"\xef\xbb\xbf" + json.dumps({"k": "v"}).encode("utf-8")
    p.write_bytes(content)
    out = svc.extract(str(p))
    assert isinstance(out, str)
    assert '"k"' in out


# ---------------------------------------------------------------------------
# .json — errores
# ---------------------------------------------------------------------------


def test_json_invalido_devuelve_error(svc, tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{no es json", encoding="utf-8")
    out = svc.extract(str(p))
    assert isinstance(out, ErrorResult)
    assert out.error_type == ERROR_TYPE_VALIDATION
    assert "json" in out.message.lower()


def test_json_dict_vacio_devuelve_error(svc, tmp_path):
    p = tmp_path / "empty_dict.json"
    p.write_text("{}", encoding="utf-8")
    out = svc.extract(str(p))
    assert isinstance(out, ErrorResult)
    assert out.error_type == ERROR_TYPE_VALIDATION


def test_json_lista_vacia_devuelve_error(svc, tmp_path):
    p = tmp_path / "empty_list.json"
    p.write_text("[]", encoding="utf-8")
    out = svc.extract(str(p))
    assert isinstance(out, ErrorResult)
    assert out.error_type == ERROR_TYPE_VALIDATION


def test_json_null_devuelve_error(svc, tmp_path):
    p = tmp_path / "null.json"
    p.write_text("null", encoding="utf-8")
    out = svc.extract(str(p))
    assert isinstance(out, ErrorResult)
    assert out.error_type == ERROR_TYPE_VALIDATION


def test_json_supera_max_bytes_devuelve_error(svc, monkeypatch, tmp_path):
    monkeypatch.setenv("GRADER_CODE_MAX_BYTES", "2048")
    p = tmp_path / "big.json"
    p.write_bytes(b'{"k":"' + b"x" * 3000 + b'"}')
    out = svc.extract(str(p))
    assert isinstance(out, ErrorResult)
    assert out.error_type == ERROR_TYPE_VALIDATION
    assert "bytes" in out.message.lower()


# ---------------------------------------------------------------------------
# General
# ---------------------------------------------------------------------------


def test_ruta_vacia_devuelve_error(svc):
    out = svc.extract("  ")
    assert isinstance(out, ErrorResult)
    assert out.error_type == ERROR_TYPE_VALIDATION


def test_archivo_inexistente_devuelve_error(svc, tmp_path):
    out = svc.extract(str(tmp_path / "missing.txt"))
    assert isinstance(out, ErrorResult)
    assert out.error_type == ERROR_TYPE_VALIDATION


def test_extension_desconocida_devuelve_error(svc, tmp_path):
    p = tmp_path / "datos.csv"
    p.write_text("a,b,c\n1,2,3\n", encoding="utf-8")
    out = svc.extract(str(p))
    assert isinstance(out, ErrorResult)
    assert out.error_type == ERROR_TYPE_VALIDATION
    assert ".csv" in (out.detail or "")
```

- [ ] **Step 2: Verificar que los tests fallan (el módulo no existe aún)**

```bash
pytest tests/test_plain_text_extraction.py -v 2>&1 | head -20
```

Salida esperada: `ModuleNotFoundError: No module named 'grader_agent.services.plain_text_extraction'`

- [ ] **Step 3: Implementar el servicio**

Crear `src/grader_agent/services/plain_text_extraction.py`:

```python
"""Plain-text submission extraction: reads .txt (UTF-8) and .json submissions."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Union

from grader_agent.grading_config import code_max_bytes, code_max_chars
from grader_agent.models import ERROR_TYPE_VALIDATION, ErrorResult

_logger = logging.getLogger(__name__)


class PlainTextExtractionService:
    """Reads .txt or .json submission files and returns plain text for grading."""

    def extract(self, file_path: str, *, request_id: str | None = None) -> Union[str, ErrorResult]:
        if request_id:
            _logger.debug("plain_text_extract request_id=%s path=%s", request_id, file_path)
        path = (file_path or "").strip()
        if not path:
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="La ruta del archivo de texto está vacía.",
                detail=None,
            )
        p = Path(path)
        if not p.is_file():
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="El archivo de entrega no existe o no es un archivo regular.",
                detail=path,
            )
        try:
            st = p.stat()
        except OSError as exc:
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="No se pudo acceder al archivo de entrega.",
                detail=str(exc),
            )
        max_b = code_max_bytes()
        if st.st_size > max_b:
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message=(
                    f"El archivo supera el tamaño máximo permitido "
                    f"({max_b} bytes). Reducí el entregable o subí GRADER_CODE_MAX_BYTES."
                ),
                detail=None,
            )
        suffix = p.suffix.lower()
        if suffix == ".txt":
            return self._extract_txt(p)
        if suffix == ".json":
            return self._extract_json(p)
        return ErrorResult(
            error_type=ERROR_TYPE_VALIDATION,
            message="Solo se aceptan archivos .txt o .json para este tipo de entrega.",
            detail=suffix,
        )

    def _apply_char_limit(self, text: str) -> str | ErrorResult:
        max_c = code_max_chars()
        if len(text) <= max_c:
            return text
        return ErrorResult(
            error_type=ERROR_TYPE_VALIDATION,
            message=(
                f"El texto extraído supera el máximo de {max_c} caracteres. "
                "Acotá el archivo o subí GRADER_CODE_MAX_CHARS."
            ),
            detail=None,
        )

    def _extract_txt(self, path: Path) -> str | ErrorResult:
        try:
            raw_bytes = path.read_bytes()
        except OSError as exc:
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="No se pudo leer el archivo de texto.",
                detail=str(exc),
            )
        try:
            text = raw_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="El archivo .txt no es UTF-8 válido.",
                detail=None,
            )
        text = text.strip()
        if not text:
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="El archivo .txt está vacío o solo tiene espacios.",
                detail=None,
            )
        return self._apply_char_limit(text)

    def _extract_json(self, path: Path) -> str | ErrorResult:
        try:
            raw_bytes = path.read_bytes()
        except OSError as exc:
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="No se pudo leer el archivo JSON.",
                detail=str(exc),
            )
        try:
            text = raw_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="El archivo .json no es UTF-8 válido.",
                detail=None,
            )
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="El archivo no es JSON válido. Verificá que el entregable esté bien formado.",
                detail=str(exc),
            )
        if not data:
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="El JSON no contiene contenido evaluable.",
                detail=None,
            )
        serialized = json.dumps(data, ensure_ascii=False, indent=2)
        return self._apply_char_limit(serialized)


__all__ = ["PlainTextExtractionService"]
```

- [ ] **Step 4: Correr los tests y verificar que pasan**

```bash
pytest tests/test_plain_text_extraction.py -v
```

Salida esperada: todos los tests en `PASSED`. Cero fallos.

- [ ] **Step 5: Commit**

```bash
git add src/grader_agent/services/plain_text_extraction.py tests/test_plain_text_extraction.py
git -c skill.commit=true commit -m "feat(services): add PlainTextExtractionService for .txt and .json submissions"
```

---

## Task 3: Cablear el servicio en el pipeline

**Files:**
- Modify: `src/grader_agent/pipeline.py`

- [ ] **Step 1: Agregar el import de `PlainTextExtractionService`**

En `src/grader_agent/pipeline.py`, el bloque de imports de servicios actualmente importa:

```python
from grader_agent.services.code_notebook_extraction import CodeNotebookExtractionService
from grader_agent.services.pdf_extraction import PDFExtractionService
```

Agregar a continuación:

```python
from grader_agent.services.plain_text_extraction import PlainTextExtractionService
```

- [ ] **Step 2: Agregar parámetro y atributo en `__init__`**

El `__init__` actual termina en:

```python
        feedback: FeedbackService,
        research: RubricResearchService | None = None,
    ) -> None:
        """Wire all pipeline stages; callers typically use ``create_grading_pipeline``."""
        self._transcription = transcription_service
        self._pdf = pdf_extraction_service
        self._code_nb = code_notebook_extraction_service
```

Reemplazar la firma y asignaciones por:

```python
        feedback: FeedbackService,
        plain_text_extraction_service: PlainTextExtractionService,
        research: RubricResearchService | None = None,
    ) -> None:
        """Wire all pipeline stages; callers typically use ``create_grading_pipeline``."""
        self._transcription = transcription_service
        self._pdf = pdf_extraction_service
        self._code_nb = code_notebook_extraction_service
        self._plain_text = plain_text_extraction_service
```

- [ ] **Step 3: Agregar rama en `_step1_acquire_text`**

La función `_step1_acquire_text` termina con el bloque para `CODE_DELIVERABLE` y luego el fallback de error. Agregar la nueva rama **antes** del fallback final:

```python
        if delivery == DeliveryType.CODE_DELIVERABLE:
            out = self._code_nb.extract(request.content.strip(), request_id=request_id)
            if isinstance(out, ErrorResult):
                return out
            path = request.content.strip()
            return out, "", path

        if delivery == DeliveryType.PLAIN_TEXT_DELIVERABLE:
            out = self._plain_text.extract(request.content.strip(), request_id=request_id)
            if isinstance(out, ErrorResult):
                return out
            path = request.content.strip()
            return out, "", path

        return ErrorResult(
            error_type=ERROR_TYPE_VALIDATION,
            message="Tipo de entrega no soportado.",
            detail=str(delivery),
        )
```

- [ ] **Step 4: Agregar caso en `_submission_body_heading`**

La función `_submission_body_heading` actualmente:

```python
def _submission_body_heading(delivery: DeliveryType, artifact_path: str) -> str:
    """Encabezado del bloque de entrega en el prompt de calificación multi-criterio."""
    if delivery == DeliveryType.PDF_DELIVERABLE:
        low = (artifact_path or "").lower()
        if low.endswith(".docx"):
            return "TEXTO PLANO DEL ENTREGABLE (DOCX)"
        return "TEXTO PLANO DEL ENTREGABLE (PDF)"
    if delivery == DeliveryType.CODE_DELIVERABLE:
        low = artifact_path.lower()
        if low.endswith(".ipynb"):
            return "CONTENIDO EXTRAÍDO DEL NOTEBOOK (celdas de código, en orden)"
        return "CÓDIGO FUENTE DEL ARCHIVO PYTHON"
    return "TEXTO PLANO DEL ENTREGABLE (PDF)"
```

Reemplazar por:

```python
def _submission_body_heading(delivery: DeliveryType, artifact_path: str) -> str:
    """Encabezado del bloque de entrega en el prompt de calificación multi-criterio."""
    if delivery == DeliveryType.PDF_DELIVERABLE:
        low = (artifact_path or "").lower()
        if low.endswith(".docx"):
            return "TEXTO PLANO DEL ENTREGABLE (DOCX)"
        return "TEXTO PLANO DEL ENTREGABLE (PDF)"
    if delivery == DeliveryType.CODE_DELIVERABLE:
        low = artifact_path.lower()
        if low.endswith(".ipynb"):
            return "CONTENIDO EXTRAÍDO DEL NOTEBOOK (celdas de código, en orden)"
        return "CÓDIGO FUENTE DEL ARCHIVO PYTHON"
    if delivery == DeliveryType.PLAIN_TEXT_DELIVERABLE:
        low = (artifact_path or "").lower()
        if low.endswith(".json"):
            return "CONTENIDO JSON DEL ENTREGABLE"
        return "TEXTO PLANO DEL ENTREGABLE (TXT)"
    return "TEXTO PLANO DEL ENTREGABLE (PDF)"
```

- [ ] **Step 5: Correr tests existentes del pipeline para verificar que no se rompió nada**

```bash
pytest tests/test_pipeline.py -v
```

Salida esperada: todos los tests en `PASSED`. Si alguno falla con `TypeError: __init__() missing ... 'plain_text_extraction_service'`, es porque el factory aún no fue actualizado — eso se hace en Task 5. Los tests del pipeline que instancian `GradingPipeline` directamente sí requieren el nuevo parámetro; ver si aplica.

> **Nota:** Si `test_pipeline.py` instancia `GradingPipeline` directamente, agregar `plain_text_extraction_service=PlainTextExtractionService()` en esas instancias antes de seguir.

- [ ] **Step 6: Commit**

```bash
git add src/grader_agent/pipeline.py
git -c skill.commit=true commit -m "feat(pipeline): wire PlainTextExtractionService for PLAIN_TEXT_DELIVERABLE"
```

---

## Task 4: Builder HTTP + rutas Flask + tests de rutas

**Files:**
- Modify: `app/grading_http.py`
- Modify: `app/routes.py`
- Create: `tests/test_routes_txt_json.py`

- [ ] **Step 1: Agregar `build_plain_text_grading_request` en `grading_http.py`**

En `app/grading_http.py`, el bloque de imports al inicio:

```python
from grader_agent.models import (
    ERROR_TYPE_OPENAI,
    ERROR_TYPE_RUBRIC,
    ERROR_TYPE_VALIDATION,
    CriterionScore,
    DeliveryType,
    ErrorResult,
    GradingRequest,
    GradingResult,
)
```

No requiere cambios (ya importa `DeliveryType` y `GradingRequest`).

Al final del archivo, después de `build_code_deliverable_grading_request`, agregar:

```python
def build_plain_text_grading_request(
    *,
    rubric: str,
    student_name: str,
    file_path: str,
) -> GradingRequest:
    """Build a ``PLAIN_TEXT_DELIVERABLE`` request (``.txt`` / ``.json``) whose ``content`` is the file path."""
    return GradingRequest(
        delivery_type=DeliveryType.PLAIN_TEXT_DELIVERABLE,
        content=file_path.strip(),
        student_name=student_name.strip() or "Alumno",
        rubric_content=rubric,
    )
```

- [ ] **Step 2: Actualizar `routes.py` — import**

En `app/routes.py`, la línea de imports de `app.grading_http`:

```python
from app.grading_http import (
    build_audio_grading_request,
    build_code_deliverable_grading_request,
    build_pdf_grading_request,
    build_text_grading_request,
    ...
)
```

Agregar `build_plain_text_grading_request` a la lista:

```python
from app.grading_http import (
    build_audio_grading_request,
    build_code_deliverable_grading_request,
    build_pdf_grading_request,
    build_plain_text_grading_request,
    build_text_grading_request,
    error_result_http_response,
    grading_rejection_message,
    grading_result_rejection_http_response,
    grading_result_to_pdf_ui_dict,
    grading_result_to_text_audio_ui_dict,
    run_grading_request,
)
```

- [ ] **Step 3: Actualizar `_suffix_entregable_multimodal` en `routes.py`**

Función actual:

```python
def _suffix_entregable_multimodal(filename: str) -> str | None:
    """Sufijo temporal válido para PDF, Word, Python o Jupyter; ``None`` si no está permitido."""
    low = (filename or "").lower()
    for suf in (".pdf", ".docx", ".py", ".ipynb"):
        if low.endswith(suf):
            return suf
    return None
```

Reemplazar por:

```python
def _suffix_entregable_multimodal(filename: str) -> str | None:
    """Sufijo temporal válido para PDF, Word, Python, Jupyter, texto plano o JSON; ``None`` si no está permitido."""
    low = (filename or "").lower()
    for suf in (".pdf", ".docx", ".py", ".ipynb", ".txt", ".json"):
        if low.endswith(suf):
            return suf
    return None
```

- [ ] **Step 4: Actualizar rama de ruteo en `calificar_entregable` (single-file)**

En la ruta `calificar_entregable`, el bloque actual es:

```python
        suf = _suffix_entregable_multimodal(archivo.filename or "")
        if suf is None:
            return jsonify({"error": "Solo se aceptan archivos .pdf, .docx, .py o .ipynb"}), 400
```

Reemplazar el mensaje de error:

```python
        suf = _suffix_entregable_multimodal(archivo.filename or "")
        if suf is None:
            return jsonify({"error": "Solo se aceptan archivos .pdf, .docx, .py, .ipynb, .txt o .json"}), 400
```

Y el bloque de ruteo dentro del `try`:

```python
            if suf in (".pdf", ".docx"):
                pipe_req = build_pdf_grading_request(
                    rubric=rubrica,
                    student_name=nombre_alumno,
                    pdf_path=ruta_tmp,
                )
            else:
                pipe_req = build_code_deliverable_grading_request(
                    rubric=rubrica,
                    student_name=nombre_alumno,
                    file_path=ruta_tmp,
                )
```

Reemplazar por:

```python
            if suf in (".pdf", ".docx"):
                pipe_req = build_pdf_grading_request(
                    rubric=rubrica,
                    student_name=nombre_alumno,
                    pdf_path=ruta_tmp,
                )
            elif suf in (".txt", ".json"):
                pipe_req = build_plain_text_grading_request(
                    rubric=rubrica,
                    student_name=nombre_alumno,
                    file_path=ruta_tmp,
                )
            else:
                pipe_req = build_code_deliverable_grading_request(
                    rubric=rubrica,
                    student_name=nombre_alumno,
                    file_path=ruta_tmp,
                )
```

- [ ] **Step 5: Actualizar rama de ruteo en `calificar_carpeta_entregables` (batch)**

Dentro del loop `for i in range(n):`, la sección de validación de sufijo:

```python
            suf = _suffix_entregable_multimodal(sub.filename or "")
            if suf is None:
                errores.append(
                    {
                        "alumno": alumno,
                        "carpeta_origen": carpeta,
                        "error": "Extensión no permitida (solo .pdf, .docx, .py o .ipynb).",
                    }
                )
                continue
```

Actualizar el mensaje de error:

```python
            suf = _suffix_entregable_multimodal(sub.filename or "")
            if suf is None:
                errores.append(
                    {
                        "alumno": alumno,
                        "carpeta_origen": carpeta,
                        "error": "Extensión no permitida (solo .pdf, .docx, .py, .ipynb, .txt o .json).",
                    }
                )
                continue
```

Y el bloque de ruteo dentro del `try` interno del batch:

```python
                    if suf in (".pdf", ".docx"):
                        pipe_req = build_pdf_grading_request(
                            rubric=rubrica,
                            student_name=alumno,
                            pdf_path=ruta_tmp,
                        )
                    else:
                        pipe_req = build_code_deliverable_grading_request(
                            rubric=rubrica,
                            student_name=alumno,
                            file_path=ruta_tmp,
                        )
```

Reemplazar por:

```python
                    if suf in (".pdf", ".docx"):
                        pipe_req = build_pdf_grading_request(
                            rubric=rubrica,
                            student_name=alumno,
                            pdf_path=ruta_tmp,
                        )
                    elif suf in (".txt", ".json"):
                        pipe_req = build_plain_text_grading_request(
                            rubric=rubrica,
                            student_name=alumno,
                            file_path=ruta_tmp,
                        )
                    else:
                        pipe_req = build_code_deliverable_grading_request(
                            rubric=rubrica,
                            student_name=alumno,
                            file_path=ruta_tmp,
                        )
```

También actualizar el mensaje de error en la respuesta inicial del endpoint batch:

```python
        if not archivos_subida:
            return jsonify({"error": "No se recibieron archivos de entrega (.pdf, .docx, .py, .ipynb, .txt o .json)"}), 400
```

- [ ] **Step 6: Escribir los tests de rutas**

Crear `tests/test_routes_txt_json.py`:

```python
"""Tests de rutas Flask para entregables .txt y .json (sin API real)."""
from __future__ import annotations

import json
from io import BytesIO
from unittest.mock import patch

import app.routes as routes_module
from grader_agent.models import CriterionScore, GradingResult
from tests.conftest import write_rubrica_parcial


def _fake_grading_result(alumno: str = "Ana") -> GradingResult:
    return GradingResult(
        scores_by_criterion={"Criterio 1": CriterionScore(8.0, 10.0, "Bien")},
        total_score=8.0,
        total_max_score=10.0,
        feedback="Buen trabajo.",
        student_name=alumno,
        item_label=None,
        transcription=None,
        deliverable_kind="plain_text_deliverable",
        status="success",
        rejection=None,
    )


# ---------------------------------------------------------------------------
# Single-file: /calificar-entregable
# ---------------------------------------------------------------------------


@patch.object(routes_module, "run_grading_request")
def test_entregable_txt_es_aceptado(mock_run, app_client):
    write_rubrica_parcial(app_client["rubrics"])
    mock_run.return_value = _fake_grading_result("Luis")
    rv = app_client["client"].post(
        "/calificar-entregable",
        data={
            "alumno": "Luis",
            "entregable": (BytesIO(b"Este es mi ensayo.\n"), "entrega.txt"),
        },
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["alumno"] == "Luis"
    assert body["total_obtenido"] == 8.0
    mock_run.assert_called_once()


@patch.object(routes_module, "run_grading_request")
def test_entregable_json_es_aceptado(mock_run, app_client):
    write_rubrica_parcial(app_client["rubrics"])
    mock_run.return_value = _fake_grading_result("Maria")
    payload = json.dumps({"respuesta": "Mi respuesta completa."}).encode("utf-8")
    rv = app_client["client"].post(
        "/calificar-entregable",
        data={
            "alumno": "Maria",
            "entregable": (BytesIO(payload), "entrega.json"),
        },
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["alumno"] == "Maria"
    mock_run.assert_called_once()


def test_entregable_csv_es_rechazado(app_client):
    write_rubrica_parcial(app_client["rubrics"])
    rv = app_client["client"].post(
        "/calificar-entregable",
        data={
            "alumno": "Pedro",
            "entregable": (BytesIO(b"a,b,c\n1,2,3\n"), "datos.csv"),
        },
        content_type="multipart/form-data",
    )
    assert rv.status_code == 400
    body = rv.get_json()
    assert "error" in body
    assert ".csv" not in body["error"].lower() or "no" in body["error"].lower()


def test_entregable_sin_rubrica_devuelve_400(app_client):
    rv = app_client["client"].post(
        "/calificar-entregable",
        data={
            "alumno": "Pedro",
            "entregable": (BytesIO(b"Texto de ensayo."), "ensayo.txt"),
        },
        content_type="multipart/form-data",
    )
    assert rv.status_code == 400
    body = rv.get_json()
    assert "rúbrica" in body["error"].lower()


# ---------------------------------------------------------------------------
# Batch: /calificar-carpeta-entregables
# ---------------------------------------------------------------------------


@patch.object(routes_module, "run_grading_request")
@patch("app.routes.metadatos_criterios_desde_rubrica")
def test_batch_txt_aparece_en_resultados(mock_meta, mock_run, app_client):
    write_rubrica_parcial(app_client["rubrics"])
    mock_meta.return_value = [{"criterio": "Criterio 1", "puntaje_maximo": 10.0}]
    mock_run.return_value = _fake_grading_result("Carlos")

    rv = app_client["client"].post(
        "/calificar-carpeta-entregables",
        data={
            "entregable": (BytesIO(b"Mi ensayo en texto.\n"), "entrega.txt"),
            "alumno": "Carlos",
            "nombre_completo": "Carlos López",
            "id_estudiante": "12345",
            "carpeta_origen": "",
            "archivo_entregable": "entrega.txt",
        },
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert len(body["resultados"]) == 1
    assert body["errores"] == []
    assert body["resultados"][0]["alumno"] == "Carlos"


@patch.object(routes_module, "run_grading_request")
@patch("app.routes.metadatos_criterios_desde_rubrica")
def test_batch_json_aparece_en_resultados(mock_meta, mock_run, app_client):
    write_rubrica_parcial(app_client["rubrics"])
    mock_meta.return_value = [{"criterio": "Criterio 1", "puntaje_maximo": 10.0}]
    mock_run.return_value = _fake_grading_result("Sofía")
    payload = json.dumps({"respuesta": "respuesta JSON"}).encode("utf-8")

    rv = app_client["client"].post(
        "/calificar-carpeta-entregables",
        data={
            "entregable": (BytesIO(payload), "entrega.json"),
            "alumno": "Sofía",
            "nombre_completo": "Sofía Gómez",
            "id_estudiante": "67890",
            "carpeta_origen": "",
            "archivo_entregable": "entrega.json",
        },
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert len(body["resultados"]) == 1
    assert body["errores"] == []


@patch("app.routes.metadatos_criterios_desde_rubrica")
def test_batch_extension_invalida_aparece_en_errores(mock_meta, app_client):
    write_rubrica_parcial(app_client["rubrics"])
    mock_meta.return_value = [{"criterio": "Criterio 1", "puntaje_maximo": 10.0}]

    rv = app_client["client"].post(
        "/calificar-carpeta-entregables",
        data={
            "entregable": (BytesIO(b"a,b,c"), "datos.csv"),
            "alumno": "Pedro",
            "nombre_completo": "",
            "id_estudiante": "",
            "carpeta_origen": "",
            "archivo_entregable": "datos.csv",
        },
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["resultados"] == []
    assert len(body["errores"]) == 1
    assert "pedro" in body["errores"][0]["alumno"].lower()
```

- [ ] **Step 7: Correr los tests de rutas**

```bash
pytest tests/test_routes_txt_json.py -v
```

Salida esperada: todos los tests en `PASSED`.

- [ ] **Step 8: Correr el conjunto completo de tests de rutas existentes para verificar regresiones**

```bash
pytest tests/test_app_routes.py -v
```

Salida esperada: todos en `PASSED`.

- [ ] **Step 9: Commit**

```bash
git add app/grading_http.py app/routes.py tests/test_routes_txt_json.py
git -c skill.commit=true commit -m "feat(routes): accept .txt and .json submissions in single-file and batch endpoints"
```

---

## Task 5: Actualizar el factory del pipeline

**Files:**
- Modify: `app/grading_pipeline_factory.py`

- [ ] **Step 1: Agregar import y pasar el servicio al constructor**

El archivo actualmente importa servicios al inicio. Agregar el import:

```python
from grader_agent.services.plain_text_extraction import PlainTextExtractionService
```

Y en `create_grading_pipeline()`, el `return GradingPipeline(...)` actualmente:

```python
    return GradingPipeline(
        transcription_service=TranscriptionService(whisper),
        pdf_extraction_service=PDFExtractionService(),
        code_notebook_extraction_service=CodeNotebookExtractionService(),
        content_validation=ContentValidationService(chat),
        rubric_validation=RubricValidationService(),
        grading=GradingService(chat),
        output_validation=OutputValidationService(),
        feedback=FeedbackService(chat),
        research=RubricResearchService(chat, paths=paths),
    )
```

Reemplazar por:

```python
    return GradingPipeline(
        transcription_service=TranscriptionService(whisper),
        pdf_extraction_service=PDFExtractionService(),
        code_notebook_extraction_service=CodeNotebookExtractionService(),
        plain_text_extraction_service=PlainTextExtractionService(),
        content_validation=ContentValidationService(chat),
        rubric_validation=RubricValidationService(),
        grading=GradingService(chat),
        output_validation=OutputValidationService(),
        feedback=FeedbackService(chat),
        research=RubricResearchService(chat, paths=paths),
    )
```

- [ ] **Step 2: Verificar que la app arranca sin errores de importación**

```bash
python -c "from app import create_app; app = create_app(testing=True); print('OK')"
```

Salida esperada: `OK`

- [ ] **Step 3: Correr el suite completo para verificar integración**

```bash
pytest -v 2>&1 | tail -20
```

Salida esperada: todos los tests en `PASSED`, cero fallos.

- [ ] **Step 4: Commit**

```bash
git add app/grading_pipeline_factory.py
git -c skill.commit=true commit -m "feat(factory): wire PlainTextExtractionService into GradingPipeline"
```

---

## Task 6: Actualizar el frontend

**Files:**
- Modify: `app/templates/index.html`

- [ ] **Step 1: Actualizar `esExtensionEntregableMultimodal` en JS**

Buscar en `index.html` la función:

```javascript
  function esExtensionEntregableMultimodal(name) {
    var n = (name || "").toLowerCase();
    return n.endsWith(".pdf") || n.endsWith(".docx") || n.endsWith(".py") || n.endsWith(".ipynb");
  }
```

Reemplazar por:

```javascript
  function esExtensionEntregableMultimodal(name) {
    var n = (name || "").toLowerCase();
    return n.endsWith(".pdf") || n.endsWith(".docx") || n.endsWith(".py") || n.endsWith(".ipynb") || n.endsWith(".txt") || n.endsWith(".json");
  }
```

- [ ] **Step 2: Actualizar el atributo `accept` del input de entregable individual**

Buscar:

```html
<input type="file" id="archivo-entregable-multimodal" accept=".pdf,.docx,.py,.ipynb,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document">
```

Reemplazar por:

```html
<input type="file" id="archivo-entregable-multimodal" accept=".pdf,.docx,.py,.ipynb,.txt,.json,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain,application/json">
```

- [ ] **Step 3: Actualizar el texto descriptivo del entregable individual**

Buscar:

```html
<p class="hint">PDF (máx. {{ pdf_max_pages }} {% if pdf_max_pages == 1 %}página{% else %}páginas{% endif %}), Word (.docx), archivo Python o notebook Jupyter. Se evalúa el texto o celdas de código extraídas.</p>
```

Reemplazar por:

```html
<p class="hint">PDF (máx. {{ pdf_max_pages }} {% if pdf_max_pages == 1 %}página{% else %}páginas{% endif %}), Word (.docx), archivo Python, notebook Jupyter, texto plano (.txt) o JSON (.json). Se evalúa el texto extraído según cada criterio de la rúbrica.</p>
```

- [ ] **Step 4: Actualizar el mensaje de validación en JS del single-file**

Buscar:

```javascript
    if (!archivo) { alert("Seleccioná un archivo (.pdf, .docx, .py o .ipynb)"); return; }
```

Reemplazar por:

```javascript
    if (!archivo) { alert("Seleccioná un archivo (.pdf, .docx, .py, .ipynb, .txt o .json)"); return; }
```

- [ ] **Step 5: Actualizar el texto descriptivo del modo batch**

Buscar la línea que menciona las extensiones permitidas en el bloque de carpeta:

```html
      y dentro debe haber <strong>un solo</strong> entregable admitido: PDF, <code>.docx</code>, <code>.py</code> o <code>.ipynb</code> (ej. «tarea.ipynb»). Chrome o Edge recomendados.
```

Reemplazar por:

```html
      y dentro debe haber <strong>un solo</strong> entregable admitido: PDF, <code>.docx</code>, <code>.py</code>, <code>.ipynb</code>, <code>.txt</code> o <code>.json</code>. Chrome o Edge recomendados.
```

- [ ] **Step 6: Actualizar el mensaje de error JS del batch para extensión desconocida**

Buscar en el JS del batch:

```javascript
              ? "No hay ningún entregable admitido (.pdf, .docx, .py o .ipynb) en la carpeta."
              : "Hay varios entregables admitidos: usá el filtro por nombre (ej. solucion)."
```

Reemplazar por:

```javascript
              ? "No hay ningún entregable admitido (.pdf, .docx, .py, .ipynb, .txt o .json) en la carpeta."
              : "Hay varios entregables admitidos: usá el filtro por nombre (ej. solucion)."
```

- [ ] **Step 7: Commit**

```bash
git add app/templates/index.html
git -c skill.commit=true commit -m "feat(ui): accept .txt and .json in entregable inputs and batch file picker"
```

---

## Task 7: Verificación final

- [ ] **Step 1: Correr el suite completo**

```bash
pytest -v
```

Salida esperada: todos los tests en `PASSED`, incluyendo:
- `tests/test_plain_text_extraction.py` — 16 tests
- `tests/test_routes_txt_json.py` — 7 tests
- `tests/test_app_routes.py` — sin regresiones
- `tests/test_pipeline.py` — sin regresiones

- [ ] **Step 2: Verificar que el servidor arranca**

```bash
python -m app
```

Debe arrancar sin errores de importación ni `TypeError` en el constructor del pipeline.

---

## Self-review del plan

### Cobertura de la spec

| Requisito de la spec | Task |
|---------------------|------|
| `PLAIN_TEXT_DELIVERABLE` enum | Task 1 |
| `PlainTextExtractionService` con `.txt` y `.json` | Task 2 |
| Pipeline: rama en `_step1_acquire_text` | Task 3 |
| Pipeline: heading por sufijo | Task 3 |
| `build_plain_text_grading_request()` | Task 4 |
| Rutas single-file: `.txt` y `.json` aceptados | Task 4 |
| Rutas batch: `.txt` y `.json` aceptados | Task 4 |
| Factory wiring | Task 5 |
| Frontend: JS filter, accept attr, textos | Task 6 |
| Tests unitarios del servicio | Task 2 |
| Tests de rutas | Task 4 |

### Consistencia de tipos

- `PlainTextExtractionService.extract()` → `str | ErrorResult` — usado así en Task 3
- `build_plain_text_grading_request()` → `GradingRequest` con `PLAIN_TEXT_DELIVERABLE` — usado así en Task 4
- `self._plain_text` en pipeline → instancia de `PlainTextExtractionService` — asignado en Task 3, instanciado en Task 5

### Placeholders

Ninguno — todos los pasos contienen código completo.
