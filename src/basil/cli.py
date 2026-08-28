from __future__ import annotations

import argparse
import json

from . import __version__
from .doctor import healthy, run_doctor
from .priority import classify_priority
from .registry import filter_capabilities


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="basil", description="Project BASIL executable core")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("priority", help="classify Importance × Urgency using the current BASIL 3×3 matrix")
    p.add_argument("importance", type=int, help="importance score, 1–10")
    p.add_argument("urgency", type=int, help="urgency score, 1–10")
    p.add_argument("--json", action="store_true", dest="as_json")

    p = sub.add_parser("capabilities", help="list registered BASIL capabilities, maturity and repository migration state")
    p.add_argument("--owner")
    p.add_argument("--maturity")
    p.add_argument("--repo-status", choices=["placeholder", "migrating", "canonical", "retired"])
    p.add_argument("--json", action="store_true", dest="as_json")

    sub.add_parser("doctor", help="verify repository structure and registered local artefacts")
    sub.add_parser("version", help="print BASIL core version")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "priority":
        result = classify_priority(args.importance, args.urgency)
        data = {
            "importance_score": result.importance_score,
            "importance": result.importance.value,
            "urgency_score": result.urgency_score,
            "urgency": result.urgency.value,
            "matrix_priority": result.matrix_priority,
        }
        if args.as_json:
            print(json.dumps(data, indent=2))
        else:
            print(f"Importance: {data['importance']} ({data['importance_score']}/10)")
            print(f"Urgency: {data['urgency']} ({data['urgency_score']}/10)")
            print(f"Matrix priority: {data['matrix_priority']}")
        return 0

    if args.command == "capabilities":
        items = filter_capabilities(owner=args.owner, maturity=args.maturity, repo_status=args.repo_status)
        if args.as_json:
            print(json.dumps([x.__dict__ for x in items], indent=2))
        else:
            for x in items:
                print(f"{x.id:42} {x.owner:10} {x.maturity:16} {x.repo_status:12} {x.name}")
        return 0

    if args.command == "doctor":
        checks = run_doctor()
        for check in checks:
            print(f"{'PASS' if check.passed else 'FAIL'}  {check.name} — {check.detail}")
        return 0 if healthy(checks) else 1

    if args.command == "version":
        print(__version__)
        return 0

    return 2
