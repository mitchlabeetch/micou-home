#!/usr/bin/env bash
set -euo pipefail

service_id="${1:-}"
managed_root="${MICOU_MANAGED_ROOT:-/srv/micou-services}"

if [[ -z "${service_id}" ]]; then
  echo "usage: $0 <micou-homepage|widdypad>" >&2
  exit 1
fi

if [[ "${EUID}" -ne 0 ]]; then
  echo "This script must run as root." >&2
  exit 1
fi

copy_tree() {
  local src="$1"
  local dst="$2"
  mkdir -p "${dst}"
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete "${src}" "${dst}"
  else
    rm -rf "${dst}"
    mkdir -p "${dst}"
    cp -a "${src}"/. "${dst}"/
  fi
}

copy_file() {
  local src="$1"
  local dst="$2"
  install -D -m 0644 "${src}" "${dst}"
}

patch_widdypad_server() {
  local path="$1"
  python3 - "$path" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

old = "BASE_DIR = Path(__file__).resolve().parent\n"
new = (
    "BASE_DIR = Path(__file__).resolve().parent\n"
    "LIBRARY_DIR = Path(os.environ.get(\"MP3WIDDY_LIBRARY_DIR\", str(BASE_DIR))).resolve()\n"
)
if old not in text:
    raise SystemExit("Could not find BASE_DIR declaration")
text = text.replace(old, new, 1)

text = text.replace("p = (BASE_DIR / name).resolve()", "p = (LIBRARY_DIR / name).resolve()")
text = text.replace("base_resolved = BASE_DIR.resolve()", "base_resolved = LIBRARY_DIR.resolve()")
text = text.replace("base_resolved = BASE_DIR", "base_resolved = LIBRARY_DIR")
text = text.replace("for p in BASE_DIR.iterdir():", "for p in LIBRARY_DIR.iterdir():")

path.write_text(text, encoding="utf-8")
PY
}

snapshot_note() {
  local path="$1"
  printf 'Snapshot created at %s\n' "${path}"
}

case "${service_id}" in
  micou-homepage)
    target="${managed_root}/micou-homepage"
    install -d -m 0755 "${target}/app" "${target}/backend" "${target}/data" "${target}/cms" "${target}/deploy" "${target}/docs"

    copy_file /home/micou_org/index.html "${target}/app/index.html"
    copy_file /home/micou_org/home.html "${target}/app/home.html"
    copy_file /home/micou_org/admin.html "${target}/app/admin.html"
    copy_tree /home/micou_org/illustrations/ "${target}/app/illustrations/"

    copy_file /home/micou_org/forms_service.py "${target}/backend/forms_service.py"
    copy_file /home/micou_org/catalog.json "${target}/data/catalog.json"
    copy_file /home/micou_org/grants.json "${target}/data/grants.json"
    copy_file /home/micou_org/site_content.json "${target}/data/site_content.json"
    copy_file /home/micou_org/decap.config.yml "${target}/cms/decap.config.yml"
    copy_file /home/micou_org/SERVICE_CONTROL_PLANE.md "${target}/docs/SERVICE_CONTROL_PLANE.md"
    copy_file /home/micou_org/SETUP.md "${target}/docs/SETUP.md"
    copy_file /home/micou_org/MIGRATION_PLAN.md "${target}/docs/MIGRATION_PLAN.md"

    chown -R mitch:mitch "${target}"
    snapshot_note "${target}"
    cat <<EOF
Next steps:
  1. Update /etc/micou_org/forms.env so MICOU_*_PATH variables point into ${target}/data
  2. Update nginx aliases for micou.org/illustrations if you want to serve from ${target}/app
  3. Restart micou-forms.service
EOF
    ;;

  widdypad)
    target="${managed_root}/widdypad"
    install -d -m 0755 "${target}/app" "${target}/data" "${target}/source-snapshots"

    copy_file /media/musicwiddy/server.py "${target}/app/server.py"
    copy_file /etc/skel/media/musicwiddy/server.py "${target}/source-snapshots/skel-server.py"
    patch_widdypad_server "${target}/app/server.py"

    if cmp -s /media/musicwiddy/server.py /etc/skel/media/musicwiddy/server.py; then
      printf 'WiddyPad source files are identical in /media and /etc/skel.\n' > "${target}/source-snapshots/README.txt"
    else
      cat > "${target}/source-snapshots/README.txt" <<'EOF'
The live /media/musicwiddy/server.py and /etc/skel/media/musicwiddy/server.py differ.
Review both before cutting production over to the managed tree.
EOF
    fi

    if command -v rsync >/dev/null 2>&1; then
      rsync -a --delete --exclude='server.py' /media/musicwiddy/ "${target}/data/"
    else
      find "${target}/data" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
      find /media/musicwiddy -mindepth 1 -maxdepth 1 ! -name 'server.py' -exec cp -a {} "${target}/data/" \;
    fi

    chown -R mitch:mitch "${target}"
    snapshot_note "${target}"
    cat <<EOF
Next steps:
  1. Update /etc/systemd/system/widdypad.service:
     WorkingDirectory=${target}/app
     ExecStart=/usr/bin/python3 ${target}/app/server.py
     Environment=MP3WIDDY_BASE_PATH=/widdypad
     Environment=MP3WIDDY_LIBRARY_DIR=${target}/data
  2. Point the service to ${target}/data if you refactor server.py to use a dedicated data dir
  3. Run systemctl daemon-reload && systemctl restart widdypad.service
EOF
    ;;

  *)
    echo "Unsupported service id: ${service_id}" >&2
    exit 1
    ;;
esac
