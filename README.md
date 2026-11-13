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

The UI includes tenant-backed operational registries for incidents, workflows, knowledge articles, dashboards, tasks, approvals and SLO definitions; an audit viewer; live resource inventory; a configurable Copilot chat panel; and an MCP registration form. Features requiring external providers remain explicitly marked as unavailable until configured.

## Current implementation status

### Frontend
The GitHub Pages site is a public product preview. Entra SSO is intentionally disabled for the initial release. Users sign in with administrator-created local accounts through the protected API. The first administrator is bootstrapped from server-side environment variables; there is no public self-registration route.

### API
The FastAPI backend includes local email/password authentication with Argon2 password hashing, administrator bootstrap and user management, tenant-scoped records and audit events, admin/operator/viewer roles, protected API routes, health/readiness endpoints, tenant-scoped integration registration, HTTPS-only remote MCP endpoint validation, secret-reference metadata, read-only Kubernetes/OpenShift inventory, optional ONTAP REST connectivity, operational workspace CRUD and an optional server-side AI chat gateway.

The integration registry records metadata with status `pending_validation`; it does **not** launch MCP servers. An isolated worker runtime, policy engine, secret manager and approval service are still required before tool invocation or write actions can be enabled. The Copilot currently has no live infrastructure or MCP tool context.

### PostgreSQL
Alembic migrations `0001_initial` through `0003_workspace_items` create tenant-scoped integration, audit, account and operational workspace tables. The connected Neon project uses PostgreSQL 17. For local development:
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
6. Configure the frontend API base URL.
7. Sign in with the bootstrap administrator and create operator, viewer or additional administrator accounts.

There is no public sign-up route. User creation and account deactivation require the administrator role. Passwords are stored as Argon2 hashes; session tokens expire after `TOKEN_TTL_HOURS` (default 8 hours). Entra SSO can be added later as an optional identity provider.

## Free Render deployment

A Render Blueprint is provided in `render.yaml` for a **free** web service in Singapore. No paid Render plan or Render-hosted database is provisioned. The app uses the existing Neon PostgreSQL database. The container runs versioned Alembic migrations at startup because Render's pre-deploy command is not available on its free web-service plan.

1. Connect this GitHub repository to Render and create a Blueprint from `render.yaml`.
2. Set `DATABASE_URL` using the Neon `hiaido_app` role connection string in Render's secret environment variables. Never commit it.
3. Set `BOOTSTRAP_ADMIN_EMAIL` and a unique `BOOTSTRAP_ADMIN_PASSWORD` of at least 16 characters. Render generates `SESSION_SECRET`.
4. Deploy and wait for `/health`; confirm `/ready` returns ready.
5. Set the frontend `HIAIDO_API_BASE` to the deployed HTTPS API origin and publish Pages again.

Free web services can spin down when idle and may take time to wake on the next request; they are suitable for a no-cost preview, not reliable production availability. The Blueprint does not configure an AI key, ONTAP credentials or cluster credentials. Add those only when required and approved. Never use production or employer credentials in a demo deployment.

## OpenShift deployment scaffold

`deploy/openshift/api.yaml` provides a dedicated service account, limited read-only node/pod RBAC, hardened deployment, health probes, internal service and TLS-terminating OpenShift Route.

Before applying, build and publish the backend image, create namespace and secret, configure PostgreSQL/TLS/backups/network policy, review RBAC, run `deploy/openshift/migrate-job.yaml`, deploy and verify health/readiness. Cluster deployment is intentionally not automated and requires an approved target cluster and authorized release process.

## Enterprise workspace modules

The enterprise navigation includes service catalog, projects and applications, architecture records, deployment tracking, change intelligence, asset inventory, infrastructure exploration, incidents, SLO definitions, runbooks, automation definitions, AI agent registry, knowledge, approvals, security findings, FinOps, operational analytics, integrations/MCP, audit and administration. The additional workspace records are tenant-scoped in PostgreSQL and support create/list/update with audit events.

The initial release deliberately distinguishes persisted definitions from live execution:
- Agent, workflow, architecture, service, asset, change, policy and runbook records are persisted and editable.
- MCP registrations store connection metadata only. They do not launch arbitrary server processes or invoke remote tools.
- Infrastructure inventory is read-only and only appears when an authorized Kubernetes/OpenShift runtime or configured provider responds.
- The AI gateway is provider-independent and requires an explicitly configured OpenAI-compatible endpoint, model and API key. No paid AI provider is enabled by default.
- Terminal sessions, live telemetry, cloud billing, predictive analytics, autonomous remediation and isolated MCP workers require additional secured runtime services and provider credentials.

## Not production-ready yet

Still roadmap: isolated MCP worker pool, secret-manager integration, AI model routing/streaming/retrieval grounding/live tool context, full Entra group RBAC, approval engine and policy-enforced tool execution, durable event pipeline, immutable audit, alerting/SLO telemetry, full cloud connectors, automated security testing and production runbooks.

The backend is a foundation, not a certified production SaaS service. Do not expose it before identity, database, network, secrets and security review are complete.

## Public preview

Frontend: https://kolamani803.github.io/hiaido-ai/

GitHub Actions deploys the static frontend to GitHub Pages on pushes to `main`. Backend image workflow: `.github/workflows/backend-image.yml`.

Never commit credentials, API tokens, kubeconfigs, private keys or production connection strings.
