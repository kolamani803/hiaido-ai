import os
from datetime import datetime, timezone
from typing import Any

import requests
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from kubernetes import client, config
from kubernetes.client.rest import ApiException

app = FastAPI(title="HiAIDo.ai API", version="0.1.0")
origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "").split(",") if x.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["Authorization", "Content-Type"],
)

def authorize(authorization: str | None) -> None:
    expected = os.getenv("HIAIDO_API_TOKEN")
    if expected and authorization != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="Unauthorized")

def kube_clients():
    try:
        config.load_incluster_config()
    except config.ConfigException:
        try:
            config.load_kube_config()
        except Exception as exc:
            raise RuntimeError("Kubernetes credentials are not available to the API service") from exc
    return client.CoreV1Api()

def pod_ready(pod: Any) -> bool:
    return any(c.type == "Ready" and c.status == "True" for c in (pod.status.conditions or []))

@app.get("/health")
def health():
    return {"status": "ok", "service": "hiaido-api"}

@app.get("/api/v1/overview")
def overview(authorization: str | None = Header(default=None)):
    authorize(authorization)
    providers: dict[str, Any] = {
        "openshift": {"connected": False},
        "ontap": {"connected": False},
    }
    resources: list[dict[str, str]] = []
    activity: list[dict[str, str]] = []
    resource_count = healthy_count = active_operations = 0

    try:
        core = kube_clients()
        nodes = core.list_node().items
        pods = core.list_pod_for_all_namespaces(limit=500).items
        resource_count = len(nodes) + len(pods)
        healthy_count = sum(1 for n in nodes if any(c.type == "Ready" and c.status == "True" for c in (n.status.conditions or [])))
        healthy_count += sum(1 for p in pods if pod_ready(p))
        providers["openshift"] = {"connected": True, "cluster": os.getenv("KUBERNETES_SERVICE_HOST", "in-cluster")}
        for node in nodes:
            ready = any(c.type == "Ready" and c.status == "True" for c in (node.status.conditions or []))
            resources.append({"name": node.metadata.name, "type": "Node", "environment": "Kubernetes", "status": "Healthy" if ready else "NotReady"})
        for pod in pods:
            phase = pod.status.phase or "Unknown"
            status = "Healthy" if pod_ready(pod) else ("Critical" if phase == "Failed" else phase)
            resources.append({"name": f"{pod.metadata.namespace}/{pod.metadata.name}", "type": "Pod", "environment": pod.metadata.namespace, "status": status})
            if phase in ("Pending", "Failed"):
                active_operations += 1
                activity.append({"title": f"Pod {pod.metadata.name}: {phase}", "source": pod.metadata.namespace, "time": pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else "Current"})
    except (RuntimeError, ApiException) as exc:
        providers["openshift"] = {"connected": False, "error": str(exc)[:240]}

    ontap_url = os.getenv("ONTAP_BASE_URL", "").rstrip("/")
    ontap_user = os.getenv("ONTAP_USERNAME")
    ontap_password = os.getenv("ONTAP_PASSWORD")
    if ontap_url and ontap_user and ontap_password:
        try:
            response = requests.get(
                f"{ontap_url}/api/cluster",
                auth=(ontap_user, ontap_password),
                verify=os.getenv("ONTAP_VERIFY_TLS", "true").lower() == "true",
                timeout=8,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            cluster_info = response.json().get("name", "ONTAP cluster")
            providers["ontap"] = {"connected": True, "name": cluster_info}
            resource_count += 1
        except requests.RequestException as exc:
            providers["ontap"] = {"connected": False, "error": str(exc)[:240]}

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "resource_count": resource_count,
        "healthy_count": healthy_count,
        "active_operations": active_operations,
        "connected_integrations": sum(1 for p in providers.values() if p.get("connected")),
        "providers": providers,
        "resources": resources[:100],
        "activity": activity[:20],
    }
