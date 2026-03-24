# Admin Operations Handbook

This handbook documents the current micou.org operating model and the main admin flows.

## Core model

- `https://micou.org/` is the public homepage and request surface.
- `https://micou.org/yunohost/sso/` is the authenticated member space.
- `https://micou.org/admin.html` is the service registry, grant editor, and operations console.
- `/srv/micou-services/micou-homepage/app` is the live public site root.
- `/srv/micou-services/micou-homepage/data` stores the live control-plane data:
  - `catalog.json`
  - `grants.json`
  - `site_content.json`
  - `admin_audit.log`

## Public pages with Webstudio

Use Webstudio for public pages only.

Do not use it as the source of truth for:

- YunoHost member portal
- YunoHost auth state
- app visibility rules
- systemd, nginx, Docker, or server operations

### Workflow

1. Edit the page in Webstudio Cloud.
2. Export the project.
3. Copy the export folder to the VPS.
4. Deploy with:

```bash
bash /home/micou_org/scripts/deploy_public_export.sh /path/to/webstudio-export
```

5. Verify:

```bash
curl -I https://micou.org/
```

### Notes

- The deploy script updates the live public root.
- It does not replace `admin.html`, `illustrations/`, backend code, or data files.
- The member-space CTA must keep pointing to `/yunohost/sso/`.

## Create a new public page

1. Open the `Pages and content` panel in admin.
2. Click `Add page`.
3. Set:
   - `id`
   - `title`
   - `path`
   - `editor`
   - `source_type`
   - `source_app`
   - `repo_url`
   - `visibility`
   - `notes`
4. Save all.
5. Create and deploy the actual page files.

Recommended defaults:

- public page edited in Webstudio:
  - `editor=webstudio`
  - `source_type=repo` or `source_type=content`
  - `source_app=webstudio`
- simple repo-backed page:
  - `editor=git-backed`
  - `source_type=repo`

## User accounts and app access

Keep user creation in YunoHost.

Use this admin page to manage:

- grants metadata
- per-user app access
- groups
- expected member-space visibility

### Create a user

Preferred source of truth: YunoHost.

Example CLI:

```bash
sudo yunohost user create username --fullname "Person Name" --mail person@example.org
```

Then in admin:

1. Add the person in `Grant helpers` or edit `Grants JSON`.
2. Add apps and groups as needed.
3. Save all.
4. Run `Sync YunoHost access`.

### Verify

- The user appears in the YunoHost snapshot.
- The user appears in `grants.json`.
- After login, the YunoHost portal shows the expected apps.

## Import an installed YunoHost app

1. Open `Discover YunoHost apps`.
2. Click `Import` on the target app.
3. Review and fix:
   - translations
   - category
   - order
   - homepage visibility
   - dashboard visibility
   - allowed groups
4. Save all.
5. Sync access if required.

## Sync YunoHost portal access

Use this after changing:

- `allowed_groups`
- grants
- auth settings
- dashboard visibility for restricted apps

### Steps

1. Save all.
2. Click `Sync YunoHost access`.
3. Read the action output.
4. Check the YunoHost snapshot.
5. Test with a real user account.

### Fallback

If the result looks wrong:

1. Stop.
2. Review `grants.json` and the affected service entry.
3. Correct the metadata.
4. Save again.
5. Retry sync.

## Git-backed custom service

Use this for your own apps and services.

### Minimum information to store

- `repo_url`
- `branch`
- `deploy_path`
- `public_url`
- `systemd_unit` if relevant
- deploy/update/restart/logs/backup commands

### Flow

1. Create a service from a template or from `Add service`.
2. Fill deployment and operations fields.
3. Save all.
4. Run `Bootstrap repo` if configured.
5. Run `Deploy` or `Update`.

Example commands:

```bash
git clone https://example.org/your-app.git /srv/micou-services/your-app/app
git -C /srv/micou-services/your-app/app pull --ff-only
```

## Docker or Compose app

Use this for container-first services.

### Required fields

- `deployment_mode=docker` or `compose`
- `deployment.compose_file`
- `deployment.container_name`
- `deployment.internal_url`
- `deployment.healthcheck_url`
- suitable operations commands

Example commands:

```bash
docker compose -f /srv/micou-services/example/docker-compose.yml pull
docker compose -f /srv/micou-services/example/docker-compose.yml up -d
```

### Flow

1. Register the service.
2. Fill deployment fields.
3. Save all.
4. Run `Compose pull`.
5. Run `Compose up`.
6. Check the health URL.
7. Expose it publicly only after verification.

## YunoHost package creation for micou.org

Use this when a custom service should graduate from a local deployment into a reusable YunoHost package.

### Main framework files

- `/home/micou_org/YUNOHOST_APPGEN_FRAMEWORK.md`
- `/home/micou_org/yunohost_appgen/MICOU_APPGEN_BASELINES.json`
- `/home/micou_org/yunohost_appgen/MICOU_APPGEN_QUESTIONNAIRE_TEMPLATE.md`
- `/home/micou_org/scripts/scaffold_yunohost_appgen.py`

### Generate a package brief

```bash
python3 /home/micou_org/scripts/scaffold_yunohost_appgen.py \
  --app-id myapp \
  --app-name "My App" \
  --mode tutorial \
  --description-en "Short app summary" \
  --description-fr "Resume court de l'app"
```

This creates:

- `appgen_answers.json`
- `GENERATOR_INPUT.md`
- `MICOU_DEPLOY_CHECKLIST.md`

### Rule of thumb

- Use `tutorial` mode for new packages and uncertain auth/runtime assumptions.
- Use `streamlined` mode for mature patterns and cleaner package repos.
- Do not claim LDAP or SSO support until the upstream app really supports it.

## Team-based access for a shared service

Example: office suite, collaborative writing space, project media workspace.

### Flow

1. Create a group in `Grant helpers`, for example `office-team`.
2. Ensure the real users exist in YunoHost.
3. Add those users to the group in `grants.json`.
4. Add `group:office-team` to the service `allowed_groups`.
5. Save all.
6. Run `Sync YunoHost access`.

### Verify

- The group exists in grants and in the YunoHost snapshot.
- Only team members see the service in the portal.

## Import an already-running local VPS service

1. Open `Discover local services`.
2. Import the service.
3. Review:
   - `public_url`
   - `systemd_unit`
   - `deploy_path`
   - `service_kind`
   - translations
4. Fill operations commands.
5. Save all.
6. Test `Restart` and `Logs`.

## Homepage, i18n, and editorial maintenance

Use app cards for metadata changes:

- names
- descriptions
- categories
- order
- visibility

Use public-page editing for:

- layout
- CTA placement
- large text blocks
- styling

### Editorial checklist

- Review French, English, German, and Spanish.
- Confirm the member-space CTA remains localized.
- Check long strings on mobile.
- Keep public vs restricted wording explicit.

## Rollback and troubleshooting

### First checks

```bash
systemctl --no-pager --full status micou-forms.service
systemctl --no-pager --full status widdypad.service
tail -n 50 /srv/micou-services/micou-homepage/data/admin_audit.log
ls -1 /srv/micou-services/micou-homepage/backups
```

### Rules

- Prefer rerunning a dedicated script over improvising ad-hoc edits.
- Prefer restoring a known-good export over patching generated output in panic.
- Hide a broken service from the homepage if needed while keeping the member portal stable.

## Root scripts

Main scripts currently in use:

- `/home/micou_org/scripts/apply_root_stack_changes.sh`
- `/home/micou_org/scripts/finalize_public_stack.sh`
- `/home/micou_org/scripts/deploy_public_export.sh`
- `/home/micou_org/scripts/activate_studio_workspace.sh`
- `/home/micou_org/scripts/install_webstudio_runtime.sh`
- `/home/micou_org/scripts/configure_www_homepage.sh`
- `/home/micou_org/scripts/migrate_service_to_managed_root.sh`
