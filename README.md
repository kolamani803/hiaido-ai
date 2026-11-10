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
