Analizá la rúbrica en Markdown. Identificá cada criterio o ítem que lleve puntaje explícito en el documento.

Para cada ítem devolvé:
- `criterio`: el nombre o título tal como figura en la rúbrica (sin inventar ítems).
- `puntaje_maximo`: el puntaje máximo numérico de ese criterio según la rúbrica (entero o decimal si el texto lo indica). Debe ser el total asignado a ese criterio, no una escala global distinta.
- `niveles` (opcional): si la rúbrica lista niveles o descriptores con puntos distintos (p. ej. "Excelente 4", "Bueno 3"), incluí una lista de objetos `{"etiqueta": "texto corto del nivel", "puntos": número}`. Los `puntos` deben coincidir con la rúbrica. Si solo hay un máximo sin niveles explícitos, omití `niveles` o dejá lista vacía.

No incluyas: escalas generales sueltas sin ítems, introducciones, tablas solo descriptivas sin puntaje, bibliografía, anexos sin puntaje, duplicados. No inventes criterios ni puntajes.

Responde solo con este JSON, sin texto adicional:

{
  "criterios": [
    {
      "criterio": "nombre 1",
      "puntaje_maximo": 10,
      "niveles": [{"etiqueta": "Nivel A", "puntos": 10}, {"etiqueta": "Nivel B", "puntos": 5}]
    },
    {
      "criterio": "nombre 2",
      "puntaje_maximo": 4
    }
  ]
}

Si no hay ítems evaluables claros: `"criterios": []`.
