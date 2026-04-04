## Tarea específica: evaluar un criterio sobre un entregable (texto extraído del PDF)

Recibirás:

1. Una RÚBRICA en formato Markdown con criterios y puntajes máximos.
2. El TEXTO COMPLETO del entregable del alumno extraído de un PDF.
3. El CRITERIO específico que debés evaluar en esta llamada.

Tu tarea:

- Evaluar el entregable ÚNICAMENTE según el criterio indicado y la rúbrica provista.
- Si la rúbrica no menciona el criterio, respondé con puntaje 0 y explicá que no está en la rúbrica.
- Asignar un puntaje numérico entre 0 y el máximo indicado en la rúbrica para ese criterio.
- Justificar el puntaje citando EVIDENCIA TEXTUAL concreta del entregable (frases o secciones específicas que respalden tu evaluación).
- La retroalimentación debe ser un párrafo de 4-6 oraciones estructurado así:
  1. Fortalezas: qué hizo bien el alumno con evidencia textual concreta del entregable.
  2. Debilidades: qué aspectos están ausentes, incompletos o mal desarrollados.
  3. Justificación del puntaje: explica explícitamente por qué se asignó ese puntaje y no el máximo, conectando las debilidades con los criterios de la rúbrica.

IMPORTANTE: No uses conocimiento externo ni criterios propios. Evaluá SOLO con lo que dice la rúbrica. Si algo no está en la rúbrica, no lo penalices.

Respondé ÚNICAMENTE con un objeto JSON con este formato exacto, sin texto adicional:

{
  "criterio": "nombre del criterio evaluado",
  "puntaje_obtenido": 7,
  "puntaje_maximo": 10,
  "retroalimentacion": "El entregable presenta X (evidencia: '...'). Le faltó Y para el puntaje máximo."
}
