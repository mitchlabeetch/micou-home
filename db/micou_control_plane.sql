CREATE SCHEMA IF NOT EXISTS micou;

CREATE TABLE IF NOT EXISTS micou.sync_runs (
  sync_run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  trigger_name TEXT NOT NULL,
  actor_key TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'ok', 'error')),
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ,
  summary JSONB NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(summary) = 'object')
);

CREATE TABLE IF NOT EXISTS micou.source_documents (
  document_key TEXT PRIMARY KEY,
  payload JSONB NOT NULL CHECK (jsonb_typeof(payload) = 'object'),
  payload_sha256 TEXT NOT NULL,
  synced_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS micou.service_categories (
  category_slug TEXT PRIMARY KEY,
  order_rank BIGINT NOT NULL DEFAULT 9999,
  name_i18n JSONB NOT NULL CHECK (jsonb_typeof(name_i18n) = 'object'),
  raw_category JSONB NOT NULL CHECK (jsonb_typeof(raw_category) = 'object')
);

CREATE TABLE IF NOT EXISTS micou.services (
  service_key TEXT PRIMARY KEY,
  source TEXT NOT NULL,
  yunohost_app_id TEXT NOT NULL DEFAULT '',
  installed BOOLEAN NOT NULL DEFAULT FALSE,
  service_kind TEXT NOT NULL,
  category_slug TEXT NOT NULL REFERENCES micou.service_categories(category_slug) ON DELETE RESTRICT,
  deployment_mode TEXT NOT NULL,
  access_mode TEXT NOT NULL,
  cta_mode TEXT NOT NULL,
  default_url TEXT NOT NULL DEFAULT '',
  docs_url TEXT NOT NULL DEFAULT '',
  icon_path TEXT NOT NULL DEFAULT '',
  illustration_path TEXT NOT NULL DEFAULT '',
  repo_url TEXT NOT NULL DEFAULT '',
  upstream_url TEXT NOT NULL DEFAULT '',
  package_repo_url TEXT NOT NULL DEFAULT '',
  show_on_homepage BOOLEAN NOT NULL DEFAULT FALSE,
  show_on_dashboard BOOLEAN NOT NULL DEFAULT FALSE,
  order_rank BIGINT NOT NULL DEFAULT 9999,
  tags TEXT[] NOT NULL DEFAULT '{}'::text[],
  raw_service JSONB NOT NULL CHECK (jsonb_typeof(raw_service) = 'object')
);

CREATE INDEX IF NOT EXISTS services_category_idx ON micou.services (category_slug);
CREATE INDEX IF NOT EXISTS services_yunohost_app_idx ON micou.services (yunohost_app_id);
CREATE INDEX IF NOT EXISTS services_source_access_idx ON micou.services (source, access_mode);

CREATE TABLE IF NOT EXISTS micou.service_i18n (
  service_key TEXT NOT NULL REFERENCES micou.services(service_key) ON DELETE CASCADE,
  lang TEXT NOT NULL CHECK (lang IN ('fr', 'en', 'de', 'es')),
  display_name TEXT NOT NULL DEFAULT '',
  description TEXT NOT NULL DEFAULT '',
  button_label TEXT NOT NULL DEFAULT '',
  PRIMARY KEY (service_key, lang)
);

CREATE INDEX IF NOT EXISTS service_i18n_lang_idx ON micou.service_i18n (lang);

CREATE TABLE IF NOT EXISTS micou.service_auth (
  service_key TEXT PRIMARY KEY REFERENCES micou.services(service_key) ON DELETE CASCADE,
  mode TEXT NOT NULL,
  provider TEXT NOT NULL,
  managed_by TEXT NOT NULL,
  request_policy TEXT NOT NULL,
  notes TEXT NOT NULL DEFAULT '',
  allowed_groups JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(allowed_groups) = 'array')
);

CREATE TABLE IF NOT EXISTS micou.service_access_rules (
  service_key TEXT NOT NULL REFERENCES micou.services(service_key) ON DELETE CASCADE,
  ruleset_name TEXT NOT NULL,
  ordinal BIGINT NOT NULL,
  access_rule TEXT NOT NULL,
  PRIMARY KEY (service_key, ruleset_name, ordinal)
);

CREATE INDEX IF NOT EXISTS service_access_rules_rule_idx ON micou.service_access_rules (access_rule);

CREATE TABLE IF NOT EXISTS micou.service_deployment (
  service_key TEXT PRIMARY KEY REFERENCES micou.services(service_key) ON DELETE CASCADE,
  strategy TEXT NOT NULL DEFAULT '',
  source_type TEXT NOT NULL DEFAULT '',
  branch_name TEXT NOT NULL DEFAULT '',
  deploy_path TEXT NOT NULL DEFAULT '',
  compose_file TEXT NOT NULL DEFAULT '',
  systemd_unit TEXT NOT NULL DEFAULT '',
  container_name TEXT NOT NULL DEFAULT '',
  internal_url TEXT NOT NULL DEFAULT '',
  healthcheck_url TEXT NOT NULL DEFAULT '',
  repo_url TEXT NOT NULL DEFAULT '',
  package_repo_url TEXT NOT NULL DEFAULT '',
  upstream_url TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS micou.service_links (
  service_key TEXT PRIMARY KEY REFERENCES micou.services(service_key) ON DELETE CASCADE,
  public_url TEXT NOT NULL DEFAULT '',
  docs_url TEXT NOT NULL DEFAULT '',
  admin_url TEXT NOT NULL DEFAULT '',
  dashboard_url TEXT NOT NULL DEFAULT '',
  health_url TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS micou.service_operations (
  service_key TEXT PRIMARY KEY REFERENCES micou.services(service_key) ON DELETE CASCADE,
  deploy_command TEXT NOT NULL DEFAULT '',
  update_command TEXT NOT NULL DEFAULT '',
  restart_command TEXT NOT NULL DEFAULT '',
  logs_command TEXT NOT NULL DEFAULT '',
  backup_command TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS micou.grant_admins (
  admin_key TEXT PRIMARY KEY,
  identity_kind TEXT NOT NULL,
  resolved_username TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS micou.grant_groups (
  group_name TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS micou.grant_group_members (
  group_name TEXT NOT NULL REFERENCES micou.grant_groups(group_name) ON DELETE CASCADE,
  member_key TEXT NOT NULL,
  identity_kind TEXT NOT NULL,
  resolved_username TEXT NOT NULL DEFAULT '',
  PRIMARY KEY (group_name, member_key)
);

CREATE INDEX IF NOT EXISTS grant_group_members_member_idx ON micou.grant_group_members (member_key);

CREATE TABLE IF NOT EXISTS micou.grant_users (
  user_key TEXT PRIMARY KEY,
  identity_kind TEXT NOT NULL,
  resolved_username TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS micou.grant_user_groups (
  user_key TEXT NOT NULL REFERENCES micou.grant_users(user_key) ON DELETE CASCADE,
  group_name TEXT NOT NULL REFERENCES micou.grant_groups(group_name) ON DELETE CASCADE,
  PRIMARY KEY (user_key, group_name)
);

CREATE TABLE IF NOT EXISTS micou.grant_user_service_access (
  user_key TEXT NOT NULL REFERENCES micou.grant_users(user_key) ON DELETE CASCADE,
  service_key TEXT NOT NULL REFERENCES micou.services(service_key) ON DELETE CASCADE,
  PRIMARY KEY (user_key, service_key)
);

CREATE INDEX IF NOT EXISTS grant_user_service_access_service_idx ON micou.grant_user_service_access (service_key);

CREATE TABLE IF NOT EXISTS micou.site_pages (
  page_id TEXT PRIMARY KEY,
  title TEXT NOT NULL DEFAULT '',
  path TEXT NOT NULL DEFAULT '',
  editor_mode TEXT NOT NULL DEFAULT '',
  source_type TEXT NOT NULL DEFAULT '',
  source_app_key TEXT NOT NULL DEFAULT '',
  repo_url TEXT NOT NULL DEFAULT '',
  visibility TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  deploy_target TEXT NOT NULL DEFAULT '',
  deploy_command TEXT NOT NULL DEFAULT '',
  publish_notes TEXT NOT NULL DEFAULT '',
  raw_page JSONB NOT NULL CHECK (jsonb_typeof(raw_page) = 'object')
);

CREATE INDEX IF NOT EXISTS site_pages_source_app_idx ON micou.site_pages (source_app_key);

CREATE TABLE IF NOT EXISTS micou.site_settings (
  setting_key TEXT PRIMARY KEY,
  payload JSONB NOT NULL CHECK (jsonb_typeof(payload) = 'object')
);

CREATE TABLE IF NOT EXISTS micou.discovered_custom_services (
  service_key TEXT PRIMARY KEY,
  discovery_source TEXT NOT NULL DEFAULT '',
  route_path TEXT NOT NULL DEFAULT '',
  public_url TEXT NOT NULL DEFAULT '',
  internal_url TEXT NOT NULL DEFAULT '',
  deploy_path TEXT NOT NULL DEFAULT '',
  systemd_unit TEXT NOT NULL DEFAULT '',
  proxy_target TEXT NOT NULL DEFAULT '',
  configured BOOLEAN NOT NULL DEFAULT FALSE,
  category_hint TEXT NOT NULL DEFAULT '',
  service_kind_hint TEXT NOT NULL DEFAULT '',
  description TEXT NOT NULL DEFAULT '',
  raw_service JSONB NOT NULL CHECK (jsonb_typeof(raw_service) = 'object')
);

CREATE TABLE IF NOT EXISTS micou.yunohost_apps (
  yunohost_app_id TEXT PRIMARY KEY,
  display_name TEXT NOT NULL DEFAULT '',
  description TEXT NOT NULL DEFAULT '',
  version_text TEXT NOT NULL DEFAULT '',
  domain_path TEXT NOT NULL DEFAULT '',
  raw_app JSONB NOT NULL CHECK (jsonb_typeof(raw_app) = 'object')
);

CREATE TABLE IF NOT EXISTS micou.yunohost_users (
  username TEXT PRIMARY KEY,
  primary_email TEXT,
  full_name TEXT NOT NULL DEFAULT '',
  mailbox_quota TEXT NOT NULL DEFAULT '',
  raw_user JSONB NOT NULL CHECK (jsonb_typeof(raw_user) = 'object')
);

CREATE UNIQUE INDEX IF NOT EXISTS yunohost_users_lower_email_uidx
  ON micou.yunohost_users (LOWER(primary_email)) WHERE primary_email IS NOT NULL;

CREATE TABLE IF NOT EXISTS micou.yunohost_groups (
  group_name TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS micou.yunohost_group_members (
  group_name TEXT NOT NULL REFERENCES micou.yunohost_groups(group_name) ON DELETE CASCADE,
  username TEXT NOT NULL REFERENCES micou.yunohost_users(username) ON DELETE CASCADE,
  PRIMARY KEY (group_name, username)
);

CREATE INDEX IF NOT EXISTS yunohost_group_members_user_idx ON micou.yunohost_group_members (username);

CREATE TABLE IF NOT EXISTS micou.yunohost_permissions (
  permission_name TEXT PRIMARY KEY,
  permission_label TEXT NOT NULL DEFAULT '',
  url TEXT NOT NULL DEFAULT '',
  auth_header BOOLEAN,
  show_tile BOOLEAN,
  protected BOOLEAN,
  raw_permission JSONB NOT NULL CHECK (jsonb_typeof(raw_permission) = 'object')
);

CREATE TABLE IF NOT EXISTS micou.yunohost_permission_principals (
  permission_name TEXT NOT NULL REFERENCES micou.yunohost_permissions(permission_name) ON DELETE CASCADE,
  principal TEXT NOT NULL,
  principal_kind TEXT NOT NULL,
  PRIMARY KEY (permission_name, principal)
);

CREATE INDEX IF NOT EXISTS yunohost_permission_principals_principal_idx
  ON micou.yunohost_permission_principals (principal);

CREATE TABLE IF NOT EXISTS micou.service_expected_principals (
  service_key TEXT NOT NULL REFERENCES micou.services(service_key) ON DELETE CASCADE,
  permission_name TEXT NOT NULL DEFAULT '',
  principal TEXT NOT NULL,
  principal_kind TEXT NOT NULL,
  PRIMARY KEY (service_key, principal)
);

CREATE INDEX IF NOT EXISTS service_expected_principals_permission_idx
  ON micou.service_expected_principals (permission_name);

CREATE TABLE IF NOT EXISTS micou.service_observed_principals (
  service_key TEXT NOT NULL REFERENCES micou.services(service_key) ON DELETE CASCADE,
  permission_name TEXT NOT NULL DEFAULT '',
  principal TEXT NOT NULL,
  principal_kind TEXT NOT NULL,
  PRIMARY KEY (service_key, principal)
);

CREATE INDEX IF NOT EXISTS service_observed_principals_permission_idx
  ON micou.service_observed_principals (permission_name);

CREATE TABLE IF NOT EXISTS micou.viewer_service_access (
  viewer_key TEXT NOT NULL,
  identity_kind TEXT NOT NULL,
  resolved_username TEXT NOT NULL DEFAULT '',
  service_key TEXT NOT NULL REFERENCES micou.services(service_key) ON DELETE CASCADE,
  roles TEXT[] NOT NULL DEFAULT '{}'::text[],
  groups TEXT[] NOT NULL DEFAULT '{}'::text[],
  app_grants TEXT[] NOT NULL DEFAULT '{}'::text[],
  allowed_for_viewer BOOLEAN NOT NULL,
  requires_request BOOLEAN NOT NULL,
  match_reasons TEXT[] NOT NULL DEFAULT '{}'::text[],
  PRIMARY KEY (viewer_key, service_key)
);

CREATE INDEX IF NOT EXISTS viewer_service_access_service_idx ON micou.viewer_service_access (service_key);
CREATE INDEX IF NOT EXISTS viewer_service_access_allowed_idx ON micou.viewer_service_access (allowed_for_viewer, requires_request);

CREATE TABLE IF NOT EXISTS micou.sync_issues (
  issue_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  severity TEXT NOT NULL CHECK (severity IN ('info', 'warning', 'error')),
  issue_code TEXT NOT NULL,
  service_key TEXT NOT NULL DEFAULT '',
  related_user_key TEXT NOT NULL DEFAULT '',
  related_group_name TEXT NOT NULL DEFAULT '',
  related_page_id TEXT NOT NULL DEFAULT '',
  detail TEXT NOT NULL,
  expected_state JSONB NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(expected_state) = 'object'),
  actual_state JSONB NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(actual_state) = 'object'),
  observed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS sync_issues_service_idx ON micou.sync_issues (service_key);
CREATE INDEX IF NOT EXISTS sync_issues_code_idx ON micou.sync_issues (issue_code, severity);

ALTER TABLE micou.sync_issues DROP CONSTRAINT IF EXISTS sync_issues_service_key_fkey;

CREATE OR REPLACE VIEW micou.v_service_sync_status AS
WITH expected AS (
  SELECT
    service_key,
    max(permission_name) AS permission_name,
    array_agg(principal ORDER BY principal) AS expected_principals
  FROM micou.service_expected_principals
  GROUP BY service_key
),
observed AS (
  SELECT
    service_key,
    max(permission_name) AS permission_name,
    array_agg(principal ORDER BY principal) AS observed_principals
  FROM micou.service_observed_principals
  GROUP BY service_key
),
issues AS (
  SELECT
    service_key,
    count(*) FILTER (WHERE severity = 'error') AS error_count,
    count(*) FILTER (WHERE severity = 'warning') AS warning_count,
    count(*) FILTER (WHERE severity = 'info') AS info_count
  FROM micou.sync_issues
  WHERE service_key IS NOT NULL
  GROUP BY service_key
)
SELECT
  s.service_key,
  s.source,
  s.yunohost_app_id,
  s.service_kind,
  s.category_slug,
  s.access_mode,
  s.cta_mode,
  s.show_on_homepage,
  s.show_on_dashboard,
  COALESCE(expected.permission_name, observed.permission_name, '') AS permission_name,
  COALESCE(expected.expected_principals, '{}'::text[]) AS expected_principals,
  COALESCE(observed.observed_principals, '{}'::text[]) AS observed_principals,
  COALESCE(expected.expected_principals, '{}'::text[]) = COALESCE(observed.observed_principals, '{}'::text[]) AS principals_synced,
  COALESCE(issues.error_count, 0) AS error_count,
  COALESCE(issues.warning_count, 0) AS warning_count,
  COALESCE(issues.info_count, 0) AS info_count
FROM micou.services AS s
LEFT JOIN expected ON expected.service_key = s.service_key
LEFT JOIN observed ON observed.service_key = s.service_key
LEFT JOIN issues ON issues.service_key = s.service_key;

CREATE OR REPLACE VIEW micou.v_panel_access_matrix AS
SELECT
  v.viewer_key,
  v.identity_kind,
  v.resolved_username,
  s.service_key,
  s.source,
  s.access_mode,
  s.show_on_dashboard,
  v.roles,
  v.groups,
  v.app_grants,
  v.allowed_for_viewer,
  v.requires_request,
  v.match_reasons
FROM micou.viewer_service_access AS v
JOIN micou.services AS s ON s.service_key = v.service_key
ORDER BY v.viewer_key, s.order_rank, s.service_key;
