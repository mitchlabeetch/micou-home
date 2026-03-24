# micou.org hybrid portal strategy

## Decision

Use two complementary surfaces instead of forcing one tool to solve everything:

1. `https://micou.org/`
   public homepage, public catalog, request flow, editorial pages
2. `https://micou.org/yunohost/sso/`
   authenticated member space powered by YunoHost portal

## Why this is the right split

YunoHost already has the stable primitives for:

- login state
- logout state
- per-user and per-group app visibility
- protected app launching

The micou control plane is better suited for:

- public discovery and presentation
- request / approval workflows
- custom services and deploy metadata
- Git / Compose / systemd operations
- page editing and content ownership

## Dashboard behavior

For logged-in users, prefer the YunoHost portal as the default "my space".

The portal should show:

- public apps
- apps the user is explicitly approved for
- admin tools only for admins

The public homepage should show:

- public apps
- highlighted requestable apps
- a request form for restricted apps

## Request flow

Restricted apps should keep using the micou request workflow.

The approval source of truth remains:

- `catalog.json` for access intent and app policy
- `grants.json` for approved users and groups
- YunoHost permissions after sync

## Webstudio position

Webstudio should be used for public page editing and exported site projects.

Recommended model:

- YunoHost portal for authenticated dashboard / member space
- Webstudio for content pages like homepage, blog, and future marketing pages
- micou control plane for deploy, auth sync, and storage migration

## `www.micou.org`

Recommended behavior:

- redirect `www.micou.org` to `https://micou.org/`

This avoids duplicate content and prevents `www` from falling through to the YunoHost panel.
