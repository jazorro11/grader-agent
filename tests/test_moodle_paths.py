from grader_agent.moodle_paths import parse_carpeta_moodle


def test_parse_carpeta_moodle_ejemplos_reales():
    p = parse_carpeta_moodle("ALEJANDRO TAFUR RODRIGUEZ_456290_assignsubmission_file")
    assert p["nombre_completo"] == "ALEJANDRO TAFUR RODRIGUEZ"
    assert p["id_estudiante"] == "456290"
    assert p["carpeta_origen"] == "ALEJANDRO TAFUR RODRIGUEZ_456290_assignsubmission_file"

    p2 = parse_carpeta_moodle("DANIEL CAMILO OCAMPO TORRES_456289_assignsubmission_file")
    assert p2["id_estudiante"] == "456289"
    assert "OCAMPO" in p2["nombre_completo"]


def test_parse_carpeta_moodle_sin_patron_usa_segmento_completo():
    p = parse_carpeta_moodle("carpeta_rara_sin_id")
    assert p["carpeta_origen"] == "carpeta_rara_sin_id"
    assert p["id_estudiante"] == ""
    assert p["nombre_completo"] == "carpeta_rara_sin_id"


def test_parse_carpeta_moodle_id_no_seis_digitos_no_matchea():
    p = parse_carpeta_moodle("JUAN_12345_assignsubmission_file")
    assert p["id_estudiante"] == ""
    assert p["nombre_completo"] == "JUAN_12345_assignsubmission_file"


def test_parse_carpeta_moodle_strip_espacios():
    p = parse_carpeta_moodle("  ANA LOPEZ_111222_assignsubmission_file  ")
    assert p["id_estudiante"] == "111222"
    assert p["nombre_completo"] == "ANA LOPEZ"
    assert p["carpeta_origen"] == "ANA LOPEZ_111222_assignsubmission_file"
