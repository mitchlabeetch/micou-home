# Bootstrap Checklist

Use this checklist when turning the current local folder into the production Git-backed workflow.

## Phase 1: Local cleanup

- [ ] remove stray files such as `.DS_Store`
- [ ] confirm which legacy markdown files should remain in the repo
- [ ] confirm whether `content-fr.md`, `content-en.md`, `content-de.md`, `content-es.md` are still needed
- [ ] confirm whether `50-services-micou-guide.md` and related notes belong in `docs/` or should stay outside

## Phase 2: Create `micou-site` repo

- [ ] create repository `micou-site` in Forgejo
- [ ] copy current project into the target repo layout described in `MIGRATION_PLAN.md`
- [ ] commit initial import
- [ ] add `.gitignore`
- [ ] add README describing architecture and deploy paths

## Phase 3: Git-backed content editing

- [ ] configure Decap CMS against the Forgejo repo
- [ ] create OAuth app in Forgejo for Decap
- [ ] fill `cms/decap.config.yml`
- [ ] decide which page content is edited in Decap vs custom admin UI

## Phase 4: App governance

- [ ] fill `repo_url` for each custom app
- [ ] fill `upstream_url` for each packaged app
- [ ] fill `package_repo_url` for each YunoHost package or fork
- [ ] set `deployment_mode` consistently for all catalog entries

## Phase 5: Production cutover

- [ ] point backend env vars to repo `data/` files
- [ ] point nginx aliases to repo `app/` files
- [ ] switch `home.micou.org` to the repo-based dashboard/admin
- [ ] verify save flows from admin UI
- [ ] verify public homepage still serves correctly

## Phase 6: After cutover

- [ ] integrate YunoHost group/user sync if desired
- [ ] replace file-based grants with a more formal source if needed
- [ ] decide whether to add a dedicated `admin.micou.org`
- [ ] add deployment automation from Forgejo repos to VPS
