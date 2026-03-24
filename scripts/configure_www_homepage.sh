#!/usr/bin/env bash
set -euo pipefail

mode="${1:-redirect}"
target="/etc/nginx/conf.d/www.micou.org.d/10-homepage.conf"

if [[ "${EUID}" -ne 0 ]]; then
  echo "This script must run as root." >&2
  exit 1
fi

mkdir -p /etc/nginx/conf.d/www.micou.org.d

case "${mode}" in
  redirect)
    cat > "${target}" <<'EOF'
location / {
    access_by_lua_file /etc/nginx/allow.lua;
    return 301 https://micou.org$request_uri;
}
EOF
    ;;

  serve)
    cat > "${target}" <<'EOF'
location = / {
    access_by_lua_file /etc/nginx/allow.lua;
    root /home/micou_org;
    index index.html;
}

location = /index.html {
    return 301 https://www.micou.org/;
}

location ^~ /illustrations/ {
    access_by_lua_file /etc/nginx/allow.lua;
    alias /home/micou_org/illustrations/;
}
EOF
    ;;

  *)
    echo "usage: $0 [redirect|serve]" >&2
    exit 1
    ;;
esac

nginx -t
systemctl reload nginx
echo "Configured www.micou.org homepage mode: ${mode}"
