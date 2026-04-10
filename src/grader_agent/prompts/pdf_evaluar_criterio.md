## Criterio sobre entregable (texto del PDF)

Entrada: rúbrica Markdown, texto completo del entregable, criterio a evaluar en esta llamada.

- Evalúa únicamente ese criterio con la rúbrica. Si el criterio no aparece en la rúbrica: puntaje 0 y explica en `retroalimentacion` que no está en la rúbrica.
- Puntaje de 0 al máximo del criterio en la rúbrica.
- En `retroalimentacion` aplica el bloque Retroalimentación del system (está al final de este mensaje). Escribe un texto orgánico: cubre qué encaja con la rúbrica citando o parafraseando el PDF dentro de las oraciones, qué faltaría o está flojo si aplica, y si hace falta una frase breve sobre el puntaje sin tono de acta. **Imperativo** para orientar (cualquier puntaje), como en ese bloque. El orden y la cantidad de oraciones pueden variar según el caso.
- Nunca uses la palabra "evidencia" ni rellenes con "El entregable presenta..." como apertura. Piensa en abrir con tú o con el contenido ("Cuando explicas que...", "Lo de la IMU y el GPS...").
- No pidas al alumno que repita estructuras fijas ni uses tú mismo estructuras de informe repetitivas entre criterios.
- No penalices temas que la rúbrica no mencione.

Responde solo con este JSON, sin texto adicional:

{
  "criterio": "nombre del criterio evaluado",
  "puntaje_obtenido": 7,
  "puntaje_maximo": 10,
  "retroalimentacion": "..."
}
