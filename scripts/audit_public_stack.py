#!/usr/bin/env python3
import argparse
import json
import ssl
import sys
import urllib.error
import urllib.request


def build_opener(follow_redirects: bool):
    ctx = ssl.create_default_context()
    https_handler = urllib.request.HTTPSHandler(context=ctx)
    if follow_redirects:
        return urllib.request.build_opener(https_handler)

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    return urllib.request.build_opener(NoRedirect, https_handler)


def fetch(url: str, *, follow_redirects: bool = False, timeout: int = 15):
    opener = build_opener(follow_redirects)
    req = urllib.request.Request(url, headers={"User-Agent": "micou-audit/1.0"})
    try:
        with opener.open(req, timeout=timeout) as resp:
            body = resp.read(200).decode("utf-8", "ignore")
            return {
                "ok": True,
                "status": resp.status,
                "url": resp.geturl(),
                "location": resp.headers.get("Location", ""),
                "body": body,
            }
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read(200).decode("utf-8", "ignore")
        except Exception:
            pass
        return {
            "ok": False,
            "status": exc.code,
            "url": url,
            "location": exc.headers.get("Location", ""),
            "body": body,
        }
    except urllib.error.URLError as exc:
        return {
            "ok": False,
            "status": 0,
            "url": url,
            "location": "",
            "body": "",
            "error": str(exc.reason),
        }


def expect(condition: bool, message: str, issues: list[str]):
    if not condition:
        issues.append(message)


def looks_like_sso(location: str) -> bool:
    return "/yunohost/sso" in (location or "")


def looks_like_admin_redirect(location: str) -> bool:
    return "/admin" in (location or "")


def core_checks(expect_studio: bool) -> list[str]:
    issues: list[str] = []

    apex = fetch("https://micou.org/")
    expect(apex["status"] == 200, "https://micou.org/ must return 200", issues)

    www = fetch("https://www.micou.org/")
    expect(www["status"] in {301, 302}, "https://www.micou.org/ must redirect", issues)
    expect((www["location"] or "").rstrip("/") == "https://micou.org", "https://www.micou.org/ must redirect to https://micou.org/", issues)

    admin = fetch("https://micou.org/admin")
    expect(admin["status"] in {302, 303}, "/admin must redirect", issues)
    expect(
        admin["location"] in {"/admin.html", "https://micou.org/admin.html"} or looks_like_sso(admin["location"]),
        "/admin must lead to admin.html or YunoHost SSO",
        issues,
    )

    admin_html = fetch("https://micou.org/admin.html")
    expect(admin_html["status"] in {302, 303}, "/admin.html must be protected", issues)
    expect(looks_like_sso(admin_html["location"]), "/admin.html must redirect to YunoHost SSO", issues)

    home = fetch("https://micou.org/home")
    expect(home["status"] in {302, 303}, "/home must redirect", issues)
    expect(
        home["location"] in {"/home.html", "https://micou.org/home.html"} or looks_like_sso(home["location"]),
        "/home must lead to home.html or YunoHost SSO",
        issues,
    )

    home_html = fetch("https://micou.org/home.html")
    expect(home_html["status"] in {302, 303}, "/home.html must be protected", issues)
    expect(looks_like_sso(home_html["location"]), "/home.html must redirect to YunoHost SSO", issues)

    home_api = fetch("https://micou.org/home-api/api/admin/state")
    expect(home_api["status"] in {302, 303}, "/home-api/api/admin/state must be protected", issues)
    expect(looks_like_sso(home_api["location"]), "/home-api/api/admin/state must redirect to YunoHost SSO", issues)

    if expect_studio:
        studio = fetch("https://studio.micou.org/")
        expect(
            studio["status"] == 200 or looks_like_sso(studio["location"]) or looks_like_admin_redirect(studio["location"]),
            "https://studio.micou.org/ must return 200 or redirect to the protected admin surface",
            issues,
        )

    return issues


def app_checks() -> list[str]:
    issues: list[str] = []
    opener = build_opener(True)
    req = urllib.request.Request("https://micou.org/api/catalog", headers={"User-Agent": "micou-audit/1.0"})
    try:
        with opener.open(req, timeout=20) as resp:
            payload = json.load(resp)
    except Exception as exc:
        return [f"/api/catalog must return valid JSON ({exc})"]

    if not isinstance(payload, dict):
        return ["/api/catalog must return 200"]

    for app in payload.get("apps", []):
        if not app.get("show_on_homepage"):
            continue
        app_id = str(app.get("id") or "")
        access_mode = str(app.get("access_mode") or "public")
        cta_mode = str(app.get("cta_mode") or "auto")
        deployment = app.get("deployment") or {}
        target = deployment.get("healthcheck_url") or ""
        if not target and (access_mode == "public" or cta_mode == "open"):
            target = app.get("default_url") or ""
        if not target:
            continue

        result = fetch(target, follow_redirects=False)
        status = int(result["status"])
        location = result["location"] or ""
        effective = result
        if status in {301, 302, 303, 307, 308} and location and not looks_like_sso(location):
            effective = fetch(target, follow_redirects=True)
        effective_status = int(effective["status"])
        effective_url = effective["url"] or target

        if access_mode == "public" or cta_mode == "open":
            expect(
                200 <= effective_status < 400,
                f"{app_id} public endpoint {target} returned {effective_status or result.get('error', 'unreachable')}",
                issues,
            )
            expect(
                "/yunohost/sso" not in effective_url and not looks_like_sso(location),
                f"{app_id} public endpoint {target} must not redirect to YunoHost SSO",
                issues,
            )
        else:
            expect(
                effective_status == 200 or looks_like_sso(location) or "/yunohost/sso" in effective_url,
                f"{app_id} restricted endpoint {target} must return 200 or redirect to YunoHost SSO (got {effective_status or result.get('error', 'unreachable')})",
                issues,
            )

    return issues


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expect-studio", action="store_true")
    args = parser.parse_args(argv)

    issues = []
    issues.extend(core_checks(args.expect_studio))
    issues.extend(app_checks())

    if issues:
        print("Public stack audit failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("Public stack audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
