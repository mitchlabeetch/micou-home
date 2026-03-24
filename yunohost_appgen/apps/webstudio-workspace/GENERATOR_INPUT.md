# Webstudio workspace packaging brief

Mode: `streamlined`
Package type: `portal_shortcut`

## General information (1/7)

- App name: Webstudio workspace
- Application identifier (id): webstudio-workspace
- Short description (en): Admin-only Webstudio workspace shortcut for micou public-page editing.
- Short description (fr): Raccourci Webstudio réservé à l'admin pour l'édition des pages publiques micou.
- Comprehensive presentation:

Package the current studio.micou.org workspace as a first-class YunoHost admin app so the shortcut appears in the portal with a real permission object. The package should document that the route currently acts as an operational workspace around Webstudio exports and deployment rather than a fully self-hosted editor stack.

## Upstream information (2/7)

- License: AGPL-3.0-only
- Official website: https://studio.micou.org/
- Official app demo: 
- Admin documentation: https://docs.webstudio.is/university/self-hosting
- Usage documentation: https://docs.webstudio.is/university/self-hosting
- Code repository: 

## Integration in YunoHost (3/7)

- Version: 0.1.0~ynh1
- Maintainer of the generated app: micou
- Packaging format: 2
- Architectures: all
- App main technology: static
- Multi-instance: False
- LDAP integration: False
- YunoHost SSO integration: True

## Questions to ask during installation (4/7)

- URL requirement: full_domain
- Access level: admins
- Admin access level: admins

## Resources to initialize (5/7)

- Source type: filesystem
- Application source code or executable: https://studio.micou.org/
- Automatic source updates: manual
- Initialize a system user: False
- Initialize an installation folder: True -> /srv/micou-services/webstudio
- Initialize a data folder: False -> 
- apt dependencies: 
- Initialize a database: False (none)

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

Keep the package focused on the admin-only route and its portal exposure. Do not overstate it as a full self-hosted Webstudio installation unless the runtime is actually packaged too.

- Pre-install notes:



- Post-install notes:

Verify the tile appears only for admins and still routes through the expected studio workspace URL.

## Micou alignment

- Target service category: publishing
- Target service URL: https://studio.micou.org/
- Package repo URL: 
- Public homepage visibility: hidden
- Member portal visibility: admins
- Runtime notes:

Current runtime is a static workspace route tied to public-page export procedures.

- Storage notes:



- Auth notes:

Keep the surface admin-only and managed by YunoHost SSO.

## Micou follow-up
- Install the package on the target host and verify that YunoHost exposes the tile and permission.
- Update the micou service registry entry so access, URLs, and package repo metadata match the installed app.
- Run the control-plane syncs after the install to verify the portal, grants, and PostgreSQL projection.

## Micou rules
- Keep public discovery on micou.org and authenticated launching in the YunoHost portal.
- Document privacy limitations, auth behavior, and reverse-proxy assumptions in package docs.
- Mirror package deployment metadata back into the micou service registry after installation.
