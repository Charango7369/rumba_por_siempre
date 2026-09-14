from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_home_loads():
    response = client.get("/")
    assert response.status_code == 200
    assert "Rumba X Siempre" in response.text


def test_quote_api_returns_estimate():
    response = client.post(
        "/api/cotizacion",
        json={
            "nombre": "Edwin",
            "telefono": "72836437",
            "ciudad": "Santa Cruz",
            "fecha": "2026-12-20",
            "tipo_evento": "Boda",
            "invitados": 180,
            "paquete": "premium",
            "extras": ["pantallas"],
        },
    )

    assert response.status_code == 200
    assert response.json()["resumen"]["estimado_bob"] >= 4100