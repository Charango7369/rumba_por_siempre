from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_public_services_endpoint():
    res = client.get("/api/v1/services")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    # Comprobar que no hay precios null
    for item in data:
        assert item["precio_base"] is not None
        assert "nombre" in item
        assert "slug" in item

def test_dynamic_quote_calculation():
    # Enviar cotización solicitando el servicio real y un extra
    res = client.post(
        "/api/v1/quotes",
        json={
            "nombre": "Carlos Perez",
            "telefono": "71234567",
            "ciudad": "Apolo",
            "fecha": "2026-12-15",
            "tipo_evento": "Matrimonio",
            "invitados": 200,
            "paquete": "paquete-rumba-apolo",
            "extras": ["pantallas", "humo"]
        }
    )
    assert res.status_code == 200
    body = res.json()
    assert "codigo_seguimiento" in body
    assert body["codigo_seguimiento"].startswith("RXS-")
    assert body["resumen"]["estimado_bob"] > 0
    # Desglose transparente
    desglose = body["resumen"]["desglose"]
    assert "paquete" in desglose
    assert "extras" in desglose
    assert len(desglose["extras"]) == 2

def test_auth_login_and_rbac_permissions():
    # 1. Login como SuperAdmin
    login_super = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@rumbaporsiempre.com", "password": "RumbaAdmin2026!"}
    )
    assert login_super.status_code == 200
    super_data = login_super.json()
    assert "access_token" in super_data
    token_super = super_data["access_token"]

    # 2. Login como Comercial
    login_comercial = client.post(
        "/api/v1/auth/login",
        json={"email": "ventas@rumbaporsiempre.com", "password": "VentasRxS2026!"}
    )
    assert login_comercial.status_code == 200
    comercial_data = login_comercial.json()
    token_comercial = comercial_data["access_token"]

    # 3. SuperAdmin tiene acceso a auditoría
    res_audit = client.get("/api/v1/admin/audit", headers={"Authorization": f"Bearer {token_super}"})
    assert res_audit.status_code == 200

    # 4. Comercial NO tiene acceso a auditoría (403 Forbidden)
    res_audit_forbidden = client.get("/api/v1/admin/audit", headers={"Authorization": f"Bearer {token_comercial}"})
    assert res_audit_forbidden.status_code == 403

    # 5. Comercial SÍ tiene acceso a ver cotizaciones
    res_quotes = client.get("/api/v1/admin/quotes", headers={"Authorization": f"Bearer {token_comercial}"})
    assert res_quotes.status_code == 200
