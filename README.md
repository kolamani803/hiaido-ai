# HiAIDo.ai
**Build and Ops with AI**

HiAIDo.ai is an enterprise AI cloud-operations workspace for infrastructure visibility, AI-assisted operations, automation, observability, MCP integrations and governance.

## Product workspaces

- Command Center and provider health overview
- Resource Explorer and environment views
- AI Operations Copilot workspace
- Observability, SRE and incident management
- Automation Studio and dashboard builder
- Knowledge Hub for runbooks and internal documentation
- MCP Marketplace for OpenShift, NetApp ONTAP, AWS, Azure, GCP, VMware, observability and custom MCP servers
- Secure terminal workspace concept
- FinOps, tasks, governance, audit and administration

The UI distinguishes product capabilities from connected services. It does not fabricate infrastructure metrics or simulated AI responses.

## Current implementation status

### Frontend
The GitHub Pages site is a public product preview. It includes a Microsoft Entra browser sign-in integration scaffold using MSAL Browser. Authentication remains disabled until the public identifiers in `config.js` are configured and the matching Entra app registrations, redirect URI, delegated API scope and role assignment are created.

Only public identifiers belong in `config.js`. Never put client secrets, API tokens, certificates or infrastructure credentials in frontend files.

### API
The FastAPI backend now includes:
- Entra v2 access-token validation against tenant-specific Microsoft JWKS
- Required API audience, issuer, tenant and application-role checks
- Fail-closed behavior when Entra configuration is absent
- `GET /health` and database-backed `GET /ready`
- `GET /api/v1/me`
- Tenant-scoped integration registry endpoints
- HTTPS-only validation for remote Streamable HTTP MCP endpoints
- Secret-manager reference storage only; raw secrets are never accepted
- Read-only Kubernetes/OpenShift inventory overview
- Optional ONTAP REST cluster connectivity with TLS verification enabled by default

The integration registry records metadata with status `pending_validation`; it does **not** launch MCP servers. A separate isolated worker runtime, policy engine, secret manager and approval service are still required before any tool invocation or write action can be enabled.

### PostgreSQL
Alembic migration `0001_initial` creates tenant-scoped `integrations` and `audit_events` tables. Run migrations explicitly as a deployment step:
```bash
cd backend
alembic upgrade head
```

A local PostgreSQL service is defined in `docker-compose.yml`. The example password is for local development only.

## Entra configuration

Create an Entra single-page application registration for the frontend and a separate API app registration:
1. Configure the exact GitHub Pages redirect URI: `https://kolamani803.github.io/hiaido-ai/`.
2. Expose a delegated API scope such as `api://<API-APP-CLIENT-ID>/access_as_user`.
3. Define an app role named `HiAIDo.Access` and assign it to the intended users/groups.
4. Grant the SPA delegated permission to the API scope and grant admin consent as required by your tenant.
5. Set `tenantId`, `clientId` (SPA client ID) and `apiScope` in `config.js`.
6. Configure the API deployment environment with `ENTRA_TENANT_ID`, `ENTRA_API_AUDIENCE` (the API app's audience/client ID or configured Application ID URI as appropriate for the token), and `ENTRA_REQUIRED_APP_ROLE=HiAIDo.Access`.
7. Configure `CORS_ORIGINS` to the exact trusted frontend origin.

Do not enable access until the token's `aud`, `iss`, `tid` and `roles` claims have been verified against the actual Entra-issued access token in your tenant.

## OpenShift deployment scaffold

`deploy/openshift/api.yaml` provides:
- Dedicated service account
- ClusterRole limited to get/list/watch for nodes and pods
- Two-replica API deployment
- Non-root container, read-only root filesystem, dropped Linux capabilities and resource limits
- Kubernetes health/readiness probes
- Internal service and TLS-terminating OpenShift Route

Before applying:
1. Build and publish the backend image; replace the image tag in the manifest with the immutable release tag.
2. Create namespace `hiaido`.
3. Create secret `hiaido-api-secrets` with `DATABASE_URL`, `ENTRA_TENANT_ID`, `ENTRA_API_AUDIENCE`, and any optional ONTAP credentials.
4. Configure the external PostgreSQL service, TLS, backups and network policy.
5. Review the cluster-wide read-only RBAC grant with the platform security team.
6. Apply the manifest and run Alembic migrations as a controlled release job before scaling the API.

The current API image workflow publishes to GHCR when backend files change. Cluster deployment is intentionally not automated: it requires an approved target cluster, image pull configuration, secrets, and an authorized release process.

## Not production-ready yet

The following are still roadmap items and must not be represented as active:
- Isolated MCP worker pool for stdio and Streamable HTTP
- Secret-manager integration and credential rotation
- AI model gateway, streaming chat, model routing and grounded retrieval
- Full Entra group-to-workspace RBAC and multi-tenant administration UI
- Approval engine and policy-enforced tool execution
- Durable event pipeline, comprehensive immutable audit, alerting and SLOs
- Full Kubernetes inventory permissions, cloud connectors, ONTAP telemetry and ITSM integrations
- Automated tests, threat modeling, penetration testing and production operational runbooks

The backend is a foundation, not a certified production SaaS service. Do not expose it before the identity, database, network, secrets and security review are complete.

## Public preview and deployment

Frontend URL: https://kolamani803.github.io/hiaido-ai/

GitHub Actions deploys the static frontend to GitHub Pages on pushes to `main`. GitHub Pages should use **GitHub Actions** as its publishing source.

Backend image workflow: `.github/workflows/backend-image.yml`. Publishing requires GitHub Actions package write permissions and appropriate GHCR package access.

Never commit credentials, API tokens, kubeconfigs, private keys or production connection strings.
