# Rúbrica de Calificación — Taller: Dispositivo TinyML

**Asignatura:** Sistemas de Adquisición de Datos  
**Programa:** Ingeniería de Datos e Inteligencia Artificial — Universidad Santo Tomás  
**Semestre:** Primero

---

## Escala de valoración

| Nivel | Porcentaje | Descripción general |
|-------|-----------|---------------------|
| **Nivel 1** | 25% | Insuficiente — No cumple o cumple de forma muy superficial |
| **Nivel 2** | 50% | Básico — Cumple parcialmente, con vacíos importantes |
| **Nivel 3** | 75% | Bueno — Cumple satisfactoriamente con observaciones menores |
| **Nivel 4** | 100% | Excelente — Cumple a cabalidad con profundidad y rigor |

---

## Criterio 1: Justificación del Paradigma TinyML (Fase 1)

*Peso sugerido: 20%*

| Nivel | % | Descriptor |
|-------|---|------------|
| 1 | 25% | Menciona TinyML sin justificar por qué es preferible a la nube. No selecciona criterios (latencia, privacidad, ancho de banda, energía/costos) o los lista sin relacionarlos con su propuesta. |
| 2 | 50% | Selecciona al menos 3 criterios, pero la justificación es genérica o teórica. No conecta claramente cada criterio con las características específicas de su dispositivo. |
| 3 | 75% | Selecciona y justifica al menos 3 criterios con argumentos concretos vinculados a su propuesta. Algún criterio carece de profundidad o de un ejemplo que lo respalde. |
| 4 | 100% | Selecciona y justifica 3 o más criterios con argumentos sólidos, específicos y bien articulados. Demuestra comprensión clara de por qué el procesamiento en el borde es indispensable para su caso y no simplemente conveniente. |

---

## Criterio 2: Arquitectura del Sistema de Adquisición de Datos (Fase 2)

*Peso sugerido: 25%*

| Nivel | % | Descriptor |
|-------|---|------------|
| 1 | 25% | No identifica sensores concretos o los menciona de forma vaga. No aborda restricciones del entorno embebido ni describe el flujo de Machine Learning. |
| 2 | 50% | Identifica los sensores pero sin especificar las señales físicas exactas que se medirán. Menciona restricciones de hardware de manera superficial. El flujo de ML (entrenamiento e inferencia) se describe de forma incompleta o confusa. |
| 3 | 75% | Identifica sensores y señales físicas con claridad. Describe las restricciones de memoria, procesamiento y batería con relación a su diseño. Explica el flujo de entrenamiento e inferencia, aunque falta detalle en alguna de las dos fases. |
| 4 | 100% | Especifica con precisión los sensores, las señales físicas y su relevancia para el problema. Analiza cómo las restricciones del microcontrolador condicionan decisiones de diseño concretas (tipo de modelo, resolución de datos, frecuencia de muestreo, etc.). Describe con claridad tanto la fuente de datos históricos para entrenamiento como el proceso de inferencia en tiempo real. |

---

## Criterio 3: Evolución hacia IoT 2.0 — Intelligence of Things (Fase 3)

*Peso sugerido: 20%*

| Nivel | % | Descriptor |
|-------|---|------------|
| 1 | 25% | No diferencia entre IoT 1.0 e IoT 2.0. La propuesta se presenta como un sensor que solo transmite datos sin procesamiento local inteligente. |
| 2 | 50% | Menciona la diferencia entre IoT 1.0 e IoT 2.0, pero no argumenta de forma convincente cómo su dispositivo específico aporta inteligencia local. La explicación es teórica y no conecta con su propuesta. |
| 3 | 75% | Argumenta correctamente por qué su dispositivo pertenece al ecosistema IoT 2.0. Explica cómo identifica patrones, reconoce estados o predice eventos localmente, aunque la argumentación podría ser más detallada. |
| 4 | 100% | Argumenta con solidez la pertenencia al IoT 2.0 con ejemplos concretos de inteligencia local en su dispositivo (reconocimiento de patrones, clasificación de estados, predicción de eventos). Establece un contraste claro y bien fundamentado con un enfoque IoT 1.0 equivalente. |

---

## Criterio 4: Análisis Crítico frente al Caso de Éxito (Fase 4)

*Peso sugerido: 20%*

| Nivel | % | Descriptor |
|-------|---|------------|
| 1 | 25% | No hace referencia al caso del collar OpenSource para elefantes, o la referencia es superficial sin identificar similitudes ni obstáculos. |
| 2 | 50% | Identifica una similitud con el caso de referencia, pero es genérica (ej. "ambos usan sensores"). No anticipa obstáculos concretos para su propio dispositivo o los describe sin profundidad. |
| 3 | 75% | Identifica una similitud técnica, funcional o de impacto relevante y bien explicada. Anticipa obstáculos físicos, ambientales o técnicos para su dispositivo, aunque el análisis podría ser más específico o completo. |
| 4 | 100% | Identifica una similitud significativa y la explica con detalle técnico o funcional. Anticipa obstáculos realistas y específicos (condiciones climáticas, desgaste, autonomía energética, calidad de datos en campo, etc.) demostrando pensamiento crítico sobre el despliegue real de su dispositivo. |

---

## Criterio 5: Formato, Estructura y Comunicación del Entregable

*Peso sugerido: 15%*

| Nivel | % | Descriptor |
|-------|---|------------|
| 1 | 25% | No cumple con el formato PDF o excede significativamente las 2 páginas. Falta el título del proyecto o la descripción del problema. La estructura no sigue las 4 fases solicitadas. Redacción con errores frecuentes. |
| 2 | 50% | Entrega en PDF pero no respeta el límite de 2 páginas, o falta algún elemento estructural (título, descripción breve del problema, alguna fase). La redacción es comprensible pero desorganizada. |
| 3 | 75% | Cumple con el formato PDF y la extensión de 2 páginas. Incluye título, descripción del problema y las 4 fases. La redacción es clara, con observaciones menores de organización o presentación. |
| 4 | 100% | Cumple con todos los requisitos formales (PDF, máximo 2 páginas). Documento bien organizado con título claro, descripción concisa del problema y desarrollo ordenado de las 4 fases. Redacción precisa, coherente y con uso adecuado de vocabulario técnico. |

---

## Tabla resumen de pesos

| Criterio | Peso |
|----------|------|
| 1. Justificación del Paradigma TinyML | 20% |
| 2. Arquitectura del Sistema | 25% |
| 3. Evolución hacia IoT 2.0 | 20% |
| 4. Análisis Crítico — Caso de Éxito | 20% |
| 5. Formato, Estructura y Comunicación | 15% |
| **Total** | **100%** |

---

### Fórmula de calificación

**Nota final = Σ (porcentaje del nivel obtenido × peso del criterio)**

*Ejemplo: Un estudiante obtiene Nivel 4 (100%) en los criterios 1, 2 y 5, y Nivel 3 (75%) en los criterios 3 y 4.*  
*Nota = (100%×0.20) + (100%×0.25) + (75%×0.20) + (75%×0.20) + (100%×0.15) = 0.20 + 0.25 + 0.15 + 0.15 + 0.15 = **0.90 → 90/100***
