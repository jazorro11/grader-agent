# Convención típica de carpetas al descargar entregas desde Moodle.

from __future__ import annotations

import re

_MOODLE_CARPETA = re.compile(r"^(.+)_(\d{6})_assignsubmission_file$")


def parse_carpeta_moodle(segmento: str) -> dict[str, str]:
    """
    Interpreta el nombre de carpeta del estudiante.

    Patrón esperado: NOMBRE COMPLETO_######_assignsubmission_file
    Si no coincide, id_estudiante queda vacío y nombre_completo es el segmento tal cual.
    """
    segmento = segmento.strip()
    m = _MOODLE_CARPETA.match(segmento)
    if not m:
        return {
            "nombre_completo": segmento,
            "id_estudiante": "",
            "carpeta_origen": segmento,
        }
    return {
        "nombre_completo": m.group(1).strip(),
        "id_estudiante": m.group(2),
        "carpeta_origen": segmento,
    }
