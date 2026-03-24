#!/usr/bin/env bash
set -euo pipefail

studio_domain="${MICOU_WEBSTUDIO_DOMAIN:-studio.micou.org}"
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

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this script as root, for example: sudo bash $0 [--activate-studio]" >&2
  exit 1
fi

timestamp="$(date +%F-%H%M%S)"
widdypad_service="/etc/systemd/system/widdypad.service"

backup_file() {
  local path="$1"
  if [[ -e "${path}" ]]; then
    cp -a "${path}" "${path}.bak.${timestamp}"
  fi
}

echo "==> Fixing widdypad systemd environment placement"
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

systemctl daemon-reload
systemctl restart widdypad.service

echo "==> Verifying public services"
systemctl --no-pager --full status widdypad.service | sed -n '1,20p'
printf '\n'
curl -I -s https://micou.org/ | sed -n '1,12p'
printf '\n'
curl -I -s https://www.micou.org/ | sed -n '1,12p'

if [[ "${activate_studio}" -eq 1 ]]; then
  echo
  echo "==> Activating ${studio_domain}"
  /home/micou_org/scripts/activate_studio_workspace.sh
  printf '\n'
  curl -I -s "https://${studio_domain}/" | sed -n '1,12p'
else
  echo
  echo "==> Studio workspace not activated by this run"
  echo "If the DNS record for ${studio_domain} now points to this VPS, run:"
  echo "  sudo bash /home/micou_org/scripts/finalize_public_stack.sh --activate-studio"
fi
