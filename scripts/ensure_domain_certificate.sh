#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this script as root." >&2
  exit 1
fi

domain="${1:-}"
if [[ -z "${domain}" ]]; then
  echo "Usage: sudo bash $0 domain.tld" >&2
  exit 1
fi

if ! command -v yunohost >/dev/null 2>&1; then
  echo "yunohost command not found." >&2
  exit 1
fi

if ! yunohost domain info "${domain}" >/dev/null 2>&1; then
  echo "Skipping certificate check: ${domain} is not a configured YunoHost domain."
  exit 0
fi

issuer="$(echo | openssl s_client -servername "${domain}" -connect "${domain}:443" 2>/dev/null | openssl x509 -noout -issuer 2>/dev/null || true)"

if [[ -n "${issuer}" ]] && ! grep -Eq 'CN = micou\.org|O = micou' <<<"${issuer}"; then
  echo "Trusted-looking certificate already present for ${domain}; skipping reinstall."
  exit 0
fi

echo "Installing a trusted certificate for ${domain}"
if ! yunohost domain cert install "${domain}"; then
  echo "Standard certificate install failed for ${domain}; retrying without checks."
  yunohost domain cert install "${domain}" --no-checks
fi

nginx -t
systemctl reload nginx
echo "Certificate repair completed for ${domain}"
