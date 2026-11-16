"""API docs are generated from the routes: check they are served and complete."""


def test_swagger_ui_is_served_offline(client):
    page = client.get("/api/v1/docs/swagger")
    assert page.status_code == 200
    assert b"swagger-ui" in page.data and b"unpkg" not in page.data and b"cdn" not in page.data.lower()


def test_spec_documents_every_route_and_the_booking_contract(client):
    spec = client.get("/api/v1/docs/openapi.json").get_json()
    assert set(spec["paths"]) == {
        "/api/v1/health", "/api/v1/towns", "/api/v1/fares", "/api/v1/trips", "/api/v1/bookings",
        "/api/v1/bookings/{reference}", "/api/v1/admin/trips", "/api/v1/admin/trips/{trip_id}/status",
    }
    booking = spec["paths"]["/api/v1/bookings"]["post"]
    assert {"200", "201", "404", "409", "422"} <= set(booking["responses"])
    assert any(p["name"] == "Idempotency-Key" and p["in"] == "header" for p in booking["parameters"])
