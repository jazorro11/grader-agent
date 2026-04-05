"""Fragmentos de texto reutilizables para mensajes de usuario hacia el modelo."""


def bloque_niveles_usuario(niveles: list[dict] | None) -> str:
    if not niveles:
        return ""
    lines = [
        "NIVELES (elegí exactamente un valor «puntos»):",
    ]
    for n in niveles:
        try:
            pto = n["puntos"]
        except (KeyError, TypeError):
            continue
        etq = n.get("etiqueta", "")
        lines.append(f"  - {etq}: {pto} puntos")
    return "\n".join(lines) + "\n"
