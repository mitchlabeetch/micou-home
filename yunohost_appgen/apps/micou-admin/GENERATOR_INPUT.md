# micou admin control plane packaging brief

Mode: `streamlined`
Package type: `admin_surface`

## General information (1/7)

- App name: micou admin control plane
- Application identifier (id): micou-admin
- Short description (en): Admin-only control plane for the micou.org registry, content, and access model.
- Short description (fr): Plan de contrôle réservé à l'admin pour le registre, les contenus et les accès micou.org.
- Comprehensive presentation:

Package the existing micou control plane as a first-class YunoHost admin webapp so the route, tile, and permission are managed through YunoHost instead of portal-only custom JSON. The package should expose /admin.html on micou.org, keep access restricted to admins, and document the relationship with the public homepage backend and PostgreSQL control-plane sync.

## Upstream information (2/7)

- License: AGPL-3.0-only
- Official website: https://micou.org/admin.html
- Official app demo: 
- Admin documentation: https://micou.org/admin.html
- Usage documentation: https://micou.org/admin.html
- Code repository: 

## Integration in YunoHost (3/7)

- Version: 0.1.0~ynh1
- Maintainer of the generated app: micou
- Packaging format: 2
- Architectures: all
- App main technology: python
- Multi-instance: False
- LDAP integration: False
- YunoHost SSO integration: True

## Questions to ask during installation (4/7)

- URL requirement: domain_and_path
- Access level: admins
- Admin access level: admins

## Resources to initialize (5/7)

- Source type: filesystem
- Application source code or executable: https://micou.org/admin.html
- Automatic source updates: manual
- Initialize a system user: False
- Initialize an installation folder: True -> /srv/micou-services/micou-homepage
- Initialize a data folder: False -> 
- apt dependencies: python3
- Initialize a database: True (postgresql)

## App build and configuration (6/7)

- Use composer: False
- Use Yarn: False
- NodeJS version: 
- Go version: 
- Installation specific commands: 
- Command to start the app daemon: 
- Use logrotate: True
- Add a specific configuration file: 
- App config content:

```text

```

## Advanced options (7/7)

- Support URL change: False
- Protect against brute force attacks: False
- Fail2Ban regex: 
- Configure a CRON task: False
- CRON expression: 
- CRON command: 

## Additional documentation bits

- General admin tips:

Keep the package aligned with the managed micou-homepage service tree and the existing forms_service unit. Document all root-managed files touched by deployment and restart procedures.

- Pre-install notes:

Ensure the host already has the micou homepage stack and PostgreSQL control-plane database available, or convert those dependencies into package-managed resources explicitly.

- Post-install notes:

After installation, sync YunoHost access and verify that /api/admin/state still reports zero sync drift.

## Micou alignment

- Target service category: publishing
- Target service URL: https://micou.org/admin.html
- Package repo URL: 
- Public homepage visibility: hidden
- Member portal visibility: admins
- Runtime notes:

Wrap the existing admin route and backend rather than creating a second standalone runtime.

- Storage notes:



- Auth notes:

Keep access admin-only and let YunoHost own the permission and tile.

## Micou follow-up
- Install the package on the target host and verify that YunoHost exposes the tile and permission.
- Update the micou service registry entry so access, URLs, and package repo metadata match the installed app.
- Run the control-plane syncs after the install to verify the portal, grants, and PostgreSQL projection.

## Micou rules
- Keep public discovery on micou.org and authenticated launching in the YunoHost portal.
- Document privacy limitations, auth behavior, and reverse-proxy assumptions in package docs.
- Mirror package deployment metadata back into the micou service registry after installation.
