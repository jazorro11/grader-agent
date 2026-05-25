---
version: "1.0.0"
date: "2026-04-22"
changelog: "Archivo de referencia; no referenciado por prompts_loader en esta versión."
---

## Ítem de parcial (texto o transcripción)

> Nota: el pipeline actual usa `texto_puntaje_item` + `texto_retro_item` por separado. Conservamos este texto por si se recompone una llamada única.

Entrada: rúbrica Markdown y respuesta del alumno al ítem o pregunta que indica el docente.

- Ubica el ítem y sus descriptores. Puntaje de 0 al máximo de la rúbrica para ese ítem.
- En `retroalimentacion` aplica el bloque Retroalimentación del system (está al final de este mensaje). Orientación: típicamente 3 a 5 ideas en viñetas u oraciones cortas, ajusta según el caso. **Imperativo** para orientar (cualquier puntaje), como en ese bloque; citas o paráfrasis integradas en el relato, sin la palabra "evidencia" ni etiquetas. Vínculo explícito a la rúbrica. Di qué faltaría para el máximo. No abras con "El entregable" ni "El documento" (acá es respuesta escrita u oral, habla de lo que dijo o escribió).

Responde solo con este JSON, sin texto adicional:

{
  "pregunta": "nombre o número de la pregunta",
  "puntaje_obtenido": 7,
  "puntaje_maximo": 10,
  "retroalimentacion": "..."
}
