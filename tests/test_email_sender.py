from email_sender import build_email_html

def test_contains_name():
    html = build_email_html("Juan Pérez", "Excelente", "Técnico fuerte", ["D1", "D2"])
    assert "Juan Pérez" in html

def test_contains_score_label():
    html = build_email_html("Ana", "Bueno", "Comunicación", ["D1", "D2"])
    assert "Bueno" in html

def test_contains_both_weaknesses():
    html = build_email_html("Carlos", "En desarrollo", "Puntual", ["Mejorar redacción", "Agregar certificaciones"])
    assert "Mejorar redacción" in html
    assert "Agregar certificaciones" in html

def test_contains_strength():
    html = build_email_html("Laura", "Excelente", "Liderazgo excepcional", ["D1", "D2"])
    assert "Liderazgo excepcional" in html

def test_is_valid_html():
    html = build_email_html("Test", "Bueno", "F", ["D1", "D2"])
    assert "<!DOCTYPE html>" in html
    assert "</html>" in html
