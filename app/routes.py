"""Flask HTTP routes for the grading demo."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path

from flask import Flask, current_app, jsonify, render_template, request
from openai import OpenAIError

from app.grading_http import (
    build_audio_grading_request,
    build_code_deliverable_grading_request,
    build_pdf_grading_request,
    build_text_grading_request,
    error_result_http_response,
    grading_rejection_message,
    grading_result_rejection_http_response,
    grading_result_to_pdf_ui_dict,
    grading_result_to_text_audio_ui_dict,
    run_grading_request,
)
from grader_agent.export_csv import resultados_entregables_a_csv
from grader_agent.grading_config import pdf_max_pages
from grader_agent.grading.pdf import metadatos_criterios_desde_rubrica
from grader_agent.moodle_paths import parse_carpeta_moodle
from grader_agent.models import ErrorResult, GradingResult
from grader_agent.settings import GraderPaths

_logger = logging.getLogger(__name__)


def _paths() -> GraderPaths:
    return current_app.config["GRADER_PATHS"]


def _leer_rubrica_activa() -> str:
    path = _paths().active_rubric_file
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def _guardar_resultado(_alumno: str, resultado: dict) -> None:
    """Append one grading result to the JSON log under the configured data directory."""
    ruta = _paths().results_json
    datos: list = []
    if ruta.is_file():
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    datos.append(resultado)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")


def _suffix_entregable_multimodal(filename: str) -> str | None:
    """Sufijo temporal válido para PDF, Python o Jupyter; ``None`` si la extensión no está permitida."""
    low = (filename or "").lower()
    for suf in (".pdf", ".py", ".ipynb"):
        if low.endswith(suf):
            return suf
    return None


def _contenido_rubrica_desde_upload(archivo):
    """Return (text, None) on success, or (None, (response, status)) on UTF-8 error."""
    try:
        return archivo.read().decode("utf-8"), None
    except UnicodeDecodeError:
        return None, (jsonify({"error": "El archivo no es texto UTF-8 válido"}), 400)


def register_routes(app: Flask) -> None:
    """Attach all URL rules to ``app``."""

    @app.route("/")
    def index():
        return render_template("index.html", pdf_max_pages=pdf_max_pages())

    @app.route("/calificar-texto", methods=["POST"])
    def calificar_texto():
        data = request.get_json(silent=True)
        if data is None:
            return jsonify({"error": "Se esperaba un cuerpo JSON válido"}), 400
        pregunta = (data.get("pregunta") or "").strip()
        respuesta = (data.get("respuesta") or "").strip()
        nombre_alumno = data.get("alumno", "Alumno")

        if not pregunta:
            return jsonify({"error": "La pregunta / ítem no puede estar vacío"}), 400
        if not respuesta:
            return jsonify({"error": "La respuesta del alumno no puede estar vacía"}), 400

        rubrica = _leer_rubrica_activa()
        if not rubrica:
            return jsonify({"error": "Primero cargá una rúbrica"}), 400

        pipe_req = build_text_grading_request(
            rubric=rubrica,
            student_name=str(nombre_alumno),
            pregunta=pregunta,
            respuesta=respuesta,
        )
        out = run_grading_request(pipe_req)
        if isinstance(out, ErrorResult):
            return error_result_http_response(out)
        if not isinstance(out, GradingResult):
            return jsonify({"error": "Respuesta inválida del motor de calificación."}), 500

        rej = grading_result_rejection_http_response(out)
        if rej is not None:
            return rej

        resultado = grading_result_to_text_audio_ui_dict(out)
        _guardar_resultado(resultado["alumno"], resultado)
        return jsonify(resultado)

    @app.route("/calificar-audio", methods=["POST"])
    def calificar_audio():
        audio = request.files.get("audio")
        pregunta = (request.form.get("pregunta") or "").strip()
        nombre_alumno = request.form.get("alumno", "Alumno")

        if not audio:
            return jsonify({"error": "No se recibió audio"}), 400
        if not pregunta:
            return jsonify({"error": "La pregunta / ítem no puede estar vacía"}), 400

        rubrica = _leer_rubrica_activa()
        if not rubrica:
            return jsonify({"error": "Primero cargá una rúbrica"}), 400

        suffix = Path(audio.filename or "").suffix or ".webm"
        fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        try:
            audio.save(tmp_path)
            pipe_req = build_audio_grading_request(
                rubric=rubrica,
                student_name=str(nombre_alumno),
                pregunta=pregunta,
                audio_path=tmp_path,
            )
            out = run_grading_request(pipe_req)
            if isinstance(out, ErrorResult):
                return error_result_http_response(out)
            if not isinstance(out, GradingResult):
                return jsonify({"error": "Respuesta inválida del motor de calificación."}), 500

            rej = grading_result_rejection_http_response(out)
            if rej is not None:
                return rej

            resultado = grading_result_to_text_audio_ui_dict(out)
            _guardar_resultado(resultado["alumno"], resultado)
            return jsonify(resultado)
        finally:
            if os.path.isfile(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    @app.route("/resultados", methods=["GET"])
    def ver_resultados():
        ruta = _paths().results_json
        if not ruta.is_file():
            return jsonify([])
        return jsonify(json.loads(ruta.read_text(encoding="utf-8")))

    @app.route("/limpiar-resultados", methods=["POST"])
    def limpiar_resultados():
        ruta = _paths().results_json
        if ruta.is_file():
            ruta.unlink()
        return jsonify({"ok": True, "mensaje": "Resultados borrados"})

    @app.route("/cargar-rubrica", methods=["POST"])
    def cargar_rubrica():
        archivo = request.files.get("rubrica")
        if not archivo:
            return jsonify({"error": "No se recibió archivo"}), 400
        contenido, resp_err = _contenido_rubrica_desde_upload(archivo)
        if resp_err is not None:
            return resp_err
        path = _paths().active_rubric_file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contenido, encoding="utf-8")
        return jsonify({"ok": True, "mensaje": "Rúbrica de parcial cargada"})

    @app.route("/calificar-entregable", methods=["POST"])
    def calificar_entregable():
        archivo = request.files.get("entregable") or request.files.get("pdf")
        nombre_alumno = request.form.get("alumno", "Alumno")

        if not archivo:
            return jsonify({"error": "No se recibió archivo de entrega"}), 400

        suf = _suffix_entregable_multimodal(archivo.filename or "")
        if suf is None:
            return jsonify({"error": "Solo se aceptan archivos .pdf, .py o .ipynb"}), 400

        rubrica = _leer_rubrica_activa()
        if not rubrica:
            return jsonify({"error": "Primero cargá una rúbrica (.md) en este bloque"}), 400

        fd, ruta_tmp = tempfile.mkstemp(suffix=suf)
        os.close(fd)
        try:
            archivo.save(ruta_tmp)
            if suf == ".pdf":
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
            out = run_grading_request(pipe_req)
            if isinstance(out, ErrorResult):
                return error_result_http_response(out)
            if not isinstance(out, GradingResult):
                return jsonify({"error": "Respuesta inválida del motor de calificación."}), 500

            rej = grading_result_rejection_http_response(out)
            if rej is not None:
                return rej

            resultado = grading_result_to_pdf_ui_dict(out)
            _guardar_resultado(nombre_alumno, resultado)
            return jsonify(resultado)
        finally:
            if os.path.isfile(ruta_tmp):
                try:
                    os.remove(ruta_tmp)
                except OSError:
                    pass

    @app.route("/calificar-carpeta-entregables", methods=["POST"])
    def calificar_carpeta_entregables():
        entregables = request.files.getlist("entregable")
        pdfs_legacy = request.files.getlist("pdf")
        archivos_subida = entregables if entregables else pdfs_legacy
        alumnos = request.form.getlist("alumno")
        nombres_completos = request.form.getlist("nombre_completo")
        ids = request.form.getlist("id_estudiante")
        carpetas = request.form.getlist("carpeta_origen")
        archivos = request.form.getlist("archivo_pdf")

        if not archivos_subida:
            return jsonify({"error": "No se recibieron archivos de entrega (.pdf, .py o .ipynb)"}), 400

        n = len(archivos_subida)
        if len(alumnos) != n:
            return (
                jsonify(
                    {
                        "error": (
                            "La cantidad de valores «alumno» no coincide con la de archivos de entrega"
                        )
                    }
                ),
                400,
            )

        def _pad(lst: list[str], length: int) -> list[str]:
            out = list(lst)
            while len(out) < length:
                out.append("")
            return out[:length]

        nombres_completos = _pad(nombres_completos, n)
        ids = _pad(ids, n)
        carpetas = _pad(carpetas, n)
        archivos = _pad(archivos, n)

        rubrica = _leer_rubrica_activa()
        if not rubrica:
            return jsonify({"error": "Primero cargá una rúbrica (.md) en este bloque"}), 400

        try:
            metadatos = metadatos_criterios_desde_rubrica(rubrica)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except OpenAIError:
            return (
                jsonify(
                    {
                        "error": (
                            "The AI grading service failed or is temporarily unavailable. "
                            "Check your API key, quota, and network, then try again."
                        )
                    }
                ),
                502,
            )

        if not metadatos:
            return (
                jsonify(
                    {
                        "error": (
                            "No se identificaron criterios evaluables en la rúbrica. "
                            "Revisá que el .md describa ítems o criterios con puntaje."
                        )
                    }
                ),
                400,
            )
        criterios = [m["criterio"] for m in metadatos]

        resultados: list[dict] = []
        errores: list[dict] = []

        for i in range(n):
            sub = archivos_subida[i]
            alumno = alumnos[i] or "Alumno"
            carpeta = carpetas[i]
            archivo_nom = archivos[i] or (sub.filename or "")

            parsed = parse_carpeta_moodle(carpeta) if carpeta else {}
            nombre_completo = (nombres_completos[i] or "").strip() or parsed.get(
                "nombre_completo", ""
            )
            id_est = (ids[i] or "").strip() or (parsed.get("id_estudiante") or "")

            if not nombre_completo:
                nombre_completo = alumno

            suf = _suffix_entregable_multimodal(sub.filename or "")
            if suf is None:
                errores.append(
                    {
                        "alumno": alumno,
                        "carpeta_origen": carpeta,
                        "error": "Extensión no permitida (solo .pdf, .py o .ipynb).",
                    }
                )
                continue

            resultado_dict: dict | None = None
            fd, ruta_tmp = tempfile.mkstemp(suffix=suf)
            os.close(fd)
            try:
                sub.save(ruta_tmp)
                try:
                    if suf == ".pdf":
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
                    out = run_grading_request(pipe_req)
                    if isinstance(out, ErrorResult):
                        errores.append(
                            {
                                "alumno": alumno,
                                "carpeta_origen": carpeta,
                                "error": out.message,
                            }
                        )
                    elif isinstance(out, GradingResult):
                        rmsg = grading_rejection_message(out)
                        if rmsg is not None:
                            errores.append(
                                {
                                    "alumno": alumno,
                                    "carpeta_origen": carpeta,
                                    "error": rmsg,
                                }
                            )
                        else:
                            resultado_dict = grading_result_to_pdf_ui_dict(
                                out,
                                criterios_order=criterios,
                            )
                    else:
                        errores.append(
                            {
                                "alumno": alumno,
                                "carpeta_origen": carpeta,
                                "error": "Respuesta inválida del motor de calificación.",
                            }
                        )
                except Exception:
                    _logger.exception("Unexpected error while grading entregable for alumno=%s", alumno)
                    errores.append(
                        {
                            "alumno": alumno,
                            "carpeta_origen": carpeta,
                            "error": (
                                "An unexpected error occurred while grading this file. "
                                "See server logs for details."
                            ),
                        }
                    )
            finally:
                if os.path.exists(ruta_tmp):
                    try:
                        os.remove(ruta_tmp)
                    except OSError:
                        pass

            if resultado_dict is None:
                continue

            resultado_dict["nombre_completo"] = nombre_completo
            resultado_dict["id_estudiante"] = id_est
            resultado_dict["carpeta_origen"] = carpeta
            resultado_dict["archivo_pdf"] = archivo_nom

            _guardar_resultado(alumno, resultado_dict)
            resultados.append(resultado_dict)

        csv_text = resultados_entregables_a_csv(resultados, criterios)
        return jsonify(
            {
                "resultados": resultados,
                "errores": errores,
                "csv": csv_text,
            }
        )

    @app.errorhandler(413)
    def _payload_demasiado_grande(_e):
        return (
            jsonify({"error": "El archivo supera el tamaño máximo permitido (16 MB)"}),
            413,
        )
