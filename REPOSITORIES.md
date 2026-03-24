# Repository Plan

This file defines the repository strategy for production.

## Core repository

### `micou-site`

This should become the main Git repository for:

- homepage
- dashboard (`home.html`)
- admin editor (`admin.html`)
- `catalog.json`
- `grants.json`
- `site_content.json`
- deploy helper files

## App repositories

Each custom app should ideally have its own repository:

- app source code
- runtime/deployment notes
- environment sample
- Docker or systemd entrypoint if relevant

Examples:

- `widdypad`
- `micouloulou-blog`
- future utilities and experiments

## Package repositories

If an app is delivered through YunoHost and needs custom maintenance, use a separate package repo:

- one repo for the YunoHost package
- optionally forked from the official package if one exists

Examples:

- `ynh-webstudio`
- `ynh-mycustomapp`
- `ynh-fork-of-existing-app`

## Catalog fields

Every catalog entry should eventually link to its code or package source:

- `repo_url`
- `upstream_url`
- `package_repo_url`
- `deployment_mode`

## Deployment modes

- `yunohost`: installed from an existing YunoHost package
- `fork`: maintained through a custom or forked YunoHost package
- `docker`: deployed from a containerized project
- `custom`: direct service or static app managed outside YunoHost packaging

## Recommended next installs

1. Forgejo
   Use as the central Git forge for:
   - site repo
   - custom app repos
   - YunoHost package forks

2. Decap CMS
   Use for Git-backed content editing of pages and blog content.

3. Optional later:
   a custom package catalog or scripts that pull from your Forgejo namespace and deploy package repos onto YunoHost.
