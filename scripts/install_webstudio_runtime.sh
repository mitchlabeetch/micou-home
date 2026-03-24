#!/usr/bin/env bash
set -euo pipefail

install_docker=0
if [[ "${1:-}" == "--install-docker" ]]; then
  install_docker=1
fi

managed_root="${MICOU_MANAGED_ROOT:-/srv/micou-services}"
studio_root="${managed_root}/webstudio"
studio_domain="${MICOU_WEBSTUDIO_DOMAIN:-studio.micou.org}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "This script must run as root." >&2
  exit 1
fi

docker_ready=1
if ! command -v docker >/dev/null 2>&1; then
  docker_ready=0
  if [[ "${install_docker}" -eq 1 ]]; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable --now docker
    docker_ready=1
  fi
fi

install -d -m 0755 "${studio_root}/workspace" "${studio_root}/projects" "${studio_root}/deploy" "${studio_root}/docs"

cat > "${studio_root}/workspace/index.html" <<EOF
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>studio.micou.org</title>
  <style>
    :root {
      --bg: #f7f3eb;
      --panel: #ffffff;
      --text: #1b1b1b;
      --muted: #5f5f5f;
      --green: #22c55e;
      --purple: #8b5cf6;
      --orange: #f97316;
      --blue: #3b82f6;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Georgia, serif;
      background: linear-gradient(180deg, #fffdf8 0%, var(--bg) 100%);
      color: var(--text);
    }
    .wrap {
      max-width: 980px;
      margin: 0 auto;
      padding: 32px 20px 56px;
    }
    .hero, .panel {
      background: var(--panel);
      border: 4px solid var(--text);
      box-shadow: 6px 6px 0 var(--purple);
      padding: 28px;
      margin-bottom: 24px;
    }
    .hero h1, .panel h2 {
      margin: 0 0 14px;
      font-family: "Arial Black", sans-serif;
      letter-spacing: -0.04em;
      text-transform: uppercase;
    }
    .hero p, .panel p, li {
      line-height: 1.65;
      font-size: 1rem;
    }
    .actions {
      display: flex;
      gap: 14px;
      flex-wrap: wrap;
      margin-top: 18px;
    }
    .btn {
      display: inline-block;
      padding: 12px 18px;
      border: 3px solid var(--text);
      background: var(--green);
      color: #fff;
      text-decoration: none;
      font-family: monospace;
      font-weight: 700;
      box-shadow: 4px 4px 0 var(--text);
    }
    .btn.secondary {
      background: #fff;
      color: var(--text);
    }
    .btn.blue {
      background: var(--blue);
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 18px;
    }
    .checklist {
      margin-top: 14px;
      display: grid;
      gap: 8px;
    }
    .check {
      border: 2px solid var(--text);
      background: #fffdf8;
      padding: 10px 12px;
    }
    code {
      font-family: monospace;
      background: #f5f2ff;
      padding: 2px 6px;
      border: 1px solid #d8cbff;
    }
    ul {
      margin: 12px 0 0 20px;
      padding: 0;
    }
  </style>
</head>
<body>
  <main class="wrap">
    <section class="hero">
      <h1>micou public pages studio</h1>
      <p>This workspace is the operational bridge between Webstudio Cloud and the public pages served on micou.org.</p>
      <p>YunoHost remains the authenticated member dashboard. Webstudio is used for public pages only: homepage, blog, and future public landing pages.</p>
      <div class="actions">
        <a class="btn" href="https://micou.org/">Open public homepage</a>
        <a class="btn secondary" href="https://micou.org/yunohost/sso/">Open member space</a>
        <a class="btn secondary" href="https://micou.org/admin.html">Open control plane</a>
        <a class="btn blue" href="https://webstudio.is/" rel="noreferrer">Open Webstudio Cloud</a>
      </div>
      <div class="checklist">
        <div class="check">1. Edit a public page in Webstudio Cloud.</div>
        <div class="check">2. Export the project files.</div>
        <div class="check">3. Copy the export to the VPS.</div>
        <div class="check">4. Deploy with <code>/home/micou_org/scripts/deploy_public_export.sh</code>.</div>
      </div>
    </section>

    <div class="grid">
      <section class="panel">
        <h2>Edit flow</h2>
        <ul>
          <li>Edit the public page in Webstudio Cloud.</li>
          <li>Export the project.</li>
          <li>Copy the export to the VPS.</li>
          <li>Deploy it with <code>/home/micou_org/scripts/deploy_public_export.sh</code>.</li>
        </ul>
      </section>
      <section class="panel">
        <h2>Source of truth</h2>
        <p>Managed public site root:</p>
        <p><code>/srv/micou-services/micou-homepage/app</code></p>
        <p>Protected operational files stay outside the Webstudio export flow: <code>admin.html</code>, <code>home.html</code>, backend code, registry data, and nginx/systemd configuration.</p>
      </section>
      <section class="panel">
        <h2>Deploy commands</h2>
        <ul>
          <li><code>bash /home/micou_org/scripts/deploy_public_export.sh /path/to/webstudio-export</code></li>
          <li><code>sudo bash /home/micou_org/scripts/final_full_deploy.sh --activate-studio</code></li>
        </ul>
      </section>
      <section class="panel">
        <h2>References</h2>
        <ul>
          <li><a href="https://docs.webstudio.is/university/self-hosting">Webstudio self-hosting docs</a></li>
          <li><a href="https://docs.webstudio.is/university/self-hosting/static-export">Static export docs</a></li>
          <li><a href="https://micou.org/admin.html">micou control plane</a></li>
        </ul>
      </section>
    </div>
  </main>
</body>
</html>
EOF

cat > "${studio_root}/docs/README.md" <<EOF
# Webstudio workspace

This directory was prepared for the micou.org control plane.

Recommended model:
- use Webstudio to edit public pages and exported site projects
- keep YunoHost SSO as the authenticated member dashboard
- deploy exported projects from Git repositories into this VPS

Upstream references:
- https://docs.webstudio.is/university/self-hosting
- https://docs.webstudio.is/university/self-hosting/static-export

Suggested domain:
- ${studio_domain}

Recommended activation command:
- sudo bash /home/micou_org/scripts/final_full_deploy.sh --activate-studio
EOF

cat > "${studio_root}/deploy/${studio_domain}.conf.example" <<EOF
location = / {
    access_by_lua_file /etc/nginx/allow.lua;
    root ${studio_root}/workspace;
    index index.html;
}

location = /index.html {
    access_by_lua_file /etc/nginx/allow.lua;
    alias ${studio_root}/workspace/index.html;
}
EOF

chown -R mitch:mitch "${studio_root}"

cat <<EOF
Prepared Webstudio workspace in ${studio_root}

Important:
  - Webstudio's official docs support self-hosting exported projects.
  - The selected micou model uses Webstudio for editing public pages, not for replacing YunoHost's authenticated member dashboard.

Next steps:
  1. Add the YunoHost domain: ${studio_domain}
  2. Install the nginx include from ${studio_root}/deploy/${studio_domain}.conf.example
  3. Connect homepage/blog page entries to Webstudio-managed repos in the admin UI
EOF

if [[ "${docker_ready}" -eq 0 ]]; then
  cat <<EOF

Docker was not installed. That is acceptable for the selected static workspace model.
Re-run with --install-docker only if you later want Docker available for other services.
EOF
fi
