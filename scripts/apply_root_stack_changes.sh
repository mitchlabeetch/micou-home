#!/usr/bin/env bash
set -euo pipefail

install_docker=0
if [[ "${1:-}" == "--install-docker" ]]; then
  install_docker=1
fi

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this script as root, for example: sudo bash $0 [--install-docker]" >&2
  exit 1
fi

timestamp="$(date +%F-%H%M%S)"
managed_root="/srv/micou-services"
homepage_root="${managed_root}/micou-homepage"
widdypad_root="${managed_root}/widdypad"

backup_file() {
  local path="$1"
  if [[ -e "${path}" ]]; then
    cp -a "${path}" "${path}.bak.${timestamp}"
  fi
}

echo "==> Backing up current live config"
backup_file /etc/systemd/system/micou-forms.service
backup_file /etc/systemd/system/widdypad.service
backup_file /etc/micou_org/forms.env
backup_file /etc/nginx/conf.d/micou.org.d/10-micou-custom-proxies.conf
backup_file /etc/nginx/conf.d/www.micou.org.d/10-homepage.conf

echo "==> Creating managed service copies"
/home/micou_org/scripts/migrate_service_to_managed_root.sh micou-homepage
/home/micou_org/scripts/migrate_service_to_managed_root.sh widdypad

echo "==> Preparing Webstudio workspace"
if [[ "${install_docker}" -eq 1 ]]; then
  /home/micou_org/scripts/install_webstudio_runtime.sh --install-docker
else
  /home/micou_org/scripts/install_webstudio_runtime.sh
fi

echo "==> Updating www.micou.org to redirect to the apex homepage"
/home/micou_org/scripts/configure_www_homepage.sh redirect

echo "==> Rewriting systemd, environment, and nginx paths"
python3 - <<PY
from pathlib import Path

managed_root = Path("${managed_root}")
homepage_root = Path("${homepage_root}")
widdypad_root = Path("${widdypad_root}")

forms_service = Path("/etc/systemd/system/micou-forms.service")
widdypad_service = Path("/etc/systemd/system/widdypad.service")
forms_env = Path("/etc/micou_org/forms.env")
nginx_conf = Path("/etc/nginx/conf.d/micou.org.d/10-micou-custom-proxies.conf")

def set_or_replace_line(text: str, prefix: str, new_line: str) -> str:
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        if line.startswith(prefix):
            lines[idx] = new_line
            return "\\n".join(lines) + "\\n"
    lines.append(new_line)
    return "\\n".join(lines) + "\\n"

def set_or_insert_in_section(text: str, section: str, prefix: str, new_line: str) -> str:
    lines = text.splitlines()
    section_header = f"[{section}]"
    in_section = False
    insert_at = None
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped == section_header:
            in_section = True
            insert_at = idx + 1
            continue
        if in_section and stripped.startswith("[") and stripped.endswith("]"):
            insert_at = idx
            break
        if in_section:
            if line.startswith(prefix):
                lines[idx] = new_line
                return "\\n".join(lines) + "\\n"
            insert_at = idx + 1
    if insert_at is None:
        lines.extend([section_header, new_line])
    else:
        lines.insert(insert_at, new_line)
    return "\\n".join(lines) + "\\n"

forms_text = forms_service.read_text(encoding="utf-8")
forms_text = set_or_replace_line(forms_text, "WorkingDirectory=", f"WorkingDirectory={homepage_root / 'backend'}")
forms_text = set_or_replace_line(forms_text, "ExecStart=", f"ExecStart=/usr/bin/python3 {homepage_root / 'backend' / 'forms_service.py'}")
forms_service.write_text(forms_text, encoding="utf-8")

widdy_text = widdypad_service.read_text(encoding="utf-8")
widdy_text = set_or_replace_line(widdy_text, "WorkingDirectory=", f"WorkingDirectory={widdypad_root / 'app'}")
widdy_text = set_or_replace_line(widdy_text, "ExecStart=", f"ExecStart=/usr/bin/python3 {widdypad_root / 'app' / 'server.py'}")
widdy_text = set_or_insert_in_section(widdy_text, "Service", "Environment=MP3WIDDY_LIBRARY_DIR=", f"Environment=MP3WIDDY_LIBRARY_DIR={widdypad_root / 'data'}")
widdypad_service.write_text(widdy_text, encoding="utf-8")

env_lines = forms_env.read_text(encoding="utf-8").splitlines() if forms_env.exists() else []
updates = {
    "MICOU_CATALOG_PATH": str(homepage_root / "data" / "catalog.json"),
    "MICOU_GRANTS_PATH": str(homepage_root / "data" / "grants.json"),
    "MICOU_CONTENT_PATH": str(homepage_root / "data" / "site_content.json"),
    "MICOU_AUDIT_LOG_PATH": str(homepage_root / "data" / "admin_audit.log"),
    "MICOU_SERVICES_ROOT": str(managed_root),
}
seen = set()
new_lines = []
for line in env_lines:
    if "=" not in line or line.lstrip().startswith("#"):
      new_lines.append(line)
      continue
    key, _, _ = line.partition("=")
    if key in updates:
      new_lines.append(f"{key}={updates[key]}")
      seen.add(key)
    else:
      new_lines.append(line)
for key, value in updates.items():
    if key not in seen:
      new_lines.append(f"{key}={value}")
forms_env.write_text("\\n".join(new_lines).rstrip() + "\\n", encoding="utf-8")

nginx_text = nginx_conf.read_text(encoding="utf-8")
nginx_text = nginx_text.replace("/home/micou_org", str(homepage_root / "app"))
nginx_conf.write_text(nginx_text, encoding="utf-8")

(homepage_root / "data" / "admin_audit.log").touch(exist_ok=True)
PY

echo "==> Validating managed Python services"
python3 -m py_compile \
  "${homepage_root}/backend/forms_service.py" \
  "${widdypad_root}/app/server.py"

echo "==> Reloading services"
systemctl daemon-reload
nginx -t
systemctl restart micou-forms.service
systemctl restart widdypad.service
systemctl reload nginx

echo "==> Verification"
curl -I -s https://micou.org/ | sed -n '1,20p'
printf '\n'
curl -I -s https://www.micou.org/ | sed -n '1,20p'
printf '\n'
curl -I -s https://micou.org/widdypad/ | sed -n '1,20p'
printf '\n'
catalog_tmp="/tmp/micou-catalog-${timestamp}.json"
curl -s https://micou.org/api/catalog > "${catalog_tmp}"
python3 - "${catalog_tmp}" <<'PY'
import json, sys
payload = json.load(open(sys.argv[1], "r", encoding="utf-8"))
print(json.dumps({
    "generated_at": payload.get("generated_at"),
    "apps": len(payload.get("apps") or []),
    "available_apps": len(payload.get("available_apps") or []),
    "discovered_services": len(payload.get("discovered_services") or []),
}, indent=2))
PY
printf '\n'
systemctl --no-pager --full status micou-forms.service | sed -n '1,20p'
printf '\n'
systemctl --no-pager --full status widdypad.service | sed -n '1,20p'
