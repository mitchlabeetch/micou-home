#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


BASELINES_PATH = Path("/home/micou_org/yunohost_appgen/MICOU_APPGEN_BASELINES.json")


def load_baselines() -> dict:
    return json.loads(BASELINES_PATH.read_text(encoding="utf-8"))


def split_items(raw: str) -> list[str]:
    return [item for item in raw.replace(",", " ").split() if item]


def bool_flag(parser: argparse.ArgumentParser, name: str, help_text: str) -> None:
    parser.add_argument(f"--{name}", action="store_true", help=help_text)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scaffold a micou-specific YunoHost app-generator brief.")
    parser.add_argument("--from-json", help="Read an already assembled payload from JSON.")
    parser.add_argument("--from-service-json", help="Read a micou catalog service entry and derive the generator payload.")
    parser.add_argument("--app-id", help="Technical application identifier, lowercase, no spaces.")
    parser.add_argument("--app-name", help="Human-readable application name.")
    parser.add_argument("--mode", choices=["tutorial", "streamlined"], default="tutorial")
    parser.add_argument("--output-dir", help="Target directory. Defaults to /home/micou_org/yunohost_appgen/apps/<app-id>.")
    parser.add_argument("--description-en", default="")
    parser.add_argument("--description-fr", default="")
    parser.add_argument("--presentation", default="")
    parser.add_argument("--version", default="0.0.0~ynh1")
    parser.add_argument("--license", dest="license_id", default="AGPL-3.0-only")
    parser.add_argument("--upstream-url", default="")
    parser.add_argument("--demo-url", default="")
    parser.add_argument("--admin-doc-url", default="")
    parser.add_argument("--user-doc-url", default="")
    parser.add_argument("--code-repo-url", default="")
    parser.add_argument("--source-url", default="")
    parser.add_argument("--package-repo-url", default="")
    parser.add_argument("--service-url", default="")
    parser.add_argument("--category", default="utility")
    parser.add_argument("--maintainer", default="micou")
    parser.add_argument("--package-type", choices=["webapp", "daemon", "admin_surface", "portal_shortcut"], default="webapp")
    parser.add_argument("--packaging-format", type=int, default=2)
    parser.add_argument("--architectures", default="all")
    parser.add_argument("--main-technology", default="mixed")
    parser.add_argument("--url-requirement", choices=["domain_and_path", "full_domain", "none"], default="domain_and_path")
    parser.add_argument("--access-level", choices=["visitors", "all_users", "admins", "custom", "none"], default="all_users")
    parser.add_argument("--admin-access-level", choices=["visitors", "all_users", "admins", "custom", "none"], default="none")
    parser.add_argument("--source-type", choices=["download_archive", "github_release", "git", "filesystem", "manual"], default="manual")
    parser.add_argument("--update-mode", choices=["none", "latest_github_release", "latest_git_tag", "latest_commit", "manual"], default="manual")
    parser.add_argument("--install-dir", default="")
    parser.add_argument("--data-dir", default="")
    parser.add_argument("--apt-deps", default="")
    parser.add_argument("--database-engine", choices=["none", "postgresql", "mysql"], default="none")
    parser.add_argument("--node-version", default="")
    parser.add_argument("--go-version", default="")
    parser.add_argument("--start-command", default="")
    parser.add_argument("--install-command", default="")
    parser.add_argument("--config-file", default="")
    parser.add_argument("--config-content", default="")
    parser.add_argument("--fail2ban-regex", default="")
    parser.add_argument("--cron-expression", default="")
    parser.add_argument("--cron-command", default="")
    parser.add_argument("--admin-notes", default="")
    parser.add_argument("--pre-install-notes", default="")
    parser.add_argument("--post-install-notes", default="")
    parser.add_argument("--homepage-visibility", default="hidden")
    parser.add_argument("--portal-visibility", default="all_users")
    parser.add_argument("--runtime-notes", default="")
    parser.add_argument("--storage-notes", default="")
    parser.add_argument("--auth-notes", default="")
    bool_flag(parser, "supports-ldap", "Enable LDAP integration.")
    bool_flag(parser, "supports-sso", "Enable YunoHost SSO integration.")
    bool_flag(parser, "multi-instance", "Allow multi-instance installs.")
    bool_flag(parser, "admin-interface", "Ask an extra admin access question.")
    bool_flag(parser, "with-db", "Initialize a database.")
    bool_flag(parser, "with-fail2ban", "Enable fail2ban settings.")
    bool_flag(parser, "with-cron", "Enable cron settings.")
    bool_flag(parser, "use-yarn", "Use Yarn in the build process.")
    bool_flag(parser, "use-composer", "Use Composer in the build process.")
    bool_flag(parser, "use-logrotate", "Use logrotate.")
    bool_flag(parser, "supports-change-url", "Support change_url in the package.")
    bool_flag(parser, "with-system-user", "Initialize a system user.")
    bool_flag(parser, "with-install-dir", "Initialize an install dir.")
    bool_flag(parser, "with-data-dir", "Initialize a data dir.")
    return parser.parse_args()


def default_install_dir(app_id: str, baselines: dict) -> str:
    return baselines["micou_environment"]["default_install_dir_pattern"].replace("__APP__", app_id)


def default_data_dir(app_id: str, baselines: dict) -> str:
    return baselines["micou_environment"]["default_data_dir_pattern"].replace("__APP__", app_id)


def payload_from_args(args: argparse.Namespace, baselines: dict) -> dict:
    if not args.app_id or not args.app_name:
        raise SystemExit("--app-id and --app-name are required unless --from-json or --from-service-json is used")
    shared = baselines["shared_defaults"]
    profile = baselines["profiles"][args.mode]
    app_id = args.app_id
    return {
        "generator_mode": args.mode,
        "profile": profile,
        "package_type": args.package_type,
        "micou_environment": baselines["micou_environment"],
        "general_information": {
            "app_name": args.app_name,
            "app_id": app_id,
            "short_description_en": args.description_en or "TODO: add English short description",
            "short_description_fr": args.description_fr or "TODO: ajouter une description courte en francais",
            "comprehensive_presentation": args.presentation or "TODO: describe the runtime, privacy, auth, and reverse-proxy expectations.",
        },
        "upstream_information": {
            "license": args.license_id,
            "official_website": args.upstream_url,
            "official_demo": args.demo_url,
            "admin_documentation": args.admin_doc_url,
            "usage_documentation": args.user_doc_url,
            "code_repository": args.code_repo_url,
        },
        "integration_in_yunohost": {
            "version": args.version,
            "maintainer": args.maintainer or shared["maintainer"],
            "packaging_format": args.packaging_format,
            "architectures": split_items(args.architectures) or ["all"],
            "app_main_technology": args.main_technology,
            "multi_instance": args.multi_instance,
            "ldap_integration": args.supports_ldap,
            "sso_integration": args.supports_sso,
        },
        "installation_questions": {
            "url_requirement": args.url_requirement,
            "access_level": args.access_level,
            "admin_access_level": args.admin_access_level if args.admin_interface or args.admin_access_level != "none" else "none",
        },
        "resources_to_initialize": {
            "source_type": args.source_type,
            "application_source": args.source_url,
            "automatic_source_updates": args.update_mode,
            "init_system_user": args.with_system_user or shared["init_system_user"],
            "init_install_dir": args.with_install_dir or shared["init_install_dir"],
            "install_dir": args.install_dir or default_install_dir(app_id, baselines),
            "init_data_dir": args.with_data_dir or shared["init_data_dir"],
            "data_dir": args.data_dir or default_data_dir(app_id, baselines),
            "apt_dependencies": split_items(args.apt_deps),
            "init_database": args.with_db,
            "database_engine": args.database_engine,
        },
        "app_build_and_configuration": {
            "use_composer": args.use_composer,
            "use_yarn": args.use_yarn,
            "node_version": args.node_version,
            "go_version": args.go_version,
            "install_commands": args.install_command,
            "start_command": args.start_command or f"__INSTALL_DIR__/{app_id}",
            "use_logrotate": args.use_logrotate or True,
            "config_file": args.config_file,
            "config_content": args.config_content,
        },
        "advanced_options": {
            "support_change_url": args.supports_change_url or shared["supports_change_url"],
            "protect_against_bruteforce": args.with_fail2ban,
            "fail2ban_regex": args.fail2ban_regex,
            "configure_cron": args.with_cron,
            "cron_expression": args.cron_expression,
            "cron_command": args.cron_command,
        },
        "additional_documentation": {
            "admin_tips": args.admin_notes,
            "pre_install": args.pre_install_notes,
            "post_install": args.post_install_notes,
        },
        "micou_registry_alignment": {
            "service_category": args.category,
            "service_url": args.service_url,
            "package_repo_url": args.package_repo_url,
            "homepage_visibility": args.homepage_visibility,
            "member_portal_visibility": args.portal_visibility,
            "runtime_notes": args.runtime_notes,
            "storage_notes": args.storage_notes,
            "auth_notes": args.auth_notes,
            "registry_follow_up": [
                "Import or update the installed app in the micou service registry.",
                "Review homepage visibility and dashboard visibility.",
                "Sync YunoHost access after finalizing groups and grants.",
            ],
            "micou_rules": shared["micou_rules"],
        },
    }


def payload_from_service(service: dict, baselines: dict) -> dict:
    appgen = service.get("appgen") if isinstance(service.get("appgen"), dict) else {}
    name = service.get("name") if isinstance(service.get("name"), dict) else {}
    description = service.get("description") if isinstance(service.get("description"), dict) else {}
    deployment = service.get("deployment") if isinstance(service.get("deployment"), dict) else {}
    auth = service.get("auth") if isinstance(service.get("auth"), dict) else {}
    package_id = str(appgen.get("package_id") or service.get("id") or "").strip()
    package_name = str(appgen.get("package_name") or name.get("en") or package_id).strip()
    return {
        "generator_mode": str(appgen.get("mode") or "tutorial"),
        "profile": baselines["profiles"].get(str(appgen.get("mode") or "tutorial"), baselines["profiles"]["tutorial"]),
        "package_type": str(appgen.get("package_type") or ("admin_surface" if service.get("access_mode") == "admin_only" else "webapp")),
        "micou_environment": baselines["micou_environment"],
        "general_information": {
            "app_name": package_name,
            "app_id": package_id,
            "short_description_en": str(appgen.get("short_description_en") or description.get("en") or ""),
            "short_description_fr": str(appgen.get("short_description_fr") or description.get("fr") or ""),
            "comprehensive_presentation": str(appgen.get("comprehensive_presentation") or ""),
        },
        "upstream_information": {
            "license": str(appgen.get("license") or "AGPL-3.0-only"),
            "official_website": str(appgen.get("official_website") or service.get("upstream_url") or service.get("default_url") or ""),
            "official_demo": str(appgen.get("official_demo") or ""),
            "admin_documentation": str(appgen.get("admin_documentation") or service.get("docs_url") or ""),
            "usage_documentation": str(appgen.get("usage_documentation") or service.get("docs_url") or ""),
            "code_repository": str(appgen.get("code_repository") or service.get("repo_url") or service.get("package_repo_url") or ""),
        },
        "integration_in_yunohost": {
            "version": str(appgen.get("version") or "0.0.0~ynh1"),
            "maintainer": str(appgen.get("maintainer") or "micou"),
            "packaging_format": int(appgen.get("packaging_format") or 2),
            "architectures": appgen.get("architectures") if isinstance(appgen.get("architectures"), list) else ["all"],
            "app_main_technology": str(appgen.get("app_main_technology") or "mixed"),
            "multi_instance": bool(appgen.get("multi_instance")),
            "ldap_integration": bool(appgen.get("ldap_integration")),
            "sso_integration": bool(appgen.get("sso_integration")),
        },
        "installation_questions": {
            "url_requirement": str(appgen.get("url_requirement") or "domain_and_path"),
            "access_level": str(appgen.get("access_level") or ("admins" if service.get("access_mode") == "admin_only" else "all_users")),
            "admin_access_level": str(appgen.get("admin_access_level") or ("admins" if service.get("access_mode") == "admin_only" else "none")),
        },
        "resources_to_initialize": {
            "source_type": str(appgen.get("source_type") or deployment.get("source_type") or "manual"),
            "application_source": str(appgen.get("application_source") or service.get("upstream_url") or service.get("repo_url") or ""),
            "automatic_source_updates": str(appgen.get("automatic_source_updates") or "manual"),
            "init_system_user": bool(appgen.get("init_system_user", service.get("access_mode") != "admin_only")),
            "init_install_dir": bool(appgen.get("init_install_dir", bool(deployment.get("deploy_path")))),
            "install_dir": str(appgen.get("install_dir") or deployment.get("deploy_path") or default_install_dir(package_id, baselines)),
            "init_data_dir": bool(appgen.get("init_data_dir")),
            "data_dir": str(appgen.get("data_dir") or ""),
            "apt_dependencies": appgen.get("apt_dependencies") if isinstance(appgen.get("apt_dependencies"), list) else [],
            "init_database": bool(appgen.get("init_database")),
            "database_engine": str(appgen.get("database_engine") or "none"),
        },
        "app_build_and_configuration": {
            "use_composer": bool(appgen.get("use_composer")),
            "use_yarn": bool(appgen.get("use_yarn")),
            "node_version": str(appgen.get("node_version") or ""),
            "go_version": str(appgen.get("go_version") or ""),
            "install_commands": str(appgen.get("install_commands") or ""),
            "start_command": str(appgen.get("start_command") or ""),
            "use_logrotate": bool(appgen.get("use_logrotate", True)),
            "config_file": str(appgen.get("config_file") or ""),
            "config_content": str(appgen.get("config_content") or ""),
        },
        "advanced_options": {
            "support_change_url": bool(appgen.get("support_change_url", service.get("access_mode") != "admin_only")),
            "protect_against_bruteforce": bool(appgen.get("protect_against_bruteforce")),
            "fail2ban_regex": str(appgen.get("fail2ban_regex") or ""),
            "configure_cron": bool(appgen.get("configure_cron")),
            "cron_expression": str(appgen.get("cron_expression") or ""),
            "cron_command": str(appgen.get("cron_command") or ""),
        },
        "additional_documentation": {
            "admin_tips": str(appgen.get("admin_tips") or ""),
            "pre_install": str(appgen.get("pre_install") or ""),
            "post_install": str(appgen.get("post_install") or ""),
        },
        "micou_registry_alignment": {
            "service_category": str(service.get("category") or "utility"),
            "service_url": str(appgen.get("service_url") or service.get("default_url") or ""),
            "package_repo_url": str(service.get("package_repo_url") or ""),
            "homepage_visibility": str(appgen.get("public_homepage_visibility") or ("public" if service.get("show_on_homepage") else "hidden")),
            "member_portal_visibility": str(appgen.get("member_portal_visibility") or ("admins" if service.get("access_mode") == "admin_only" else "all_users")),
            "runtime_notes": str(appgen.get("runtime_notes") or deployment.get("notes") or ""),
            "storage_notes": str(appgen.get("storage_notes") or ""),
            "auth_notes": str(appgen.get("auth_notes") or auth.get("notes") or ""),
            "registry_follow_up": [
                "Install the package on the target host and verify that YunoHost exposes the tile and permission.",
                "Update the micou service registry entry so access, URLs, and package repo metadata match the installed app.",
                "Run the control-plane syncs after the install to verify the portal, grants, and PostgreSQL projection.",
            ],
            "micou_rules": baselines["shared_defaults"]["micou_rules"],
        },
    }


def complete_payload(payload: dict, baselines: dict) -> dict:
    payload = dict(payload)
    payload.setdefault("generator_mode", "tutorial")
    payload.setdefault("profile", baselines["profiles"].get(payload["generator_mode"], baselines["profiles"]["tutorial"]))
    payload.setdefault("package_type", "webapp")
    payload.setdefault("micou_environment", baselines["micou_environment"])
    payload.setdefault("micou_registry_alignment", {})
    payload["micou_registry_alignment"].setdefault("registry_follow_up", [
        "Import or update the installed app in the micou service registry.",
        "Review homepage visibility and dashboard visibility.",
        "Sync YunoHost access after finalizing groups and grants.",
    ])
    payload["micou_registry_alignment"].setdefault("micou_rules", baselines["shared_defaults"]["micou_rules"])
    return payload


def write_markdown(path: Path, payload: dict) -> None:
    general = payload["general_information"]
    upstream = payload["upstream_information"]
    integration = payload["integration_in_yunohost"]
    install_q = payload["installation_questions"]
    resources = payload["resources_to_initialize"]
    build = payload["app_build_and_configuration"]
    advanced = payload["advanced_options"]
    docs = payload["additional_documentation"]
    registry = payload["micou_registry_alignment"]
    text = f"""# {general['app_name']} packaging brief

Mode: `{payload['generator_mode']}`
Package type: `{payload.get('package_type', 'webapp')}`

## General information (1/7)

- App name: {general['app_name']}
- Application identifier (id): {general['app_id']}
- Short description (en): {general['short_description_en']}
- Short description (fr): {general['short_description_fr']}
- Comprehensive presentation:

{general['comprehensive_presentation']}

## Upstream information (2/7)

- License: {upstream['license']}
- Official website: {upstream['official_website']}
- Official app demo: {upstream['official_demo']}
- Admin documentation: {upstream['admin_documentation']}
- Usage documentation: {upstream['usage_documentation']}
- Code repository: {upstream['code_repository']}

## Integration in YunoHost (3/7)

- Version: {integration['version']}
- Maintainer of the generated app: {integration['maintainer']}
- Packaging format: {integration['packaging_format']}
- Architectures: {', '.join(integration['architectures'])}
- App main technology: {integration['app_main_technology']}
- Multi-instance: {integration['multi_instance']}
- LDAP integration: {integration['ldap_integration']}
- YunoHost SSO integration: {integration['sso_integration']}

## Questions to ask during installation (4/7)

- URL requirement: {install_q['url_requirement']}
- Access level: {install_q['access_level']}
- Admin access level: {install_q['admin_access_level']}

## Resources to initialize (5/7)

- Source type: {resources['source_type']}
- Application source code or executable: {resources['application_source']}
- Automatic source updates: {resources['automatic_source_updates']}
- Initialize a system user: {resources['init_system_user']}
- Initialize an installation folder: {resources['init_install_dir']} -> {resources['install_dir']}
- Initialize a data folder: {resources['init_data_dir']} -> {resources['data_dir']}
- apt dependencies: {', '.join(resources['apt_dependencies'])}
- Initialize a database: {resources['init_database']} ({resources['database_engine']})

## App build and configuration (6/7)

- Use composer: {build['use_composer']}
- Use Yarn: {build['use_yarn']}
- NodeJS version: {build['node_version']}
- Go version: {build['go_version']}
- Installation specific commands: {build['install_commands']}
- Command to start the app daemon: {build['start_command']}
- Use logrotate: {build['use_logrotate']}
- Add a specific configuration file: {build['config_file']}
- App config content:

```text
{build['config_content']}
```

## Advanced options (7/7)

- Support URL change: {advanced['support_change_url']}
- Protect against brute force attacks: {advanced['protect_against_bruteforce']}
- Fail2Ban regex: {advanced['fail2ban_regex']}
- Configure a CRON task: {advanced['configure_cron']}
- CRON expression: {advanced['cron_expression']}
- CRON command: {advanced['cron_command']}

## Additional documentation bits

- General admin tips:

{docs['admin_tips']}

- Pre-install notes:

{docs['pre_install']}

- Post-install notes:

{docs['post_install']}

## Micou alignment

- Target service category: {registry['service_category']}
- Target service URL: {registry['service_url']}
- Package repo URL: {registry['package_repo_url']}
- Public homepage visibility: {registry['homepage_visibility']}
- Member portal visibility: {registry['member_portal_visibility']}
- Runtime notes:

{registry['runtime_notes']}

- Storage notes:

{registry['storage_notes']}

- Auth notes:

{registry['auth_notes']}

## Micou follow-up
"""
    for item in registry["registry_follow_up"]:
        text += f"- {item}\n"
    text += "\n## Micou rules\n"
    for item in registry["micou_rules"]:
        text += f"- {item}\n"
    path.write_text(text, encoding="utf-8")


def write_checklist(path: Path, payload: dict) -> None:
    app_id = payload["general_information"]["app_id"]
    mode = payload["generator_mode"]
    text = f"""# Micou packaging checklist for {app_id}

1. Confirm that the runtime, URL strategy, storage path, and authentication model are stable enough to package.
2. Review all seven official App Generator sections in `{mode}` mode and fill missing values before generation.
3. Generate the official YunoHost package skeleton with the same answers recorded in `appgen_answers.json`.
4. Complete DESCRIPTION.md, ADMIN.md, and any PRE_INSTALL.md or POST_INSTALL.md notes required by the service.
5. Test install, upgrade, backup, restore, and remove flows.
6. Install the package on a YunoHost host and confirm the tile, permission, and route behave as expected.
7. Update the micou service registry entry and YunoHost access state after the install.
8. Run the control-plane sync so PostgreSQL, grants, portal visibility, and the registry converge on the same state.
"""
    path.write_text(text, encoding="utf-8")


def main() -> None:
    args = parse_args()
    baselines = load_baselines()
    if args.from_json:
        payload = complete_payload(json.loads(Path(args.from_json).read_text(encoding="utf-8")), baselines)
    elif args.from_service_json:
        service = json.loads(Path(args.from_service_json).read_text(encoding="utf-8"))
        payload = complete_payload(payload_from_service(service, baselines), baselines)
    else:
        payload = complete_payload(payload_from_args(args, baselines), baselines)

    app_id = payload["general_information"]["app_id"]
    output_dir = Path(args.output_dir) if args.output_dir else Path("/home/micou_org/yunohost_appgen/apps") / app_id
    output_dir.mkdir(parents=True, exist_ok=True)

    (output_dir / "appgen_answers.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(output_dir / "GENERATOR_INPUT.md", payload)
    write_checklist(output_dir / "MICOU_DEPLOY_CHECKLIST.md", payload)

    print(json.dumps({
        "ok": True,
        "output_dir": str(output_dir),
        "files": [
            str(output_dir / "appgen_answers.json"),
            str(output_dir / "GENERATOR_INPUT.md"),
            str(output_dir / "MICOU_DEPLOY_CHECKLIST.md"),
        ],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
