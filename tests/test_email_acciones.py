import os, pytest
os.environ.setdefault("GOOGLE_API_KEY", "test")

from email_sender import (
    _build_aceptado_html,
    _build_agendado_html,
    _build_rechazado_html,
    send_action_email,
)

def test_aceptado_html_contiene_fecha_y_nombre():
    html = _build_aceptado_html("Juan Pérez", "Acme Corp", "2026-06-01")
    assert "Juan Pérez" in html
    assert "2026-06-01" in html
    assert "Acme Corp" in html

def test_agendado_html_contiene_cita():
    html = _build_agendado_html("María García", "Acme", "2026-05-20", "10:00", "Entrevista por Zoom")
    assert "2026-05-20" in html
    assert "10:00" in html
    assert "Entrevista por Zoom" in html

def test_agendado_html_omite_notas_vacias():
    html = _build_agendado_html("Ana", "Acme", "2026-05-20", "10:00", "")
    assert "📝" not in html

def test_rechazado_html_contiene_nombre_y_empresa():
    html = _build_rechazado_html("Pedro Ruiz", "TechCo")
    assert "Pedro Ruiz" in html
    assert "TechCo" in html

def test_rechazado_html_es_empatico():
    html = _build_rechazado_html("Pedro Ruiz", "TechCo")
    assert "agradecemos" in html.lower() or "agradece" in html.lower()

def test_send_action_email_sin_credenciales_retorna_false(monkeypatch):
    monkeypatch.delenv("GMAIL_USER", raising=False)
    monkeypatch.delenv("GMAIL_APP_PASSWORD", raising=False)
    assert send_action_email("x@test.com", "Test", "aceptado", fecha_inicio="2026-06-01") is False

def test_send_action_email_accion_invalida():
    result = send_action_email("x@test.com", "Test", "invalida")
    assert result is False

def test_html_escapa_caracteres_especiales():
    html = _build_aceptado_html('<script>alert(1)</script>', "Acme", "2026-06-01")
    assert "<script>" not in html
