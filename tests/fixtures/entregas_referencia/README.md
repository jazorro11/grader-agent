# Entregas de referencia (calibración)

Archivos de texto alineados con `tests/fixtures/rubrica_referencia.md`. El manifiesto `manifest.json` define **bandas manuales** `expected_min` / `expected_max` para el puntaje total del ítem (0–10).

Los tests de integración (`tests/test_calibration_integration.py`) calculan el `total_score` del pipeline y comprueban que caiga en la banda. La meta del brief (≥80% de aciertos con LLM real) se evalúa con tolerancia agregada: se exige que **al menos 4 de 5** casos pasen para considerar estable la corrida.
