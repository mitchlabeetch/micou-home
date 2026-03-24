# Production Strategy

This document defines the target production architecture before any further server mutation.

## Goals

- GUI editing for website pages such as homepage, blog pages, and future landing pages
- Repository-first workflow for all apps and packages
- No temporary preview-only production state
- Stable separation between:
  - public website content
  - authenticated user dashboard
  - admin catalog / access management
  - actual app deployment lifecycle

## Recommended Stack

### 1) Content editing for pages

Use a Git-backed CMS, not a full visual builder as the main production control plane.

Recommended:

- **Forgejo** as the self-hosted Git forge
- **Decap CMS** as the GUI content editor for page content stored in Git

Why:

- Decap can work directly against Gitea / Forgejo repositories
- content changes are versioned in Git
- rollback is trivial
- editors can change page content without touching deployment internals
- this is compatible with static, templated, or hybrid sites

### 2) Visual builder usage

**Webstudio should not be the primary production editor for the main site control plane.**

Use it only if needed for:

- designing isolated marketing pages
- exporting standalone static pages
- prototyping layouts before converting them into the main repo workflow

Reason:

- Webstudio's own self-hosted documentation says Builder self-hosting in production is currently more difficult and not recommended
- exported projects are better treated as code artifacts, not the operational source of truth for the whole platform

### 3) App deployment and maintenance

Use a repository model with two separate repos when relevant:

- **Upstream app repo**: the original software or your custom application source
- **Deployment/package repo**: YunoHost package or deployment wrapper used on the VPS

For each app in the catalog, track:

- `repo_url`
- `upstream_url`
- `package_repo_url`
- `deployment_mode`

`deployment_mode` should typically be one of:

- `yunohost`
- `fork`
- `docker`
- `custom`

### 4) New app policy

When adding a new app, evaluate in this order:

1. Existing maintained YunoHost package
2. Your own maintained YunoHost package or fork
3. Docker / compose deployment behind nginx + YunoHost auth integration
4. Raw custom service only if the previous options are not worth the overhead

### 5) YunoHost packaging workflow

For custom or forked packages:

- use the YunoHost app generator for initial scaffolding
- store package repos in Git
- if a package is not suitable for the official catalog, keep it in a custom catalog source

## Domain architecture

### `micou.org`

Public homepage and platform presentation.

- public pages
- public catalog
- access request flow
- no admin-only app exposure

### `home.micou.org`

Authenticated user dashboard.

- public apps
- apps allowed for the current user
- requestable restricted apps
- future team/workspace access

### `admin` surface

Keep admin editing authenticated and restricted to admins only.

Possible routes:

- `home.micou.org/admin.html`
- or later a dedicated `admin.micou.org`

## Repository strategy

### Required repos

- `micou-site`
  - homepage
  - dashboard
  - admin editor
  - `catalog.json`
  - `grants.json`

- one repo per custom app
  - app source
  - docs
  - deployment notes

- one repo per custom YunoHost package or fork
  - package scripts
  - manifest
  - patches

### Forking policy

Fork when:

- the official YunoHost package exists but needs changes specific to your platform
- you need to add auth, config, branding, patches, or maintenance before upstream catches up

Do not fork blindly if a deployment wrapper is enough.

## Editing model

### Content

Use GUI editing for:

- homepage texts
- descriptions
- docs pages
- blog entries
- category copy
- CTA labels

### Platform policy

Use the admin UI for:

- app visibility
- app ordering
- access mode
- grants
- categories
- linking repos

### Deployment metadata

Keep deployment metadata in the catalog:

- package source
- repo links
- deployment mode

But do not make the website editor responsible for actually deploying apps.

## What should happen next

1. Stabilize the current website/dashboard/admin code as the `micou-site` production repo
2. Install Forgejo for repository hosting and forks
3. Add Decap CMS for GUI page editing backed by Git
4. Keep the current admin UI for access and platform policy management
5. Use YunoHost packages or forks for apps whenever possible
6. Use a custom catalog source for packages that should not or cannot enter the official YunoHost catalog

## Non-goals

- using one giant visual builder as the only source of truth for both content and infrastructure
- editing production deployment state directly from a generic page builder
- mixing user grants and page copy in the same authoring workflow
