# Rúbrica de calificación  
## Pre-Laboratorio: Convertidores D/A — DAC, R-2R y ZOH

**Entregable evaluado:** notebook completado con ejecución de celdas, gráficas generadas, cálculos manuales y respuestas a las preguntas del pre-laboratorio.  

**Puntaje máximo:** 20 puntos  
**Cantidad de criterios evaluables:** 5  
**Puntaje por criterio:** 1 a 4 puntos  
**Peso porcentual por criterio:** 20% cada uno  
**Porcentaje total:** 100%

> **Nota importante:** La **pregunta 7 NO debe ser tenida en cuenta** para la calificación.  
> No debe asignarse puntaje, penalización ni bonificación por la respuesta a la pregunta 7.  
> La evaluación de las preguntas de análisis debe realizarse únicamente con las demás preguntas del entregable.

---

## Escala general de desempeño

| Nivel | Puntaje | Descripción general |
|---|---:|---|
| Insuficiente | 1 punto | Evidencia mínima, incompleta o incorrecta. |
| Básico | 2 puntos | Cumple parcialmente, con errores conceptuales o procedimentales importantes. |
| Bueno | 3 puntos | Cumple adecuadamente, con errores menores o explicaciones mejorables. |
| Excelente | 4 puntos | Cumple completamente, con precisión técnica, claridad y justificación. |

---

## Criterios evaluables

| Criterio | Peso | Puntaje máximo | Insuficiente — 1 punto | Básico — 2 puntos | Bueno — 3 puntos | Excelente — 4 puntos |
|---|---:|---:|---|---|---|---|
| **1. Ejecución completa del notebook y presentación del entregable** | **20%** | **4 puntos** | El notebook está incompleto, no ejecutado o no permite verificar resultados, gráficas ni respuestas. | Ejecuta solo algunas secciones; faltan salidas, gráficas o respuestas en varias partes del pre-laboratorio. | Ejecuta la mayoría de las celdas y presenta la mayoría de las gráficas y respuestas, con pequeñas omisiones. | Entrega el notebook completo, ordenado, ejecutado en secuencia, con todas las salidas, gráficas y respuestas visibles. |
| **2. Cálculos de resolución, niveles, LSB y relación entre DACs** | **20%** | **4 puntos** | No calcula correctamente niveles, LSB o relación entre DACs de 4 y 8 bits. | Calcula parcialmente niveles o LSB, pero presenta errores de fórmula, unidades o interpretación. | Calcula correctamente la mayoría de valores de LSB, número de niveles y relación entre DACs, con errores menores. | Calcula correctamente niveles, LSB de 4 y 8 bits, relación de resolución y explica con claridad por qué el DAC de 8 bits tiene escalones más finos. |
| **3. Análisis de la red R-2R y efecto de tolerancias** | **20%** | **4 puntos** | No identifica correctamente el funcionamiento de la red R-2R ni el efecto de las tolerancias. | Reconoce parcialmente la relación entre código binario y voltaje, pero comete errores importantes en los cálculos o en la recomendación de tolerancia. | Calcula adecuadamente salidas para códigos binarios y error máximo permitido, con justificación básica de la tolerancia recomendada. | Calcula correctamente las salidas para códigos como `0101` y `1010`, relaciona los valores con `Vref`, calcula el error máximo permitido y justifica técnicamente la tolerancia recomendada. |
| **4. Interpretación de generación senoidal, cuantización y Zero-Order Hold** | **20%** | **4 puntos** | No explica correctamente la cuantización, los escalones ni el efecto ZOH en la señal. | Describe de forma general los escalones o el ZOH, pero con poca relación con frecuencia, resolución o muestras por ciclo. | Explica adecuadamente la diferencia visual entre DAC de 8 bits y R-2R de 4 bits, y relaciona el ZOH con la cantidad de muestras por ciclo. | Interpreta con precisión la generación senoidal, la cuantización, el tamaño del escalón, el efecto ZOH, la derivada de la señal y la relación entre pendiente y error de retención. |
| **5. Respuestas a las preguntas de análisis y argumentación técnica** | **20%** | **4 puntos** | No responde varias preguntas evaluables o las respuestas son incoherentes, incompletas o sin sustento técnico. | Responde parcialmente las preguntas evaluables, pero con errores conceptuales en Nyquist, ZOH, sinc, unidades o interpretación de resultados. | Responde la mayoría de las preguntas evaluables con argumentos adecuados, aunque algunas justificaciones son generales o poco desarrolladas. | Responde todas las preguntas evaluables con cálculos paso a paso, unidades correctas, interpretación técnica y conclusiones claras sobre LSB, R-2R, tolerancias, ZOH, Nyquist y atenuación sinc. |

---

## Descripción de los ítems evaluados por criterio

### Criterio 1: Ejecución completa del notebook y presentación del entregable  
**Peso:** 20%  
**Puntaje máximo:** 4 puntos  

Se evalúa que el estudiante entregue el notebook completo, ejecutado en orden y con evidencia verificable de trabajo.

- Ejecución secuencial de las celdas.
- Visualización correcta de gráficas.
- Salidas numéricas visibles.
- Respuestas diligenciadas en los espacios correspondientes.
- Orden y legibilidad del entregable.
- **La pregunta 7 no se considera para asignar ni descontar puntaje.**

---

### Criterio 2: Cálculos de resolución, niveles, LSB y relación entre DACs  
**Peso:** 20%  
**Puntaje máximo:** 4 puntos  

Se evalúa la comprensión de la función de transferencia del DAC y la comparación entre resolución de 4 bits y 8 bits.

- Cálculo de número de niveles: `N = 2^b`.
- Cálculo de LSB: `LSB = V_ref / 2^b`.
- Comparación entre LSB de 4 bits y 8 bits.
- Interpretación de cuántas veces más fino es el escalón del DAC de 8 bits.
- Uso correcto de unidades en V o mV.

---

### Criterio 3: Análisis de la red R-2R y efecto de tolerancias  
**Peso:** 20%  
**Puntaje máximo:** 4 puntos  

Se evalúa la comprensión del DAC R-2R de 4 bits, su relación con el código binario y el impacto de errores resistivos.

- Cálculo de salida para códigos binarios específicos, como `0101` y `1010`.
- Relación entre código digital, peso binario y voltaje de salida.
- Cálculo del error máximo permitido: `LSB / 2`.
- Interpretación de la tabla de tolerancias.
- Recomendación justificada de tolerancia de resistencias.

---

### Criterio 4: Interpretación de generación senoidal, cuantización y Zero-Order Hold  
**Peso:** 20%  
**Puntaje máximo:** 4 puntos  

Se evalúa la interpretación de las señales generadas por DACs de distinta resolución y el comportamiento del ZOH.

- Comparación entre senoidal generada con DAC de 8 bits y R-2R de 4 bits.
- Explicación del efecto de la cuantización.
- Relación entre tamaño del escalón y número de bits.
- Interpretación del ZOH como retención de muestra.
- Relación entre pendiente de la señal y error ZOH.

---

### Criterio 5: Respuestas a las preguntas de análisis y argumentación técnica  
**Peso:** 20%  
**Puntaje máximo:** 4 puntos  

Se evalúa la calidad de las respuestas a las preguntas del pre-laboratorio, **excluyendo explícitamente la pregunta 7**.

- Respuestas completas a todas las preguntas evaluables.
- Procedimientos de cálculo claros.
- Justificación técnica, no solo numérica.
- Uso adecuado de conceptos como Nyquist, muestras por ciclo, ZOH y función sinc.
- Conclusiones coherentes con las gráficas y resultados del notebook.
- **La pregunta 7 NO debe ser evaluada.**
- **La pregunta 7 NO debe afectar el puntaje del criterio.**
- **La pregunta 7 NO debe generar penalización si está incompleta, incorrecta o ausente.**

---

## Cálculo de la nota

**Puntaje total obtenido:** suma de los puntos asignados en los 5 criterios.

**Puntaje máximo:** 20 puntos.

**Nota final sobre 5.0:**

`Nota final = (Puntaje obtenido / 20) × 5.0`

**Porcentaje obtenido:**

`Porcentaje obtenido = (Puntaje obtenido / 20) × 100`

---

## Condición sugerida de aprobación

El estudiante aprueba el pre-laboratorio si obtiene al menos:

- **12 de 20 puntos**, equivalente al **60%**, o
- la nota mínima definida por el docente para la actividad.

---

## Aclaración final sobre la pregunta 7

La **pregunta 7 queda excluida de la evaluación**.  
No se debe revisar para asignar puntaje.  
No se debe usar para descontar puntaje.  
No se debe considerar dentro de las respuestas exigidas para obtener el nivel **Excelente** en ningún criterio.