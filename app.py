# app.py
# Servidor web principal. Recibe peticiones del navegador,
# las procesa usando grader.py y transcriber.py, y devuelve resultados.

from flask import Flask, request, jsonify, render_template
from pdf_grader import calificar_entregable_pdf
from grader import calificar_respuesta      # módulo para calificar con GPT-4o
from transcriber import transcribir_audio   # módulo para transcribir con Whisper
from http_logging import configure_logging, register_http_logging
import json
import os

configure_logging()

app = Flask(__name__)  # crea la aplicación Flask. __name__ le dice a Flask dónde está el proyecto.
register_http_logging(app)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # límite de subida (audio/PDF/rúbrica)


@app.errorhandler(413)
def _payload_demasiado_grande(_e):
    return jsonify({"error": "El archivo supera el tamaño máximo permitido (16 MB)"}), 413


# Carpetas donde se guardan los archivos
RUBRICS_DIR = "rubrics"   # aquí se guarda el .md con los criterios
RESULTS_DIR = "results"   # aquí se guardan los resultados en JSON


# ── RUTA: Página principal ────────────────────────────────────
# Cuando el usuario abre http://localhost:5000 en el navegador,
# Flask busca el archivo templates/index.html y lo muestra.
@app.route("/")
def index():
    return render_template("index.html")


# ── RUTA: Calificar respuesta escrita ─────────────────────────
# El navegador envía un JSON con el nombre del alumno, la pregunta
# y la respuesta escrita. Flask lo pasa a GPT-4o y devuelve el puntaje.
@app.route("/calificar-texto", methods=["POST"])
def calificar_texto():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Se esperaba un cuerpo JSON válido"}), 400
    pregunta      = data.get("pregunta", "")
    respuesta     = data.get("respuesta", "")
    nombre_alumno = data.get("alumno", "Alumno")

    rubrica = _leer_rubrica_activa()        # carga la rúbrica guardada en disco
    if not rubrica:
        return jsonify({"error": "Primero cargá una rúbrica"}), 400

    # llama a GPT-4o con la rúbrica + pregunta + respuesta del alumno
    resultado = calificar_respuesta(rubrica, pregunta, respuesta)
    resultado["alumno"] = nombre_alumno

    _guardar_resultado(nombre_alumno, resultado)  # acumula en resultados.json

    return jsonify(resultado)  # devuelve el puntaje al navegador


# ── RUTA: Calificar respuesta de audio ───────────────────────
# El navegador envía el audio grabado junto con la pregunta y el nombre.
# Flask primero transcribe el audio con Whisper y luego califica el texto.
@app.route("/calificar-audio", methods=["POST"])
def calificar_audio():
    audio         = request.files.get("audio")          # archivo de audio grabado
    pregunta      = request.form.get("pregunta", "")    # request.form porque viene
    nombre_alumno = request.form.get("alumno", "Alumno")# junto a un archivo, no JSON

    if not audio:
        return jsonify({"error": "No se recibió audio"}), 400

    # guarda el audio temporalmente en disco para que Whisper pueda leerlo
    ruta_audio = os.path.join(RESULTS_DIR, "temp_audio.webm")
    audio.save(ruta_audio)

    # paso 1: convierte el audio a texto
    transcripcion = transcribir_audio(ruta_audio)

    rubrica = _leer_rubrica_activa()
    if not rubrica:
        return jsonify({"error": "Primero cargá una rúbrica"}), 400

    # paso 2: califica el texto transcripto igual que si fuera escrito
    resultado = calificar_respuesta(rubrica, pregunta, transcripcion)
    resultado["alumno"]        = nombre_alumno
    resultado["transcripcion"] = transcripcion  # guardamos también qué entendió Whisper

    _guardar_resultado(nombre_alumno, resultado)

    return jsonify(resultado)


# ── RUTA: Ver todos los resultados ───────────────────────────
# Devuelve el JSON con todas las calificaciones acumuladas.
# Útil para mostrar la tabla final con todos los alumnos.
@app.route("/resultados", methods=["GET"])
def ver_resultados():
    ruta = os.path.join(RESULTS_DIR, "resultados.json")
    if not os.path.exists(ruta):
        return jsonify([])  # si no hay resultados aún, devuelve lista vacía
    with open(ruta, "r", encoding="utf-8") as f:
        return jsonify(json.load(f))


# ── RUTA: Limpiar resultados para empezar sesión nueva ────────
# Borra el archivo resultados.json para poder corregir un nuevo parcial
# sin mezclar datos de alumnos anteriores.
@app.route("/limpiar-resultados", methods=["POST"])
def limpiar_resultados():
    ruta = os.path.join(RESULTS_DIR, "resultados.json")
    if os.path.exists(ruta):
        os.remove(ruta)
    return jsonify({"ok": True, "mensaje": "Resultados borrados"})


# ── RUTA: Cargar rúbrica para parcial (texto/audio) ──────────
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


# ── RUTA: Calificar entregable completo (PDF) con la rúbrica activa ──
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


# ── HELPERS (funciones internas, no son rutas web) ────────────

def _contenido_rubrica_desde_upload(archivo):
    """Devuelve (texto, None) si OK, o (None, (jsonify(...), 400)) si no es UTF-8."""
    try:
        return archivo.read().decode("utf-8"), None
    except UnicodeDecodeError:
        return None, (jsonify({"error": "El archivo no es texto UTF-8 válido"}), 400)


def _leer_rubrica_activa() -> str:
    """Lee el contenido del .md activo desde disco y lo devuelve como string."""
    ruta = os.path.join(RUBRICS_DIR, "rubrica_activa.md")
    if not os.path.exists(ruta):
        return ""  # devuelve string vacío si no hay rúbrica cargada
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()

def _guardar_resultado(alumno: str, resultado: dict):
    """
    Agrega el resultado de un alumno al archivo resultados.json.
    Si el archivo no existe, lo crea. Si ya existe, agrega al final.
    Así acumulamos todos los alumnos en una sola sesión de corrección.
    """
    ruta = os.path.join(RESULTS_DIR, "resultados.json")
    datos = []
    if os.path.exists(ruta):
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)    # carga los resultados anteriores
    datos.append(resultado)         # agrega el nuevo resultado
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)  # guarda todo de nuevo

# ── PUNTO DE ENTRADA ──────────────────────────────────────────
# Esto solo se ejecuta cuando corrés "python app.py" directamente.
# En producción o red local: no uses debug. Para desarrollo: FLASK_DEBUG=1
if __name__ == "__main__":
    _debug = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    app.run(debug=_debug)