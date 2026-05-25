# Corpus malicioso (tests de guardrails)

Esta carpeta contiene **25** textos de ejemplo usados por `tests/test_guardrails_malicious_corpus.py` para verificar que la capa determinística (`scan_text_for_policy_violations`) detecta patrones de riesgo sin consumir tokens de LLM.

## Categorías y fuentes

| Archivos | Categoría | Fuente / notas |
| --- | --- | --- |
| `inject_es_01.txt` … `inject_es_05.txt` | Inyección directa (ES) | Inspirado en patrones típicos de **deepset/prompt-injections** y **neuralchemy/Prompt-injection-dataset** (HuggingFace): anulación de instrucciones, manipulación de rol y exfiltración de prompt, **reescritos** en contexto de entrega académica. |
| `inject_en_01.txt` … `inject_en_05.txt` | Inyección directa (EN) | Misma familia de patrones que arriba, en inglés, adaptados a un curso ficticio. |
| `indirect_01.txt` … `indirect_03.txt` | Inyección indirecta (texto “académico”) | Variantes “soft” basadas en el mismo tipo de datasets (solicitudes disfrazadas de metodología o políticas alternativas). |
| `encoding_01.txt` … `encoding_03.txt` | Ofuscación / encoding | Patrones de **ofuscación** comunes en colecciones de inyección (Base64 largo, secuencias `\x..` y `\u....` repetidas). |
| `profanity_es_01.txt`, `profanity_es_02.txt`, `profanity_en_01.txt` | Lenguaje grosero | **Redacción manual** para tests; frases extremas poco probables en textos académicos reales. |
| `sexual_01.txt` … `sexual_03.txt` | Contenido sexual / acoso | **Manual**; contenido explícito solo con fines de prueba automatizada en un entorno controlado. |
| `violent_01.txt` … `violent_03.txt` | Violencia / amenazas | **Manual**; amenazas inequívocas de ejemplo. |

## Referencias HuggingFace (datasets citados en el brief)

- [deepset/prompt-injections](https://huggingface.co/datasets/deepset/prompt-injections)
- [neuralchemy/Prompt-injection-dataset](https://huggingface.co/datasets/neuralchemy/Prompt-injection-dataset)

## Uso

Los tests leen todos los `*.txt` de esta carpeta y esperan **al menos un hallazgo** por archivo en la capa regex. No ejecutes estos textos contra personas ni los uses fuera del suite de pruebas.
