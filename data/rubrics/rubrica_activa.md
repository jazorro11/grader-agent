# Rúbrica de calificación detallada  
**Taller Técnico: Análisis de Resolución, Cuantización y Relación Señal-Ruido (SNR) con ESP32**

Esta rúbrica está organizada para su uso en Moodle con 4 niveles de desempeño y los siguientes puntajes por criterio:

| Criterio | Nivel 1 | Nivel 2 | Nivel 3 | Nivel 4 |
|---|---:|---:|---:|---:|
| Cálculos teóricos: LSB y SNR | 0 | 4 | 6 | 8 |
| Análisis experimental del error | 0 | 3 | 4 | 6 |
| Conclusiones y razonamiento | 0 | 1 | 2 | 3 |
| Formato IEEE y gráficas | 0 | 1 | 2 | 3 |

## 1. Cálculos teóricos: LSB y SNR

- **Nivel 1 — 0 puntos**  
  No aplica correctamente las fórmulas de LSB y SNR, omite varias resoluciones o presenta resultados incompatibles con la teoría del taller. Hay errores conceptuales importantes, ausencia de procedimiento o uso incorrecto de unidades.

- **Nivel 2 — 4 puntos**  
  Presenta cálculos parciales o incompletos del LSB y/o del SNR. Hay errores en una o más resoluciones, en la sustitución de datos o en las unidades. El procedimiento se muestra de forma limitada y no siempre permite verificar cómo obtuvo los resultados.

- **Nivel 3 — 6 puntos**  
  Calcula correctamente la mayoría de los valores de LSB y SNR para 12, 8 y 6 bits. Puede haber un error menor de redondeo, notación o presentación, pero el procedimiento general es correcto. Las unidades aparecen casi siempre bien usadas y el desarrollo permite seguir el razonamiento.

- **Nivel 4 — 8 puntos**  
  Calcula correctamente el valor del LSB para 12, 8 y 6 bits usando el rango de 3300 mV. Calcula correctamente el SNR ideal para las tres resoluciones con la ecuación indicada en el taller. Presenta todos los resultados con unidades correctas y consistentes (mV, dB), mostrando procedimiento claro, ordenado y sin errores numéricos ni conceptuales.

## 2. Análisis experimental del error

- **Nivel 1 — 0 puntos**  
  No relaciona las gráficas de Teleplot con el límite teórico de cuantización, o lo hace de manera incorrecta. No hay justificación técnica basada en la evidencia experimental, o el análisis es meramente descriptivo y no responde al objetivo del taller.

- **Nivel 2 — 3 puntos**  
  Hace una comparación general entre teoría y experimento, pero sin suficiente precisión. Puede mencionar que el error está “dentro” o “fuera” del rango esperado sin evidencias claras, sin estimar bien la amplitud observada o sin explicar adecuadamente las variaciones.

- **Nivel 3 — 4 puntos**  
  Compara adecuadamente las gráficas de error con el límite teórico y concluye de forma correcta si los valores observados son razonables. La justificación existe, aunque puede ser breve o poco profunda en la explicación de las variaciones experimentales.

- **Nivel 4 — 6 puntos**  
  Compara de forma rigurosa los errores observados en `Error_8b[mV]` y `Error_6b[mV]` con el límite teórico de ±(1/2)LSB. Usa las gráficas de Teleplot como evidencia, identifica amplitudes máximas observadas y argumenta con claridad si los datos cumplen o no con el modelo teórico. Explica de manera técnica las diferencias entre teoría y medición, considerando el comportamiento del ruido, la granularidad y las limitaciones del montaje experimental.

## 3. Conclusiones y razonamiento

- **Nivel 1 — 0 puntos**  
  Afirma incorrectamente que `Mic_12b` es una señal ideal sin error, o da una respuesta sin justificación técnica suficiente. Evidencia confusión conceptual sobre la naturaleza del proceso A/D y el ruido de cuantización.

- **Nivel 2 — 1 punto**  
  Muestra una comprensión parcial de la pregunta. Reconoce alguna limitación de `Mic_12b`, pero la explicación es ambigua, incompleta o poco conectada con el fundamento matemático del taller.

- **Nivel 3 — 2 puntos**  
  Responde correctamente la pregunta crítica e identifica que la señal de 12 bits también posee error de cuantización. La justificación es válida, aunque no profundiza completamente en la diferencia entre referencia práctica e ideal teórico.

- **Nivel 4 — 3 puntos**  
  Responde con precisión que `Mic_12b` no está verdaderamente libre de ruido de cuantización, sino que actúa como la mejor referencia disponible dentro del experimento. Justifica matemáticamente esta idea con claridad, diferenciando entre señal ideal teórica y señal digitalizada real. La conclusión demuestra comprensión profunda de la cuantización y del alcance de la aproximación usada en el código.

## 4. Formato IEEE y gráficas

- **Nivel 1 — 0 puntos**  
  No se sigue el formato IEEE de forma suficiente o el informe presenta deficiencias severas de estructura. Las gráficas faltan, son ilegibles o no están vinculadas al análisis escrito.

- **Nivel 2 — 1 punto**  
  El informe presenta cumplimiento parcial del formato IEEE. Las gráficas existen, pero pueden tener problemas de nitidez, ejes poco visibles, escasa relación con el texto o falta de numeración y referencia adecuada.

- **Nivel 3 — 2 puntos**  
  El informe sigue en gran medida el formato IEEE y presenta gráficas útiles y legibles. Puede haber detalles menores de formato, rotulación o referenciación, pero no afectan seriamente la comprensión del documento.

- **Nivel 4 — 3 puntos**  
  El informe cumple estrictamente el formato IEEE a doble columna y se mantiene dentro de la extensión máxima solicitada. Las gráficas de Teleplot son claras, legibles, pertinentes y están correctamente integradas al texto. Los ejes, unidades y variables son visibles; las figuras están numeradas, referenciadas y respaldan directamente el análisis presentado.

## Tabla resumen para Moodle

| Criterio | Nivel 1 | Nivel 2 | Nivel 3 | Nivel 4 |
|---|---:|---:|---:|---:|
| Cálculos teóricos: LSB y SNR | 0 | 4 | 6 | 8 |
| Análisis experimental del error | 0 | 3 | 4 | 6 |
| Conclusiones y razonamiento | 0 | 1 | 2 | 3 |
| Formato IEEE y gráficas | 0 | 1 | 2 | 3 |
