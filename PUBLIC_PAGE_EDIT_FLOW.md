# Public page editing flow

## Chosen model

Use a hybrid setup:

- `micou.org/` for public pages
- `studio.micou.org/` for the public-page editing workspace and deployment guidance
- `micou.org/yunohost/sso/` for authenticated member space
- YunoHost for auth and member app visibility
- Webstudio for public-page design and editing
- the micou control plane for deploy metadata, service sync, and server operations

## What gets edited in Webstudio

Webstudio is for public pages only:

- homepage
- blog
- future public landing pages
- project presentation pages

Webstudio is **not** the source of truth for:

- YunoHost portal
- member app dashboard
- access control
- nginx, systemd, Docker, or service operations

## Day-to-day edit flow

1. Edit the public page in Webstudio Cloud.
2. Export the site from Webstudio.
3. Upload or copy the export folder to the VPS.
4. Deploy it into the managed homepage app:

```bash
bash /home/micou_org/scripts/deploy_public_export.sh /path/to/webstudio-export
```

5. Verify:

```bash
curl -I https://micou.org/
```

If the studio workspace domain is activated, it can serve as the operational reminder page for this flow:

- `https://studio.micou.org/`

To activate or refresh the full stack, including the studio workspace, run:

```bash
sudo bash /home/micou_org/scripts/final_full_deploy.sh --activate-studio
```

## What changes on the live site immediately

The deployment script updates the public page files in:

- `/srv/micou-services/micou-homepage/app`

It does not replace:

- `admin.html`
- `illustrations/`
- backend code
- control-plane data files

This means you can refresh `https://micou.org/` immediately after deployment without having to rebuild the YunoHost member space.

## Server-side source of truth

The managed homepage now lives here:

- `/srv/micou-services/micou-homepage/app`

Protected operational files remain outside the public-export workflow:

- `admin.html`
- `illustrations/`
- backend code
- registry data

## Auth flow

The homepage should link to:

- `/yunohost/sso/`

From there:

- anonymous users are prompted to authenticate
- authenticated users land on their own app panel

## Next improvement

Later, if you want a tighter pipeline, we can connect:

- Webstudio export
- a Git repository
- one deploy command from the control plane

That would remove manual file uploads while keeping YunoHost as the stable member dashboard.
