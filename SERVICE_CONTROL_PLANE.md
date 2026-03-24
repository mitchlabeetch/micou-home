# micou.org service control plane

This document defines the target operating model for micou.org services.

## Goal

Manage three service families from one admin surface:

1. YunoHost-native apps
2. Custom Git-backed apps
3. Docker or Compose stacks

The registry is the source of truth for:

- public homepage visibility
- access policy
- deployment metadata
- operational commands
- service links
- page ownership and editor mode
- imported local-service discovery metadata

## Registry contract

Each service entry should eventually carry:

- identity: `id`, `source`, `service_kind`, `tags`
- presentation: `name`, `description`, `button_label`, `icon_path`
- routing: `default_url`, `links.public_url`, `links.admin_url`, `links.dashboard_url`
- access: `access_mode`, `allowed_groups`, `auth.*`
- deployment: `deployment_mode`, `deployment.*`
- operations: `operations.deploy`, `operations.update`, `operations.restart`, `operations.logs`, `operations.backup`

The admin surface also consumes two companion datasets:

- `grants.json` for admins, groups, and per-user app access
- `site_content.json` for editable pages, homepage copy, and editor routing

## Discovery model

The control plane can import from two discovery sources:

1. installed YunoHost apps from `yunohost app list`
2. local VPS services discovered from:
   - `systemd` unit files
   - custom nginx path routes

Imported local services should be normalized into registry entries with:

- a public route when known
- a systemd unit when known
- a deploy path when known
- default restart and log commands
- a category and service kind guess that can then be refined manually

## Deployment conventions

### YunoHost app

- `source = yunohost`
- `deployment_mode = yunohost`
- `auth.provider = yunohost`
- prefer `yunohost_app_id` to match the installed package id

### Git service

- one repo per service
- include `.env.example`
- include `DEPLOY.md`
- define one stable internal port
- define one public URL target
- define restart and update commands in the registry

### Docker or Compose service

- one repo or one directory per stack
- commit `docker-compose.yml` or `compose.yml`
- keep persistent paths explicit
- define health URL when possible
- define `deployment.compose_file`, `deployment.deploy_path`, and operational commands

## Auth model

Use one of these modes per service:

- `public`
- `request`
- `sso`
- `native`
- `group`
- `disabled`

Use `allowed_groups` plus `auth.request_policy` for approval-driven services.

## Immediate roadmap

1. Keep the homepage and request form driven by the registry.
2. Expand the admin GUI to edit all registry fields.
3. Add import actions for installed YunoHost apps.
4. Add per-service deployment actions with server-side execution.
5. Add Git pull, Compose deploy, and systemd restart flows.
6. Add audit logs for admin actions.
7. Add repo bootstrap templates for new custom services.
8. Expose YunoHost live snapshots for domains, users, groups, and permissions.
9. Make page editing part of the same admin surface.

## Repo contract for future custom apps

Every new custom service should ideally provide:

- upstream repo URL
- target domain or path
- runtime type: static, systemd, docker, compose
- `DEPLOY.md`
- `.env.example`
- internal port
- persistent data paths
- health endpoint or smoke-check command

## Page model

Each page entry in `site_content.json` should ideally carry:

- `id`
- `title`
- `path`
- `editor`
- `source_type`
- `source_app`
- `repo_url`
- `visibility`
- `notes`
