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
The GitHub Pages site is a public product preview. Entra SSO is intentionally disabled for the initial release. Users sign in with administrator-created local accounts through the protected API. The first administrator is bootstrapped from server-side environment variables; there is no public self-registration route.

### API
The FastAPI backend now includes:
- Local email/password authentication with Argon2 password hashing and signed, expiring session tokens
- First-administrator bootstrap from protected environment variables
- Administrator-only user creation, user listing and account deactivation
- Tenant-scoped user records and audit events for login and account administration
- Role levels: admin, operator and viewer
- Protected API routes using bearer session tokens
- Fail-closed behavior when the session signing secret is missing or too short
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

## Account setup

1. Configure PostgreSQL and set `DATABASE_URL`.
2. Generate a random `SESSION_SECRET` of at least 32 characters.
3. Set `BOOTSTRAP_ADMIN_EMAIL`, `BOOTSTRAP_ADMIN_PASSWORD` (at least 16 characters), and optionally `BOOTSTRAP_ADMIN_NAME` in the backend secret store.
4. Run migrations with `cd backend && alembic upgrade head`.
5. Start the API. On first startup, it creates the bootstrap administrator only if no administrator account exists.
6. Configure the frontend API base URL in `config.js` or the Administration page.
7. Sign in with the bootstrap administrator and create operator, viewer or additional administrator accounts.

There is no public sign-up route. User creation and account deactivation require the administrator role. Passwords are stored as Argon2 hashes; session tokens are signed and expire after `TOKEN_TTL_HOURS` (default 8 hours). Entra SSO can be added later as an optional identity provider.

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
3. Create secret `hiaido-api-secrets` with `DATABASE_URL`, a random `SESSION_SECRET` (32+ characters), `BOOTSTRAP_ADMIN_EMAIL`, `BOOTSTRAP_ADMIN_PASSWORD` (16+ characters), and any optional ONTAP credentials.
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
