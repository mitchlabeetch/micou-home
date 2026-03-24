#!/usr/bin/env bash
set -euo pipefail

export_dir="${1:-}"
target_root="${MICOU_HOMEPAGE_APP_ROOT:-/srv/micou-services/micou-homepage/app}"
backup_root="${MICOU_HOMEPAGE_BACKUP_ROOT:-/srv/micou-services/micou-homepage/backups}"
timestamp="$(date +%F-%H%M%S)"

if [[ -z "${export_dir}" ]]; then
  echo "usage: $0 <webstudio-export-directory>" >&2
  exit 1
fi

if [[ ! -d "${export_dir}" ]]; then
  echo "Export directory not found: ${export_dir}" >&2
  exit 1
fi

mkdir -p "${backup_root}"
mkdir -p "${target_root}"

backup_dir="${backup_root}/public-site-${timestamp}"
mkdir -p "${backup_dir}"

for path in index.html assets static public favicon.ico favicon.svg robots.txt sitemap.xml manifest.webmanifest; do
  if [[ -e "${target_root}/${path}" ]]; then
    cp -a "${target_root}/${path}" "${backup_dir}/"
  fi
done

if command -v rsync >/dev/null 2>&1; then
  rsync -a \
    --exclude='admin.html' \
    --exclude='home.html' \
    --exclude='forms_service.py' \
    --exclude='catalog.json' \
    --exclude='grants.json' \
    --exclude='site_content.json' \
    --exclude='illustrations/' \
    "${export_dir}/" "${target_root}/"
else
  find "${export_dir}" -mindepth 1 -maxdepth 1 | while read -r item; do
    name="$(basename "${item}")"
    case "${name}" in
      admin.html|home.html|forms_service.py|catalog.json|grants.json|site_content.json|illustrations)
        continue
        ;;
    esac
    rm -rf "${target_root:?}/${name}"
    cp -a "${item}" "${target_root}/"
  done
fi

echo "Deployed public export from ${export_dir} to ${target_root}"
echo "Backup snapshot: ${backup_dir}"
echo "Next steps:"
echo "  1. Verify https://micou.org/"
echo "  2. If the export changed linked assets heavily, reload nginx: sudo systemctl reload nginx"
