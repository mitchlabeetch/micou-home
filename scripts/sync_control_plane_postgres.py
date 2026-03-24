#!/usr/bin/env python3

import argparse
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import forms_service  # noqa: E402
from control_plane_postgres import sync_snapshot_to_postgres  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync micou control-plane state into PostgreSQL.")
    parser.add_argument("--dsn", default=os.environ.get("MICOU_DATABASE_URL") or os.environ.get("DATABASE_URL") or "", help="PostgreSQL DSN")
    parser.add_argument("--trigger", default="manual", help="Sync trigger name")
    parser.add_argument("--actor", default="", help="Actor identity for the sync run")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    if not args.dsn.strip():
        print(json.dumps({"ok": False, "status": "error", "error": "dsn_required"}))
        return 2

    snapshot = forms_service._build_postgres_sync_snapshot(trigger_name=args.trigger, actor_key=args.actor)  # noqa: SLF001
    result = sync_snapshot_to_postgres(args.dsn, snapshot, trigger_name=args.trigger, actor_key=args.actor)
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
