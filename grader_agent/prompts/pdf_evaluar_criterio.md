## Criterio sobre entregable (texto del PDF)

Entrada: rúbrica Markdown, texto completo del entregable, criterio a evaluar en esta llamada.

- Evaluá solo ese criterio con la rúbrica. Si el criterio no aparece en la rúbrica: puntaje 0 y explicá en `retroalimentacion` que no está en la rúbrica.
- Puntaje de 0 al máximo del criterio en la rúbrica.
- Citá evidencia textual del entregable (comillas o referencia clara a parte del texto).
- En `retroalimentacion` aplicá el bloque Retroalimentación del system. Estructura en tres bloques con viñetas (-), oraciones cortas:
  - Fortalezas: qué cumple, con citas del entregable.
  - Debilidades: qué falta, está incompleto o débil.
  - Por qué este puntaje y no el máximo, ligado a la rúbrica.
- No penalices temas que la rúbrica no mencione.

Respondé solo con este JSON, sin texto adicional:

{
  "criterio": "nombre del criterio evaluado",
  "puntaje_obtenido": 7,
  "puntaje_maximo": 10,
  "retroalimentacion": "..."
}
