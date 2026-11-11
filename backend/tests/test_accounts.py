import os

os.environ.setdefault("SESSION_SECRET", "test-only-session-secret-that-is-long-enough-123456")
os.environ.setdefault("BOOTSTRAP_ADMIN_EMAIL", "root@hiaido.test")
os.environ.setdefault("BOOTSTRAP_ADMIN_PASSWORD", "TestOnly-Strong-Password-2026!")
os.environ.setdefault("BOOTSTRAP_ADMIN_NAME", "Test Administrator")
os.environ.setdefault("DEFAULT_TENANT_ID", "test-tenant")
os.environ.setdefault("CORS_ORIGINS", "http://testserver")

from fastapi.testclient import TestClient
from main import app


def test_admin_login_user_lifecycle_and_role_boundaries():
    with TestClient(app) as client:
        assert client.get("/ready").status_code == 200

        login = client.post("/api/v1/auth/login", json={
            "email": "ROOT@HIAIDO.TEST",
            "password": "TestOnly-Strong-Password-2026!",
        })
        assert login.status_code == 200
        admin_headers = {"Authorization": "Bearer " + login.json()["access_token"]}

        bad_login = client.post("/api/v1/auth/login", json={
            "email": "root@hiaido.test", "password": "wrong-password"
        })
        assert bad_login.status_code == 401

        viewer = client.post("/api/v1/users", headers=admin_headers, json={
            "email": "viewer@hiaido.test",
            "name": "Read Only User",
            "password": "Viewer-Strong-Password-2026!",
            "role": "viewer",
        })
        assert viewer.status_code == 201
        viewer_id = viewer.json()["id"]

        duplicate = client.post("/api/v1/users", headers=admin_headers, json={
            "email": "viewer@hiaido.test",
            "name": "Duplicate User",
            "password": "Viewer-Strong-Password-2026!",
            "role": "viewer",
        })
        assert duplicate.status_code == 409

        viewer_login = client.post("/api/v1/auth/login", json={
            "email": "viewer@hiaido.test",
            "password": "Viewer-Strong-Password-2026!",
        })
        assert viewer_login.status_code == 200
        viewer_headers = {"Authorization": "Bearer " + viewer_login.json()["access_token"]}
        assert client.get("/api/v1/users", headers=viewer_headers).status_code == 403
        assert client.post("/api/v1/integrations", headers=viewer_headers, json={
            "name": "Denied MCP",
            "provider": "custom",
            "transport": "streamable_http",
            "endpoint": "https://mcp.example.com/mcp",
        }).status_code == 403

        operator = client.post("/api/v1/users", headers=admin_headers, json={
            "email": "operator@hiaido.test",
            "name": "Platform Operator",
            "password": "Operator-Strong-Password-2026!",
            "role": "operator",
        })
        assert operator.status_code == 201

        operator_login = client.post("/api/v1/auth/login", json={
            "email": "operator@hiaido.test",
            "password": "Operator-Strong-Password-2026!",
        })
        operator_headers = {"Authorization": "Bearer " + operator_login.json()["access_token"]}
        integration = client.post("/api/v1/integrations", headers=operator_headers, json={
            "name": "Example MCP",
            "provider": "custom",
            "transport": "streamable_http",
            "endpoint": "https://mcp.example.com/mcp",
            "access_mode": "read_only",
        })
        assert integration.status_code == 201
        assert integration.json()["status"] == "pending_validation"

        disabled = client.patch(
            "/api/v1/users/" + viewer_id + "/status?active=false",
            headers=admin_headers,
        )
        assert disabled.status_code == 200
        assert client.get("/api/v1/me", headers=viewer_headers).status_code == 401


def test_workspace_records_are_tenant_scoped_and_audited():
    with TestClient(app) as client:
        login = client.post("/api/v1/auth/login", json={
            "email": "root@hiaido.test",
            "password": "TestOnly-Strong-Password-2026!",
        })
        assert login.status_code == 200
        headers = {"Authorization": "Bearer " + login.json()["access_token"]}
        created = client.post("/api/v1/workspace/incident", headers=headers, json={
            "title": "API latency investigation",
            "status": "in_progress",
            "priority": "high",
            "owner": "platform-team",
            "payload": {"service": "api", "impact": "Elevated latency"},
        })
        assert created.status_code == 201
        item_id = created.json()["id"]
        listed = client.get("/api/v1/workspace/incident", headers=headers)
        assert listed.status_code == 200
        assert any(item["id"] == item_id for item in listed.json()["items"])
        updated = client.patch("/api/v1/workspace/incident/" + item_id, headers=headers, json={"status": "completed"})
        assert updated.status_code == 200
        audit = client.get("/api/v1/audit", headers=headers)
        assert audit.status_code == 200
        assert any(row["action"] == "workspace.incident.create" for row in audit.json()["items"])
