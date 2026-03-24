# micou-site

Production repository for the micou.org website, user dashboard, and access management UI.

## Scope

- public homepage
- authenticated user dashboard
- admin editor for catalog, grants, and page content
- JSON data models for app visibility and access policy
- deploy helper files for `home.micou.org`

## Main files today

- `index.html`: public homepage
- `home.html`: authenticated dashboard
- `admin.html`: admin editor
- `forms_service.py`: backend API for catalog, grants, content, and access requests
- `catalog.json`: app inventory and app policy
- `grants.json`: user/group/admin grants
- `site_content.json`: editable page content

## Production model

- public site on `micou.org`
- authenticated dashboard on `home.micou.org`
- Git-backed page editing via Forgejo + Decap CMS
- repository-first deployment metadata for all apps and YunoHost packages

## Important docs

- `PROD_STRATEGY.md`
- `REPOSITORIES.md`
- `MIGRATION_PLAN.md`
- `BOOTSTRAP_CHECKLIST.md`
- `DEPLOY_COMMANDS.md`
