# micou.org — VPS Setup (Web, YunoHost Admin, Forms, Mail Relay, Anti-Abuse)

This document describes the current production setup on the VPS and the exact steps to reproduce / maintain it.

## 1) Architecture Overview

**Public entrypoint**
- HTTPS is terminated by Caddy on ports 80/443.
- Caddy routes requests by path:
  - `/` → static homepage served from `/home/micou_org`
  - `/api/*` → micou.org forms backend (localhost `127.0.0.1:9100`)
  - `/widdypad/*` → WiddyPad service (localhost `127.0.0.1:8000`)
  - `/admin` → redirect to `/yunohost/admin/`
  - `/yunohost/admin/*` → YunoHost admin frontend (static files from `/usr/share/yunohost/admin`)
  - `/yunohost/api/*` and `/yunohost/ws/*` → YunoHost API (localhost `127.0.0.1:6787`)
  - `/healthz` → health check (`ok`)

**Local services**
- `caddy` (reverse-proxy / static hosting)
- `micou-forms` (custom form handler + conditional proof-of-work)
- `widdypad` (MP3 server)
- `yunohost-api` + `yunohost-portal-api` (YunoHost)
- `postfix` (MTA; outbound relayed via SMTP provider)
- `fail2ban` (bans abusive IPs based on Caddy logs)

## 2) Files and Services

### Caddy
- Config: `/etc/caddy/Caddyfile`
- Service: `systemctl status caddy`
- Access logs: `/var/log/caddy/access.log` (JSON)

### Homepage
- Document root: `/home/micou_org`
- Main file: `/home/micou_org/index.html`
- Assets: `/home/micou_org/illustrations/`

### Forms backend
- Code: `/home/micou_org/forms_service.py`
- Environment: `/etc/micou_org/forms.env`
- Service: `systemctl status micou-forms`
- Local listen: `127.0.0.1:9100`
- Public endpoints:
  - `POST /api/access-request`
  - `GET /api/pow`

### WiddyPad
- Service: `systemctl status widdypad`
- Local listen: `127.0.0.1:8000`
- Public base path: `/widdypad`

### YunoHost
- API service: `systemctl status yunohost-api` (listens on `127.0.0.1:6787`)
- Portal API: `systemctl status yunohost-portal-api` (listens on `127.0.0.1:6788`)
- Admin UI public URL: `https://micou.org/admin` (redirects to `/yunohost/admin/`)

## 3) DNS Records (micou.org)

### Website
```dns
@ 3600 IN A 87.106.4.95
www 3600 IN A 87.106.4.95
@ 3600 IN CAA 0 issue "letsencrypt.org"
```

### Mail (YunoHost + relay-friendly)

**If you want YunoHost to receive inbound mail for `micou.org`, set:**
```dns
@ 3600 IN MX 10 micou.org.
```

**SPF**
- Use a single SPF record.
- For Mailjet relay + YunoHost baseline, use:
```dns
@ 3600 IN TXT "v=spf1 a mx include:spf.mailjet.com ~all"
```

**DKIM**
- Keep YunoHost DKIM for inbound reputation:
```dns
mail._domainkey 3600 IN TXT "v=DKIM1; h=sha256; k=rsa; p=PASTE_THE_KEY_FROM_YUNOHOST_DNS_SUGGEST"
```
- Also enable DKIM inside Mailjet and add the DKIM TXT record that Mailjet provides (its selector is typically different, e.g. `mailjet._domainkey`).

**DMARC**
```dns
_dmarc 3600 IN TXT "v=DMARC1; p=none"
```
After deliverability is confirmed, change `p=none` → `p=quarantine` → `p=reject`.

## 4) Mail Deliverability Strategy (Chosen Option)

### Why a relay is required
This VPS cannot open outbound SMTP on TCP/25 to the internet (common provider policy), which breaks direct delivery and forwarding to external providers.

### Chosen solution
Use **Mailjet SMTP relay (port 587)** for all outbound mail (including forwards).

### Configure Mailjet relay in Postfix

1. Create a Mailjet account, then obtain:
   - SMTP username
   - SMTP password

2. Edit `/etc/postfix/sasl_passwd`:
```txt
[in-v3.mailjet.com]:587 YOUR_REAL_SMTP_USERNAME:YOUR_REAL_SMTP_PASSWORD
```

3. Compile the map + restart Postfix:
```bash
sudo postmap /etc/postfix/sasl_passwd
sudo systemctl restart postfix@-
```

4. Check queue:
```bash
sudo postqueue -p
```

## 5) Address Behavior

### micou@micou.org
- Implemented as a YunoHost **mail alias** on the existing user `mitch`.
- Forwarding configured to:
  - `c72b9627-4925-49c2-88e1-e2e35580a50f@anonaddy.com`

To review:
```bash
sudo yunohost user info mitch
```

## 6) Anti-Abuse: Conditional Proof-of-Work + Fail2ban

### Conditional challenge (no captcha for normal users)
- The forms backend has in-memory rate limiting per-IP.
- Past a soft threshold, the server responds `429` with `pow_required=true`.
- The homepage automatically solves a small SHA-256 proof-of-work challenge and retries.
- Past a hard threshold, the server blocks with `429` regardless.

### Fail2ban
- Caddy logs requests to `/var/log/caddy/access.log` in JSON.
- Fail2ban watches abusive status codes for `/api/access-request` and bans offenders.

Files:
- `/etc/fail2ban/filter.d/caddy-micou-forms.conf`
- `/etc/fail2ban/jail.d/caddy-micou-forms.local`

Commands:
```bash
sudo fail2ban-client status
sudo fail2ban-client status caddy-micou-forms
```

## 7) Operations / Troubleshooting

### Restart everything (safe order)
```bash
sudo systemctl restart postfix@-
sudo systemctl restart yunohost-api
sudo systemctl restart micou-forms
sudo systemctl restart widdypad
sudo systemctl restart caddy
```

### Quick health checks
```bash
curl -sS https://micou.org/healthz
curl -sS -I https://micou.org/
curl -sS -I https://micou.org/api/pow
curl -sS -I https://micou.org/widdypad/
curl -sS -I https://micou.org/admin
curl -sS https://micou.org/yunohost/api/installed
```

### Mail debugging
```bash
sudo postqueue -p
sudo journalctl -u postfix@- -n 100 --no-pager
```

### Caddy debugging
```bash
sudo caddy validate --config /etc/caddy/Caddyfile
sudo journalctl -u caddy -n 100 --no-pager
tail -n 50 /var/log/caddy/access.log
```

