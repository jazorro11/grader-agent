## Ubicar ítem en la rúbrica (solo escala)

Te pasan la rúbrica en Markdown y la pregunta o ítem que el docente quiere calificar (puede ser número, título o fragmento). Ubicá ese ítem en la rúbrica.

- Devolvé `item` con el nombre o identificador del ítem tal como figura en la rúbrica.
- Devolvé `puntaje_maximo` con el máximo numérico de ese ítem según el texto. No uses otra escala (p. ej. 100 si la rúbrica dice sobre 10).
- Si hay niveles con puntos explícitos, incluí `niveles` como lista de `{"etiqueta": "...", "puntos": número}`.
- Si no encontrás un ítem evaluable que corresponda a la pregunta: `puntaje_maximo` 0 y `item` cadena vacía.

Responde solo con este JSON, sin texto adicional:

{
  "item": "nombre del ítem",
  "puntaje_maximo": 10,
  "niveles": []
}
