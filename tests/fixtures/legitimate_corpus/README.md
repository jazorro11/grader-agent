# Corpus legítimo (falsos positivos)

Diez textos académicos en español e inglés con vocabulario que podría confundir heurísticas ingenuas (violencia histórica, “instrucciones del laboratorio”, “sistema”, “prompt” literario, menciones benignas de “ignore” en redes, etc.).

Los tests verifican que **no** haya coincidencias en `scan_text_for_policy_violations` y que, con `SKIP_LLM_VALIDATION=true`, `ContentValidationService` marque el texto como `clean` sin invocar chat completions al cliente OpenRouter.
