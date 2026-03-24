# Ecosystem Audit and Roadmap

Date: 2026-03-15

## Current architecture

### Public surface

- `https://micou.org/` is now the public homepage.
- `https://www.micou.org/` redirects to the apex homepage.
- The live public root is:
  - `/srv/micou-services/micou-homepage/app`

### Authenticated member surface

- `https://micou.org/yunohost/sso/` is the right member-space entrypoint.
- YunoHost remains the canonical layer for:
  - login state
  - logout
  - per-user app visibility
  - group-based access

### Control plane

- `admin.html` is the service registry and operations UI.
- `forms_service.py` is the backend that serves:
  - catalog
  - content
  - admin save/action endpoints
  - audit trail
- The live control-plane data root is:
  - `/srv/micou-services/micou-homepage/data`

### Managed services

- Managed service copies now live under:
  - `/srv/micou-services`
- Confirmed live managed services:
  - `micou-homepage`
  - `widdypad`
  - `webstudio` workspace staging

## Audit findings

### Good

- Public homepage routing is corrected.
- `www.micou.org` now redirects to the apex.
- Public/member split is much cleaner than the original YunoHost-panel-on-root behavior.
- Service registry, grants model, audit log, and local/YunoHost discovery are all in place.
- Webstudio is correctly scoped to public pages instead of trying to replace YunoHost auth surfaces.

### Risks and weaknesses

1. Static admin surfaces must be protected explicitly.
   - `admin.html` and legacy `home.html` are static files.
   - The backend already enforces admin roles, but the page itself still needs route-level protection.

2. Admin UI is feature-rich but still operationally dense.
   - It now has guides and a packaging workbench, but the interface remains crowded.
   - This is acceptable for the current operating model because the admin surface is for a single technical operator.
   - The next UI pass should prioritize density, breadth of control, richer status visibility, and faster access to advanced actions rather than simplification.

3. The service registry is strong enough for operations, but not yet the only source of deploy truth.
   - Some service reality still lives in systemd, nginx, Compose files, and ad-hoc repos.
   - The next step is stronger repo conventions and service bootstrapping.

4. Public-page deployment is workable, but still export-driven.
   - Webstudio export plus `deploy_public_export.sh` is safe.
   - A Git-based publish pipeline would make it less manual.

5. Admin-side i18n remains incomplete.
   - Public-site multilingual coverage is stronger now.
   - The admin interface still needs a dedicated multilingual pass if it should be used comfortably in the same four-language model as the public homepage.

## Recommended next architecture

### 1. Stabilize the lanes

Keep three explicit lanes:

- Public pages:
  - Webstudio export
  - deploy into `/srv/micou-services/micou-homepage/app`
- Member space:
  - YunoHost portal only
- Services and operations:
  - control plane plus systemd/Docker/Git

### 2. Standardize custom services

Every custom service should converge toward:

- one repo per service
- a clear runtime model:
  - systemd
  - docker compose
  - static export
- a stable deploy path under `/srv/micou-services/<service>`
- a `DEPLOY.md`
- a `.env.example`
- one public URL decision

### 3. Package stable services for YunoHost

Use YunoHost packaging for services that are:

- stable enough
- useful beyond this single VPS
- good fits for YunoHost auth/permissions/backups/upgrades

Keep experimental services as custom Git or Docker deployments until stable.

### 4. Make admin protection explicit

Protect:

- `/admin`
- `/admin.html`
- `/home`
- `/home.html`
- `/home-api/`

Recommended current approach:

- explicit nginx routes on `micou.org`
- keep those routes behind the existing YunoHost SSO / SSOwat layer
- forward authenticated YunoHost user headers to `/home-api/`
- let the backend decide admin rights from `grants.json`

Longer-term preferred approach:

- convert the admin surface into a proper YunoHost-protected route or package

### 5. Improve publishing UX

Next UX improvements should prioritize:

- a denser “new service” workflow with direct access to packaging, deploy, auth, and routing controls
- a richer “new page” workflow with live preview, publish history, and export metadata
- a guided “import installed app” review flow that preserves power-user access to raw fields
- better separation between:
  - metadata editing
  - access editing
  - deployment actions

## UI polish priorities

### Public homepage

- tighten service-card spacing on mobile
- improve section rhythm between intro, rules, services, and form
- unify icon density and card heights
- continue editorial cleanup in all four languages

### Admin UI

- add stronger operator tooling: bulk actions, filters, richer health/status views, and denser service cards
- keep advanced deployment/auth/ops controls visible and fast to reach
- expand page preview, publish history, and deployment metadata inside the control plane
- add service-level audit/history summaries near the editable fields
- multilingual admin coverage remains optional because the admin surface is operated by a single technical admin

## Immediate next deploy goals

1. restart `micou-forms` with the latest backend file
2. make `admin.html`, `home.html`, and `/home-api/` explicit nginx routes while keeping them behind YunoHost auth
3. reload nginx
4. verify:
   - public homepage still works
   - admin pages are no longer public
   - admin backend still works for an authenticated admin user
