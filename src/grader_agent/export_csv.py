# Generación de CSV para resultados de entregables PDF por criterios.

from __future__ import annotations

import csv
import io
from typing import Any


def _titulo_corto(titulo: str, max_len: int = 55) -> str:
    one = titulo.replace("\r", " ").replace("\n", " ").strip()
    if len(one) <= max_len:
        return one
    return one[: max_len - 3] + "..."


def _clave_orden(resultado: dict[str, Any]) -> str:
    nombre = (
        resultado.get("nombre_completo")
        or resultado.get("alumno")
        or resultado.get("carpeta_origen")
        or ""
    )
    return str(nombre).casefold()


def resultados_entregables_a_csv(
    resultados: list[dict[str, Any]],
    criterios_orden: list[str],
) -> str:
    """
    Devuelve texto CSV en UTF-8 con BOM para Excel (Windows).
    Ordena filas por nombre_completo / alumno (alfabético, sin depender de locale).
    """
    headers = [
        "id_estudiante",
        "nombre_completo",
        "carpeta_origen",
        "archivo_pdf",
        "total_obtenido",
        "total_maximo",
    ]
    for i, titulo in enumerate(criterios_orden, start=1):
        short = _titulo_corto(titulo)
        headers.append(f"[{i}] {short} — puntos")
        headers.append(f"[{i}] {short} — retro")

    buf = io.StringIO()
    writer = csv.writer(buf, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(headers)

    for r in sorted(resultados, key=_clave_orden):
        row: list[Any] = [
            r.get("id_estudiante", ""),
            r.get("nombre_completo") or r.get("alumno", ""),
            r.get("carpeta_origen", ""),
            r.get("archivo_pdf", ""),
            r.get("total_obtenido", ""),
            r.get("total_maximo", ""),
        ]
        lista_c = r.get("criterios") or []
        for j in range(len(criterios_orden)):
            c = lista_c[j] if j < len(lista_c) else {}
            row.append(c.get("puntaje_obtenido", ""))
            row.append(c.get("retroalimentacion", ""))
        writer.writerow(row)

    return "\ufeff" + buf.getvalue()
