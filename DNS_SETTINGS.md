# DNS settings

## Current public server IP

Current public IPv4 observed from the VPS:

- `87.106.4.95`

## Recommended records

### Main site

```dns
@     3600 IN A 87.106.4.95
www   3600 IN A 87.106.4.95
```

`www.micou.org` should exist in DNS, but the web server should redirect it to `https://micou.org/`.

### Public editor/workspace domain

Recommended for the selected Webstudio workflow:

```dns
studio 3600 IN A 87.106.4.95
```

This should point to the same VPS and serve the static Webstudio workspace page.

### Optional alternate public site domain

If you still want a dedicated `home.micou.org` alias later:

```dns
home 3600 IN A 87.106.4.95
```

## YunoHost actions after DNS

For any new subdomain managed by YunoHost, add the domain first:

```bash
sudo bash /home/micou_org/scripts/final_full_deploy.sh --activate-studio
```

This wrapper will:

- sync the latest public/admin source files into `/srv`
- keep admin routes behind YunoHost auth
- fix the WiddyPad systemd unit if needed
- add the `studio.micou.org` YunoHost domain if needed
- request/install the certificate
- write the nginx include for the studio workspace
- reload nginx and verify the result

## Keep / do not change

Keep the apex `micou.org` as the main public entrypoint.

Do not point `www.micou.org` at a different server. It should resolve here and be redirected to the apex.

## Recommended command order

1. Create or update the `A` records above.
2. Wait for DNS propagation.
3. Run:

```bash
sudo bash /home/micou_org/scripts/final_full_deploy.sh --activate-studio
```

4. Verify:

```bash
curl -I https://studio.micou.org/
curl -I https://www.micou.org/
curl -I https://micou.org/
```
