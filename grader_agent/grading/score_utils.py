"""Utilidades para puntajes numéricos."""

from __future__ import annotations


def clamp_puntaje(obtenido, puntaje_maximo) -> float:
    """
    Limita el puntaje al intervalo [0, puntaje_maximo].
    Valores no numéricos en obtenido se tratan como 0.
    """
    try:
        x = float(obtenido)
    except (TypeError, ValueError):
        x = 0.0
    try:
        m = float(puntaje_maximo)
    except (TypeError, ValueError):
        m = 0.0
    if m < 0:
        m = 0.0
    return max(0.0, min(x, m))


def ajustar_puntaje_a_niveles_discretos(
    obtenido,
    niveles: list[dict] | None,
    puntaje_maximo,
) -> float:
    """
    Si hay niveles con puntos explícitos, devuelve el punto de la lista más cercano
    al valor ya acotado; si no hay niveles, solo aplica clamp al máximo canónico.
    Si dos puntos están a la misma distancia, ``min`` elige el de menor valor numérico.
    """
    if not niveles:
        return clamp_puntaje(obtenido, puntaje_maximo)
    puntos: list[float] = []
    for n in niveles:
        if not isinstance(n, dict):
            continue
        try:
            puntos.append(float(n["puntos"]))
        except (KeyError, TypeError, ValueError):
            continue
    puntos = sorted(set(puntos))
    if not puntos:
        return clamp_puntaje(obtenido, puntaje_maximo)
    o = clamp_puntaje(obtenido, puntaje_maximo)
    return min(puntos, key=lambda p: abs(p - o))
