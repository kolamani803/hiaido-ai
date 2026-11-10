# HiAIDo.ai
**Build and Ops with AI**

HiAIDo.ai is an AI-powered cloud operations workspace concept. This repository currently contains a deployable frontend prototype.

## Current prototype
- Responsive operations dashboard
- Workspace navigation and MCP marketplace entry point
- OpenShift, NetApp ONTAP, cloud infrastructure and AI builder tiles
- Sample environment health and activity views
- GitHub Pages deployment workflow

> The current site is a UI prototype with sample data. It does not yet provide real MCP connectivity, AI inference, persistent user accounts, authentication, or live infrastructure monitoring. Do not enter real credentials or sensitive information.

## Deploy
GitHub Actions deploys the static site to GitHub Pages on every push to `main`. In repository Settings → Pages, ensure the publishing source is set to **GitHub Actions** if GitHub has not enabled it automatically.

After a successful workflow, the deployment URL appears in Actions → Deploy HiAIDo.ai to GitHub Pages.

## Planned production architecture
- React frontend and FastAPI API
- PostgreSQL persistence
- Entra ID SSO and role-based access
- Isolated MCP workers supporting stdio and Streamable HTTP transports
- Secrets management, audit logs, and policy-controlled tool permissions
- Container deployment to Kubernetes / OpenShift

Production authentication and backend services must be implemented before issuing user credentials.


<!-- Pages deployment trigger: public demo setup -->


## Current UI and live-data mode
The frontend has been rebuilt around the original enterprise workspace concept: Dashboard, Resource Inventory, Environments, Operations, AI Assistant, Automation, Tools & Data, Activity & Tasks, Governance, Audit & History, and Administration. It no longer renders invented sample metrics. When the API is unavailable, values remain blank and the UI explains which connection is missing.

## Backend starter (not yet deployed)
A FastAPI service is included under `backend/`. It can read Kubernetes/OpenShift nodes and pods using its in-cluster service account and can optionally test an ONTAP REST connection using server-side environment variables. It exposes `GET /health` and `GET /api/v1/overview`.

The GitHub Pages site is only the static frontend. **Live data will not appear until the backend is built, deployed inside an authorized cluster, and the frontend is configured with its HTTPS API base URL.** The included OpenShift manifest is a starting point and must be reviewed by your platform/security team. It grants read-only list/get/watch access to nodes, pods, namespaces and events. Do not expose the API publicly without Entra/OAuth authentication, TLS, a strict CORS allowlist and secrets management.

Build the API image from `backend/`, publish it to your approved registry, review `deploy/openshift`, deploy it in a protected namespace, then set `window.HIAIDO_API_BASE` in `config.js` to the protected API URL. Never commit credentials or tokens.
