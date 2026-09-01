from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .renderers.seedance import SeedanceRenderer
from .workflow import build_prompt, idempotency_key, to_render_request, validate_plan


def _load(path: str) -> dict:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"无法读取 JSON: {exc}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="video-skill")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "build-prompt", "render"):
        command = sub.add_parser(name)
        command.add_argument("plan")
        if name == "render":
            command.add_argument("--output-dir", default="./video-output")
            command.add_argument("--base-url", default=None)
    args = parser.parse_args(argv)
    try:
        plan = validate_plan(_load(args.plan))
    except ValueError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2
    if args.command == "validate":
        print(json.dumps({"valid": True, "references": len(plan.references), "idempotency_key": idempotency_key(plan)}, ensure_ascii=False, indent=2))
    elif args.command == "build-prompt":
        print(build_prompt(plan))
    else:
        renderer = SeedanceRenderer(base_url=args.base_url, output_dir=args.output_dir)
        try:
            artifact = renderer.wait(renderer.create(to_render_request(plan)))
        except Exception as exc:  # provider errors are rendered as a concise CLI failure
            print(f"RENDER_FAILED: {exc}", file=sys.stderr)
            return 3
        print(json.dumps({"task_id": artifact.task_id, "path": str(artifact.path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
