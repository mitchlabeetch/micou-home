# Deploy Commands

Use this sequence for the current micou.org stack.

## 1) Base migration and managed service switch

Run the consolidated root wrapper once:

```bash
sudo bash /home/micou_org/scripts/apply_root_stack_changes.sh
```

If you also want it to install Docker before preparing the Webstudio workspace:

```bash
sudo bash /home/micou_org/scripts/apply_root_stack_changes.sh --install-docker
```

This wrapper will:

- stages managed copies for the homepage and WiddyPad in `/srv/micou-services`
- switches `micou-forms` and `widdypad` to those managed paths
- updates `micou.org` static paths
- redirects `www.micou.org` to the apex homepage
- prepares the Webstudio workspace
- reload nginx and restart the relevant services

## 2) Final deploy and protection pass

Run the final wrapper once after the base migration:

```bash
sudo bash /home/micou_org/scripts/final_full_deploy.sh
```

This step:

- syncs the latest public/admin source files into `/srv`
- keeps admin routes behind YunoHost auth
- fixes the `widdypad.service` environment placement
- restarts `micou-forms` and `widdypad`
- verifies the public homepage, admin protection, and `www` redirect

## 3) Activate `studio.micou.org`

After the `studio` DNS record points to this VPS:

```bash
sudo bash /home/micou_org/scripts/final_full_deploy.sh --activate-studio
```

This will:

- run the full final deploy sync
- add `studio.micou.org` to YunoHost if missing
- request/install its certificate
- install the nginx workspace include
- reload nginx

## 4) Public page deployment from Webstudio export

After editing a public page in Webstudio Cloud and exporting it, deploy the export into the managed homepage app with:

```bash
bash /home/micou_org/scripts/deploy_public_export.sh /path/to/webstudio-export
```

Detailed flow:

- [PUBLIC_PAGE_EDIT_FLOW.md](/home/micou_org/PUBLIC_PAGE_EDIT_FLOW.md)
- [DNS_SETTINGS.md](/home/micou_org/DNS_SETTINGS.md)
- [NEXT_TASKS.md](/home/micou_org/NEXT_TASKS.md)

## 5) Restart backend if needed

```bash
sudo systemctl restart micou-forms
```

## 6) Stage managed service storage manually

```bash
sudo /home/micou_org/scripts/migrate_service_to_managed_root.sh micou-homepage
sudo /home/micou_org/scripts/migrate_service_to_managed_root.sh widdypad
```

This creates managed copies in `/srv/micou-services/` without deleting the live sources.

## 7) `www.micou.org`

Recommended: redirect `www` to the apex homepage.

```bash
sudo /home/micou_org/scripts/configure_www_homepage.sh redirect
```

Alternative: serve the homepage files directly on `www`.

```bash
sudo /home/micou_org/scripts/configure_www_homepage.sh serve
```

## 8) Prepare the Webstudio workspace only

```bash
sudo /home/micou_org/scripts/install_webstudio_runtime.sh
```

If Docker is not installed yet:

```bash
sudo /home/micou_org/scripts/install_webstudio_runtime.sh --install-docker
```

## 9) Verification

```bash
curl -I https://micou.org/
curl -I https://www.micou.org/
curl -s https://micou.org/api/catalog | jq '{viewer, dashboard: {public: (.dashboard.public_apps|length), allowed: (.dashboard.allowed_apps|length), requestable: (.dashboard.requestable_apps|length)}}'
curl -I https://studio.micou.org/
```

## 10) Notes

- `admin.html` uses the micou control plane backend and should remain outside the Webstudio export workflow.
- Public homepage data still uses `/api/catalog`.
- The editable control-plane files are:
  - `/srv/micou-services/micou-homepage/data/catalog.json`
  - `/srv/micou-services/micou-homepage/data/grants.json`
  - `/srv/micou-services/micou-homepage/data/site_content.json`
- The recommended hybrid model is:
  - `micou.org/` for public discovery and requests
  - `micou.org/yunohost/sso/` for the authenticated member space
  - `studio.micou.org/` for the public-page editing workspace and deployment guidance
