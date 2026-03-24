import email.utils
import glob
import hmac
import json
import os
import re
import secrets
import smtplib
import subprocess
import tempfile
import time
from collections import deque
from copy import deepcopy
from hashlib import sha256
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from urllib import error as urlerror
from urllib import request as urlrequest

try:
    from control_plane_postgres import sync_snapshot_to_postgres
except Exception:
    sync_snapshot_to_postgres = None

try:
    import psycopg2
except Exception:
    psycopg2 = None


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
LANGS = ("fr", "en", "de", "es")
CATALOG_PATH = os.environ.get("MICOU_CATALOG_PATH", "/home/micou_org/catalog.json")
GRANTS_PATH = os.environ.get("MICOU_GRANTS_PATH", "/home/micou_org/grants.json")
CONTENT_PATH = os.environ.get("MICOU_CONTENT_PATH", "/home/micou_org/site_content.json")
AUDIT_LOG_PATH = os.environ.get("MICOU_AUDIT_LOG_PATH", "/home/micou_org/admin_audit.log")
DATABASE_URL = os.environ.get("MICOU_DATABASE_URL") or os.environ.get("DATABASE_URL") or ""
SERVICES_ROOT = os.environ.get("MICOU_SERVICES_ROOT", "/srv/micou-services")
ADMIN_ONLY_IDS = {"cockpit", "code-server", "fail2ban-web", "olivetin"}
CATALOG_CACHE_TTL = 30
ACTION_NAMES = ("deploy", "update", "restart", "logs", "backup")
ACTION_OUTPUT_LIMIT = 16000
NGINX_DISCOVERY_GLOB = os.environ.get("MICOU_NGINX_DISCOVERY_GLOB", "/etc/nginx/conf.d/micou.org.d/*.conf")
SYSTEMD_DISCOVERY_GLOB = os.environ.get("MICOU_SYSTEMD_DISCOVERY_GLOB", "/etc/systemd/system/*.service")
BUILTIN_ADMIN_ACTIONS = (
    "sync_access",
    "sync_projection",
    "bootstrap_repo",
    "compose_pull",
    "compose_up",
    "systemd_restart",
    "scaffold_repo",
    "scaffold_appgen",
)
INTERNAL_DISCOVERY_PATHS = {"/home-api/"}
RESERVED_SYSTEM_SERVICE_IDS = {"micou-homepage", "webstudio", "yunohost-portal", "micou-forms"}

_catalog_cache = {"ts": 0, "payload": None}

ADMIN_ENUMS = {
    "roles": ["visitor", "user", "admin"],
    "service_kinds": [
        "portal",
        "collaboration",
        "publishing",
        "media",
        "knowledge",
        "utility",
        "automation",
        "admin",
        "custom",
    ],
    "access_modes": ["public", "restricted", "authenticated", "admin_only"],
    "cta_modes": ["auto", "open", "request", "docs"],
    "deployment_modes": ["yunohost", "custom", "docker", "compose", "systemd", "static", "fork"],
    "auth_modes": ["public", "request", "sso", "native", "group", "disabled"],
    "auth_providers": ["none", "yunohost", "app_native", "proxy", "manual"],
    "deployment_source_types": ["yunohost", "git", "docker", "compose", "filesystem", "upstream"],
    "appgen_modes": ["tutorial", "streamlined"],
    "appgen_package_types": ["webapp", "daemon", "admin_surface", "portal_shortcut"],
    "appgen_architectures": ["all", "amd64", "arm64", "armhf"],
    "appgen_main_technologies": ["python", "nodejs", "php", "go", "ruby", "rust", "static", "binary", "mixed"],
    "appgen_url_requirements": ["domain_and_path", "full_domain", "none"],
    "appgen_access_levels": ["visitors", "all_users", "admins", "custom", "none"],
    "appgen_source_types": ["download_archive", "github_release", "git", "filesystem", "manual"],
    "appgen_update_modes": ["none", "latest_github_release", "latest_git_tag", "latest_commit", "manual"],
    "appgen_database_engines": ["none", "postgresql", "mysql"],
    "page_editor_modes": ["git-backed", "webstudio", "markdown", "static", "custom"],
    "page_visibility_modes": ["public", "restricted", "admin_only", "hidden"],
    "page_source_types": ["content", "repo", "service", "external"],
}

SERVICE_TEMPLATES = [
    {
        "id": "git-service",
        "label": "Git service",
        "description": "A custom app deployed from a Git repository.",
        "defaults": {
            "source": "custom",
            "deployment_mode": "custom",
            "service_kind": "custom",
            "access_mode": "public",
            "cta_mode": "open",
            "auth": {"mode": "public", "provider": "none", "managed_by": "micou", "request_policy": "open"},
            "deployment": {"strategy": "custom", "source_type": "git", "branch": "main"},
        },
    },
    {
        "id": "docker-compose",
        "label": "Docker compose",
        "description": "A service managed from a Docker Compose project.",
        "defaults": {
            "source": "custom",
            "deployment_mode": "docker",
            "service_kind": "custom",
            "access_mode": "public",
            "cta_mode": "open",
            "auth": {"mode": "public", "provider": "proxy", "managed_by": "micou", "request_policy": "open"},
            "deployment": {"strategy": "docker", "source_type": "compose", "branch": "main"},
        },
    },
    {
        "id": "private-stack",
        "label": "Private stack",
        "description": "A custom service requiring manual access review.",
        "defaults": {
            "source": "custom",
            "deployment_mode": "docker",
            "service_kind": "custom",
            "access_mode": "restricted",
            "cta_mode": "auto",
            "auth": {"mode": "request", "provider": "manual", "managed_by": "micou", "request_policy": "manual_review"},
            "deployment": {"strategy": "docker", "source_type": "compose", "branch": "main"},
        },
    },
    {
        "id": "systemd-service",
        "label": "Systemd service",
        "description": "A custom process managed by systemd on the VPS.",
        "defaults": {
            "source": "custom",
            "deployment_mode": "systemd",
            "service_kind": "utility",
            "access_mode": "public",
            "cta_mode": "open",
            "auth": {"mode": "public", "provider": "proxy", "managed_by": "micou", "request_policy": "open"},
            "deployment": {"strategy": "systemd", "source_type": "filesystem", "branch": "main"},
        },
    },
    {
        "id": "webstudio-site",
        "label": "Webstudio site",
        "description": "A visually edited website deployed from a Git or Docker-backed project.",
        "defaults": {
            "source": "custom",
            "deployment_mode": "docker",
            "service_kind": "publishing",
            "access_mode": "public",
            "cta_mode": "open",
            "tags": ["website", "visual-editor"],
            "auth": {"mode": "public", "provider": "proxy", "managed_by": "micou", "request_policy": "open"},
            "deployment": {"strategy": "docker", "source_type": "compose", "branch": "main"},
        },
    },
    {
        "id": "admin-surface",
        "label": "Admin surface",
        "description": "An admin-only route that should become a first-class YunoHost app and portal tile.",
        "defaults": {
            "source": "custom",
            "deployment_mode": "custom",
            "service_kind": "admin",
            "access_mode": "admin_only",
            "cta_mode": "docs",
            "tags": ["admin-surface", "yunohost-package"],
            "auth": {"mode": "sso", "provider": "yunohost", "managed_by": "yunohost", "request_policy": "admin_only"},
            "deployment": {"strategy": "custom", "source_type": "filesystem", "branch": "main"},
            "appgen": {"package_type": "admin_surface", "access_level": "admins", "admin_access_level": "admins", "member_portal_visibility": "admins", "public_homepage_visibility": "hidden"},
        },
    },
    {
        "id": "yunohost-package",
        "label": "YunoHost package",
        "description": "A service that should become a reusable YunoHost app package.",
        "defaults": {
            "source": "custom",
            "deployment_mode": "fork",
            "service_kind": "utility",
            "access_mode": "restricted",
            "cta_mode": "request",
            "tags": ["yunohost-package", "packaging"],
            "auth": {"mode": "request", "provider": "yunohost", "managed_by": "yunohost", "request_policy": "manual_review"},
            "deployment": {"strategy": "fork", "source_type": "upstream", "branch": "main"},
        },
    },
]

APPGEN_PROFILES = [
    {
        "id": "tutorial",
        "label": "Tutorial mode",
        "description": "Generator output with extra comments to explain the package structure and scripts.",
        "best_for": [
            "first YunoHost package for a custom service",
            "learning packaging internals",
            "services that will need iterative review",
        ],
        "micou_defaults": {
            "maintainer": "micou",
            "supports_change_url": True,
            "ask_domain_path": True,
            "ask_access_group": True,
            "init_system_user": True,
            "init_install_dir": True,
            "init_data_dir": True,
            "auto_source_updates": True,
            "packaging_notes": [
                "Prefer path or subdomain choices that fit the existing micou.org routing model.",
                "Document privacy and auth assumptions in DESCRIPTION.md and ADMIN.md.",
                "Keep app visibility aligned with the control-plane registry after install.",
            ],
        },
    },
    {
        "id": "streamlined",
        "label": "Streamlined mode",
        "description": "Minimal generator output with only the required files and the least amount of explanatory comments.",
        "best_for": [
            "apps already understood technically",
            "repeatable packaging of similar micou custom services",
            "clean production packaging repos",
        ],
        "micou_defaults": {
            "maintainer": "micou",
            "supports_change_url": True,
            "ask_domain_path": True,
            "ask_access_group": True,
            "init_system_user": True,
            "init_install_dir": True,
            "init_data_dir": True,
            "auto_source_updates": True,
            "packaging_notes": [
                "Use this only after runtime, storage, auth, and reverse-proxy assumptions are already clear.",
                "Pair the package repo with a service registry entry so deployment metadata stays in sync.",
            ],
        },
    },
]

APPGEN_SECTIONS = [
    {
        "id": "general_information",
        "title": "General information (1/7)",
        "official": True,
        "fields": [
            "app_name",
            "app_id",
            "short_description_en",
            "short_description_fr",
            "comprehensive_presentation",
        ],
    },
    {
        "id": "upstream_information",
        "title": "Upstream information (2/7)",
        "official": True,
        "fields": [
            "license",
            "official_website",
            "official_demo",
            "admin_documentation",
            "usage_documentation",
            "code_repository",
        ],
    },
    {
        "id": "integration_in_yunohost",
        "title": "Integration in YunoHost (3/7)",
        "official": True,
        "fields": [
            "version",
            "maintainer",
            "packaging_format",
            "architectures",
            "app_main_technology",
            "multi_instance",
            "ldap_integration",
            "sso_integration",
        ],
    },
    {
        "id": "installation_questions",
        "title": "Questions to ask during installation (4/7)",
        "official": True,
        "fields": [
            "url_requirement",
            "access_level",
            "admin_access_level",
        ],
    },
    {
        "id": "resources_to_initialize",
        "title": "Resources to initialize (5/7)",
        "official": True,
        "fields": [
            "source_type",
            "application_source",
            "automatic_source_updates",
            "init_system_user",
            "init_install_dir",
            "install_dir",
            "init_data_dir",
            "data_dir",
            "apt_dependencies",
            "init_database",
            "database_engine",
        ],
    },
    {
        "id": "app_build_and_configuration",
        "title": "App build and configuration (6/7)",
        "official": True,
        "fields": [
            "use_composer",
            "use_yarn",
            "node_version",
            "go_version",
            "install_commands",
            "start_command",
            "use_logrotate",
            "config_file",
            "config_content",
        ],
    },
    {
        "id": "advanced_options",
        "title": "Advanced options (7/7)",
        "official": True,
        "fields": [
            "support_change_url",
            "protect_against_bruteforce",
            "fail2ban_regex",
            "configure_cron",
            "cron_expression",
            "cron_command",
        ],
    },
]

APPGEN_PROCESS = [
    "Stabilize the service runtime, auth model, URL strategy, and storage before packaging.",
    "Capture all seven official App Generator sections with the micou workbench fields before generating anything.",
    "Run the scaffold action or CLI to create the packaging brief, then fill the official generator with those answers.",
    "Create the package repository and complete DESCRIPTION.md, ADMIN.md, and pre/post-install notes where relevant.",
    "Test install, upgrade, backup, restore, and remove flows on a disposable host or staging VPS.",
    "Install the resulting app on the target YunoHost host, sync access, and then update the micou registry entry to match the installed reality.",
]

APPGEN_ADMIN_PRESETS = [
    {
        "catalog_id": "micou-homepage",
        "package_id": "micou-admin",
        "label": "micou admin control plane",
        "surface": "https://micou.org/admin.html",
        "package_type": "admin_surface",
        "notes": "Package the control plane as an admin-only YunoHost webapp entry instead of relying only on a portal-side custom tile.",
    },
    {
        "catalog_id": "webstudio",
        "package_id": "webstudio-workspace",
        "label": "Webstudio workspace",
        "surface": "https://studio.micou.org/",
        "package_type": "portal_shortcut",
        "notes": "Treat the Webstudio route as an admin-only shortcut package or webapp wrapper so it becomes a first-class YunoHost app.",
    },
]


def _now() -> int:
    return int(time.time())


def _json_bytes(obj: dict) -> bytes:
    return json.dumps(obj, ensure_ascii=False).encode("utf-8")


def _hmac_hex(secret: bytes, msg: str) -> str:
    return hmac.new(secret, msg.encode("utf-8"), sha256).hexdigest()


def _read_catalog_file() -> dict:
    with open(CATALOG_PATH, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("catalog must be a JSON object")
    return data


def _read_grants_file() -> dict:
    with open(GRANTS_PATH, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("grants must be a JSON object")
    return data


def _read_content_file() -> dict:
    with open(CONTENT_PATH, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("content must be a JSON object")
    return data


def _write_json_file(path: str, payload: dict):
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    os.replace(tmp_path, path)


def _normalize_translations(value, fallback: str = "") -> dict[str, str]:
    if isinstance(value, dict):
        out = {}
        for lang in LANGS:
            raw = value.get(lang, fallback)
            out[lang] = str(raw or fallback)
        return out
    base = str(value or fallback)
    return {lang: base for lang in LANGS}


def _normalize_domain_path(domain_path: str) -> str:
    value = (domain_path or "").strip()
    if not value:
        return ""
    if value.endswith("/"):
        return value
    domain, sep, path = value.partition("/")
    return f"{domain}/" if sep and not path else value


def _normalize_category_map(raw_categories) -> dict[str, dict]:
    result = {}
    if not isinstance(raw_categories, dict):
        return result
    for category_id, value in raw_categories.items():
        if not isinstance(value, dict):
            continue
        result[str(category_id)] = {
            "id": str(category_id),
            "order": int(value.get("order", 9999)),
            "name": _normalize_translations(value.get("name"), str(category_id)),
        }
    return result


def _normalize_groups(raw_groups) -> dict[str, list[str]]:
    groups = {}
    if not isinstance(raw_groups, dict):
        return groups
    for name, members in raw_groups.items():
        if isinstance(members, list):
            groups[str(name)] = [str(member).strip().lower() for member in members if str(member).strip()]
    return groups


def _normalize_user_grants(raw_users) -> dict[str, dict]:
    users = {}
    if not isinstance(raw_users, dict):
        return users
    for email, data in raw_users.items():
        key = str(email).strip().lower()
        if not key or not isinstance(data, dict):
            continue
        users[key] = {
            "apps": [str(item) for item in data.get("apps", []) if str(item).strip()],
            "groups": [str(item) for item in data.get("groups", []) if str(item).strip()],
        }
    return users


def _string(value, fallback: str = "") -> str:
    if value is None:
        return fallback
    return str(value).strip()


def _normalize_string_list(raw_value) -> list[str]:
    if not isinstance(raw_value, list):
        return []
    return [str(item).strip() for item in raw_value if str(item).strip()]


def _normalize_service_kind(source: str, access_mode: str, raw_kind) -> str:
    value = _string(raw_kind)
    if value:
        return value
    if source == "yunohost" and access_mode == "admin_only":
        return "admin"
    if source == "yunohost":
        return "portal"
    return "custom"


def _normalize_auth_config(raw_auth, source: str, access_mode: str, allowed_groups: list[str]) -> dict:
    auth = raw_auth if isinstance(raw_auth, dict) else {}
    default_mode = "public" if access_mode == "public" else "request"
    default_provider = "yunohost" if source == "yunohost" else ("none" if access_mode == "public" else "manual")
    default_policy = "open" if access_mode == "public" else "manual_review"
    return {
        "mode": _string(auth.get("mode"), default_mode),
        "provider": _string(auth.get("provider"), default_provider),
        "managed_by": _string(auth.get("managed_by"), "yunohost" if source == "yunohost" else "micou"),
        "request_policy": _string(auth.get("request_policy"), default_policy),
        "allowed_groups": _normalize_string_list(auth.get("allowed_groups")) or list(allowed_groups),
        "notes": _string(auth.get("notes")),
    }


def _normalize_deployment_config(raw_deployment, source: str, deployment_mode: str, default_url: str, repo_url: str, package_repo_url: str, upstream_url: str) -> dict:
    deployment = raw_deployment if isinstance(raw_deployment, dict) else {}
    return {
        "strategy": _string(deployment.get("strategy"), deployment_mode),
        "source_type": _string(deployment.get("source_type"), "yunohost" if source == "yunohost" else "git"),
        "repo_url": _string(deployment.get("repo_url"), repo_url),
        "package_repo_url": _string(deployment.get("package_repo_url"), package_repo_url),
        "upstream_url": _string(deployment.get("upstream_url"), upstream_url),
        "branch": _string(deployment.get("branch"), "main" if source != "yunohost" else ""),
        "deploy_path": _string(deployment.get("deploy_path")),
        "compose_file": _string(deployment.get("compose_file")),
        "systemd_unit": _string(deployment.get("systemd_unit")),
        "container_name": _string(deployment.get("container_name")),
        "internal_url": _string(deployment.get("internal_url")),
        "healthcheck_url": _string(deployment.get("healthcheck_url"), default_url),
        "notes": _string(deployment.get("notes")),
    }


def _normalize_operations_config(raw_operations) -> dict:
    operations = raw_operations if isinstance(raw_operations, dict) else {}
    return {
        "deploy": _string(operations.get("deploy")),
        "update": _string(operations.get("update")),
        "restart": _string(operations.get("restart")),
        "logs": _string(operations.get("logs")),
        "backup": _string(operations.get("backup")),
    }


def _normalize_links_config(raw_links, default_url: str, docs_url: str) -> dict:
    links = raw_links if isinstance(raw_links, dict) else {}
    return {
        "public_url": _string(links.get("public_url"), default_url),
        "docs_url": _string(links.get("docs_url"), docs_url),
        "admin_url": _string(links.get("admin_url")),
        "dashboard_url": _string(links.get("dashboard_url")),
        "health_url": _string(links.get("health_url")),
    }


def _normalize_appgen_access_level(value: str, fallback: str) -> str:
    allowed = set(ADMIN_ENUMS["appgen_access_levels"])
    candidate = _string(value, fallback)
    return candidate if candidate in allowed else fallback


def _normalize_appgen_update_mode(value: str) -> str:
    allowed = set(ADMIN_ENUMS["appgen_update_modes"])
    candidate = _string(value, "manual")
    return candidate if candidate in allowed else "manual"


def _normalize_appgen_source_type(value: str) -> str:
    allowed = set(ADMIN_ENUMS["appgen_source_types"])
    candidate = _string(value, "manual")
    return candidate if candidate in allowed else "manual"


def _normalize_appgen_database_engine(value: str) -> str:
    allowed = set(ADMIN_ENUMS["appgen_database_engines"])
    candidate = _string(value, "none")
    return candidate if candidate in allowed else "none"


def _normalize_appgen_url_requirement(value: str) -> str:
    allowed = set(ADMIN_ENUMS["appgen_url_requirements"])
    candidate = _string(value, "domain_and_path")
    return candidate if candidate in allowed else "domain_and_path"


def _normalize_appgen_package_type(value: str, access_mode: str) -> str:
    allowed = set(ADMIN_ENUMS["appgen_package_types"])
    fallback = "admin_surface" if access_mode == "admin_only" else "webapp"
    candidate = _string(value, fallback)
    return candidate if candidate in allowed else fallback


def _normalize_appgen_technology(value: str) -> str:
    allowed = set(ADMIN_ENUMS["appgen_main_technologies"])
    candidate = _string(value, "mixed")
    return candidate if candidate in allowed else "mixed"


def _normalize_appgen_config(raw_appgen, entry: dict, source: str, access_mode: str, default_url: str, deployment: dict, docs_url: str) -> dict:
    appgen = raw_appgen if isinstance(raw_appgen, dict) else {}
    package_id = _string(appgen.get("package_id"), _string(entry.get("id")))
    admin_default = "admins" if access_mode == "admin_only" else "none"
    return {
        "mode": _string(appgen.get("mode"), "tutorial"),
        "package_type": _normalize_appgen_package_type(appgen.get("package_type"), access_mode),
        "package_id": package_id,
        "package_name": _string(appgen.get("package_name"), _string((entry.get("name") or {}).get("en"), package_id)),
        "short_description_en": _string(appgen.get("short_description_en"), _string((entry.get("description") or {}).get("en"))),
        "short_description_fr": _string(appgen.get("short_description_fr"), _string((entry.get("description") or {}).get("fr"))),
        "comprehensive_presentation": _string(appgen.get("comprehensive_presentation")),
        "license": _string(appgen.get("license"), "AGPL-3.0-only"),
        "official_website": _string(appgen.get("official_website"), _string(entry.get("upstream_url") or default_url)),
        "official_demo": _string(appgen.get("official_demo")),
        "admin_documentation": _string(appgen.get("admin_documentation"), docs_url),
        "usage_documentation": _string(appgen.get("usage_documentation"), docs_url),
        "code_repository": _string(appgen.get("code_repository"), _string(entry.get("repo_url") or entry.get("package_repo_url"))),
        "version": _string(appgen.get("version"), "0.0.0~ynh1"),
        "maintainer": _string(appgen.get("maintainer"), "micou"),
        "packaging_format": int(appgen.get("packaging_format") or 2),
        "architectures": _normalize_string_list(appgen.get("architectures")) or ["all"],
        "app_main_technology": _normalize_appgen_technology(appgen.get("app_main_technology")),
        "multi_instance": bool(appgen.get("multi_instance")),
        "ldap_integration": bool(appgen.get("ldap_integration")),
        "sso_integration": bool(appgen.get("sso_integration")),
        "url_requirement": _normalize_appgen_url_requirement(appgen.get("url_requirement")),
        "access_level": _normalize_appgen_access_level(appgen.get("access_level"), "admins" if access_mode == "admin_only" else "all_users"),
        "admin_access_level": _normalize_appgen_access_level(appgen.get("admin_access_level"), admin_default),
        "source_type": _normalize_appgen_source_type(appgen.get("source_type") or deployment.get("source_type")),
        "application_source": _string(appgen.get("application_source"), _string(entry.get("upstream_url") or entry.get("repo_url"))),
        "automatic_source_updates": _normalize_appgen_update_mode(appgen.get("automatic_source_updates")),
        "init_system_user": bool(appgen.get("init_system_user", access_mode != "admin_only")),
        "init_install_dir": bool(appgen.get("init_install_dir", bool(deployment.get("deploy_path")))),
        "install_dir": _string(appgen.get("install_dir"), _string(deployment.get("deploy_path"))),
        "init_data_dir": bool(appgen.get("init_data_dir")),
        "data_dir": _string(appgen.get("data_dir")),
        "apt_dependencies": _normalize_string_list(appgen.get("apt_dependencies")),
        "init_database": bool(appgen.get("init_database")),
        "database_engine": _normalize_appgen_database_engine(appgen.get("database_engine")),
        "use_composer": bool(appgen.get("use_composer")),
        "use_yarn": bool(appgen.get("use_yarn")),
        "node_version": _string(appgen.get("node_version")),
        "go_version": _string(appgen.get("go_version")),
        "install_commands": _string(appgen.get("install_commands")),
        "start_command": _string(appgen.get("start_command")),
        "use_logrotate": bool(appgen.get("use_logrotate", True)),
        "config_file": _string(appgen.get("config_file")),
        "config_content": _string(appgen.get("config_content")),
        "support_change_url": bool(appgen.get("support_change_url", access_mode != "admin_only")),
        "protect_against_bruteforce": bool(appgen.get("protect_against_bruteforce")),
        "fail2ban_regex": _string(appgen.get("fail2ban_regex")),
        "configure_cron": bool(appgen.get("configure_cron")),
        "cron_expression": _string(appgen.get("cron_expression")),
        "cron_command": _string(appgen.get("cron_command")),
        "admin_tips": _string(appgen.get("admin_tips")),
        "pre_install": _string(appgen.get("pre_install")),
        "post_install": _string(appgen.get("post_install")),
        "service_url": _string(appgen.get("service_url"), default_url),
        "public_homepage_visibility": _string(appgen.get("public_homepage_visibility"), "hidden" if not entry.get("show_on_homepage") else "public"),
        "member_portal_visibility": _string(appgen.get("member_portal_visibility"), "admins" if access_mode == "admin_only" else "all_users"),
        "runtime_notes": _string(appgen.get("runtime_notes"), _string((deployment or {}).get("notes"))),
        "storage_notes": _string(appgen.get("storage_notes")),
        "auth_notes": _string(appgen.get("auth_notes"), _string(((entry.get("auth") or {}).get("notes")))),
    }


def _title_case_slug(value: str) -> str:
    text = re.sub(r"[-_]+", " ", _string(value))
    return text.title() if text else value


def _slug_from_route(path: str) -> str:
    cleaned = _string(path).strip()
    if not cleaned or cleaned == "/" or cleaned.startswith("@"):
        return ""
    segment = cleaned.strip("/").split("/", 1)[0]
    return re.sub(r"[^a-z0-9-]+", "-", segment.lower()).strip("-")


def _route_public_url(path: str) -> str:
    cleaned = _string(path).strip()
    if not cleaned or cleaned.startswith("@"):
        return ""
    return f"https://micou.org{cleaned}"


def _normalized_urlish(value: str) -> str:
    text = _string(value).strip()
    if not text:
        return ""
    if text.startswith("http://") or text.startswith("https://"):
        parsed = urlparse(text)
        host = parsed.netloc.lower()
        path = parsed.path or "/"
        normalized = f"{parsed.scheme.lower()}://{host}{path}"
    else:
        normalized = text
    return normalized.rstrip("/") or "/"


def _service_alias_keys(app: dict) -> set[str]:
    item = app if isinstance(app, dict) else {}
    links = item.get("links") if isinstance(item.get("links"), dict) else {}
    keys = set()
    for raw in (
        item.get("id"),
        item.get("yunohost_app_id"),
        item.get("default_url"),
        links.get("public_url"),
        links.get("health_url"),
    ):
        normalized = _normalized_urlish(_string(raw))
        if normalized:
            keys.add(normalized)
    return keys


def _category_for_service_hint(*values: str) -> tuple[str, str]:
    haystack = " ".join([_string(value).lower() for value in values if _string(value)])
    if any(token in haystack for token in ("music", "audio", "mp3", "radio", "video", "photo", "gallery", "widdy")):
        return "media", "media"
    if any(token in haystack for token in ("blog", "site", "publish", "write", "cms", "webstudio")):
        return "publishing", "publishing"
    if any(token in haystack for token in ("wiki", "read", "book", "docs", "knowledge")):
        return "knowledge", "knowledge"
    if any(token in haystack for token in ("chat", "forum", "todo", "office", "group", "collective", "agora")):
        return "collaboration", "collaboration"
    if any(token in haystack for token in ("ticket", "event", "booking", "pretix")):
        return "events", "portal"
    return "utilities", "custom"


def _parse_systemd_unit_file(path: str) -> dict:
    unit = {
        "unit": os.path.basename(path),
        "path": path,
        "description": "",
        "working_directory": "",
        "exec_start": "",
        "environment": {},
        "port": "",
    }
    section = ""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for raw_line in fh:
                line = raw_line.strip()
                if not line or line.startswith("#") or line.startswith(";"):
                    continue
                if line.startswith("[") and line.endswith("]"):
                    section = line[1:-1].strip().lower()
                    continue
                key, sep, value = line.partition("=")
                if not sep:
                    continue
                key = key.strip().lower()
                value = value.strip()
                if section == "unit" and key == "description":
                    unit["description"] = value
                if section != "service":
                    continue
                if key == "workingdirectory":
                    unit["working_directory"] = value
                elif key == "execstart":
                    unit["exec_start"] = value
                elif key == "environment":
                    env_text = value.strip().strip('"').strip("'")
                    env_key, env_sep, env_value = env_text.partition("=")
                    if env_sep and env_key.strip():
                        unit["environment"][env_key.strip()] = env_value.strip().strip('"').strip("'")
    except Exception:
        return unit

    for env_key, env_value in unit["environment"].items():
        if env_key.endswith("_PORT") and str(env_value).isdigit():
            unit["port"] = str(env_value)
            break
    if not unit["port"]:
        match = re.search(r":(\d{2,5})(?:/|$)", unit["exec_start"])
        if not match:
            match = re.search(r"\b(\d{2,5})\b", unit["exec_start"])
        if match:
            unit["port"] = match.group(1)
    return unit


def _load_systemd_units() -> list[dict]:
    units = []
    for path in sorted(glob.glob(SYSTEMD_DISCOVERY_GLOB)):
        units.append(_parse_systemd_unit_file(path))
    return units


def _load_nginx_locations() -> list[dict]:
    locations = []
    for conf_path in sorted(glob.glob(NGINX_DISCOVERY_GLOB)):
        try:
            with open(conf_path, "r", encoding="utf-8") as fh:
                lines = fh.readlines()
        except Exception:
            continue
        idx = 0
        while idx < len(lines):
            header = lines[idx].strip()
            if not header.startswith("location "):
                idx += 1
                continue
            header_text = header[:-1].strip() if header.endswith("{") else header
            parts = header_text.split()
            path = ""
            if len(parts) >= 3 and parts[1] in ("=", "^~", "~", "~*"):
                path = parts[2]
            elif len(parts) >= 2:
                path = parts[1]
            block = []
            depth = lines[idx].count("{") - lines[idx].count("}")
            idx += 1
            while idx < len(lines) and depth > 0:
                block_line = lines[idx]
                block.append(block_line)
                depth += block_line.count("{") - block_line.count("}")
                idx += 1

            item = {
                "conf_path": conf_path,
                "path": path,
                "proxy_pass": "",
                "alias": "",
                "root": "",
                "return": "",
            }
            for raw_line in block:
                line = raw_line.strip().rstrip(";")
                if line.startswith("proxy_pass "):
                    item["proxy_pass"] = line.split(None, 1)[1].strip()
                elif line.startswith("alias "):
                    item["alias"] = line.split(None, 1)[1].strip()
                elif line.startswith("root "):
                    item["root"] = line.split(None, 1)[1].strip()
                elif line.startswith("return "):
                    item["return"] = line.split(None, 1)[1].strip()
            locations.append(item)
    return locations


def _discovery_import_defaults(item: dict) -> dict:
    category, service_kind = _category_for_service_hint(
        item.get("id"),
        item.get("description"),
        item.get("exec_start"),
        item.get("route_path"),
    )
    public_url = _string(item.get("public_url"))
    internal_url = _string(item.get("internal_url"))
    deploy_path = _string(item.get("deploy_path"))
    systemd_unit = _string(item.get("systemd_unit"))
    repo_detected = bool(deploy_path and os.path.isdir(os.path.join(deploy_path, ".git")))
    compose_file = ""
    if deploy_path:
        for candidate in ("docker-compose.yml", "compose.yml"):
            full_path = os.path.join(deploy_path, candidate)
            if os.path.exists(full_path):
                compose_file = full_path
                break
    deployment_mode = "compose" if compose_file else ("systemd" if systemd_unit else "custom")
    source_type = "compose" if compose_file else ("git" if repo_detected else "filesystem")
    button_label = {"fr": "Ouvrir", "en": "Open", "de": "Öffnen", "es": "Abrir"}
    if category == "media":
        button_label = {"fr": "Écouter", "en": "Listen", "de": "Anhören", "es": "Escuchar"}
    operations = {
        "deploy": "",
        "update": "",
        "restart": f"systemctl restart {systemd_unit}" if systemd_unit else "",
        "logs": f"journalctl -u {systemd_unit} --no-pager -n 200" if systemd_unit else "",
        "backup": "",
    }
    if deploy_path:
        if repo_detected:
            operations["update"] = f"git -C {json.dumps(deploy_path)} pull --ff-only"
        if compose_file:
            operations["deploy"] = f"docker compose -f {json.dumps(compose_file)} up -d"
    return {
        "source": "custom",
        "deployment_mode": deployment_mode,
        "service_kind": service_kind,
        "category": category,
        "access_mode": "public",
        "cta_mode": "open",
        "default_url": public_url,
        "show_on_homepage": True,
        "show_on_dashboard": True,
        "allowed_groups": ["visitor", "user:all", "admin"],
        "auth": {
            "mode": "public",
            "provider": "proxy",
            "managed_by": "micou",
            "request_policy": "open",
            "allowed_groups": ["visitor", "user:all", "admin"],
            "notes": "",
        },
        "deployment": {
            "strategy": deployment_mode,
            "source_type": source_type,
            "repo_url": "",
            "package_repo_url": "",
            "upstream_url": "",
            "branch": "main",
            "deploy_path": deploy_path,
            "compose_file": compose_file,
            "systemd_unit": systemd_unit,
            "container_name": "",
            "internal_url": internal_url,
            "healthcheck_url": public_url or internal_url,
            "notes": f"Imported from local discovery ({_string(item.get('discovery_source'))}).",
        },
        "operations": operations,
        "links": {
            "public_url": public_url,
            "docs_url": "",
            "admin_url": "",
            "dashboard_url": "",
            "health_url": public_url or internal_url,
        },
        "button_label": button_label,
    }


def _discover_local_services() -> list[dict]:
    configured_ids = set()
    configured_aliases = set()
    try:
        _, apps = _normalized_catalog_state()
        configured_ids = {app.get("id") for app in apps if app.get("id")}
        for app in apps:
            configured_aliases.update(_service_alias_keys(app))
    except Exception:
        configured_ids = set()
        configured_aliases = set()
    try:
        yunohost_apps = _load_yunohost_apps()
        yunohost_ids = set(yunohost_apps.keys())
        for app in yunohost_apps.values():
            domain_path = _normalize_domain_path(str((app or {}).get("domain_path") or ""))
            if domain_path:
                configured_aliases.add(_normalized_urlish(f"https://{domain_path}"))
    except Exception:
        yunohost_apps = {}
        yunohost_ids = set()

    units = _load_systemd_units()
    routes = _load_nginx_locations()
    units_by_port: dict[str, list[dict]] = {}
    for unit in units:
        port = _string(unit.get("port"))
        if port:
            units_by_port.setdefault(port, []).append(unit)

    discovered = []
    seen_ids = set()
    for route in routes:
        path = _string(route.get("path"))
        proxy_pass = _string(route.get("proxy_pass"))
        public_url = _route_public_url(path)
        route_alias = _normalized_urlish(public_url)
        if (
            not path
            or not proxy_pass
            or path in ("/", "/api/", "/illustrations/")
            or path.startswith("@")
            or path in INTERNAL_DISCOVERY_PATHS
            or "/socket.io" in path
            or route_alias in configured_aliases
        ):
            continue
        service_id = _slug_from_route(path)
        if (
            not service_id
            or service_id in seen_ids
            or service_id in yunohost_ids
            or service_id in RESERVED_SYSTEM_SERVICE_IDS
        ):
            continue
        parsed = urlparse(proxy_pass)
        port = str(parsed.port or "")
        unit = (units_by_port.get(port) or [None])[0]
        description = _string((unit or {}).get("description")) or f"Locally hosted service routed at {path}"
        category, service_kind = _category_for_service_hint(service_id, description, proxy_pass)
        item = {
            "id": service_id,
            "name": _title_case_slug(service_id),
            "description": description,
            "configured": service_id in configured_ids,
            "service_kind": service_kind,
            "category": category,
            "route_path": path,
            "public_url": public_url,
            "internal_url": proxy_pass,
            "proxy_pass": proxy_pass,
            "systemd_unit": _string((unit or {}).get("unit")),
            "deploy_path": _string((unit or {}).get("working_directory")),
            "exec_start": _string((unit or {}).get("exec_start")),
            "conf_path": _string(route.get("conf_path")),
            "discovery_source": "nginx+systemd" if unit else "nginx",
        }
        item["repo_detected"] = bool(item["deploy_path"] and os.path.isdir(os.path.join(item["deploy_path"], ".git")))
        item["import_defaults"] = _discovery_import_defaults(item)
        discovered.append(item)
        seen_ids.add(service_id)

    for unit in units:
        unit_name = _string(unit.get("unit")).removesuffix(".service")
        working_directory = _string(unit.get("working_directory"))
        if (
            not unit_name
            or unit_name in seen_ids
            or unit_name in configured_ids
            or unit_name in yunohost_ids
            or unit_name in RESERVED_SYSTEM_SERVICE_IDS
            or not working_directory
            or not working_directory.startswith(("/home", "/srv", "/media", "/opt"))
        ):
            continue
        category, service_kind = _category_for_service_hint(unit_name, unit.get("description"), unit.get("exec_start"))
        port = _string(unit.get("port"))
        internal_url = f"http://127.0.0.1:{port}" if port else ""
        item = {
            "id": unit_name,
            "name": _title_case_slug(unit_name),
            "description": _string(unit.get("description")) or f"Custom systemd service {unit_name}",
            "configured": False,
            "service_kind": service_kind,
            "category": category,
            "route_path": "",
            "public_url": "",
            "internal_url": internal_url,
            "proxy_pass": internal_url,
            "systemd_unit": _string(unit.get("unit")),
            "deploy_path": working_directory,
            "exec_start": _string(unit.get("exec_start")),
            "conf_path": "",
            "discovery_source": "systemd",
        }
        item["repo_detected"] = bool(item["deploy_path"] and os.path.isdir(os.path.join(item["deploy_path"], ".git")))
        item["import_defaults"] = _discovery_import_defaults(item)
        discovered.append(item)
        seen_ids.add(unit_name)

    discovered.sort(key=lambda item: (item.get("configured", False), item.get("id", "")))
    return discovered


def _load_access_snapshot() -> dict:
    snapshot = {
        "ok": True,
        "domains": [],
        "users": [],
        "groups": {},
        "permissions": [],
        "errors": [],
    }
    try:
        payload = _run_yunohost_json(["domain", "list"])
        domains = payload.get("domains") if isinstance(payload, dict) else payload
        if isinstance(domains, list):
            snapshot["domains"] = sorted([_string(item) for item in domains if _string(item)])
    except Exception as exc:
        snapshot["ok"] = False
        snapshot["errors"].append(f"domains: {exc}")

    try:
        payload = _run_yunohost_json(["user", "list"])
        users = []
        if isinstance(payload, dict):
            users = payload.get("users") or payload.get("data") or []
            if isinstance(users, dict):
                users = [{"username": key, **(value if isinstance(value, dict) else {})} for key, value in users.items()]
        elif isinstance(payload, list):
            users = payload
        snapshot["users"] = sorted(
            [
                {
                    "username": _string(item.get("username") or item.get("user") or item.get("id")),
                    "mail": _string(item.get("mail") or item.get("email")),
                }
                for item in users
                if isinstance(item, dict) and _string(item.get("username") or item.get("user") or item.get("id"))
            ],
            key=lambda item: item["username"],
        )
    except Exception as exc:
        snapshot["ok"] = False
        snapshot["errors"].append(f"users: {exc}")

    try:
        snapshot["groups"] = {
            name: sorted(list(members))
            for name, members in sorted(_load_yunohost_groups_state().items())
        }
    except Exception as exc:
        snapshot["ok"] = False
        snapshot["errors"].append(f"groups: {exc}")

    try:
        snapshot["permissions"] = [
            {"name": name, "allowed": sorted(list((data or {}).get("allowed") or []))}
            for name, data in sorted(_load_yunohost_permissions_state().items())
        ]
    except Exception as exc:
        snapshot["ok"] = False
        snapshot["errors"].append(f"permissions: {exc}")

    return snapshot


def _load_yunohost_apps() -> dict[str, dict]:
    proc = subprocess.run(
        ["yunohost", "app", "list", "--output-as", "json"],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(proc.stdout)
    if isinstance(payload, dict):
        apps = payload.get("apps") or payload.get("applications") or []
    elif isinstance(payload, list):
        apps = payload
    else:
        apps = []

    indexed = {}
    for app in apps:
        if not isinstance(app, dict):
            continue
        app_id = str(app.get("id") or "").strip()
        if not app_id:
            continue
        indexed[app_id] = app
    return indexed


def _default_button_label(access_mode: str) -> dict[str, str]:
    if access_mode == "public":
        return {"fr": "Ouvrir", "en": "Open", "de": "Öffnen", "es": "Abrir"}
    return {
        "fr": "Demander l'accès",
        "en": "Request access",
        "de": "Zugang anfragen",
        "es": "Solicitar acceso",
    }


def _load_grants() -> dict:
    raw = _read_grants_file()
    admins = [str(item).strip().lower() for item in raw.get("admins", []) if str(item).strip()]
    return {
        "admins": admins,
        "groups": _normalize_groups(raw.get("groups")),
        "users": _normalize_user_grants(raw.get("users")),
    }


def _normalize_catalog_entry(entry: dict, yh_apps: dict[str, dict], category_ids: set[str]) -> dict:
    app_id = str(entry.get("id") or "").strip()
    if not app_id:
        raise ValueError("catalog app entry missing id")

    source = str(entry.get("source") or "custom")
    yh_id = str(entry.get("yunohost_app_id") or app_id)
    yh_app = yh_apps.get(yh_id)
    installed = bool(yh_app)

    fallback_name = str((yh_app or {}).get("name") or app_id)
    fallback_description = str((yh_app or {}).get("description") or "Self-hosted app.")
    fallback_url = ""
    if yh_app:
        domain_path = _normalize_domain_path(str(yh_app.get("domain_path") or ""))
        if domain_path:
            fallback_url = f"https://{domain_path}"

    category = str(entry.get("category") or "other")
    if category not in category_ids:
        category = "other"

    access_mode = str(entry.get("access_mode") or "public")
    cta_mode = str(entry.get("cta_mode") or "auto")
    default_url = str(entry.get("default_url") or fallback_url)
    docs_url = str(entry.get("docs_url") or "")
    icon_path = str(entry.get("icon_path") or "")
    illustration_path = str(entry.get("illustration_path") or "")
    repo_url = str(entry.get("repo_url") or "")
    upstream_url = str(entry.get("upstream_url") or "")
    package_repo_url = str(entry.get("package_repo_url") or "")
    deployment_mode = str(entry.get("deployment_mode") or ("yunohost" if source == "yunohost" else "custom"))
    show_on_homepage = bool(entry.get("show_on_homepage", app_id not in ADMIN_ONLY_IDS))
    show_on_dashboard = bool(entry.get("show_on_dashboard", show_on_homepage))
    allowed_groups = entry.get("allowed_groups")
    if not isinstance(allowed_groups, list):
        allowed_groups = ["visitor"] if access_mode == "public" else ["admin", "user:authorized"]
    allowed_groups = [str(item).strip() for item in allowed_groups if str(item).strip()]
    service_kind = _normalize_service_kind(source, access_mode, entry.get("service_kind"))
    tags = _normalize_string_list(entry.get("tags"))
    auth = _normalize_auth_config(entry.get("auth"), source, access_mode, allowed_groups)
    deployment = _normalize_deployment_config(
        entry.get("deployment"),
        source,
        deployment_mode,
        default_url,
        repo_url,
        package_repo_url,
        upstream_url,
    )
    operations = _normalize_operations_config(entry.get("operations"))
    links = _normalize_links_config(entry.get("links"), default_url, docs_url)
    appgen = _normalize_appgen_config(entry.get("appgen"), entry, source, access_mode, default_url, deployment, docs_url)

    return {
        "id": app_id,
        "source": source,
        "yunohost_app_id": yh_id if source == "yunohost" else "",
        "installed": installed if source == "yunohost" else bool(entry.get("installed", True)),
        "service_kind": service_kind,
        "tags": tags,
        "name": _normalize_translations(entry.get("name"), fallback_name),
        "description": _normalize_translations(entry.get("description"), fallback_description),
        "button_label": _normalize_translations(entry.get("button_label"), _default_button_label(access_mode)["en"]),
        "docs_url": docs_url,
        "icon_path": icon_path,
        "illustration_path": illustration_path,
        "repo_url": repo_url,
        "upstream_url": upstream_url,
        "package_repo_url": package_repo_url,
        "deployment_mode": deployment_mode,
        "show_on_homepage": show_on_homepage,
        "show_on_dashboard": show_on_dashboard,
        "allowed_groups": allowed_groups,
        "default_url": default_url,
        "category": category,
        "order": int(entry.get("order", 9999)),
        "access_mode": access_mode,
        "cta_mode": cta_mode,
        "auth": auth,
        "deployment": deployment,
        "operations": operations,
        "links": links,
        "appgen": appgen,
    }


def _build_catalog_payload() -> dict:
    now = _now()
    cached = _catalog_cache.get("payload")
    if cached and now - int(_catalog_cache.get("ts", 0)) < CATALOG_CACHE_TTL:
        return cached

    config = _read_catalog_file()
    categories = _normalize_category_map(config.get("categories"))
    if "other" not in categories:
        categories["other"] = {
            "id": "other",
            "order": 9999,
            "name": {"fr": "Autres", "en": "Other", "de": "Weitere", "es": "Otros"},
        }
    category_ids = set(categories.keys())
    yh_apps = _load_yunohost_apps()

    configured_apps = []
    seen_ids = set()
    for raw in config.get("apps") or []:
        if not isinstance(raw, dict):
            continue
        normalized = _normalize_catalog_entry(raw, yh_apps, category_ids)
        configured_apps.append(normalized)
        seen_ids.add(normalized["id"])

    available_apps = []
    for app_id, app in yh_apps.items():
        domain_path = _normalize_domain_path(str(app.get("domain_path") or ""))
        if not domain_path:
            continue
        url = f"https://{domain_path}"
        available_apps.append(
            {
                "id": app_id,
                "name": str(app.get("name") or app_id),
                "description": str(app.get("description") or ""),
                "domain_path": domain_path,
                "url": url,
                "default_url": url,
                "version": str(app.get("version") or ""),
                "admin_only_default": app_id in ADMIN_ONLY_IDS,
                "configured": app_id in seen_ids,
                "source": "yunohost",
            }
        )
    available_apps.sort(key=lambda item: item["name"].lower())

    visible_apps = [
        deepcopy(app)
        for app in configured_apps
        if app["show_on_homepage"] and (app["source"] != "yunohost" or app["installed"])
    ]
    visible_apps.sort(key=lambda item: (item["category"], item["order"], item["name"]["en"].lower()))

    payload = {
        "generated_at": now,
        "categories": categories,
        "apps": visible_apps,
        "available_apps": available_apps,
        "discovered_services": _discover_local_services(),
        "registry_meta": {
            "enums": ADMIN_ENUMS,
            "templates": SERVICE_TEMPLATES,
            "built_in_actions": list(BUILTIN_ADMIN_ACTIONS),
            "appgen_profiles": APPGEN_PROFILES,
            "appgen_sections": APPGEN_SECTIONS,
            "appgen_process": APPGEN_PROCESS,
            "appgen_admin_presets": APPGEN_ADMIN_PRESETS,
        },
    }
    _catalog_cache["ts"] = now
    _catalog_cache["payload"] = payload
    return payload


def _reset_catalog_cache():
    _catalog_cache["ts"] = 0
    _catalog_cache["payload"] = None


def _normalized_catalog_state() -> tuple[dict, list[dict]]:
    config = _read_catalog_file()
    categories = _normalize_category_map(config.get("categories"))
    if "other" not in categories:
        categories["other"] = {
            "id": "other",
            "order": 9999,
            "name": {"fr": "Autres", "en": "Other", "de": "Weitere", "es": "Otros"},
        }
    yh_apps = _load_yunohost_apps()
    category_ids = set(categories.keys())
    apps = []
    for raw in config.get("apps") or []:
        if isinstance(raw, dict):
            apps.append(_normalize_catalog_entry(raw, yh_apps, category_ids))
    return categories, apps


def _find_catalog_app(app_id: str) -> dict | None:
    _, apps = _normalized_catalog_state()
    for app in apps:
        if app.get("id") == app_id:
            return app
    return None


def _truncate_text(value: str, limit: int = ACTION_OUTPUT_LIMIT) -> str:
    text = str(value or "")
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...[truncated]..."


def _append_audit_log(event: dict):
    record = dict(event)
    record["ts"] = int(record.get("ts") or _now())
    with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def _read_recent_audit_events(limit: int = 40) -> list[dict]:
    if limit <= 0:
        return []
    try:
        with open(AUDIT_LOG_PATH, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
    except FileNotFoundError:
        return []

    events = []
    for line in lines[-limit:]:
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except Exception:
            continue
        if isinstance(item, dict):
            events.append(item)
    return list(reversed(events))


def _recent_audit_by_app(events: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for event in events:
        if not isinstance(event, dict):
            continue
        app_id = _string(event.get("app_id"))
        if not app_id:
            continue
        grouped.setdefault(app_id, []).append(event)
    return grouped


def _http_health_snapshot(url: str) -> dict:
    target = _string(url)
    if not target:
        return {"ok": None, "code": None, "detail": "no-url"}
    req = urlrequest.Request(target, headers={"User-Agent": "micou-control-plane/1.0"})
    try:
        with urlrequest.urlopen(req, timeout=4) as response:
            code = int(getattr(response, "status", 200) or 200)
            return {
                "ok": 200 <= code < 400,
                "code": code,
                "detail": "reachable",
            }
    except urlerror.HTTPError as exc:
        code = int(getattr(exc, "code", 0) or 0)
        return {
            "ok": 200 <= code < 400,
            "code": code,
            "detail": "http-error",
        }
    except Exception as exc:
        return {
            "ok": False,
            "code": None,
            "detail": _string(exc, "unreachable"),
        }


def _systemd_health_snapshot(unit: str) -> dict:
    name = _string(unit)
    if not name:
        return {"active": None, "substate": "", "detail": "no-unit"}
    proc = _run_command(["systemctl", "show", name, "--property=ActiveState,SubState,UnitFileState"], timeout=30)
    if proc.returncode != 0:
        return {"active": False, "substate": "", "detail": _string(proc.stderr or proc.stdout, "systemctl failed")}
    data = {}
    for line in (proc.stdout or "").splitlines():
        key, _, value = line.partition("=")
        if key:
            data[key.strip()] = value.strip()
    active_state = _string(data.get("ActiveState"))
    sub_state = _string(data.get("SubState"))
    return {
        "active": active_state == "active",
        "substate": sub_state,
        "detail": active_state or "unknown",
        "unit_file_state": _string(data.get("UnitFileState")),
    }


def _build_service_insights(apps: list[dict], recent_audit: list[dict]) -> dict[str, dict]:
    by_app = _recent_audit_by_app(recent_audit)
    insights: dict[str, dict] = {}
    for app in apps:
        app_id = _string(app.get("id"))
        if not app_id:
            continue
        app_events = by_app.get(app_id, [])
        last_event = app_events[0] if app_events else None
        deployment = app.get("deployment") or {}
        links = app.get("links") or {}
        unit = _string(deployment.get("systemd_unit"))
        explicit_health_url = _string(links.get("health_url") or deployment.get("healthcheck_url"))
        public_url = _string(links.get("public_url") or app.get("default_url"))
        health_url = explicit_health_url or (public_url if app.get("source") != "yunohost" else "")
        systemd_status = _systemd_health_snapshot(unit) if unit else None
        http_status = _http_health_snapshot(health_url) if health_url else None
        derived = "unknown"
        if systemd_status and systemd_status.get("active") is True:
            derived = "running"
        elif systemd_status and systemd_status.get("active") is False:
            derived = "stopped"
        elif http_status and http_status.get("ok") is True:
            derived = "reachable"
        elif http_status and http_status.get("ok") is False:
            derived = "unreachable"
        elif app.get("source") == "yunohost" and app.get("installed"):
            derived = "managed"

        insights[app_id] = {
            "status": derived,
            "systemd": systemd_status,
            "http": http_status,
            "last_action": {
                "action": _string((last_event or {}).get("action")),
                "status": _string((last_event or {}).get("status")),
                "ts": int((last_event or {}).get("ts") or 0),
                "returncode": (last_event or {}).get("returncode"),
            },
            "recent_actions": [
                {
                    "action": _string(event.get("action")),
                    "status": _string(event.get("status")),
                    "ts": int(event.get("ts") or 0),
                    "returncode": event.get("returncode"),
                }
                for event in app_events[:5]
            ],
            "recent_action_count": len(app_events),
        }
    return insights


def _enrich_content_state(content: dict, recent_audit: list[dict]) -> dict:
    enriched = deepcopy(content if isinstance(content, dict) else {})
    enriched.setdefault("admin", {})
    admin_cfg = enriched["admin"] if isinstance(enriched.get("admin"), dict) else {}
    admin_cfg.setdefault("saved_views", [])
    enriched["admin"] = admin_cfg

    pages = enriched.get("pages")
    if not isinstance(pages, list):
        pages = []
    audit_by_app = _recent_audit_by_app(recent_audit)
    new_pages = []
    for raw_page in pages:
        if not isinstance(raw_page, dict):
            continue
        page = dict(raw_page)
        page.setdefault("deploy_target", _string(page.get("path")))
        page.setdefault("deploy_command", "")
        page.setdefault("publish_notes", "")
        history = page.get("publish_history")
        if not isinstance(history, list):
            history = []
        page["publish_history"] = history
        source_app = _string(page.get("source_app"))
        related = audit_by_app.get(source_app, []) if source_app else []
        page["last_service_action"] = related[0] if related else None
        new_pages.append(page)
    enriched["pages"] = new_pages
    return enriched


def _safe_service_group_name(app_id: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", str(app_id).strip().lower()).strip("_")
    slug = slug[:40] if len(slug) > 40 else slug
    return f"svc_{slug}" if slug else "svc_service"


def _run_command(argv: list[str], cwd: str | None = None, timeout: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run(
        argv,
        capture_output=True,
        text=True,
        timeout=max(timeout, 5),
        cwd=cwd or None,
        check=False,
    )


def _run_shell(command: str, cwd: str | None = None, timeout: int = 300) -> subprocess.CompletedProcess:
    return _run_command(["/bin/bash", "-lc", command], cwd=cwd, timeout=timeout)


def _parse_json_output(raw: str):
    try:
        return json.loads(raw or "")
    except Exception:
        return None


def _run_yunohost_json(args: list[str]) -> object:
    proc = _run_command(["yunohost", *args, "--output-as", "json"], timeout=180)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "YunoHost command failed")
    payload = _parse_json_output(proc.stdout)
    if payload is None:
        raise RuntimeError("YunoHost command returned invalid JSON")
    return payload


def _run_yunohost(args: list[str]) -> subprocess.CompletedProcess:
    proc = _run_command(["yunohost", *args], timeout=180)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "YunoHost command failed")
    return proc


def _load_yunohost_users_state() -> dict[str, dict]:
    payload = _run_yunohost_json(["user", "list"])
    users = []
    if isinstance(payload, dict):
        users = payload.get("users") or payload.get("user") or payload.get("data") or []
        if isinstance(users, dict):
            users = [
                {"username": key, **(value if isinstance(value, dict) else {})}
                for key, value in users.items()
            ]
    elif isinstance(payload, list):
        users = payload

    out = {}
    for user in users:
        if not isinstance(user, dict):
            continue
        username = _string(user.get("username") or user.get("user") or user.get("id"))
        if username:
            enriched = dict(user)
            try:
                info = _run_yunohost_json(["user", "info", username])
                if isinstance(info, dict):
                    enriched.update(info)
            except Exception:
                pass
            out[username] = enriched
    return out


def _identity_keys_for_user(username: str, user: dict) -> set[str]:
    item = user if isinstance(user, dict) else {}
    keys = set()
    if username:
        keys.add(username.lower())
    for raw in (
        item.get("mail"),
        item.get("email"),
    ):
        value = _string(raw).lower()
        if value:
            keys.add(value)
    for alias in item.get("mail-aliases") or item.get("aliases") or []:
        value = _string(alias).lower()
        if value:
            keys.add(value)
    return keys


def _load_yunohost_users_index() -> dict[str, str]:
    users = _load_yunohost_users_state()
    index = {}
    for username, user in users.items():
        for key in _identity_keys_for_user(username, user):
            index[key] = username
    return index


def _identity_candidates(identity_key: str, users_index: dict[str, str], users_state: dict[str, dict]) -> set[str]:
    key = _string(identity_key).lower()
    candidates = {key} if key else set()
    username = _string(users_index.get(key))
    if username:
        candidates.add(username.lower())
        candidates.update(_identity_keys_for_user(username, users_state.get(username) or {}))
    return {item for item in candidates if item}


def _load_yunohost_groups_state() -> dict[str, set[str]]:
    payload = _run_yunohost_json(["user", "group", "list"])
    groups = {}
    raw_groups = payload.get("groups") if isinstance(payload, dict) else payload
    if isinstance(raw_groups, dict):
        for name, data in raw_groups.items():
            members = set()
            if isinstance(data, dict):
                raw_members = data.get("members") or data.get("users") or []
                if isinstance(raw_members, list):
                    members = {str(item).strip() for item in raw_members if str(item).strip()}
            groups[str(name)] = members
    return groups


def _load_yunohost_permissions_state() -> dict[str, dict]:
    payload = _run_yunohost_json(["user", "permission", "list", "--full"])
    raw_permissions = payload.get("permissions") if isinstance(payload, dict) else payload
    permissions = {}
    if isinstance(raw_permissions, dict):
        for name, data in raw_permissions.items():
            if not isinstance(data, dict):
                continue
            principals = data.get("allowed") or data.get("corresponding_users") or []
            permissions[str(name)] = {
                "allowed": {str(item).strip() for item in principals if str(item).strip()},
                "raw": data,
            }
    return permissions


def _ensure_yunohost_group(name: str):
    groups = _load_yunohost_groups_state()
    if name in groups:
        return
    _run_yunohost(["user", "group", "create", name])


def _sync_group_members(group_name: str, target_members: set[str], current_groups: dict[str, set[str]] | None = None) -> dict:
    groups = current_groups or _load_yunohost_groups_state()
    current_members = set(groups.get(group_name, set()))
    created = False
    if group_name not in groups:
        _run_yunohost(["user", "group", "create", group_name])
        current_members = set()
        created = True

    added = []
    removed = []
    for username in sorted(target_members - current_members):
        _run_yunohost(["user", "group", "add", group_name, username])
        added.append(username)
    for username in sorted(current_members - target_members):
        _run_yunohost(["user", "group", "remove", group_name, username])
        removed.append(username)
    groups[group_name] = set(target_members)
    return {"group": group_name, "created": created, "added": added, "removed": removed}


def _find_primary_permission_name(app: dict, permissions: dict[str, dict]) -> str | None:
    candidates = []
    app_id = _string(app.get("yunohost_app_id") or app.get("id"))
    if not app_id:
        return None
    candidates.extend([app_id, f"{app_id}.main"])
    for candidate in candidates:
        if candidate in permissions:
            return candidate
    prefixed = sorted([name for name in permissions.keys() if name == app_id or name.startswith(f"{app_id}.")])
    if f"{app_id}.main" in prefixed:
        return f"{app_id}.main"
    return prefixed[0] if prefixed else None


def _sync_yunohost_access(viewer: dict) -> dict:
    grants = _load_grants()
    _, apps = _normalized_catalog_state()
    users_index = _load_yunohost_users_index()
    groups_state = _load_yunohost_groups_state()
    permissions_state = _load_yunohost_permissions_state()

    group_results = []
    permission_results = []

    managed_groups: dict[str, set[str]] = {}
    for group_name, member_emails in grants.get("groups", {}).items():
        usernames = {users_index[email] for email in member_emails if email in users_index}
        managed_groups[group_name] = usernames

    for app in apps:
        service_group = _safe_service_group_name(app.get("id") or "")
        service_members = set()
        needs_service_group = False
        allowed_tokens = {str(token).strip() for token in app.get("allowed_groups") or [] if str(token).strip()}
        for token in app.get("allowed_groups") or []:
            item = str(token).strip()
            if item == "user:authorized" or item.startswith("user:"):
                needs_service_group = True
        for email, data in (grants.get("users") or {}).items():
            username = users_index.get(email)
            if not username:
                continue
            if app.get("id") in set(data.get("apps") or []):
                service_members.add(username)
                needs_service_group = True
        if needs_service_group:
            managed_groups[service_group] = service_members

    for group_name, members in managed_groups.items():
        group_results.append(_sync_group_members(group_name, members, groups_state))

    groups_state = _load_yunohost_groups_state()
    permissions_state = _load_yunohost_permissions_state()

    for app in apps:
        if app.get("source") != "yunohost":
            continue
        permission_name = _find_primary_permission_name(app, permissions_state)
        if not permission_name:
            permission_results.append({"app_id": app.get("id"), "permission": None, "status": "missing"})
            continue

        target_principals = set()
        for token in app.get("allowed_groups") or []:
            item = str(token).strip()
            if not item:
                continue
            if item == "visitor":
                target_principals.add("visitors")
            elif item == "user:all":
                target_principals.add("all_users")
            elif item == "admin":
                target_principals.add("admins")
            elif item == "user:authorized":
                target_principals.add(_safe_service_group_name(app.get("id") or ""))
            elif item.startswith("group:"):
                target_principals.add(item.split(":", 1)[1].strip())
            elif item.startswith("user:"):
                username = users_index.get(item.split(":", 1)[1].strip().lower())
                if username:
                    target_principals.add(username)

        current_allowed = set((permissions_state.get(permission_name) or {}).get("allowed") or set())
        added = []
        removed = []
        for principal in sorted(target_principals - current_allowed):
            _run_yunohost(["user", "permission", "add", permission_name, principal])
            added.append(principal)
        for principal in sorted(current_allowed - target_principals):
            _run_yunohost(["user", "permission", "remove", permission_name, principal])
            removed.append(principal)

        permission_results.append(
            {
                "app_id": app.get("id"),
                "permission": permission_name,
                "target_principals": sorted(target_principals),
                "added": added,
                "removed": removed,
                "status": "synced",
            }
        )

    return {
        "ok": True,
        "status": "ok",
        "groups": group_results,
        "permissions": permission_results,
    }


def _bootstrap_service_repo(app: dict) -> dict:
    deployment = app.get("deployment") or {}
    repo_url = _string(deployment.get("repo_url") or app.get("repo_url"))
    if not repo_url:
        raise ValueError("No repository URL configured for this service")
    deploy_path = _string(deployment.get("deploy_path")) or os.path.join(SERVICES_ROOT, app.get("id") or "service")
    branch = _string(deployment.get("branch"), "main")
    os.makedirs(os.path.dirname(deploy_path), exist_ok=True)

    if os.path.isdir(os.path.join(deploy_path, ".git")):
        command = f"git -C {json.dumps(deploy_path)} fetch --all --prune && git -C {json.dumps(deploy_path)} checkout {json.dumps(branch)} && git -C {json.dumps(deploy_path)} pull --ff-only origin {json.dumps(branch)}"
        proc = _run_shell(command, timeout=600)
        action = "updated"
    else:
        if os.path.exists(deploy_path) and os.listdir(deploy_path):
            raise ValueError("Deploy path exists and is not an empty git repository")
        command = f"git clone --branch {json.dumps(branch)} {json.dumps(repo_url)} {json.dumps(deploy_path)}"
        proc = _run_shell(command, timeout=600)
        action = "cloned"

    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "Git bootstrap failed")

    return {
        "ok": True,
        "status": "ok",
        "action": action,
        "deploy_path": deploy_path,
        "stdout": _truncate_text(proc.stdout),
        "stderr": _truncate_text(proc.stderr),
    }


def _compose_file_for_app(app: dict) -> tuple[str, str]:
    deployment = app.get("deployment") or {}
    deploy_path = _string(deployment.get("deploy_path")) or os.path.join(SERVICES_ROOT, app.get("id") or "service")
    compose_file = _string(deployment.get("compose_file"))
    if not compose_file:
        for candidate in ("docker-compose.yml", "compose.yml"):
            full = os.path.join(deploy_path, candidate)
            if os.path.exists(full):
                compose_file = full
                break
    if not compose_file:
        raise ValueError("No compose file configured for this service")
    return deploy_path, compose_file


def _compose_service_action(app: dict, action: str) -> dict:
    deploy_path, compose_file = _compose_file_for_app(app)
    if action == "compose_pull":
        proc = _run_command(["docker", "compose", "-f", compose_file, "pull"], cwd=deploy_path, timeout=900)
    elif action == "compose_up":
        proc = _run_command(["docker", "compose", "-f", compose_file, "up", "-d"], cwd=deploy_path, timeout=900)
    else:
        raise ValueError("Unsupported compose action")

    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "Compose action failed")
    return {
        "ok": True,
        "status": "ok",
        "stdout": _truncate_text(proc.stdout),
        "stderr": _truncate_text(proc.stderr),
        "deploy_path": deploy_path,
        "compose_file": compose_file,
    }


def _systemd_restart_for_app(app: dict) -> dict:
    unit = _string(((app.get("deployment") or {}).get("systemd_unit")))
    if not unit:
        raise ValueError("No systemd unit configured for this service")
    proc = _run_command(["systemctl", "restart", unit], timeout=300)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "systemd restart failed")
    status_proc = _run_command(["systemctl", "status", "--no-pager", unit], timeout=120)
    return {
        "ok": True,
        "status": "ok",
        "stdout": _truncate_text(status_proc.stdout or proc.stdout),
        "stderr": _truncate_text(status_proc.stderr or proc.stderr),
        "unit": unit,
    }


def _scaffold_service_repo(app: dict) -> dict:
    deployment = app.get("deployment") or {}
    deploy_path = _string(deployment.get("deploy_path")) or os.path.join(SERVICES_ROOT, app.get("id") or "service")
    if os.path.exists(deploy_path) and os.listdir(deploy_path):
        raise ValueError("Deploy path already exists and is not empty")
    os.makedirs(deploy_path, exist_ok=True)

    service_name = app.get("id") or "service"
    public_url = _string((app.get("links") or {}).get("public_url") or app.get("default_url"))
    compose_template = (
        "services:\n"
        f"  {service_name}:\n"
        "    image: alpine:latest\n"
        "    command: [\"sh\", \"-c\", \"while true; do sleep 3600; done\"]\n"
        "    restart: unless-stopped\n"
    )
    files = {
        "README.md": f"# {service_name}\n\nManaged by micou.org service control plane.\n",
        ".env.example": f"SERVICE_NAME={service_name}\nPUBLIC_URL={public_url}\n",
        "DEPLOY.md": (
            f"# Deploy {service_name}\n\n"
            f"- Public URL: {public_url or 'set in catalog'}\n"
            f"- Deploy path: {deploy_path}\n"
            "- Update registry deployment metadata before first deploy.\n"
        ),
        "docker-compose.yml": compose_template,
    }
    for name, content in files.items():
        with open(os.path.join(deploy_path, name), "w", encoding="utf-8") as fh:
            fh.write(content)

    return {
        "ok": True,
        "status": "ok",
        "deploy_path": deploy_path,
        "files": sorted(files.keys()),
        "stdout": "",
        "stderr": "",
    }


def _scaffold_yunohost_appgen(app: dict) -> dict:
    app_id = _string(app.get("id"))
    if not app_id:
        raise ValueError("Service is missing an id")
    script_path = "/home/micou_org/scripts/scaffold_yunohost_appgen.py"
    if not os.path.exists(script_path):
        raise ValueError(f"Missing scaffold script: {script_path}")
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as fh:
        json.dump(app, fh, ensure_ascii=False, indent=2)
        tmp_path = fh.name
    try:
        proc = subprocess.run(
            ["python3", script_path, "--from-service-json", tmp_path],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
    ok = proc.returncode == 0
    stdout = _truncate_text(proc.stdout or "")
    stderr = _truncate_text(proc.stderr or "")
    result = {
        "ok": ok,
        "status": "ok" if ok else "failed",
        "returncode": proc.returncode,
        "stdout": stdout,
        "stderr": stderr,
    }
    if ok and stdout:
        try:
            payload = json.loads(stdout)
        except Exception:
            payload = None
        if isinstance(payload, dict):
            result["output_dir"] = _string(payload.get("output_dir"))
            result["files"] = payload.get("files") or []
    return result


def _run_admin_action(app: dict, action: str, viewer: dict) -> dict:
    if action in BUILTIN_ADMIN_ACTIONS:
        started_at = _now()
        command = f"built-in:{action}"
        try:
            if action == "sync_access":
                result = _sync_yunohost_access(viewer)
                command = "built-in:sync_yunohost_access"
            elif action == "sync_projection":
                result = _maybe_sync_postgres_projection("sync_projection", viewer.get("email") or viewer.get("username") or "")
                command = "built-in:sync_postgres_projection"
            elif action == "bootstrap_repo":
                result = _bootstrap_service_repo(app)
                command = "built-in:bootstrap_repo"
            elif action in ("compose_pull", "compose_up"):
                result = _compose_service_action(app, action)
                command = f"built-in:{action}"
            elif action == "systemd_restart":
                result = _systemd_restart_for_app(app)
                command = "built-in:systemd_restart"
            elif action == "scaffold_repo":
                result = _scaffold_service_repo(app)
                command = "built-in:scaffold_repo"
            elif action == "scaffold_appgen":
                result = _scaffold_yunohost_appgen(app)
                command = "built-in:scaffold_yunohost_appgen"
            else:
                raise ValueError("Unsupported action")
        except Exception as exc:
            result = {
                "ok": False,
                "status": "error",
                "returncode": None,
                "stdout": "",
                "stderr": _truncate_text(str(exc)),
            }

        audit_event = {
            "ts": started_at,
            "viewer": viewer.get("email") or "",
            "app_id": app.get("id") or "",
            "action": action,
            "command": command,
            "status": result.get("status", "ok"),
            "ok": bool(result.get("ok")),
            "returncode": result.get("returncode"),
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
        }
        _append_audit_log(audit_event)
        result["audit_event"] = audit_event
        return result

    if action not in ACTION_NAMES:
        raise ValueError("Unsupported action")

    command = _string(((app.get("operations") or {}).get(action)))
    if not command:
        raise ValueError(f'No "{action}" command configured for this service')

    timeout_default = 600 if action != "logs" else 120
    try:
        timeout = int(os.environ.get("MICOU_ADMIN_ACTION_TIMEOUT", str(timeout_default)))
    except Exception:
        timeout = timeout_default

    started_at = _now()
    try:
        proc = subprocess.run(
            ["/bin/bash", "-lc", command],
            capture_output=True,
            text=True,
            timeout=max(timeout, 5),
            cwd=_string(((app.get("deployment") or {}).get("deploy_path"))) or None,
            env=os.environ.copy(),
        )
        success = proc.returncode == 0
        result = {
            "ok": success,
            "status": "ok" if success else "failed",
            "returncode": proc.returncode,
            "stdout": _truncate_text(proc.stdout),
            "stderr": _truncate_text(proc.stderr),
        }
    except subprocess.TimeoutExpired as exc:
        result = {
            "ok": False,
            "status": "timeout",
            "returncode": None,
            "stdout": _truncate_text(exc.stdout or ""),
            "stderr": _truncate_text(exc.stderr or ""),
        }
    except Exception as exc:
        result = {
            "ok": False,
            "status": "error",
            "returncode": None,
            "stdout": "",
            "stderr": _truncate_text(str(exc)),
        }

    audit_event = {
        "ts": started_at,
        "viewer": viewer.get("email") or "",
        "app_id": app.get("id") or "",
        "action": action,
        "command": command,
        "status": result["status"],
        "ok": bool(result["ok"]),
        "returncode": result.get("returncode"),
        "stdout": result.get("stdout", ""),
        "stderr": result.get("stderr", ""),
    }
    _append_audit_log(audit_event)
    result["audit_event"] = audit_event
    return result


def _viewer_email_from_headers(headers) -> str:
    candidates = (
        "X-YNH-User",
        "X_YNH_USER",
        "Remote-User",
        "X-Remote-User",
        "Ynh-User",
    )
    for key in candidates:
        value = headers.get(key)
        if value:
            return str(value).strip().lower()
    return ""


def _resolve_viewer(headers) -> dict:
    grants = _load_grants()
    identity = _viewer_email_from_headers(headers)
    try:
        users_state = _load_yunohost_users_state()
        users_index = _load_yunohost_users_index()
    except Exception:
        users_state = {}
        users_index = {}
    return _viewer_from_identity(identity, grants, users_index, users_state)


def _is_allowed_for_viewer(app: dict, viewer: dict) -> bool:
    return bool(_allowed_rules_for_viewer(app, viewer))


def _allowed_rules_for_viewer(app: dict, viewer: dict) -> list[str]:
    allowed_groups = app.get("allowed_groups") or []
    identity_keys = {str(item).strip().lower() for item in viewer.get("identity_keys") or [] if str(item).strip()}
    roles = set(viewer.get("roles") or [])
    viewer_groups = set(viewer.get("groups") or [])
    granted_apps = set(viewer.get("app_grants") or [])
    matches = []

    for rule in allowed_groups:
        token = str(rule).strip()
        if not token:
            continue
        if token == "visitor":
            matches.append(token)
        elif token == "admin" and "admin" in roles:
            matches.append(token)
        elif token == "user:all" and "user" in roles:
            matches.append(token)
        elif token == "user:authorized" and app.get("id") in granted_apps:
            matches.append(token)
        elif token.startswith("user:") and token[5:].strip().lower() in identity_keys:
            matches.append(token)
        elif token.startswith("group:") and token[6:].strip() in viewer_groups:
            matches.append(token)
    return matches


def _resolve_yunohost_username(identity_key: str, users_index: dict[str, str]) -> str:
    key = _string(identity_key).lower()
    if not key:
        return ""
    return _string(users_index.get(key))


def _viewer_from_identity(identity_key: str, grants: dict, users_index: dict[str, str] | None = None, users_state: dict[str, dict] | None = None) -> dict:
    key = _string(identity_key).lower()
    users_index = users_index or {}
    users_state = users_state or {}
    candidates = _identity_candidates(key, users_index, users_state) or ({key} if key else set())
    username = _string(users_index.get(key))
    user = users_state.get(username) if username else {}
    primary_email = _string((user or {}).get("mail") or (user or {}).get("email")).lower()
    groups = set()
    app_grants = set()
    for candidate in candidates:
        user_grants = (grants.get("users") or {}).get(candidate, {})
        groups.update((user_grants or {}).get("groups", []))
        app_grants.update((user_grants or {}).get("apps", []))
    roles = {"visitor"}
    if key:
        roles.add("user")
    if candidates & set(grants.get("admins") or []):
        roles.add("admin")
    return {
        "email": primary_email or (key if "@" in key else ""),
        "username": username,
        "identity_keys": sorted(candidates),
        "roles": sorted(roles),
        "groups": sorted(groups),
        "app_grants": sorted(app_grants),
    }


def _build_expected_yunohost_access_snapshot(grants: dict, apps: list[dict], users_index: dict[str, str], permissions_state: dict[str, dict]) -> dict:
    managed_groups: dict[str, set[str]] = {}
    for group_name, member_keys in (grants.get("groups") or {}).items():
        usernames = {_resolve_yunohost_username(member_key, users_index) for member_key in member_keys}
        managed_groups[group_name] = {item for item in usernames if item}

    app_permissions = {}
    for app in apps:
        service_group = _safe_service_group_name(app.get("id") or "")
        service_members = set()
        needs_service_group = False
        allowed_tokens = {str(token).strip() for token in app.get("allowed_groups") or [] if str(token).strip()}
        for token in app.get("allowed_groups") or []:
            item = str(token).strip()
            if item == "user:authorized" or item.startswith("user:"):
                needs_service_group = True
        for user_key, data in (grants.get("users") or {}).items():
            username = _resolve_yunohost_username(user_key, users_index)
            if not username:
                continue
            if app.get("id") in set((data or {}).get("apps") or []):
                service_members.add(username)
                needs_service_group = True
        if needs_service_group:
            managed_groups[service_group] = service_members

        if app.get("source") != "yunohost":
            continue

        permission_name = _find_primary_permission_name(app, permissions_state) or ""
        target_principals = set()
        for token in app.get("allowed_groups") or []:
            item = str(token).strip()
            if not item:
                continue
            if item == "visitor":
                target_principals.add("visitors")
            elif item == "user:all":
                target_principals.add("all_users")
            elif item == "admin":
                target_principals.add("admins")
            elif item == "user:authorized":
                target_principals.add(service_group)
            elif item.startswith("group:"):
                target_principals.add(item.split(":", 1)[1].strip())
            elif item.startswith("user:"):
                username = _resolve_yunohost_username(item.split(":", 1)[1].strip(), users_index)
                if username:
                    target_principals.add(username)

        app_permissions[app.get("id") or ""] = {
            "permission_name": permission_name,
            "principals": sorted(target_principals),
        }

    return {
        "managed_groups": {name: sorted(members) for name, members in managed_groups.items()},
        "app_permissions": app_permissions,
    }


def _build_postgres_sync_snapshot(trigger_name: str = "manual", actor_key: str = "") -> dict:
    raw_catalog = _read_catalog_file()
    raw_grants = _read_grants_file()
    raw_content = _read_content_file()
    recent_audit = _read_recent_audit_events()
    categories, apps = _normalized_catalog_state()
    grants = _load_grants()
    content = _enrich_content_state(raw_content, recent_audit)

    try:
        yunohost_apps = _load_yunohost_apps()
        yunohost_users = _load_yunohost_users_state()
        yunohost_users_index = _load_yunohost_users_index()
        yunohost_groups = {name: sorted(members) for name, members in _load_yunohost_groups_state().items()}
        yunohost_permissions_state = _load_yunohost_permissions_state()
        yunohost_permissions = {
            name: {
                **(data.get("raw") if isinstance(data.get("raw"), dict) else {}),
                "allowed": sorted(data.get("allowed") or []),
            }
            for name, data in yunohost_permissions_state.items()
        }
        yunohost_error = ""
    except Exception as exc:
        yunohost_apps = {}
        yunohost_users = {}
        yunohost_users_index = {}
        yunohost_groups = {}
        yunohost_permissions_state = {}
        yunohost_permissions = {}
        yunohost_error = str(exc)

    resolved_users = {
        user_key: _resolve_yunohost_username(user_key, yunohost_users_index)
        for user_key in (grants.get("users") or {}).keys()
    }
    resolved_admins = {
        admin_key: _resolve_yunohost_username(admin_key, yunohost_users_index)
        for admin_key in grants.get("admins") or []
    }
    resolved_group_members = {
        group_name: {
            member_key: _resolve_yunohost_username(member_key, yunohost_users_index)
            for member_key in members
        }
        for group_name, members in (grants.get("groups") or {}).items()
    }

    viewer_keys = set(grants.get("admins") or [])
    viewer_keys.update((grants.get("users") or {}).keys())
    for username, user in yunohost_users.items():
        viewer_keys.add(username)
        primary_email = _string((user or {}).get("mail") or (user or {}).get("email"))
        if primary_email:
            viewer_keys.add(primary_email.lower())

    viewer_access = []
    for viewer_key in sorted({_string(item).lower() for item in viewer_keys if _string(item)}):
        viewer = _viewer_from_identity(viewer_key, grants, yunohost_users_index, yunohost_users)
        for app in apps:
            match_reasons = _allowed_rules_for_viewer(app, viewer)
            viewer_access.append(
                {
                    "viewer_key": viewer_key,
                    "identity_kind": "email" if "@" in viewer_key else "username",
                    "resolved_username": _resolve_yunohost_username(viewer_key, yunohost_users_index),
                    "service_key": app.get("id") or "",
                    "roles": viewer.get("roles") or [],
                    "groups": viewer.get("groups") or [],
                    "app_grants": viewer.get("app_grants") or [],
                    "allowed_for_viewer": bool(match_reasons),
                    "requires_request": app.get("access_mode") != "public" and not bool(match_reasons),
                    "match_reasons": match_reasons,
                }
            )

    expected_access = _build_expected_yunohost_access_snapshot(grants, apps, yunohost_users_index, yunohost_permissions_state)

    return {
        "trigger_name": trigger_name,
        "actor_key": actor_key,
        "raw_documents": {
            "catalog": raw_catalog,
            "grants": raw_grants,
            "content": raw_content,
        },
        "categories": categories,
        "services": apps,
        "grants": {
            **grants,
            "resolved_users": resolved_users,
            "resolved_admins": resolved_admins,
            "resolved_group_members": resolved_group_members,
        },
        "content": content,
        "discovered_services": _discover_local_services(),
        "yunohost": {
            "apps": yunohost_apps,
            "users": yunohost_users,
            "groups": yunohost_groups,
            "permissions": yunohost_permissions,
            "error": yunohost_error,
        },
        "viewer_access": viewer_access,
        "expected_access": expected_access,
        "recent_audit": recent_audit,
    }


def _maybe_sync_postgres_projection(trigger_name: str, actor_key: str = "") -> dict:
    if not DATABASE_URL or sync_snapshot_to_postgres is None:
        return {"ok": False, "status": "disabled", "reason": "database_sync_not_configured"}
    snapshot = _build_postgres_sync_snapshot(trigger_name=trigger_name, actor_key=actor_key)
    return sync_snapshot_to_postgres(DATABASE_URL, snapshot, trigger_name=trigger_name, actor_key=actor_key)


def _load_postgres_sync_state(limit_issues: int = 30) -> dict:
    if not DATABASE_URL or psycopg2 is None:
        return {
            "enabled": False,
            "status": "disabled",
            "reason": "database_sync_not_configured",
            "latest_run": None,
            "counts": {"errors": 0, "warnings": 0, "info": 0},
            "issues": [],
            "service_mismatches": [],
        }

    try:
        conn = psycopg2.connect(DATABASE_URL)
    except Exception as exc:
        return {
            "enabled": True,
            "status": "error",
            "reason": str(exc),
            "latest_run": None,
            "counts": {"errors": 0, "warnings": 0, "info": 0},
            "issues": [],
            "service_mismatches": [],
        }

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT sync_run_id, trigger_name, actor_key, status, started_at, completed_at, summary
                    FROM micou.sync_runs
                    ORDER BY sync_run_id DESC
                    LIMIT 1
                    """
                )
                row = cur.fetchone()
                latest_run = None
                if row:
                    latest_run = {
                        "sync_run_id": row[0],
                        "trigger_name": row[1],
                        "actor_key": row[2],
                        "status": row[3],
                        "started_at": row[4].isoformat() if row[4] else "",
                        "completed_at": row[5].isoformat() if row[5] else "",
                        "summary": row[6] if isinstance(row[6], dict) else {},
                    }

                cur.execute(
                    """
                    SELECT severity, count(*)
                    FROM micou.sync_issues
                    GROUP BY severity
                    """
                )
                counts = {"errors": 0, "warnings": 0, "info": 0}
                for severity, count in cur.fetchall():
                    if severity == "error":
                        counts["errors"] = int(count)
                    elif severity == "warning":
                        counts["warnings"] = int(count)
                    elif severity == "info":
                        counts["info"] = int(count)

                cur.execute(
                    """
                    SELECT severity, issue_code, service_key, related_user_key, related_group_name, related_page_id, detail
                    FROM micou.sync_issues
                    ORDER BY
                      CASE severity WHEN 'error' THEN 0 WHEN 'warning' THEN 1 ELSE 2 END,
                      issue_code,
                      service_key,
                      related_user_key
                    LIMIT %s
                    """,
                    (max(limit_issues, 1),),
                )
                issues = [
                    {
                        "severity": row[0],
                        "issue_code": row[1],
                        "service_key": row[2],
                        "related_user_key": row[3],
                        "related_group_name": row[4],
                        "related_page_id": row[5],
                        "detail": row[6],
                    }
                    for row in cur.fetchall()
                ]

                cur.execute(
                    """
                    SELECT service_key, source, permission_name, expected_principals, observed_principals, error_count, warning_count
                    FROM micou.v_service_sync_status
                    WHERE principals_synced = false OR error_count > 0 OR warning_count > 0
                    ORDER BY error_count DESC, warning_count DESC, service_key
                    LIMIT 24
                    """
                )
                service_mismatches = [
                    {
                    "service_key": row[0],
                    "source": row[1],
                    "permission_name": row[2],
                    "expected_principals": list(row[3] or []),
                    "observed_principals": list(row[4] or []),
                    "error_count": int(row[5] or 0),
                    "warning_count": int(row[6] or 0),
                    }
                    for row in cur.fetchall()
                ]

        return {
            "enabled": True,
            "status": "ok",
            "latest_run": latest_run,
            "counts": counts,
            "issues": issues,
            "service_mismatches": service_mismatches,
        }
    finally:
        conn.close()


def _catalog_for_viewer(viewer: dict) -> dict:
    payload = deepcopy(_build_catalog_payload())
    apps = payload.get("apps", [])
    for app in apps:
        app["allowed_for_viewer"] = _is_allowed_for_viewer(app, viewer)
        app["requires_request"] = app.get("access_mode") != "public" and not app["allowed_for_viewer"]

    payload["viewer"] = viewer
    payload["dashboard"] = {
        "public_apps": [app for app in apps if app.get("access_mode") == "public"],
        "allowed_apps": [app for app in apps if app.get("allowed_for_viewer")],
        "requestable_apps": [app for app in apps if app.get("requires_request")],
    }
    return payload


def _admin_required(viewer: dict) -> bool:
    return "admin" in set(viewer.get("roles") or [])


class Limiter:
    def __init__(self):
        self._hits: dict[str, deque[int]] = {}

    def add(self, key: str, ts: int):
        dq = self._hits.get(key)
        if dq is None:
            dq = deque()
            self._hits[key] = dq
        dq.append(ts)

    def count_since(self, key: str, earliest_ts: int) -> int:
        dq = self._hits.get(key)
        if dq is None:
            return 0
        while dq and dq[0] < earliest_ts:
            dq.popleft()
        return len(dq)


_limiter = Limiter()


def _client_ip(h: BaseHTTPRequestHandler) -> str:
    xf = h.headers.get("X-Forwarded-For", "")
    if xf:
        return xf.split(",")[0].strip()
    return h.client_address[0] if h.client_address else ""


def _read_json(h: BaseHTTPRequestHandler, max_bytes: int = 64 * 1024) -> tuple[dict | None, str | None]:
    try:
        length = int(h.headers.get("Content-Length") or "0")
    except Exception:
        length = 0
    if length <= 0 or length > max_bytes:
        return None, "Invalid body"
    try:
        body = h.rfile.read(length)
    except Exception:
        return None, "Invalid body"
    try:
        obj = json.loads(body.decode("utf-8"))
    except Exception:
        return None, "Invalid JSON"
    if not isinstance(obj, dict):
        return None, "Invalid payload"
    return obj, None


def _pow_challenge(secret: bytes) -> dict:
    nonce = secrets.token_urlsafe(18)
    exp = _now() + 300
    mac = _hmac_hex(secret, f"{nonce}.{exp}")[:32]
    token = f"{nonce}.{exp}.{mac}"
    return {"token": token, "expires": exp, "difficulty_zeros": 4}


def _verify_pow(secret: bytes, pow_obj: dict) -> bool:
    token = str(pow_obj.get("token") or "")
    try:
        counter = int(pow_obj.get("counter"))
    except Exception:
        return False
    if counter < 0 or counter > 1_000_000_000:
        return False
    provided_hash = str(pow_obj.get("hash") or "").lower()
    parts = token.split(".")
    if len(parts) != 3:
        return False
    nonce, exp_s, mac = parts
    try:
        exp = int(exp_s)
    except Exception:
        return False
    if exp < _now():
        return False
    expected_mac = _hmac_hex(secret, f"{nonce}.{exp}")[:32]
    if not hmac.compare_digest(mac, expected_mac):
        return False
    digest = sha256(f"{token}:{counter}".encode("utf-8")).hexdigest()
    if provided_hash and provided_hash != digest:
        return False
    return digest.startswith("0000")


def _send_mail(to_addr: str, reply_to: str, subject: str, body: str):
    from_addr = os.environ.get("MICOU_FORMS_FROM", "no-reply@micou.org")
    from_name = os.environ.get("MICOU_FORMS_FROM_NAME", "micou.org")
    msg_id = email.utils.make_msgid(domain="micou.org")
    date_hdr = email.utils.formatdate(localtime=True)
    headers = [
        f"From: {from_name} <{from_addr}>",
        f"To: {to_addr}",
        f"Reply-To: {reply_to}",
        f"Subject: {subject}",
        f"Date: {date_hdr}",
        f"Message-ID: {msg_id}",
        "MIME-Version: 1.0",
        "Content-Type: text/plain; charset=utf-8",
        "Content-Transfer-Encoding: 8bit",
        "",
    ]
    raw = ("\n".join(headers) + body).encode("utf-8")
    smtp_host = os.environ.get("MICOU_FORMS_SMTP_HOST", "").strip()
    if smtp_host:
        try:
            smtp_port = int(os.environ.get("MICOU_FORMS_SMTP_PORT", "587"))
        except Exception:
            smtp_port = 587
        smtp_user = os.environ.get("MICOU_FORMS_SMTP_USER", "").strip()
        smtp_pass = os.environ.get("MICOU_FORMS_SMTP_PASS", "")
        smtp_starttls = os.environ.get("MICOU_FORMS_SMTP_STARTTLS", "1").strip() != "0"
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as smtp:
            smtp.ehlo()
            if smtp_starttls:
                smtp.starttls()
                smtp.ehlo()
            if smtp_user and smtp_pass:
                smtp.login(smtp_user, smtp_pass)
            smtp.sendmail(from_addr, [to_addr], raw)
        return
    subprocess.run(["/usr/sbin/sendmail", "-t", "-i"], input=raw, check=True)


class Handler(BaseHTTPRequestHandler):
    server_version = "micou-forms/1.0"

    def log_message(self, fmt, *args):
        return

    def _send(self, code: int, body: bytes, content_type: str):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _send_json(self, code: int, obj: dict):
        self._send(code, _json_bytes(obj), "application/json; charset=utf-8")

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Content-Length", "0")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()

    def do_GET(self):
        self._handle_read_request()

    def do_HEAD(self):
        self._handle_read_request()

    def _handle_read_request(self):
        path = urlparse(self.path).path
        if path == "/api/pow":
            secret = (os.environ.get("MICOU_FORMS_SECRET") or "").encode("utf-8")
            if not secret:
                self._send_json(500, {"error": "Server not configured"})
                return
            self._send_json(200, _pow_challenge(secret))
            return
        if path == "/api/catalog":
            try:
                viewer = _resolve_viewer(self.headers)
                self._send_json(200, _catalog_for_viewer(viewer))
            except Exception:
                self._send_json(500, {"error": "Could not load catalog"})
            return
        if path == "/api/viewer":
            try:
                viewer = _resolve_viewer(self.headers)
                payload = _catalog_for_viewer(viewer)
                self._send_json(
                    200,
                    {
                        "viewer": payload["viewer"],
                        "dashboard": payload["dashboard"],
                    },
                )
            except Exception:
                self._send_json(500, {"error": "Could not load viewer"})
            return
        if path == "/api/content":
            try:
                self._send_json(200, _read_content_file())
            except Exception:
                self._send_json(500, {"error": "Could not load content"})
            return
        if path == "/api/admin/state":
            try:
                viewer = _resolve_viewer(self.headers)
                if not _admin_required(viewer):
                    self._send_json(403, {"error": "Admin access required"})
                    return
                recent_audit = _read_recent_audit_events()
                normalized_categories, normalized_apps = _normalized_catalog_state()
                self._send_json(
                    200,
                    {
                        "viewer": viewer,
                        "catalog": _read_catalog_file(),
                        "catalog_resolved": {
                            "categories": normalized_categories,
                            "apps": normalized_apps,
                        },
                        "grants": _read_grants_file(),
                        "content": _enrich_content_state(_read_content_file(), recent_audit),
                        "available_apps": _build_catalog_payload().get("available_apps", []),
                        "discovered_services": _build_catalog_payload().get("discovered_services", []),
                        "registry_meta": _build_catalog_payload().get("registry_meta", {}),
                        "access_snapshot": _load_access_snapshot(),
                        "recent_audit": recent_audit,
                        "service_insights": _build_service_insights(normalized_apps, recent_audit),
                        "postgres_state": _load_postgres_sync_state(),
                    },
                )
            except Exception:
                self._send_json(500, {"error": "Could not load admin state"})
            return
        self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/admin/save":
            viewer = _resolve_viewer(self.headers)
            if not _admin_required(viewer):
                self._send_json(403, {"error": "Admin access required"})
                return
            data, err = _read_json(self, max_bytes=512 * 1024)
            if err:
                self._send_json(400, {"error": err})
                return
            catalog = data.get("catalog")
            grants = data.get("grants")
            content = data.get("content")
            if not isinstance(catalog, dict) or not isinstance(grants, dict) or not isinstance(content, dict):
                self._send_json(400, {"error": "catalog, grants and content must be JSON objects"})
                return
            try:
                _write_json_file(CATALOG_PATH, catalog)
                _write_json_file(GRANTS_PATH, grants)
                _write_json_file(CONTENT_PATH, content)
                _reset_catalog_cache()
                postgres_sync = _maybe_sync_postgres_projection("admin_save", viewer.get("email") or "")
                self._send_json(200, {"ok": True, "postgres_sync": postgres_sync})
            except Exception:
                self._send_json(500, {"error": "Could not save admin state"})
            return
        if path == "/api/admin/action":
            viewer = _resolve_viewer(self.headers)
            if not _admin_required(viewer):
                self._send_json(403, {"error": "Admin access required"})
                return
            data, err = _read_json(self, max_bytes=64 * 1024)
            if err:
                self._send_json(400, {"error": err})
                return
            app_id = _string(data.get("app_id"))
            action = _string(data.get("action"))
            if not action:
                self._send_json(400, {"error": "action is required"})
                return
            try:
                app = {"id": "global-admin"}
                if action != "sync_access":
                    if not app_id:
                        self._send_json(400, {"error": "app_id is required for this action"})
                        return
                    app = _find_catalog_app(app_id)
                    if not app:
                        self._send_json(404, {"error": "Service not found"})
                        return
                result = _run_admin_action(app, action, viewer)
                if action == "sync_access" and result.get("ok"):
                    result["postgres_sync"] = _maybe_sync_postgres_projection("sync_access", viewer.get("email") or "")
                result["recent_audit"] = _read_recent_audit_events()
                self._send_json(200 if result.get("ok") else 400, result)
            except ValueError as exc:
                self._send_json(400, {"error": str(exc)})
            except Exception:
                self._send_json(500, {"error": "Could not execute admin action"})
            return
        if path == "/api/admin/bulk-action":
            viewer = _resolve_viewer(self.headers)
            if not _admin_required(viewer):
                self._send_json(403, {"error": "Admin access required"})
                return
            data, err = _read_json(self, max_bytes=128 * 1024)
            if err:
                self._send_json(400, {"error": err})
                return
            action = _string(data.get("action"))
            app_ids = data.get("app_ids")
            if not action:
                self._send_json(400, {"error": "action is required"})
                return
            if not isinstance(app_ids, list) or not app_ids:
                self._send_json(400, {"error": "app_ids must be a non-empty list"})
                return
            results = []
            overall_ok = True
            try:
                for raw_app_id in app_ids:
                    app_id = _string(raw_app_id)
                    if not app_id:
                        continue
                    app = _find_catalog_app(app_id)
                    if not app:
                        results.append({"app_id": app_id, "ok": False, "status": "missing", "error": "Service not found"})
                        overall_ok = False
                        continue
                    try:
                        result = _run_admin_action(app, action, viewer)
                        results.append({"app_id": app_id, **result})
                        if not result.get("ok"):
                            overall_ok = False
                    except Exception as exc:
                        results.append({"app_id": app_id, "ok": False, "status": "error", "error": str(exc)})
                        overall_ok = False
                self._send_json(
                    200 if overall_ok else 400,
                    {
                        "ok": overall_ok,
                        "status": "ok" if overall_ok else "partial_failure",
                        "action": action,
                        "results": results,
                        "recent_audit": _read_recent_audit_events(),
                    },
                )
            except Exception:
                self._send_json(500, {"error": "Could not execute bulk action"})
            return
        if path != "/api/access-request":
            self._send_json(404, {"error": "Not found"})
            return

        ip = _client_ip(self)
        user_agent = self.headers.get("User-Agent") or ""

        data, err = _read_json(self)
        if err:
            self._send_json(400, {"error": err})
            return

        email_addr = (data.get("email") or "").strip()
        if not email_addr or not EMAIL_RE.match(email_addr):
            self._send_json(400, {"error": "Invalid email"})
            return

        services = data.get("services") or []
        if not isinstance(services, list):
            services = []
        services = [str(item)[:64] for item in services][:20]

        language = (data.get("language") or "").strip()[:8]
        known_as = (data.get("known_as") or "").strip()[:256]
        usage = (data.get("usage") or "").strip()[:4000]
        requests = (data.get("requests") or "").strip()[:4000]
        request_scope = (data.get("request_scope") or "individual").strip()[:32]
        if request_scope not in {"individual", "team", "custom"}:
            request_scope = "individual"
        team_name = (data.get("team_name") or "").strip()[:256]
        team_size = (data.get("team_size") or "").strip()[:64]

        now = _now()
        window_start = now - 3600
        current = _limiter.count_since(ip, window_start)
        _limiter.add(ip, now)

        if current >= 30:
            self._send_json(429, {"error": "Too many requests", "pow_required": False})
            return

        if current >= 5:
            secret = (os.environ.get("MICOU_FORMS_SECRET") or "").encode("utf-8")
            if not secret:
                self._send_json(429, {"error": "Too many requests", "pow_required": False})
                return
            pow_obj = data.get("pow")
            if not isinstance(pow_obj, dict) or not _verify_pow(secret, pow_obj):
                self._send_json(429, {"error": "Too many requests", "pow_required": True})
                return

        to_addr = os.environ.get("MICOU_FORMS_TO", "micou@micou.org")
        subject = f"[micou.org] Access request ({email_addr})"
        body = (
            "\n"
            "New access request\n"
            "==================\n"
            f"Time: {time.strftime('%Y-%m-%d %H:%M:%S %Z', time.localtime(now))}\n"
            f"IP: {ip}\n"
            f"User-Agent: {user_agent}\n"
            f"Language: {language}\n"
            f"Request scope: {request_scope}\n"
            "\n"
            f"Email: {email_addr}\n"
            f"Services: {', '.join(services) if services else '—'}\n"
            f"Known as: {known_as or '—'}\n"
            f"Team name: {team_name or '—'}\n"
            f"Team size: {team_size or '—'}\n"
            "\n"
            "Usage\n"
            "-----\n"
            f"{usage or '—'}\n"
            "\n"
            "Requests\n"
            "--------\n"
            f"{requests or '—'}\n"
            "\n"
        )

        try:
            _send_mail(to_addr=to_addr, reply_to=email_addr, subject=subject, body=body)
        except Exception:
            self._send_json(500, {"error": "Failed to send email"})
            return

        self._send_json(200, {"ok": True})


def main():
    host = os.environ.get("MICOU_FORMS_HOST", "127.0.0.1")
    try:
        port = int(os.environ.get("MICOU_FORMS_PORT", "9100"))
    except Exception:
        port = 9100
    httpd = ThreadingHTTPServer((host, port), Handler)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
