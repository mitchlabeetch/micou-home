#!/usr/bin/env bash
set -euo pipefail

wallos_conf="/etc/nginx/conf.d/micou.org.d/wallos.conf"
source_catalog="/home/micou_org/catalog.json"
live_catalog="/srv/micou-services/micou-homepage/data/catalog.json"
timestamp="$(date +%F-%H%M%S)"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this script as root." >&2
  exit 1
fi

if [[ ! -f "${wallos_conf}" ]]; then
  echo "Wallos nginx config not found; keeping Wallos hidden."
  exit 1
fi

backup_file="${wallos_conf}.bak.${timestamp}"
cp -a "${wallos_conf}" "${backup_file}"

set_catalog_visibility() {
  local visible="$1"
  local target
  for target in "${source_catalog}" "${live_catalog}"; do
    [[ -f "${target}" ]] || continue
    python3 - "${target}" "${visible}" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
visible = sys.argv[2] == "1"
data = json.loads(path.read_text(encoding="utf-8"))
for app in data.get("apps", []):
    if str(app.get("id")) == "wallos":
        app["show_on_homepage"] = False
        app["show_on_dashboard"] = visible
path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY
  done
}

extract_current_socket() {
  sed -n 's/^[[:space:]]*fastcgi_pass[[:space:]]\+unix:\(.*\);/\1/p' "${wallos_conf}" | head -n 1
}

update_socket() {
  local socket="$1"
  python3 - "${wallos_conf}" "${socket}" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
socket = sys.argv[2]
text = path.read_text(encoding="utf-8")
text, count = re.subn(
    r'(^\s*fastcgi_pass\s+unix:).*(;\s*$)',
    rf'\1{socket}\2',
    text,
    flags=re.MULTILINE,
)
if count != 1:
    raise SystemExit("Could not update wallos fastcgi socket")
path.write_text(text, encoding="utf-8")
PY
}

restart_php_service_for_socket() {
  local socket="$1"
  local service=""
  if [[ "${socket}" =~ php([0-9]+\.[0-9]+)-fpm ]]; then
    service="php${BASH_REMATCH[1]}-fpm.service"
  fi
  if [[ -n "${service}" ]]; then
    systemctl restart "${service}" || true
  fi
}

wallos_healthcheck() {
  local code
  code="$(curl -k -sS -o /tmp/wallos-health.out -w '%{http_code}' https://micou.org/abos/ || true)"
  case "${code}" in
    200|301|302|303|307|308|401|403)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

declare -A seen=()
candidates=()
current_socket="$(extract_current_socket || true)"
if [[ -n "${current_socket}" ]]; then
  candidates+=("${current_socket}")
fi

while IFS= read -r pool_file; do
  [[ -n "${pool_file}" ]] || continue
  socket="$(sed -n 's/^[[:space:]]*listen[[:space:]]*=[[:space:]]*//p' "${pool_file}" | head -n 1)"
  [[ -n "${socket}" ]] || continue
  [[ -S "${socket}" ]] || continue
  if [[ -z "${seen[${socket}]+x}" ]]; then
    candidates+=("${socket}")
    seen["${socket}"]=1
  fi
done < <(find /etc/php -path '*/fpm/pool.d/*wallos*.conf' -type f 2>/dev/null | sort)

if [[ "${#candidates[@]}" -eq 0 ]]; then
  echo "No Wallos-specific PHP-FPM socket discovered; keeping Wallos hidden."
  set_catalog_visibility 0
  exit 1
fi

for socket in "${candidates[@]}"; do
  echo "Testing Wallos with socket ${socket}"
  update_socket "${socket}"
  restart_php_service_for_socket "${socket}"
  nginx -t
  systemctl reload nginx
  if wallos_healthcheck; then
    echo "Wallos responded successfully with socket ${socket}"
    set_catalog_visibility 1
    systemctl restart micou-forms.service || true
    exit 0
  fi
done

cp -a "${backup_file}" "${wallos_conf}"
nginx -t
systemctl reload nginx
set_catalog_visibility 0
echo "Wallos is still unhealthy; original nginx config restored and Wallos kept hidden."
exit 1
