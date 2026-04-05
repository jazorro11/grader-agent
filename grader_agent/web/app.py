# Servidor web: recibe peticiones del navegador y devuelve resultados de calificación.

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from grader_agent.export_csv import resultados_entregables_a_csv
from grader_agent.grading.pdf import (
    calificar_entregable_pdf,
    metadatos_criterios_desde_rubrica,
)
from grader_agent.moodle_paths import parse_carpeta_moodle
from grader_agent.grading.text import calificar_respuesta
from grader_agent.http_logging import configure_logging, register_http_logging
from grader_agent.transcription import transcribir_audio

_WEB_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _WEB_DIR.parent.parent

configure_logging()

app = Flask(
    __name__,
    template_folder=str(_PROJECT_ROOT / "templates"),
)
register_http_logging(app)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024


@app.errorhandler(413)
def _payload_demasiado_grande(_e):
    return jsonify({"error": "El archivo supera el tamaño máximo permitido (16 MB)"}), 413


RUBRICS_DIR = "rubrics"
RESULTS_DIR = "results"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/calificar-texto", methods=["POST"])
def calificar_texto():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Se esperaba un cuerpo JSON válido"}), 400
    pregunta = data.get("pregunta", "")
    respuesta = data.get("respuesta", "")
    nombre_alumno = data.get("alumno", "Alumno")

    rubrica = _leer_rubrica_activa()
    if not rubrica:
        return jsonify({"error": "Primero cargá una rúbrica"}), 400

    resultado = calificar_respuesta(rubrica, pregunta, respuesta)
    resultado["alumno"] = nombre_alumno

    _guardar_resultado(nombre_alumno, resultado)

    return jsonify(resultado)


@app.route("/calificar-audio", methods=["POST"])
def calificar_audio():
    audio = request.files.get("audio")
    pregunta = request.form.get("pregunta", "")
    nombre_alumno = request.form.get("alumno", "Alumno")

    if not audio:
        return jsonify({"error": "No se recibió audio"}), 400

    ruta_audio = os.path.join(RESULTS_DIR, "temp_audio.webm")
    audio.save(ruta_audio)

    transcripcion = transcribir_audio(ruta_audio)

    rubrica = _leer_rubrica_activa()
    if not rubrica:
        return jsonify({"error": "Primero cargá una rúbrica"}), 400

    resultado = calificar_respuesta(rubrica, pregunta, transcripcion)
    resultado["alumno"] = nombre_alumno
    resultado["transcripcion"] = transcripcion

    _guardar_resultado(nombre_alumno, resultado)

    return jsonify(resultado)


@app.route("/resultados", methods=["GET"])
def ver_resultados():
    ruta = os.path.join(RESULTS_DIR, "resultados.json")
    if not os.path.exists(ruta):
        return jsonify([])
    with open(ruta, "r", encoding="utf-8") as f:
        return jsonify(json.load(f))


@app.route("/limpiar-resultados", methods=["POST"])
def limpiar_resultados():
    ruta = os.path.join(RESULTS_DIR, "resultados.json")
    if os.path.exists(ruta):
        os.remove(ruta)
    return jsonify({"ok": True, "mensaje": "Resultados borrados"})


@app.route("/cargar-rubrica", methods=["POST"])
def cargar_rubrica():
    archivo = request.files.get("rubrica")
    if not archivo:
        return jsonify({"error": "No se recibió archivo"}), 400
    contenido, resp_err = _contenido_rubrica_desde_upload(archivo)
    if resp_err is not None:
        return resp_err
    ruta = os.path.join(RUBRICS_DIR, "rubrica_activa.md")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(contenido)
    return jsonify({"ok": True, "mensaje": "Rúbrica de parcial cargada"})


@app.route("/calificar-entregable", methods=["POST"])
def calificar_entregable():
    pdf = request.files.get("pdf")
    nombre_alumno = request.form.get("alumno", "Alumno")

    if not pdf:
        return jsonify({"error": "No se recibió PDF"}), 400

    rubrica = _leer_rubrica_activa()
    if not rubrica:
        return jsonify({"error": "Primero cargá una rúbrica (.md) en este bloque"}), 400

    ruta_pdf = os.path.join(RESULTS_DIR, "temp_entregable.pdf")
    pdf.save(ruta_pdf)

    try:
        resultado = calificar_entregable_pdf(rubrica, ruta_pdf, nombre_alumno)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    _guardar_resultado(nombre_alumno, resultado)
    return jsonify(resultado)


@app.route("/calificar-carpeta-entregables", methods=["POST"])
def calificar_carpeta_entregables():
    pdfs = request.files.getlist("pdf")
    alumnos = request.form.getlist("alumno")
    nombres_completos = request.form.getlist("nombre_completo")
    ids = request.form.getlist("id_estudiante")
    carpetas = request.form.getlist("carpeta_origen")
    archivos = request.form.getlist("archivo_pdf")

    if not pdfs:
        return jsonify({"error": "No se recibieron archivos PDF"}), 400

    n = len(pdfs)
    if len(alumnos) != n:
        return jsonify(
            {"error": "La cantidad de valores «alumno» no coincide con la de archivos PDF"}
        ), 400

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

    metadatos = metadatos_criterios_desde_rubrica(rubrica)
    if not metadatos:
        return jsonify(
            {
                "error": (
                    "No se identificaron criterios evaluables en la rúbrica. "
                    "Revisá que el .md describa ítems o criterios con puntaje."
                )
            }
        ), 400
    criterios = [m["criterio"] for m in metadatos]

    resultados: list[dict] = []
    errores: list[dict] = []

    for i in range(n):
        pdf = pdfs[i]
        alumno = alumnos[i] or "Alumno"
        carpeta = carpetas[i]
        archivo_nom = archivos[i] or (pdf.filename or "")

        parsed = parse_carpeta_moodle(carpeta) if carpeta else {}
        nombre_completo = (nombres_completos[i] or "").strip() or parsed.get(
            "nombre_completo", ""
        )
        id_est = (ids[i] or "").strip() or (parsed.get("id_estudiante") or "")

        if not nombre_completo:
            nombre_completo = alumno

        resultado = None
        fd, ruta_tmp = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        try:
            pdf.save(ruta_tmp)
            resultado = calificar_entregable_pdf(
                rubrica, ruta_tmp, alumno, metadatos_criterios=metadatos
            )
        except ValueError as e:
            errores.append(
                {
                    "alumno": alumno,
                    "carpeta_origen": carpeta,
                    "error": str(e),
                }
            )
        except Exception as e:
            errores.append(
                {
                    "alumno": alumno,
                    "carpeta_origen": carpeta,
                    "error": str(e),
                }
            )
        finally:
            if os.path.exists(ruta_tmp):
                try:
                    os.remove(ruta_tmp)
                except OSError:
                    pass

        if resultado is None:
            continue

        resultado["nombre_completo"] = nombre_completo
        resultado["id_estudiante"] = id_est
        resultado["carpeta_origen"] = carpeta
        resultado["archivo_pdf"] = archivo_nom

        _guardar_resultado(alumno, resultado)
        resultados.append(resultado)

    csv_text = resultados_entregables_a_csv(resultados, criterios)
    return jsonify(
        {
            "resultados": resultados,
            "errores": errores,
            "csv": csv_text,
        }
    )


def _contenido_rubrica_desde_upload(archivo):
    """Devuelve (texto, None) si OK, o (None, (jsonify(...), 400)) si no es UTF-8."""
    try:
        return archivo.read().decode("utf-8"), None
    except UnicodeDecodeError:
        return None, (jsonify({"error": "El archivo no es texto UTF-8 válido"}), 400)


def _leer_rubrica_activa() -> str:
    ruta = os.path.join(RUBRICS_DIR, "rubrica_activa.md")
    if not os.path.exists(ruta):
        return ""
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def _guardar_resultado(alumno: str, resultado: dict):
    ruta = os.path.join(RESULTS_DIR, "resultados.json")
    datos = []
    if os.path.exists(ruta):
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)
    datos.append(resultado)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
