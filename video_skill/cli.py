from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .workflow import build_prompt, idempotency_key, validate_plan


def _load(path: str) -> dict:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"无法读取 JSON: {exc}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="video-skill")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "build-prompt"):
        command = sub.add_parser(name)
        command.add_argument("plan")
    args = parser.parse_args(argv)
    try:
        plan = validate_plan(_load(args.plan))
    except ValueError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2
    if args.command == "validate":
        print(json.dumps({"valid": True, "references": len(plan.references), "idempotency_key": idempotency_key(plan)}, ensure_ascii=False, indent=2))
    else:
        print(build_prompt(plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
