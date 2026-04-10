from unittest.mock import patch

import pytest

import grader_agent.grading.pdf as pdf_grader


def test_extraer_texto_pdf_fitz_open_falla_valueerror():
    with patch("grader_agent.grading.pdf.fitz.open", side_effect=RuntimeError("boom")):
        with pytest.raises(ValueError, match="could not be read as a PDF"):
            pdf_grader.extraer_texto_pdf("cualquier.pdf")
