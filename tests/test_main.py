from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_home_loads():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "API operativa"

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
            "paquete": "paquete-rumba-apolo",
            "extras": ["pantallas"],
        },
    )
    assert response.status_code == 200
    assert response.json()["resumen"]["estimado_bob"] > 0
    assert "codigo_seguimiento" in response.json()
