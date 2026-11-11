# HiAIDo.ai
**Build and Ops with AI**

HiAIDo.ai is an enterprise AI cloud-operations workspace designed to bring infrastructure visibility, AI-assisted operations, automation, observability, MCP integrations and governance into one product.

## Product experience

The responsive frontend includes:
- Unified command center and provider health overview
- Resource explorer and environment views
- AI Operations Copilot workspace
- Observability and SRE / incident-management workspaces
- Automation Studio and dashboard builder
- Knowledge Hub for runbooks and internal documentation
- MCP Marketplace for OpenShift, NetApp ONTAP, AWS, Azure, GCP, VMware, observability and custom MCP servers
- Secure terminal workspace concept
- FinOps and optimization workspace
- Tasks, activity, governance, audit and administration

The UI distinguishes product capabilities from connected services. It does not fabricate infrastructure metrics or simulate AI responses.

## Public preview

The GitHub Pages deployment is a **frontend preview**, not a production service. It has no user authentication, tenant isolation, persistent database, AI model gateway, MCP worker runtime, or production action execution. Do not enter credentials, tokens, confidential data or production information.

Some controls explain the intended production flow but do not establish integrations or execute operations. The API URL field is a browser-session convenience for testing a protected API; it does not add authentication or make a public API safe.

## Current backend starter

A FastAPI starter is available under `backend/`. It exposes:
- `GET /health`
- `GET /api/v1/overview`

The overview endpoint attempts read-only Kubernetes/OpenShift inventory using the service account or a configured kubeconfig, and can optionally test an ONTAP REST connection using server-side environment variables.

The backend is not yet a production-ready multi-tenant service. Its optional bearer-token check is not a replacement for Entra OIDC authentication, and the current overview contract is limited. Do not expose it publicly as-is.

## Production architecture roadmap

1. **Identity and tenancy:** Microsoft Entra OIDC, secure sessions, tenant isolation, workspace roles and group-based RBAC.
2. **API and persistence:** FastAPI service, PostgreSQL, migrations, audit/event storage and background job queue.
3. **AI gateway:** provider abstraction for approved models, streaming chat, tool selection, grounded retrieval, usage controls and prompt/tool audit.
4. **MCP runtime:** isolated worker pool supporting stdio and Streamable HTTP, per-server policy, scoped credentials, TLS verification, egress controls and lifecycle management.
5. **Integrations:** OpenShift/Kubernetes, NetApp ONTAP, AWS, Azure, GCP, VMware, Prometheus/Grafana, ITSM and knowledge sources.
6. **Operations:** observability, alerting, incidents, approvals, runbooks, workflow orchestration and controlled execution.
7. **Enterprise controls:** secrets manager, policy engine, immutable audit trail, rate limits, backup/restore and security monitoring.

## Deployment

GitHub Actions deploys the static frontend to GitHub Pages on pushes to `main`. In repository Settings → Pages, the publishing source should be **GitHub Actions**.

Frontend URL: https://kolamani803.github.io/hiaido-ai/

A successful Pages deployment does not deploy the FastAPI backend. Production backend deployment requires an approved container registry and protected Kubernetes/OpenShift namespace, Entra authentication, TLS, strict CORS, secret management and security review.

## Development

Frontend: `index.html` (self-contained HTML/CSS/JavaScript).
Runtime API URL can be set in Administration for the current browser session. The API must already be securely deployed and must implement the frontend's overview contract.

Backend dependencies: `backend/requirements.txt`.
Container build context: `backend/`.

Never commit credentials, API tokens, kubeconfigs, private keys or production connection strings.
