import csv
import io

from grader_agent.export_csv import resultados_entregables_a_csv


def test_csv_incluye_bom_y_ordena_por_nombre():
    criterios = ["Criterio A", "Criterio B"]
    resultados = [
        {
            "alumno": "Zeta",
            "nombre_completo": "Zeta",
            "id_estudiante": "2",
            "carpeta_origen": "z",
            "archivo_pdf": "a.pdf",
            "total_obtenido": 3,
            "total_maximo": 10,
            "criterios": [
                {"puntaje_obtenido": 1, "retroalimentacion": "r1"},
                {"puntaje_obtenido": 2, "retroalimentacion": "con, coma"},
            ],
        },
        {
            "alumno": "Alpha",
            "nombre_completo": "Alpha",
            "id_estudiante": "1",
            "carpeta_origen": "a",
            "archivo_pdf": "b.pdf",
            "total_obtenido": 5,
            "total_maximo": 10,
            "criterios": [
                {"puntaje_obtenido": 3, "retroalimentacion": "x"},
                {"puntaje_obtenido": 2, "retroalimentacion": "y\nlinea"},
            ],
        },
    ]
    csv_text = resultados_entregables_a_csv(resultados, criterios)
    assert csv_text.startswith("\ufeff")
    rows = list(csv.reader(io.StringIO(csv_text.lstrip("\ufeff"))))
    assert len(rows) == 3
    assert rows[1][1] == "Alpha"
    assert rows[2][1] == "Zeta"
    assert rows[1][0] == "1"


def test_csv_filas_incompletas_rellena_vacio():
    csv_text = resultados_entregables_a_csv(
        [
            {
                "nombre_completo": "Solo",
                "total_obtenido": 0,
                "total_maximo": 5,
                "criterios": [],
            }
        ],
        ["Uno", "Dos"],
    )
    assert "\ufeff" in csv_text[:5]
    rows = list(csv.reader(io.StringIO(csv_text.lstrip("\ufeff"))))
    assert len(rows) == 2
    assert rows[1][4:6] == ["0", "5"]
    assert rows[1][6:10] == ["", "", "", ""]


def test_csv_sin_filas_solo_encabezados():
    csv_text = resultados_entregables_a_csv([], ["Criterio"])
    rows = list(csv.reader(io.StringIO(csv_text.lstrip("\ufeff"))))
    assert len(rows) == 1
    assert rows[0][0] == "id_estudiante"


def test_csv_ordena_por_alumno_si_falta_nombre_completo():
    criterios: list[str] = []
    resultados = [
        {"alumno": "Zed", "total_obtenido": 1, "total_maximo": 1, "criterios": []},
        {"alumno": "Amy", "total_obtenido": 2, "total_maximo": 2, "criterios": []},
    ]
    csv_text = resultados_entregables_a_csv(resultados, criterios)
    rows = list(csv.reader(io.StringIO(csv_text.lstrip("\ufeff"))))
    assert rows[1][1] == "Amy"
    assert rows[2][1] == "Zed"
