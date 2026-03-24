#!/usr/bin/env bash
set -euo pipefail

studio_domain="${MICOU_WEBSTUDIO_DOMAIN:-studio.micou.org}"
managed_root="${MICOU_MANAGED_ROOT:-/srv/micou-services}"
studio_root="${managed_root}/webstudio"
nginx_include="/etc/nginx/conf.d/${studio_domain}.d/10-webstudio-workspace.conf"
nginx_template="${studio_root}/deploy/${studio_domain}.conf.example"

if [[ "${EUID}" -ne 0 ]]; then
  echo "This script must run as root." >&2
  exit 1
fi

if [[ ! -f "${nginx_template}" ]]; then
  echo "Missing template: ${nginx_template}" >&2
  exit 1
fi

domain_created=0
if ! yunohost domain info "${studio_domain}" >/dev/null 2>&1; then
  yunohost domain add "${studio_domain}"
  domain_created=1
fi

if [[ "${domain_created}" -eq 1 ]]; then
  yunohost domain cert install "${studio_domain}" --no-checks
else
  echo "Certificate already present for ${studio_domain}; skipping certificate installation."
fi

mkdir -p "/etc/nginx/conf.d/${studio_domain}.d"
cp "${nginx_template}" "${nginx_include}"
nginx -t
systemctl reload nginx

echo "Activated protected Webstudio entrypoint on https://${studio_domain}/"
