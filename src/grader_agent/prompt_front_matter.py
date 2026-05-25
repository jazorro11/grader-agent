"""Quita YAML front matter (--- ... ---) de textos Markdown de prompts."""

from __future__ import annotations


def strip_yaml_front_matter(text: str) -> str:
    """Si el texto empieza con bloque front matter delimitado por ---, devuelve el cuerpo.

    Si no hay bloque bien formado (línea inicial ---, línea de cierre ---), devuelve
    ``text`` recortado con ``strip()`` sin interpretar YAML.
    """
    raw = text.strip()
    lines = raw.splitlines()
    if not lines or lines[0].strip() != "---":
        return raw
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            body = "\n".join(lines[i + 1 :])
            return body.strip()
    return raw
