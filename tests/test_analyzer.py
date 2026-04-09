import json, pytest
from analyzer import score_label, _parse_analysis

def test_score_label_excelente():
    assert score_label(10) == "Excelente"
    assert score_label(8) == "Excelente"

def test_score_label_bueno():
    assert score_label(7) == "Bueno"
    assert score_label(5) == "Bueno"

def test_score_label_en_desarrollo():
    assert score_label(4) == "En desarrollo"
    assert score_label(1) == "En desarrollo"

def test_parse_valid_json():
    raw = json.dumps({
        "nombre": "Juan Pérez", "años_experiencia": 5,
        "nivel_estudios": "Licenciatura", "habilidades_coincidentes": ["Python"],
        "puntaje": 8, "resumen": "Buen perfil",
        "fortaleza": "Técnico fuerte", "debilidades": ["Área 1", "Área 2"]
    })
    result = _parse_analysis(raw)
    assert result["nombre"] == "Juan Pérez"
    assert result["score_label"] == "Excelente"

def test_parse_json_embedded_in_text():
    raw = 'Texto antes {"nombre": "Ana", "años_experiencia": 2, "nivel_estudios": "Maestría", "habilidades_coincidentes": [], "puntaje": 6, "resumen": "ok", "fortaleza": "comunicación", "debilidades": ["d1", "d2"]} texto después'
    result = _parse_analysis(raw)
    assert result["nombre"] == "Ana"
    assert result["score_label"] == "Bueno"

def test_parse_fallback_on_bad_json():
    result = _parse_analysis("esto no es json")
    assert result["nombre"] == "No identificado"
    assert result["puntaje"] == 5
