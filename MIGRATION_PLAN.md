# Migration Plan To `micou-site`

This plan describes how the current `/home/micou_org` directory should become the production `micou-site` repository.

## Target repository layout

```text
micou-site/
  app/
    index.html
    home.html
    admin.html
    illustrations/
  backend/
    forms_service.py
  data/
    catalog.json
    grants.json
    site_content.json
  cms/
    decap.config.yml
  deploy/
    home.micou.org.conf.example
    home.micou.org.dashboard.conf.example
    DEPLOY_COMMANDS.md
  docs/
    PROD_STRATEGY.md
    REPOSITORIES.md
    SETUP.md
    MIGRATION_PLAN.md
```

## Mapping from current files

- `/home/micou_org/index.html` -> `app/index.html`
- `/home/micou_org/home.html` -> `app/home.html`
- `/home/micou_org/admin.html` -> `app/admin.html`
- `/home/micou_org/illustrations/` -> `app/illustrations/`
- `/home/micou_org/forms_service.py` -> `backend/forms_service.py`
- `/home/micou_org/catalog.json` -> `data/catalog.json`
- `/home/micou_org/grants.json` -> `data/grants.json`
- `/home/micou_org/site_content.json` -> `data/site_content.json`
- `/home/micou_org/decap.config.yml` -> `cms/decap.config.yml`
- `/home/micou_org/home.micou.org.conf.example` -> `deploy/home.micou.org.conf.example`
- `/home/micou_org/home.micou.org.dashboard.conf.example` -> `deploy/home.micou.org.dashboard.conf.example`
- `/home/micou_org/DEPLOY_COMMANDS.md` -> `deploy/DEPLOY_COMMANDS.md`
- `/home/micou_org/PROD_STRATEGY.md` -> `docs/PROD_STRATEGY.md`
- `/home/micou_org/REPOSITORIES.md` -> `docs/REPOSITORIES.md`
- `/home/micou_org/SETUP.md` -> `docs/SETUP.md`

## Files to keep outside the repo

- runtime secrets
- `/etc/micou_org/forms.env`
- nginx live config under `/etc/nginx/conf.d/...`
- systemd unit files

## Environment path updates required after migration

Once files move into the repository structure, these environment variables should be set for the backend:

```bash
MICOU_CATALOG_PATH=/path/to/micou-site/data/catalog.json
MICOU_GRANTS_PATH=/path/to/micou-site/data/grants.json
MICOU_CONTENT_PATH=/path/to/micou-site/data/site_content.json
```

## Suggested migration order

1. Create the Git repository without changing the running server
2. Copy current files into the target layout
3. Update backend path env vars in staging only
4. Verify backend reads the moved JSON files
5. Switch nginx aliases to point at the repo paths
6. Switch systemd working directory / exec path if needed
7. Only then cut production over

## Non-destructive principle

Do not move the live files in-place first.

Instead:

1. create repo copy
2. test repo copy
3. update production paths once verified

This avoids breaking the current working homepage/backend while the repo layout is still being finalized.
