# ⚠️ CONFIDENCIAL — SOLO PARA EL PROFESOR ⚠️

# CONFIDENCIAL — SOLO PARA EL PROFESOR

---

# UNIVERSIDAD SANTO TOMÁS

### Facultad de Ingeniería Electrónica

### Introducción a la Ingeniería de Datos e IA — 2026-1

---

## PARCIAL 1 — CLAVE DE RESPUESTAS

### Ciclo de Vida del Dato, Pilares Transversales y Visualización de Datos

---

## PREGUNTA 1 — Selección múltiple (30 puntos)

### Enunciado

Una empresa de telecomunicaciones opera un sistema que genera millones de registros de llamadas (CDRs) cada hora. El equipo de ingeniería de datos diseñó un pipeline donde los CDRs se transportan mediante flujos continuos de eventos hacia un almacén centralizado. Sin embargo, dado que los datos son técnicamente ilimitados (*unbounded*), el equipo definió ventanas de tiempo de 15 minutos para agruparlos y procesarlos en bloques.

Considerando las decisiones clave de ingeniería en la etapa de ingesta (bounded vs. unbounded, frecuencia, síncrona vs. asíncrona, rendimiento y escalabilidad), ¿cuál de las siguientes afirmaciones describe correctamente lo que está haciendo este equipo?

---

### ✅ Respuesta correcta: **b)**

> Están realizando una ingesta de tipo *streaming* sobre datos *unbounded*, y la definición de ventanas de 15 minutos es precisamente la técnica de "acotar" flujos continuos en lotes manejables, sin que los datos dejen de ser inherentemente ilimitados.

---

### Justificación de la respuesta correcta

Según la presentación CL2, diapositiva 9 (*Ingesta de datos*), la etapa de ingesta se define como "mover datos desde sistemas fuente hacia almacenamiento; aquí se diseñan activamente los pipelines para consumo posterior." En esa misma diapositiva, la sección **Bounded vs. Unbounded** establece que "los datos son flujos continuos; se 'acotan' al definir ventanas/lotes." La sección **Frecuencia** distingue entre Batch (intervalos, grandes volúmenes) y Streaming (eventos continuos). La opción b) refleja exactamente esta conceptualización: los CDRs son datos unbounded procesados en streaming, y las ventanas de 15 minutos son la técnica de acotamiento, no una eliminación de su naturaleza continua.

---

### Por qué las demás opciones son incorrectas

**a) Incorrecta.** Afirma que es un patrón batch puro y que las ventanas "eliminan la naturaleza continua." Esto contradice directamente la diapositiva CL2-9, donde se explica que los datos siguen siendo unbounded a pesar de acotarlos en ventanas. La naturaleza del flujo no cambia por definir ventanas; lo que cambia es cómo se procesan. Un patrón batch puro implicaría intervalos programados con volúmenes finitos predeterminados, no flujos continuos acotados.

**b) CORRECTA.**

**c) Incorrecta.** Confunde la definición de ventanas de tiempo con ingesta síncrona. Según CL2-9, la ingesta síncrona implica acoplamiento entre origen y destino (ambos deben estar disponibles simultáneamente), mientras que la asíncrona "usa búferes/colas para desacoplar y resistir fallos." Las ventanas de tiempo son un mecanismo de procesamiento de flujos, no un indicador de que el origen y destino estén acoplados sincronamente.

**d) Incorrecta.** Confunde ingesta con transformación. Según CL2-11 y CL3-10, la transformación consiste en "limpiar, estandarizar y aplicar reglas de negocio para que los datos sean coherentes." Definir ventanas de tiempo no es aplicar lógica de negocio ni limpieza; es una decisión de diseño del pipeline de ingesta para manejar datos continuos. La CL2-9 ubica explícitamente las decisiones de bounded/unbounded y frecuencia dentro de la etapa de ingesta.

---

### Fuentes de las presentaciones

- CL2, diapositiva 9: "Ingesta de datos" — definición, bounded vs. unbounded, frecuencia, síncrona vs. asíncrona, rendimiento y escalabilidad.
- CL2, diapositiva 11: "Transformación y modelado" — para distinguir que la transformación aplica lógica de negocio.
- CL3, diapositivas 8–10: Preguntas de repaso sobre las etapas del ciclo de vida.

---

---

## PREGUNTA 2 — Caso práctico integrador (70 puntos)

### Caso: AgroSensores del Altiplano S.A.S.

*(Se reproduce el escenario completo del parcial.)*

---

## Parte A — Diagnóstico del ciclo de vida y propuesta de mejora (20 puntos)

### Respuesta modelo

**1. Generación (Sistema Fuente):**
- *Situación actual:* Los sensores IoT generan datos de humedad, temperatura y luminosidad cada 10 segundos y los envían a un gateway local que los almacena en archivos CSV. Las fuentes son de tipo IoT/Archivos.
- *Problema:* La generación electrónica funciona, pero presenta fallas de calidad desde el origen: no hay registro de cuál sensor generó cada lectura (falta de identificación de la fuente) y el formato de marcas de tiempo no está estandarizado (algunos sensores usan formato 24h y otros AM/PM). Esto corresponde al riesgo principal de esta etapa señalado en CL2, diapositiva 12: calidad y schema change en la fuente.

**2. Ingesta:**
- *Situación actual:* Un técnico visita las fincas semanalmente con una USB para copiar los archivos CSV del gateway.
- *Problema:* La ingesta es completamente manual con frecuencia semanal, lo que equivale a un batch manual extremadamente lento. Para datos que se generan cada 10 segundos, una recolección semanal introduce un retraso inaceptable. No hay pipeline automatizado, no se define modalidad (batch o streaming), no se usa ningún método estándar (API, webhook, CDC, conector) y no hay manejo de ingesta síncrona o asíncrona con búferes o colas. Según CL2, diapositiva 9, la ingesta consiste en "mover datos desde sistemas fuente hacia almacenamiento; aquí se diseñan activamente los pipelines para consumo posterior", y en este caso no existe tal diseño.

**3. Almacenamiento:**
- *Situación actual:* Los CSV se guardan en la laptop personal del técnico sin respaldo. No existe copia en la nube ni en ningún otro medio.
- *Problema:* No hay redundancia, durabilidad ni política de respaldo. El robo de la laptop materializó el riesgo: se perdieron tres meses de datos. No se define un sistema de "landing" adecuado (object storage, DWH, HDFS o BD), no se gestiona la "temperatura" del dato (hot/warm/cold), no existe política de retención y no se consideran costos (FinOps). Según CL3, diapositiva 9, el almacenamiento gestiona "dónde vive" el dato, balanceando costos, durabilidad y velocidad de acceso, y aquí no se balancea nada.

**4. Transformación + Modelado:**
- *Situación actual:* El técnico filtra manualmente en Excel y copia los datos relevantes a otra hoja cuando el agrónomo los solicita.
- *Problema:* No hay limpieza automatizada, no se estandarizan formatos de fecha, no se aplican reglas de negocio ni se define un modelo de datos. No se usa ningún enfoque analítico (Inmon, Kimball, Data Vault, Wide Tables), ni se define el grain (nivel de detalle), ni se implementa normalización o desnormalización. No hay código (SQL o Spark/Python) ni orquestación del proceso de transformación. Según CL2, diapositiva 11, la transformación consiste en "aplicar lógica de negocio y estructura para convertir datos crudos en un producto útil", y aquí el filtrado manual no constituye una transformación real sino una manipulación ad hoc propensa a errores humanos y no reproducible.

**5. Servicio:**
- *Situación actual:* El agrónomo mira números en una hoja Excel sin gráficos y decide cuándo regar basándose en su intuición.
- *Problema:* La etapa de servicio está severamente degradada. No hay consumidores definidos (analistas, científicos de datos, aplicaciones), no se exponen los datos mediante dashboards, APIs, alertas ni datasets curados. No existe un producto final de datos (dashboard, dataset curado, API interna, feature store) que permita extraer valor. No se define un SLA de entrega. Según CL3, diapositiva 11, el servicio "consiste en exponer los datos ya listos y procesados para que los consumidores finales puedan extraer valor de ellos", y aquí los datos ni están listos ni se exponen de forma estructurada. Las decisiones del agrónomo por intuición evidencian que el ciclo de vida del dato no cumple su propósito: generar valor a partir de los datos.

**Propuesta de mejora para la etapa más crítica (Ingesta):**
- *Mejora concreta:* Implementar ingesta automatizada mediante conectividad celular o WiFi desde los gateways IoT, configurando un broker de mensajes (como MQTT) que transmita los datos automáticamente a un servicio de almacenamiento en la nube a intervalos regulares (por ejemplo, cada 5 minutos en modalidad micro-batch) o en streaming continuo, sin intervención humana.
- *Justificación:* Esta mejora resuelve los problemas identificados porque elimina el retraso semanal que hace inútiles los datos para decisiones oportunas, reduce la dependencia de una persona (el técnico) como punto único de falla, permite la detección temprana de anomalías en los cultivos al tener datos casi en tiempo real, y elimina el riesgo de pérdida de datos por medios físicos (USB, laptop). Además, al tener un pipeline diseñado, se habilitan las etapas posteriores (almacenamiento en la nube, transformación automatizada, servicio mediante dashboards).

---

### Rúbrica de calificación — Parte A (20 puntos)

| Criterio | Puntos |
|----------|--------|
| Identifica correctamente al menos 4 de las 5 etapas (Generación, Ingesta, Almacenamiento, Transformación, Servicio) y describe qué hace la empresa en cada una | 6 |
| Identifica problemas específicos y concretos (no genéricos) para cada etapa mencionada | 5 |
| Señala si alguna etapa está ausente o severamente degradada, con justificación | 2 |
| Propone una mejora concreta para la etapa más crítica | 4 |
| Justifica por qué la propuesta resuelve el problema identificado | 3 |

**Escala parcial:**
- 50 % (10 pts): Identifica al menos 3 etapas con descripciones superficiales, propone mejora genérica sin justificación sólida.
- 80 % (16 pts): Identifica las 5 etapas con problemas específicos del caso, propone mejora concreta con justificación.
- 100 % (20 pts): Todo lo anterior más: conecta los problemas entre etapas (cómo la falla en una afecta a las siguientes), distingue con claridad entre lo que la empresa hace y lo que debería hacer, y la mejora propuesta demuestra comprensión de los conceptos del curso (modalidad batch/streaming, pipeline, sistemas de almacenamiento, etc.).

### Fuentes: CL2, diapositiva 12 (plantilla del ciclo de vida con las 5 etapas: Generación, Ingesta, Almacenamiento, Transformación+Modelado, Servicio); CL2, diapositiva 9 (detalle de Ingesta); CL2, diapositiva 8 (Almacenamiento); CL2, diapositiva 11 (Transformación y modelado); CL3, diapositivas 8–11 (repaso de etapas); CL1, diapositivas 21–25 (ciclo de vida detallado).

---

## Parte B — Pilares transversales comprometidos (15 puntos)

### Respuesta modelo

**1. Seguridad (CL3, diapositiva 14; CL2, diapositiva 13):**
- *Falla:* No hay control de acceso a los archivos; cualquiera con la laptop podría acceder a todos los datos. No existe privilegio mínimo (cualquier persona accede a todo). No hay gestión de secretos. No hay segmentación ni auditoría (no se registra quién accede o modifica los archivos).
- *Consecuencia:* El robo de la laptop expuso todos los datos sin protección. Si los datos incluyeran información de las fincas o los propietarios, habría riesgo de violación de privacidad.

**2. Gestión de Datos / Data Management (CL3, diapositiva 15; CL2, diapositiva 13):**
- *Falla:* No hay gobernanza (no existen políticas sobre calidad, nomenclatura, ni estándares de formato). No hay lineage/trazabilidad (no se sabe de dónde viene cada dato). No hay calidad del dato (formatos inconsistentes de fechas, archivos nombrados sin convención). La gestión de datos proporciona "el marco estratégico para que el ingeniero no trabaje en un vacío técnico", y aquí ese marco no existe.
- *Consecuencia:* Los datos son incoherentes y no se puede confiar en ellos para tomar decisiones. El agrónomo no puede saber si un dato de humedad es confiable o de cuándo es realmente.

**3. Arquitectura de Datos (CL3, diapositiva 17; CL2, diapositiva 13):**
- *Falla:* No existe un diseño de sistema que evolucione con las necesidades. Todo se guarda en CSVs en una laptop sin estructura. No hay evaluación de trade-offs entre costo y accesibilidad. No hay decisiones reversibles (si se pierde la laptop, todo se pierde). La arquitectura de datos "define el diseño de sistemas que evolucionan con las necesidades de la empresa", y aquí no hay diseño alguno.
- *Consecuencia:* El sistema no es escalable. Si AgroSensores crece de 300 a 1000 sensores, el esquema actual colapsaría.

**Pilares adicionales (si el estudiante los menciona, sumar valor):**

**4. DataOps (CL3, diapositiva 16):** No hay metodologías ágiles ni procesos automatizados. Todo es manual, lo que impide reducir tiempos de entrega y mejorar calidad.

**5. Orquestación (CL3, diapositiva 18):** No hay coordinación automática de tareas. Cada paso depende de la intervención manual del técnico.

**6. Ingeniería de Software (CL3, diapositiva 19):** No hay código, no hay pipelines programáticos, no hay pruebas ni manejo de excepciones.

---

### Rúbrica de calificación — Parte B (15 puntos)

| Criterio | Puntos |
|----------|--------|
| Identifica correctamente al menos 3 pilares transversales | 3 |
| Para cada pilar, describe cómo se manifiesta la falla de manera concreta y específica al caso (no genérica) | 6 |
| Para cada pilar, explica la consecuencia práctica para la empresa | 6 |

**Escala parcial:**
- 50 % (7-8 pts): Identifica 3 pilares con descripciones superficiales o genéricas.
- 80 % (12 pts): Identifica 3 pilares con descripciones específicas del caso y al menos 2 consecuencias claras.
- 100 % (15 pts): Identifica 3+ pilares, todas las descripciones son específicas al caso con conexión explícita a las definiciones del curso, y cada pilar tiene consecuencia práctica.

### Fuentes: CL2, diapositiva 13 (diagrama de pilares transversales); CL3, diapositivas 12–19 (detalle de cada pilar).

---

## Parte C — Metadatos, linaje y riesgos (15 puntos)

### Respuesta modelo

**Metadatos faltantes (según CL1, diapositiva 20):**

1. **Quién** (Creador, Usuario, Sistema responsable): No se registra cuál sensor generó cada lectura, ni quién recopiló los datos, ni quién los modificó. Falta identificar el sistema o persona responsable.

2. **Cuándo** (Fecha de creación, Modificación, Último acceso): Las marcas de tiempo no están estandarizadas (24h vs. AM/PM), lo que impide saber con certeza cuándo se tomó cada lectura. No hay registro de cuándo se modificaron los archivos ni cuándo fue el último acceso.

3. **Cómo** (Método de recolección, Proceso, Origen): No se documenta el método de recolección (¿vía gateway? ¿copia directa?), ni el proceso de transferencia USB, ni el origen específico (finca, lote, sensor).

4. **Con qué versión** (Historial de cambios, Versión del software): No hay versionamiento de los archivos CSV. Cuando el técnico copia y filtra, se pierde el rastro del dato original. No se sabe qué firmware tienen los sensores.

5. **Qué permisos** (Niveles de acceso, Restricciones de seguridad): No existe control de quién puede acceder o modificar los archivos. Cualquier persona con acceso a la laptop puede alterar los datos.

**Por qué su ausencia convierte los datos en ruido:** Según el concepto clave de la CL1, diapositiva 20, "sin metadatos, el dato es ruido." Un valor de humedad "45.2" sin saber de qué sensor, de qué finca, a qué hora exacta, con qué calibración, ni quién lo registró, es un número sin significado. No puede usarse para tomar decisiones de riego porque carece de contexto que lo convierta en información.

**Relación del robo con linaje/provenance:** El linaje del dato es la "historia verificable del dato" que traza su recorrido desde el origen, a través de las transformaciones, hasta su uso (CL1, diapositiva 26). Al perder la laptop, se rompió completamente la cadena de linaje: no solo se perdieron los datos, sino toda posibilidad de reconstruir su historia.

**Riesgos materializados:**

1. **Pérdida de contexto:** Se perdió toda la información sobre el origen y significado de tres meses de datos. Sin la laptop, no se sabe qué datos existían, qué cubrían ni qué decisiones se tomaron con base en ellos.

2. **Mala calidad:** Los datos que quedan (en las fincas, en gateways) tienen formatos inconsistentes, sin estandarización, haciéndolos inexactos, incompletos y desactualizados.

3. **Sesgos:** Si se reconstruye el dataset solo con los datos que aún existen en gateways (parciales), los análisis futuros tendrán un sesgo de supervivencia: solo se analizarán las fincas donde todavía queden datos, no todas las que se monitoreaban.

4. **Privacidad** (potencial): Si los CSV contenían datos de ubicación de fincas o información de los agricultores, el robo expone información sensible sin cifrado ni protección.

---

### Rúbrica de calificación — Parte C (15 puntos)

| Criterio | Puntos |
|----------|--------|
| Identifica correctamente los 5 componentes del contexto mínimo y explica cuáles faltan en el caso | 4 |
| Explica por qué la ausencia de metadatos convierte los datos en ruido (con referencia conceptual) | 3 |
| Relaciona el robo de la laptop con el concepto de linaje/provenance de manera precisa | 3 |
| Identifica al menos 3 riesgos concretos con explicación específica al caso | 5 |

**Escala parcial:**
- 50 % (7-8 pts): Menciona al menos 3 componentes de metadatos y 2 riesgos, pero sin conexión clara al caso.
- 80 % (12 pts): Cubre los 5 componentes, conecta con linaje, identifica 3 riesgos vinculados al caso.
- 100 % (15 pts): Cobertura completa de metadatos con ejemplos del caso, relación profunda con linaje, y 3+ riesgos con explicación detallada de cómo se manifiestan en AgroSensores.

### Fuentes: CL1, diapositiva 20 (metadatos y contexto mínimo, concepto clave "sin metadatos el dato es ruido"); CL1, diapositiva 26 (linaje y riesgos en el origen: sesgos, pérdida de contexto, privacidad, mala calidad).

---

## Parte D — Visualización para la toma de decisiones (20 puntos)

### Respuesta modelo

**1. Definición de la Tríada (CL5, diapositiva 13):**

- **Audiencia (Quién):** Inversionistas. No son técnicos en agronomía ni en datos. Necesitan una visión ejecutiva, clara y orientada a resultados de negocio, no detalles granulares de sensores.

- **Acción (Qué):** Que los inversionistas conozcan el impacto del monitoreo en el rendimiento de los cultivos y, como resultado, mantengan o incrementen su inversión en AgroSensores. La acción deseada es generar confianza en el modelo de negocio.

- **Datos (Cómo):** Datos agregados del semestre: tendencias de humedad, temperatura y luminosidad por finca; correlación con rendimiento del cultivo; métricas de cobertura de sensores. No datos crudos de cada sensor.

**2. Tipos de gráficas propuestas:**

- **Gráfico de líneas (tendencia temporal):** Para mostrar la evolución de las variables (humedad, temperatura) a lo largo del semestre. Según Knaflic (CL5, diapositivas 18–20), los gráficos de líneas son ideales para mostrar tendencias en el tiempo. Permite al inversionista ver patrones estacionales y el impacto de las decisiones de riego. Se usarían líneas sólidas para datos reales y punteadas para pronósticos (como el ejemplo de CL5, diapositiva 40).

- **Gráfico de barras horizontales:** Para comparar el rendimiento entre fincas monitoreadas. Según Knaflic, las barras horizontales facilitan la lectura de categorías con nombres largos (nombres de fincas) y el orden descendente permite identificar rápidamente las más productivas (CL5, diapositiva 43). Se evita el gráfico de torta porque sería difícil comparar muchas fincas con precisión.

- **Se evita:** Gráficos de torta (dificultad para comparar con muchas categorías), tablas extensas (audiencia no técnica), y gráficos 3D (añaden desorden sin valor).

**3. Principios de la Gestalt y atributo preatentivo (CL5, diapositivas 22–27):**

- **Proximidad:** Agrupar las métricas relacionadas visualmente cerca unas de otras. Por ejemplo, colocar juntos el gráfico de humedad y el de riego de una misma finca, para que el inversionista los perciba como parte de un mismo análisis sin necesidad de buscar la relación.

- **Similitud:** Usar el mismo color para representar la misma variable en todos los gráficos del dashboard. Por ejemplo, azul para humedad en todos los gráficos y naranja para temperatura. Esto permite que el ojo identifique rápidamente a qué variable se refiere cada elemento.

- **Atributo preatentivo — Color:** Usar un color de atención (por ejemplo, rojo) únicamente para resaltar las fincas con bajo rendimiento o los periodos donde las variables salieron de rango óptimo, como en el ejemplo de CL5, diapositiva 41, donde un solo color destaca los objetivos no alcanzados. Esto dirige la atención del inversionista inmediatamente al punto más importante sin necesidad de leer toda la gráfica.

**Minimización de la carga cognitiva:** Según CL5, diapositiva 21, "cada elemento que se añade a una página o pantalla requiere un esfuerzo mental de la audiencia para ser procesado. El objetivo del comunicador debe ser minimizar la carga cognitiva percibida." Para inversionistas no técnicos, esto es especialmente crítico: se deben eliminar líneas de cuadrícula innecesarias, colores decorativos, leyendas redundantes y cualquier elemento que no comunique información (eliminación de desorden/clutter). Cada elemento visual debe justificar su presencia.

Además, según CL5, diapositiva 34, "el diseño de la visualización (la forma) debe estar dictado por lo que queremos que nuestra audiencia haga con los datos (la función)." Si la función es que inviertan más, la forma debe mostrar éxito y tendencias positivas de manera inmediatamente visible.

---

### Rúbrica de calificación — Parte D (20 puntos)

| Criterio | Puntos |
|----------|--------|
| Define correctamente los 3 elementos de la Tríada adaptados al caso (no genéricos) | 5 |
| Propone al menos 2 tipos de gráficas con justificación basada en Knaflic | 5 |
| Aplica correctamente al menos 2 principios Gestalt al diseño del dashboard | 4 |
| Aplica al menos 1 atributo preatentivo con ejemplo concreto | 3 |
| Explica el concepto de carga cognitiva y su relevancia para esta audiencia | 3 |

**Escala parcial:**
- 50 % (10 pts): Define la Tríada de forma genérica, propone gráficas sin justificación sólida, menciona Gestalt pero sin aplicación concreta.
- 80 % (16 pts): Tríada bien definida y adaptada, al menos 2 gráficas con justificación clara, aplica 2 principios Gestalt con ejemplos y menciona carga cognitiva.
- 100 % (20 pts): Todo lo anterior más: atributo preatentivo con ejemplo específico del dashboard, conexión explícita con diapositivas del curso, y reflexión sobre por qué el diseño debe servir a la función (forma sigue función).

### Fuentes: CL5, diapositiva 11 (contexto situacional); CL5, diapositiva 13 (Tríada: Audiencia, Acción, Datos); CL5, diapositiva 14 (objetivo claro, medio de comunicación, estilo y tono, cómo respaldarlo); CL5, diapositivas 16–20 (tipos de visualizaciones); CL5, diapositiva 21 (carga cognitiva); CL5, diapositivas 22–27 (principios Gestalt: Proximidad, Similitud, Encierro, Cierre, Continuidad, Conexión); CL5, diapositiva 34 (forma sigue función); CL5, diapositivas 39–43 (ejemplos aplicados).

---

## ⚠️ CONFIDENCIAL — SOLO PARA EL PROFESOR ⚠️
