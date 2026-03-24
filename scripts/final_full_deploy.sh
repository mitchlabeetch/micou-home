#!/usr/bin/env bash
set -euo pipefail

activate_studio=0
for arg in "$@"; do
  case "${arg}" in
    --activate-studio)
      activate_studio=1
      ;;
    *)
      echo "Unknown argument: ${arg}" >&2
      echo "Usage: sudo bash $0 [--activate-studio]" >&2
      exit 1
      ;;
  esac
done

managed_root="/srv/micou-services"
homepage_root="${managed_root}/micou-homepage"
app_root="${homepage_root}/app"
data_root="${homepage_root}/data"
backend_root="${homepage_root}/backend"
nginx_auth_conf="/etc/nginx/conf.d/micou.org.d/11-micou-dashboard.conf"
widdypad_service="/etc/systemd/system/widdypad.service"
timestamp="$(date +%F-%H%M%S)"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this script as root: sudo bash $0" >&2
  exit 1
fi

backup_file() {
  local path="$1"
  if [[ -e "${path}" ]]; then
    cp -a "${path}" "${path}.bak.${timestamp}"
  fi
}

write_nginx_dashboard_routes() {
  cat > "${nginx_auth_conf}" <<EOF
location = /admin {
    alias ${app_root}/admin.html;
}

location = /admin/ {
    return 302 /admin;
}

location = /admin.html {
    alias ${app_root}/admin.html;
}

location = /home {
    alias ${app_root}/home.html;
}

location = /home/ {
    return 302 /home;
}

location = /home.html {
    alias ${app_root}/home.html;
}

location ^~ /home-api/ {
    rewrite ^/home-api/(.*)$ /\$1 break;
    include proxy_params_with_auth;
    proxy_pass http://127.0.0.1:9100;
}
EOF
}

fix_widdypad_service() {
  backup_file "${widdypad_service}"
  python3 - <<'PY'
from pathlib import Path

path = Path("/etc/systemd/system/widdypad.service")
text = path.read_text(encoding="utf-8")
lines = text.splitlines()
target = "Environment=MP3WIDDY_LIBRARY_DIR=/srv/micou-services/widdypad/data"

filtered = []
in_install = False
for line in lines:
    stripped = line.strip()
    if stripped == "[Install]":
        in_install = True
    elif stripped.startswith("[") and stripped.endswith("]"):
        in_install = False
    if line.startswith("Environment=MP3WIDDY_LIBRARY_DIR="):
        continue
    if in_install and stripped == target:
        continue
    filtered.append(line)

lines = filtered
service_start = None
insert_at = None
for idx, line in enumerate(lines):
    stripped = line.strip()
    if stripped == "[Service]":
        service_start = idx
        insert_at = idx + 1
        continue
    if service_start is not None and stripped.startswith("[") and stripped.endswith("]"):
        break
    if service_start is not None:
        insert_at = idx + 1

if insert_at is None:
    raise SystemExit("Could not find [Service] section in widdypad.service")

lines.insert(insert_at, target)
path.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY
}

echo "==> Backing up live files"
backup_file "${app_root}/index.html"
backup_file "${app_root}/home.html"
backup_file "${app_root}/admin.html"
backup_file "${backend_root}/forms_service.py"
backup_file "${data_root}/catalog.json"
backup_file "${data_root}/grants.json"
backup_file "${data_root}/site_content.json"
backup_file "${nginx_auth_conf}"
backup_file "${widdypad_service}"

echo "==> Syncing source files into the live managed tree"
install -d -m 0755 "${app_root}" "${backend_root}" "${data_root}"
cp /home/micou_org/index.html "${app_root}/index.html"
cp /home/micou_org/home.html "${app_root}/home.html"
cp /home/micou_org/admin.html "${app_root}/admin.html"
cp /home/micou_org/forms_service.py "${backend_root}/forms_service.py"
cp /home/micou_org/catalog.json "${data_root}/catalog.json"
cp /home/micou_org/grants.json "${data_root}/grants.json"
cp /home/micou_org/site_content.json "${data_root}/site_content.json"

echo "==> Ensuring admin pages stay protected by YunoHost auth"
write_nginx_dashboard_routes

echo "==> Fixing widdypad systemd environment placement"
fix_widdypad_service

echo "==> Best-effort edge-service repairs"
if bash /home/micou_org/scripts/repair_wallos_runtime.sh; then
  echo "Wallos runtime looks healthy and was re-enabled for dashboard access while staying hidden from the homepage."
else
  echo "Wallos remains hidden from the homepage and dashboard until its runtime is healthy."
fi

echo "==> Validating application code"
python3 - <<'PY'
import py_compile
py_compile.compile('/srv/micou-services/micou-homepage/backend/forms_service.py', cfile='/tmp/micou_forms_service.pyc', doraise=True)
py_compile.compile('/home/micou_org/scripts/scaffold_yunohost_appgen.py', cfile='/tmp/scaffold_yunohost_appgen.pyc', doraise=True)
py_compile.compile('/home/micou_org/scripts/audit_content_integrity.py', cfile='/tmp/audit_content_integrity.pyc', doraise=True)
py_compile.compile('/home/micou_org/scripts/audit_public_stack.py', cfile='/tmp/audit_public_stack.pyc', doraise=True)
print('python ok')
PY
bash -n /home/micou_org/scripts/repair_wallos_runtime.sh
bash -n /home/micou_org/scripts/ensure_domain_certificate.sh
python3 /home/micou_org/scripts/audit_content_integrity.py

echo "==> Restarting backend and reloading nginx"
nginx -t
systemctl daemon-reload
systemctl restart micou-forms.service
systemctl restart widdypad.service
systemctl reload nginx

if [[ "${activate_studio}" -eq 1 ]]; then
  echo "==> Activating studio workspace"
  bash /home/micou_org/scripts/activate_studio_workspace.sh
fi

echo "==> Repairing domain certificates when needed"
if bash /home/micou_org/scripts/ensure_domain_certificate.sh pdf.micou.org; then
  echo "PDF subdomain certificate check complete."
else
  echo "PDF subdomain certificate check could not complete cleanly."
fi

echo "==> Verification"
curl -I -s https://micou.org/ | sed -n '1,12p'
printf '\n'
curl -I -s https://www.micou.org/ | sed -n '1,12p'
printf '\n'
echo "Admin routes should now stay behind YunoHost auth and redirect anonymous users to /yunohost/sso/:"
curl -I -s https://micou.org/admin | sed -n '1,12p'
printf '\n'
curl -I -s https://micou.org/admin.html | sed -n '1,12p'
printf '\n'
curl -I -s https://micou.org/home | sed -n '1,12p'
printf '\n'
curl -I -s https://micou.org/home.html | sed -n '1,12p'
printf '\n'
curl -I -s https://micou.org/home-api/api/admin/state | sed -n '1,12p'
printf '\n'
if [[ "${activate_studio}" -eq 1 ]]; then
  curl -I -s https://studio.micou.org/ | sed -n '1,12p'
  printf '\n'
fi
systemctl --no-pager --full status micou-forms.service | sed -n '1,20p'
printf '\n'
systemctl --no-pager --full status widdypad.service | sed -n '1,20p'
printf '\n'
echo "==> Public audit"
if [[ "${activate_studio}" -eq 1 ]]; then
  python3 /home/micou_org/scripts/audit_public_stack.py --expect-studio
else
  python3 /home/micou_org/scripts/audit_public_stack.py
fi

echo
echo "Done."
echo "Admin pages now rely on YunoHost auth at the nginx layer."
echo "The backend recognizes admins based on the authenticated user email found in grants.json admins."
