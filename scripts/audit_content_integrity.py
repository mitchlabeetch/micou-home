#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path


LANGS = ("fr", "en", "de", "es")
ROOT = Path("/home/micou_org")
CATALOG_PATH = ROOT / "catalog.json"
CONTENT_PATH = ROOT / "site_content.json"
INDEX_PATH = ROOT / "index.html"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def app_meta_ids(index_text: str) -> set[str]:
    return set(re.findall(r"^\s+([a-z0-9_-]+): \{ badge:", index_text, flags=re.MULTILINE))


def nonempty(value) -> bool:
    return bool(str(value or "").strip())


def require_translations(issues: list[str], owner: str, value):
    if not isinstance(value, dict):
        issues.append(f"{owner} must be a translation object for {LANGS}")
        return
    for lang in LANGS:
        if not nonempty(value.get(lang)):
            issues.append(f"{owner}.{lang} is missing")


def main() -> int:
    issues: list[str] = []
    catalog = load_json(CATALOG_PATH)
    content = load_json(CONTENT_PATH)
    index_text = INDEX_PATH.read_text(encoding="utf-8")
    curated_ids = app_meta_ids(index_text)

    homepage = content.get("homepage", {})
    hero = homepage.get("hero", {})
    for lang in LANGS:
        block = hero.get(lang)
        if not isinstance(block, dict):
            issues.append(f"site_content.homepage.hero.{lang} must be an object")
            continue
        if not nonempty(block.get("title")):
            issues.append(f"site_content.homepage.hero.{lang}.title is missing")
        if not nonempty(block.get("tagline")):
            issues.append(f"site_content.homepage.hero.{lang}.tagline is missing")

    categories = catalog.get("categories", {})
    for category_id, category in categories.items():
        require_translations(issues, f"catalog.categories.{category_id}.name", category.get("name"))

    apps = catalog.get("apps", [])
    seen_ids: set[str] = set()
    for app in apps:
        app_id = str(app.get("id") or "").strip()
        if not app_id:
            issues.append("catalog.apps entry missing id")
            continue
        if app_id in seen_ids:
            issues.append(f"catalog.apps contains duplicate id {app_id}")
        seen_ids.add(app_id)

        if app.get("show_on_homepage") and app_id not in curated_ids:
            issues.append(f"homepage-visible app {app_id} is missing a curated APP_META entry in index.html")

    expected = {
        "wallos": ("show_on_homepage", False),
        "bentopdf": ("default_url", "https://micou.org/pdf/"),
        "nitter": ("default_url", "https://y.micou.org/about"),
    }
    by_id = {str(app.get("id")): app for app in apps}
    for app_id, (field, expected_value) in expected.items():
        app = by_id.get(app_id)
        if not app:
            issues.append(f"catalog is missing required app {app_id}")
            continue
        if app.get(field) != expected_value:
            issues.append(f"catalog.{app_id}.{field} must be {expected_value!r}")

    pages = content.get("pages", [])
    page_ids: set[str] = set()
    for page in pages:
        page_id = str(page.get("id") or "").strip()
        if not page_id:
            issues.append("site_content.pages entry missing id")
            continue
        if page_id in page_ids:
            issues.append(f"site_content.pages contains duplicate id {page_id}")
        page_ids.add(page_id)
        for field in ("title", "path", "editor", "visibility"):
            if not nonempty(page.get(field)):
                issues.append(f"site_content.pages.{page_id}.{field} is missing")

    if issues:
        print("Content integrity audit failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("Content integrity audit passed.")
    print(f"Curated homepage app metadata: {len(curated_ids)} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
