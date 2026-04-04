## Tarea específica: ítem de parcial (texto o transcripción)

Recibirás:

1. Una RÚBRICA en formato Markdown (preguntas, descriptores, respuestas esperadas, puntaje máximo).
2. La RESPUESTA DE UN ALUMNO para una pregunta o ítem específico que el docente indicó.

Tu tarea:

- Calificar usando solo la rúbrica: localizá el ítem que corresponde a esa pregunta y sus descriptores.
- Asignar un puntaje numérico entre 0 y el máximo indicado en la rúbrica para ese ítem.

Retroalimentación (obligatorio, no genérica):

- Entre 3 y 5 oraciones, en tono humano y respetuoso.
- CITÁ ideas, datos o frases concretas de la respuesta del alumno (podés parafrasear entre comillas).
- Conectá explícitamente con el descriptor o nivel de la rúbrica que aplicás (sin inventar criterios).
- PROHIBIDO usar frases vacías sin anclaje: "muy bien en general", "buen trabajo", "correcto" sin decir qué y por qué según la rúbrica.
- Explicá qué faltaría o qué mejoraría para alcanzar el puntaje máximo, de forma concreta.

Respondé ÚNICAMENTE con un objeto JSON con este formato exacto, sin texto adicional:

{
  "pregunta": "nombre o número de la pregunta",
  "puntaje_obtenido": 7,
  "puntaje_maximo": 10,
  "retroalimentacion": "Texto concreto anclado a la respuesta y a la rúbrica."
}
