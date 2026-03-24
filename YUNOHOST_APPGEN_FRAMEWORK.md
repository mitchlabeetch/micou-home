# YunoHost App Generator Framework for micou.org

This framework standardizes how micou.org turns a custom service into a YunoHost package.

It does not replace the official YunoHost generator. It prepares the inputs, defaults, and follow-up steps so packaging stays consistent with the micou.org environment.

## Goals

- use the official YunoHost app generator cleanly
- keep package repos aligned with the micou service registry
- preserve the hybrid model:
  - public discovery on `micou.org`
  - authenticated launching on `micou.org/yunohost/sso/`
- make package creation repeatable across custom services

## Core files

- baseline defaults:
  - `/home/micou_org/yunohost_appgen/MICOU_APPGEN_BASELINES.json`
- human-readable generator template:
  - `/home/micou_org/yunohost_appgen/MICOU_APPGEN_QUESTIONNAIRE_TEMPLATE.md`
- scaffolding script:
  - `/home/micou_org/scripts/scaffold_yunohost_appgen.py`

## Current official reference

- official generator:
  - `https://appgenerator.yunohost.org/`
- audited generator version for this framework:
  - `0.21.0`

The micou workbench now tracks the full seven-section official generator model plus the extra fields needed to keep portal visibility, registry metadata, and admin-only surfaces aligned with the live micou.org stack.

## Modes

### Tutorial mode

Use this when:

- packaging a service for the first time
- onboarding another maintainer
- LDAP/SSO assumptions still need validation

Benefits:

- generated package contains more comments
- easier to understand the install and config scripts
- safer for early iterations

### Streamlined mode

Use this when:

- the service pattern is already understood
- you want a cleaner package repo
- the package is mainly routine maintenance

Benefits:

- leaner generated output
- less scaffolding noise
- better for repeated package creation

## Recommended micou process

1. Stabilize the service as a Git, systemd, or Docker deployment first if needed.
2. Decide whether the service truly benefits from becoming a YunoHost package.
3. Generate the micou brief:

```bash
python3 /home/micou_org/scripts/scaffold_yunohost_appgen.py \
  --app-id myapp \
  --app-name "My App" \
  --mode tutorial \
  --description-en "Short app summary" \
  --description-fr "Resume court de l'app"
```

4. Use the generated files to fill the official generator.
5. Create or update the package repository.
6. Test install, upgrade, backup, restore, and removal.
7. Install the package on the target host.
8. Update the micou service registry entry and sync YunoHost access.

For existing micou admin surfaces such as the control plane and the Webstudio workspace, keep the package brief focused on making them first-class YunoHost apps with real permissions and tiles instead of relying only on custom portal JSON entries.

## Official generator sections to complete

The generated brief mirrors these sections:

1. General information
2. Upstream information
3. Integration in YunoHost
4. Questions to ask during installation
5. Resources to initialize
6. App build and configuration
7. Advanced options

It also adds micou-specific follow-up notes:

- target URL and visibility
- package repo link
- service registry alignment
- auth and privacy notes

## Micou defaults

Default assumptions unless the service proves otherwise:

- ask for domain/path
- ask for access group
- support change_url
- initialize system user, install dir, and data dir
- prefer automatic source update support when upstream tagging allows it
- keep LDAP and SSO disabled until verified

## Packaging decision rules

Package a service when:

- it has a stable runtime and install path
- it should be reproducible on another YunoHost host
- auth and upgrade expectations are clear

Keep it as a custom deployment when:

- the upstream runtime is still shifting quickly
- the app is very experimental
- packaging overhead would slow down iteration more than it helps

## After package installation

Always do these follow-up actions:

1. import or update the app in the micou service registry
2. review category, visibility, and translations
3. review groups and allowed access
4. sync YunoHost access
5. verify what a real member sees in the YunoHost portal
