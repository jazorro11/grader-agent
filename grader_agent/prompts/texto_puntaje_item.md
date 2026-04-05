## Puntaje de un ítem de parcial (solo número)

Entrada: rúbrica, pregunta/ítem a calificar, respuesta del alumno, y **puntaje máximo canónico** (fijo en el mensaje de usuario).

- Ubicá el ítem en la rúbrica. El `puntaje_obtenido` debe estar entre 0 y el máximo canónico, inclusive.
- Si hay **niveles** con puntos discretos en el mensaje de usuario, el puntaje debe ser **exactamente** uno de esos valores.
- Si el ítem no aplica: 0.
- Sin retroalimentación en esta respuesta; solo el JSON.

Responde solo con este JSON, sin texto adicional:

{
  "puntaje_obtenido": 0
}
