import hashlib
import json
from pathlib import Path

import psycopg2
from psycopg2.extras import Json


ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = ROOT / "db" / "micou_control_plane.sql"
BUILTIN_PRINCIPALS = {"visitors", "all_users", "admins"}


def _schema_sql() -> str:
    return SCHEMA_PATH.read_text(encoding="utf-8")


def _sorted_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _payload_hash(value) -> str:
    return hashlib.sha256(_sorted_json(value).encode("utf-8")).hexdigest()


def _identity_kind(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return "unknown"
    if "@" in text:
        return "email"
    if all(ch.isalnum() or ch in {"-", "_", "."} for ch in text):
        return "username"
    return "unknown"


def _principal_kind(principal: str) -> str:
    text = str(principal or "").strip()
    if not text:
        return "unknown"
    if text in BUILTIN_PRINCIPALS:
        return "builtin"
    if text.startswith("svc-") or text.startswith("svc_") or text in {"visitors", "all_users", "admins"}:
        return "group"
    if _identity_kind(text) == "username":
        return "user"
    return "group"


def _as_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _as_dict(value) -> dict:
    return value if isinstance(value, dict) else {}


def _clear_projection_tables(cur):
    cur.execute(
        """
        TRUNCATE TABLE
          micou.sync_issues,
          micou.viewer_service_access,
          micou.service_observed_principals,
          micou.service_expected_principals,
          micou.yunohost_permission_principals,
          micou.yunohost_permissions,
          micou.yunohost_group_members,
          micou.yunohost_groups,
          micou.yunohost_users,
          micou.yunohost_apps,
          micou.discovered_custom_services,
          micou.site_settings,
          micou.site_pages,
          micou.grant_user_service_access,
          micou.grant_user_groups,
          micou.grant_users,
          micou.grant_group_members,
          micou.grant_groups,
          micou.grant_admins,
          micou.service_operations,
          micou.service_links,
          micou.service_deployment,
          micou.service_access_rules,
          micou.service_auth,
          micou.service_i18n,
          micou.services,
          micou.service_categories
        """
    )


def _write_source_documents(cur, raw_documents: dict):
    for document_key, payload in sorted(_as_dict(raw_documents).items()):
        cur.execute(
            """
            INSERT INTO micou.source_documents (document_key, payload, payload_sha256, synced_at)
            VALUES (%s, %s, %s, now())
            ON CONFLICT (document_key) DO UPDATE
            SET payload = EXCLUDED.payload,
                payload_sha256 = EXCLUDED.payload_sha256,
                synced_at = EXCLUDED.synced_at
            """,
            (document_key, Json(payload), _payload_hash(payload)),
        )


def _write_categories(cur, categories):
    category_map = categories if isinstance(categories, dict) else {item.get("id"): item for item in categories or [] if isinstance(item, dict)}
    for category_slug, category in sorted(category_map.items()):
        item = _as_dict(category)
        cur.execute(
            """
            INSERT INTO micou.service_categories (category_slug, order_rank, name_i18n, raw_category)
            VALUES (%s, %s, %s, %s)
            """,
            (
                str(category_slug),
                int(item.get("order", 9999) or 9999),
                Json(_as_dict(item.get("name"))),
                Json(item),
            ),
        )


def _write_services(cur, services: list[dict]):
    for service in services:
        item = _as_dict(service)
        service_key = str(item.get("id") or "").strip()
        if not service_key:
            continue
        auth = _as_dict(item.get("auth"))
        deployment = _as_dict(item.get("deployment"))
        links = _as_dict(item.get("links"))
        operations = _as_dict(item.get("operations"))
        cur.execute(
            """
            INSERT INTO micou.services (
              service_key, source, yunohost_app_id, installed, service_kind, category_slug,
              deployment_mode, access_mode, cta_mode, default_url, docs_url, icon_path,
              illustration_path, repo_url, upstream_url, package_repo_url, show_on_homepage,
              show_on_dashboard, order_rank, tags, raw_service
            ) VALUES (
              %s, %s, %s, %s, %s, %s,
              %s, %s, %s, %s, %s, %s,
              %s, %s, %s, %s, %s,
              %s, %s, %s, %s
            )
            """,
            (
                service_key,
                str(item.get("source") or ""),
                str(item.get("yunohost_app_id") or ""),
                bool(item.get("installed", False)),
                str(item.get("service_kind") or ""),
                str(item.get("category") or "other"),
                str(item.get("deployment_mode") or ""),
                str(item.get("access_mode") or ""),
                str(item.get("cta_mode") or ""),
                str(item.get("default_url") or ""),
                str(item.get("docs_url") or ""),
                str(item.get("icon_path") or ""),
                str(item.get("illustration_path") or ""),
                str(item.get("repo_url") or ""),
                str(item.get("upstream_url") or ""),
                str(item.get("package_repo_url") or ""),
                bool(item.get("show_on_homepage", False)),
                bool(item.get("show_on_dashboard", False)),
                int(item.get("order", 9999) or 9999),
                _as_list(item.get("tags")),
                Json(item),
            ),
        )

        names = _as_dict(item.get("name"))
        descriptions = _as_dict(item.get("description"))
        labels = _as_dict(item.get("button_label"))
        for lang in ("fr", "en", "de", "es"):
            cur.execute(
                """
                INSERT INTO micou.service_i18n (service_key, lang, display_name, description, button_label)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    service_key,
                    lang,
                    str(names.get(lang) or ""),
                    str(descriptions.get(lang) or ""),
                    str(labels.get(lang) or ""),
                ),
            )

        cur.execute(
            """
            INSERT INTO micou.service_auth (service_key, mode, provider, managed_by, request_policy, notes, allowed_groups)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                service_key,
                str(auth.get("mode") or ""),
                str(auth.get("provider") or ""),
                str(auth.get("managed_by") or ""),
                str(auth.get("request_policy") or ""),
                str(auth.get("notes") or ""),
                Json(_as_list(auth.get("allowed_groups"))),
            ),
        )

        for ruleset_name, rules in (
            ("allowed_groups", _as_list(item.get("allowed_groups"))),
            ("auth.allowed_groups", _as_list(auth.get("allowed_groups"))),
        ):
            for ordinal, rule in enumerate(rules, start=1):
                cur.execute(
                    """
                    INSERT INTO micou.service_access_rules (service_key, ruleset_name, ordinal, access_rule)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (service_key, ruleset_name, ordinal, rule),
                )

        cur.execute(
            """
            INSERT INTO micou.service_deployment (
              service_key, strategy, source_type, branch_name, deploy_path, compose_file,
              systemd_unit, container_name, internal_url, healthcheck_url, repo_url,
              package_repo_url, upstream_url, notes
            ) VALUES (
              %s, %s, %s, %s, %s, %s,
              %s, %s, %s, %s, %s,
              %s, %s, %s
            )
            """,
            (
                service_key,
                str(deployment.get("strategy") or ""),
                str(deployment.get("source_type") or ""),
                str(deployment.get("branch") or ""),
                str(deployment.get("deploy_path") or ""),
                str(deployment.get("compose_file") or ""),
                str(deployment.get("systemd_unit") or ""),
                str(deployment.get("container_name") or ""),
                str(deployment.get("internal_url") or ""),
                str(deployment.get("healthcheck_url") or ""),
                str(deployment.get("repo_url") or ""),
                str(deployment.get("package_repo_url") or ""),
                str(deployment.get("upstream_url") or ""),
                str(deployment.get("notes") or ""),
            ),
        )

        cur.execute(
            """
            INSERT INTO micou.service_links (service_key, public_url, docs_url, admin_url, dashboard_url, health_url)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                service_key,
                str(links.get("public_url") or ""),
                str(links.get("docs_url") or ""),
                str(links.get("admin_url") or ""),
                str(links.get("dashboard_url") or ""),
                str(links.get("health_url") or ""),
            ),
        )

        cur.execute(
            """
            INSERT INTO micou.service_operations (service_key, deploy_command, update_command, restart_command, logs_command, backup_command)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                service_key,
                str(operations.get("deploy") or ""),
                str(operations.get("update") or ""),
                str(operations.get("restart") or ""),
                str(operations.get("logs") or ""),
                str(operations.get("backup") or ""),
            ),
        )


def _write_grants(cur, grants: dict):
    for admin_key in sorted(_as_list(grants.get("admins"))):
        resolved_username = str(_as_dict(grants.get("resolved_admins")).get(admin_key) or "")
        cur.execute(
            "INSERT INTO micou.grant_admins (admin_key, identity_kind, resolved_username) VALUES (%s, %s, %s)",
            (admin_key, _identity_kind(admin_key), resolved_username),
        )

    groups = _as_dict(grants.get("groups"))
    resolved_members = _as_dict(grants.get("resolved_group_members"))
    for group_name in sorted(groups.keys()):
        cur.execute("INSERT INTO micou.grant_groups (group_name) VALUES (%s)", (group_name,))
        for member_key in _as_list(groups.get(group_name)):
            cur.execute(
                """
                INSERT INTO micou.grant_group_members (group_name, member_key, identity_kind, resolved_username)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    group_name,
                    member_key,
                    _identity_kind(member_key),
                    str(_as_dict(resolved_members.get(group_name)).get(member_key) or ""),
                ),
            )

    users = _as_dict(grants.get("users"))
    resolved_users = _as_dict(grants.get("resolved_users"))
    for user_key in sorted(users.keys()):
        user_data = _as_dict(users.get(user_key))
        cur.execute(
            "INSERT INTO micou.grant_users (user_key, identity_kind, resolved_username) VALUES (%s, %s, %s)",
            (user_key, _identity_kind(user_key), str(resolved_users.get(user_key) or "")),
        )
        for group_name in _as_list(user_data.get("groups")):
            cur.execute(
                "INSERT INTO micou.grant_user_groups (user_key, group_name) VALUES (%s, %s)",
                (user_key, group_name),
            )
        for service_key in _as_list(user_data.get("apps")):
            cur.execute(
                "INSERT INTO micou.grant_user_service_access (user_key, service_key) VALUES (%s, %s)",
                (user_key, service_key),
            )


def _write_site_content(cur, content: dict):
    pages = content.get("pages") if isinstance(content, dict) else []
    for raw_page in pages or []:
        page = _as_dict(raw_page)
        page_id = str(page.get("id") or "").strip()
        if not page_id:
            continue
        cur.execute(
            """
            INSERT INTO micou.site_pages (
              page_id, title, path, editor_mode, source_type, source_app_key,
              repo_url, visibility, notes, deploy_target, deploy_command,
              publish_notes, raw_page
            ) VALUES (
              %s, %s, %s, %s, %s, %s,
              %s, %s, %s, %s, %s,
              %s, %s
            )
            """,
            (
                page_id,
                str(page.get("title") or ""),
                str(page.get("path") or ""),
                str(page.get("editor") or page.get("editor_mode") or ""),
                str(page.get("source_type") or ""),
                str(page.get("source_app") or ""),
                str(page.get("repo_url") or ""),
                str(page.get("visibility") or ""),
                str(page.get("notes") or ""),
                str(page.get("deploy_target") or ""),
                str(page.get("deploy_command") or ""),
                str(page.get("publish_notes") or ""),
                Json(page),
            ),
        )

    for setting_key in ("homepage", "blog", "admin"):
        payload = _as_dict(content.get(setting_key))
        cur.execute(
            "INSERT INTO micou.site_settings (setting_key, payload) VALUES (%s, %s)",
            (setting_key, Json(payload)),
        )


def _write_discovered_services(cur, discovered_services: list[dict]):
    for raw_service in discovered_services or []:
        item = _as_dict(raw_service)
        service_key = str(item.get("id") or "").strip()
        if not service_key:
            continue
        cur.execute(
            """
            INSERT INTO micou.discovered_custom_services (
              service_key, discovery_source, route_path, public_url, internal_url,
              deploy_path, systemd_unit, proxy_target, configured, category_hint,
              service_kind_hint, description, raw_service
            ) VALUES (
              %s, %s, %s, %s, %s,
              %s, %s, %s, %s, %s,
              %s, %s, %s
            )
            """,
            (
                service_key,
                str(item.get("discovery_source") or ""),
                str(item.get("route_path") or ""),
                str(item.get("public_url") or ""),
                str(item.get("internal_url") or ""),
                str(item.get("deploy_path") or ""),
                str(item.get("systemd_unit") or ""),
                str(item.get("proxy_target") or item.get("proxy_pass") or ""),
                bool(item.get("configured", False)),
                str(item.get("category") or ""),
                str(item.get("service_kind") or ""),
                str(item.get("description") or ""),
                Json(item),
            ),
        )


def _write_yunohost_snapshot(cur, yunohost: dict):
    apps_map = _as_dict(yunohost.get("apps"))
    for yunohost_app_id, raw_app in sorted(apps_map.items()):
        app = _as_dict(raw_app)
        cur.execute(
            """
            INSERT INTO micou.yunohost_apps (yunohost_app_id, display_name, description, version_text, domain_path, raw_app)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                yunohost_app_id,
                str(app.get("name") or ""),
                str(app.get("description") or ""),
                str(app.get("version") or ""),
                str(app.get("domain_path") or ""),
                Json(app),
            ),
        )

    users_map = _as_dict(yunohost.get("users"))
    for username, raw_user in sorted(users_map.items()):
        user = _as_dict(raw_user)
        cur.execute(
            """
            INSERT INTO micou.yunohost_users (username, primary_email, full_name, mailbox_quota, raw_user)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                username,
                str(user.get("mail") or user.get("email") or "") or None,
                str(user.get("fullname") or ""),
                str(user.get("mailbox-quota") or user.get("mailbox_quota") or ""),
                Json(user),
            ),
        )

    groups_map = _as_dict(yunohost.get("groups"))
    for group_name, members in sorted(groups_map.items()):
        cur.execute("INSERT INTO micou.yunohost_groups (group_name) VALUES (%s)", (group_name,))
        for username in sorted(set(_as_list(members))):
            cur.execute(
                "INSERT INTO micou.yunohost_group_members (group_name, username) VALUES (%s, %s)",
                (group_name, username),
            )

    permissions_map = _as_dict(yunohost.get("permissions"))
    for permission_name, raw_permission in sorted(permissions_map.items()):
        permission = _as_dict(raw_permission)
        cur.execute(
            """
            INSERT INTO micou.yunohost_permissions (permission_name, permission_label, url, auth_header, show_tile, protected, raw_permission)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                permission_name,
                str(permission.get("label") or ""),
                str(permission.get("url") or ""),
                permission.get("auth_header"),
                permission.get("show_tile"),
                permission.get("protected"),
                Json(permission),
            ),
        )
        for principal in sorted(set(_as_list(permission.get("allowed")))):
            cur.execute(
                """
                INSERT INTO micou.yunohost_permission_principals (permission_name, principal, principal_kind)
                VALUES (%s, %s, %s)
                """,
                (permission_name, principal, _principal_kind(principal)),
            )


def _write_expected_and_observed(cur, snapshot: dict):
    expected_access = _as_dict(snapshot.get("expected_access"))
    app_permissions = _as_dict(expected_access.get("app_permissions"))
    yunohost_permissions = _as_dict(_as_dict(snapshot.get("yunohost")).get("permissions"))

    for service_key, raw_expected in sorted(app_permissions.items()):
        item = _as_dict(raw_expected)
        permission_name = str(item.get("permission_name") or "")
        for principal in sorted(set(_as_list(item.get("principals")))):
            cur.execute(
                """
                INSERT INTO micou.service_expected_principals (service_key, permission_name, principal, principal_kind)
                VALUES (%s, %s, %s, %s)
                """,
                (service_key, permission_name, principal, _principal_kind(principal)),
            )

        observed = _as_dict(yunohost_permissions.get(permission_name))
        for principal in sorted(set(_as_list(observed.get("allowed")))):
            cur.execute(
                """
                INSERT INTO micou.service_observed_principals (service_key, permission_name, principal, principal_kind)
                VALUES (%s, %s, %s, %s)
                """,
                (service_key, permission_name, principal, _principal_kind(principal)),
            )

    for row in snapshot.get("viewer_access") or []:
        item = _as_dict(row)
        cur.execute(
            """
            INSERT INTO micou.viewer_service_access (
              viewer_key, identity_kind, resolved_username, service_key, roles, groups,
              app_grants, allowed_for_viewer, requires_request, match_reasons
            ) VALUES (
              %s, %s, %s, %s, %s, %s,
              %s, %s, %s, %s
            )
            """,
            (
                str(item.get("viewer_key") or ""),
                str(item.get("identity_kind") or "unknown"),
                str(item.get("resolved_username") or ""),
                str(item.get("service_key") or ""),
                _as_list(item.get("roles")),
                _as_list(item.get("groups")),
                _as_list(item.get("app_grants")),
                bool(item.get("allowed_for_viewer", False)),
                bool(item.get("requires_request", False)),
                _as_list(item.get("match_reasons")),
            ),
        )


def _derive_sync_issues(snapshot: dict) -> list[dict]:
    issues = []
    services = {str(item.get("id")): _as_dict(item) for item in snapshot.get("services") or [] if str(_as_dict(item).get("id") or "").strip()}
    service_keys = set(services.keys())
    grants = _as_dict(snapshot.get("grants"))
    resolved_users = _as_dict(grants.get("resolved_users"))
    resolved_admins = _as_dict(grants.get("resolved_admins"))
    resolved_group_members = _as_dict(grants.get("resolved_group_members"))
    groups = _as_dict(grants.get("groups"))
    users = _as_dict(grants.get("users"))
    yunohost = _as_dict(snapshot.get("yunohost"))
    live_apps = set(_as_dict(yunohost.get("apps")).keys())
    live_groups = {name: sorted(set(_as_list(members))) for name, members in _as_dict(yunohost.get("groups")).items()}
    expected_access = _as_dict(snapshot.get("expected_access"))
    expected_groups = {name: sorted(set(_as_list(members))) for name, members in _as_dict(expected_access.get("managed_groups")).items()}
    expected_permissions = _as_dict(expected_access.get("app_permissions"))
    live_permissions = _as_dict(yunohost.get("permissions"))

    for admin_key in _as_list(grants.get("admins")):
        if not str(resolved_admins.get(admin_key) or ""):
            issues.append(
                {
                    "severity": "error",
                    "issue_code": "grant_admin_unresolved",
                    "related_user_key": admin_key,
                    "detail": f"Admin principal {admin_key!r} does not resolve to a live YunoHost user.",
                    "expected_state": {"admin_key": admin_key},
                    "actual_state": {"resolved_username": ""},
                }
            )

    for user_key, user_data in sorted(users.items()):
        if not str(resolved_users.get(user_key) or ""):
            issues.append(
                {
                    "severity": "error",
                    "issue_code": "grant_user_unresolved",
                    "related_user_key": user_key,
                    "detail": f"Grant user {user_key!r} does not resolve to a live YunoHost user.",
                    "expected_state": {"user_key": user_key},
                    "actual_state": {"resolved_username": ""},
                }
            )
        for service_key in _as_list(_as_dict(user_data).get("apps")):
            if service_key not in service_keys:
                issues.append(
                    {
                        "severity": "error",
                        "issue_code": "grant_user_service_missing",
                        "related_user_key": user_key,
                        "service_key": service_key,
                        "detail": f"Grant user {user_key!r} references unknown service {service_key!r}.",
                        "expected_state": {"service_key": service_key},
                        "actual_state": {"service_exists": False},
                    }
                )
        for group_name in _as_list(_as_dict(user_data).get("groups")):
            if group_name not in groups:
                issues.append(
                    {
                        "severity": "error",
                        "issue_code": "grant_user_group_missing",
                        "related_user_key": user_key,
                        "related_group_name": group_name,
                        "detail": f"Grant user {user_key!r} references unknown group {group_name!r}.",
                        "expected_state": {"group_name": group_name},
                        "actual_state": {"group_exists": False},
                    }
                )

    for group_name, members in sorted(groups.items()):
        member_map = _as_dict(resolved_group_members.get(group_name))
        for member_key in _as_list(members):
            if not str(member_map.get(member_key) or ""):
                issues.append(
                    {
                        "severity": "error",
                        "issue_code": "grant_group_member_unresolved",
                        "related_group_name": group_name,
                        "related_user_key": member_key,
                        "detail": f"Group member {member_key!r} in {group_name!r} does not resolve to a live YunoHost user.",
                        "expected_state": {"group_name": group_name, "member_key": member_key},
                        "actual_state": {"resolved_username": ""},
                    }
                )

    for service_key, service in sorted(services.items()):
        top_level_groups = sorted(set(_as_list(service.get("allowed_groups"))))
        auth_groups = sorted(set(_as_list(_as_dict(service.get("auth")).get("allowed_groups"))))
        if top_level_groups != auth_groups:
            issues.append(
                {
                    "severity": "warning",
                    "issue_code": "service_allowed_groups_mismatch",
                    "service_key": service_key,
                    "detail": f"Service {service_key!r} has different top-level and auth.allowed_groups values.",
                    "expected_state": {"allowed_groups": top_level_groups},
                    "actual_state": {"auth_allowed_groups": auth_groups},
                }
            )

        if service.get("source") == "yunohost":
            yh_id = str(service.get("yunohost_app_id") or service_key)
            if yh_id not in live_apps:
                issues.append(
                    {
                        "severity": "error",
                        "issue_code": "catalog_yunohost_app_missing",
                        "service_key": service_key,
                        "detail": f"Service {service_key!r} expects YunoHost app {yh_id!r}, but it is not installed.",
                        "expected_state": {"yunohost_app_id": yh_id},
                        "actual_state": {"installed": False},
                    }
                )

    configured_yh_ids = {
        str(_as_dict(service).get("yunohost_app_id") or _as_dict(service).get("id") or "")
        for service in snapshot.get("services") or []
        if _as_dict(service).get("source") == "yunohost"
    }
    for yunohost_app_id in sorted(live_apps - configured_yh_ids):
        issues.append(
            {
                "severity": "warning",
                "issue_code": "yunohost_app_missing_from_catalog",
                "detail": f"Installed YunoHost app {yunohost_app_id!r} is missing from the control-plane catalog.",
                "expected_state": {"catalog_entry": True},
                "actual_state": {"catalog_entry": False, "yunohost_app_id": yunohost_app_id},
            }
        )

    discovered = {str(_as_dict(item).get("id") or ""): _as_dict(item) for item in snapshot.get("discovered_services") or [] if str(_as_dict(item).get("id") or "").strip()}
    for service_key, discovered_service in sorted(discovered.items()):
        if not bool(discovered_service.get("configured", False)) and service_key not in service_keys:
            issues.append(
                {
                    "severity": "warning",
                    "issue_code": "discovered_custom_service_missing_catalog_entry",
                    "service_key": service_key,
                    "detail": f"Discovered custom service {service_key!r} is routed locally but missing from the catalog.",
                    "expected_state": {"catalog_entry": True},
                    "actual_state": {"catalog_entry": False},
                }
            )

    for group_name, target_members in sorted(expected_groups.items()):
        current_members = sorted(set(_as_list(live_groups.get(group_name))))
        if target_members != current_members:
            issues.append(
                {
                    "severity": "error",
                    "issue_code": "yunohost_group_membership_mismatch",
                    "related_group_name": group_name,
                    "detail": f"Managed YunoHost group {group_name!r} does not match the grant-derived membership.",
                    "expected_state": {"members": target_members},
                    "actual_state": {"members": current_members},
                }
            )

    for service_key, raw_expected in sorted(expected_permissions.items()):
        expected = _as_dict(raw_expected)
        permission_name = str(expected.get("permission_name") or "")
        target_principals = sorted(set(_as_list(expected.get("principals"))))
        current_principals = sorted(set(_as_list(_as_dict(live_permissions.get(permission_name)).get("allowed"))))
        if target_principals != current_principals:
            issues.append(
                {
                    "severity": "error",
                    "issue_code": "yunohost_permission_mismatch",
                    "service_key": service_key,
                    "detail": f"Permission principals for {service_key!r} do not match the control-plane model.",
                    "expected_state": {"permission_name": permission_name, "principals": target_principals},
                    "actual_state": {"permission_name": permission_name, "principals": current_principals},
                }
            )

    known_page_sources = service_keys | {"webstudio", "content", "homepage"}
    content = _as_dict(snapshot.get("content"))
    for raw_page in content.get("pages") or []:
        page = _as_dict(raw_page)
        page_id = str(page.get("id") or "").strip()
        source_app = str(page.get("source_app") or "").strip()
        source_type = str(page.get("source_type") or "").strip()
        if source_app and source_type not in {"content", "external"} and source_app not in known_page_sources:
            issues.append(
                {
                    "severity": "warning",
                    "issue_code": "page_source_app_missing",
                    "related_page_id": page_id,
                    "detail": f"Page {page_id!r} points to source app {source_app!r}, but no matching service exists.",
                    "expected_state": {"source_app": source_app},
                    "actual_state": {"service_exists": False},
                }
            )

    return issues


def _write_sync_issues(cur, issues: list[dict]):
    for issue in issues:
        item = _as_dict(issue)
        cur.execute(
            """
            INSERT INTO micou.sync_issues (
              severity, issue_code, service_key, related_user_key, related_group_name,
              related_page_id, detail, expected_state, actual_state, observed_at
            ) VALUES (
              %s, %s, %s, %s, %s,
              %s, %s, %s, %s, now()
            )
            """,
            (
                str(item.get("severity") or "warning"),
                str(item.get("issue_code") or "unknown_issue"),
                str(item.get("service_key") or ""),
                str(item.get("related_user_key") or ""),
                str(item.get("related_group_name") or ""),
                str(item.get("related_page_id") or ""),
                str(item.get("detail") or ""),
                Json(_as_dict(item.get("expected_state"))),
                Json(_as_dict(item.get("actual_state"))),
            ),
        )


def sync_snapshot_to_postgres(dsn: str, snapshot: dict, trigger_name: str = "manual", actor_key: str = "") -> dict:
    if not str(dsn or "").strip():
        raise ValueError("A PostgreSQL DSN is required")

    conn = psycopg2.connect(dsn)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(_schema_sql())
                cur.execute(
                    """
                    INSERT INTO micou.sync_runs (trigger_name, actor_key, status, started_at)
                    VALUES (%s, %s, 'running', now())
                    RETURNING sync_run_id
                    """,
                    (trigger_name, actor_key),
                )
                sync_run_id = int(cur.fetchone()[0])

                _write_source_documents(cur, _as_dict(snapshot.get("raw_documents")))
                _clear_projection_tables(cur)
                _write_categories(cur, snapshot.get("categories"))
                _write_services(cur, snapshot.get("services") or [])
                _write_grants(cur, _as_dict(snapshot.get("grants")))
                _write_site_content(cur, _as_dict(snapshot.get("content")))
                _write_discovered_services(cur, snapshot.get("discovered_services") or [])
                _write_yunohost_snapshot(cur, _as_dict(snapshot.get("yunohost")))
                _write_expected_and_observed(cur, snapshot)
                issues = _derive_sync_issues(snapshot)
                _write_sync_issues(cur, issues)

                summary = {
                    "sync_run_id": sync_run_id,
                    "services": len(snapshot.get("services") or []),
                    "categories": len(_as_dict(snapshot.get("categories")) or (snapshot.get("categories") or [])),
                    "grant_users": len(_as_dict(_as_dict(snapshot.get("grants")).get("users"))),
                    "grant_groups": len(_as_dict(_as_dict(snapshot.get("grants")).get("groups"))),
                    "pages": len(_as_dict(snapshot.get("content")).get("pages") or []),
                    "discovered_services": len(snapshot.get("discovered_services") or []),
                    "yunohost_apps": len(_as_dict(_as_dict(snapshot.get("yunohost")).get("apps"))),
                    "yunohost_users": len(_as_dict(_as_dict(snapshot.get("yunohost")).get("users"))),
                    "viewer_access_rows": len(snapshot.get("viewer_access") or []),
                    "issue_count": len(issues),
                    "error_count": sum(1 for issue in issues if issue.get("severity") == "error"),
                    "warning_count": sum(1 for issue in issues if issue.get("severity") == "warning"),
                    "info_count": sum(1 for issue in issues if issue.get("severity") == "info"),
                }
                cur.execute(
                    """
                    UPDATE micou.sync_runs
                    SET status = 'ok',
                        completed_at = now(),
                        summary = %s
                    WHERE sync_run_id = %s
                    """,
                    (Json(summary), sync_run_id),
                )

        return {
            "ok": True,
            "status": "ok",
            "trigger": trigger_name,
            "actor_key": actor_key,
            **summary,
        }
    except Exception:
        with conn:
            with conn.cursor() as cur:
                cur.execute(_schema_sql())
                cur.execute(
                    """
                    INSERT INTO micou.sync_runs (trigger_name, actor_key, status, started_at, completed_at, summary)
                    VALUES (%s, %s, 'error', now(), now(), %s)
                    """,
                    (trigger_name, actor_key, Json({"error": "sync_failed"})),
                )
        raise
    finally:
        conn.close()
