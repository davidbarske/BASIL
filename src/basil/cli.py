from __future__ import annotations

import argparse
import json
from collections import Counter

from . import __version__
from .doctor import healthy, run_doctor
from .priority import classify_priority
from .registry import filter_capabilities, get_capability, load_capabilities, registry_schema_version


REPOSITORY_AUTHORITY = "GitHub main is canonical for BASIL architecture, capability, build and implementation state."
ARCHITECTURE_PATH = "docs/architecture/CURRENT_ARCHITECTURE.md"
REGISTRY_PATH = "src/basil/data/capabilities.json"
CORE_FLOW = ("MANUEL", "BRIAN", "BASIL")
RETIRED_ARCHITECTURE = ("Logicators",)


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

    p = sub.add_parser("capability", help="show one registered BASIL capability by stable ID")
    p.add_argument("capability_id")
    p.add_argument("--json", action="store_true", dest="as_json")

    p = sub.add_parser("context", help="emit compact canonical BASIL orientation state")
    p.add_argument("--json", action="store_true", dest="as_json")

    sub.add_parser("doctor", help="verify repository structure and registered local artefacts")
    sub.add_parser("version", help="print BASIL core version")
    return parser


def _context_data() -> dict:
    items = load_capabilities()
    repo_counts = Counter(item.repo_status for item in items)
    maturity_counts = Counter(item.maturity for item in items)
    owners = sorted({item.owner for item in items})
    return {
        "project": "Project BASIL",
        "repository_authority": REPOSITORY_AUTHORITY,
        "architecture_path": ARCHITECTURE_PATH,
        "registry_path": REGISTRY_PATH,
        "registry_schema_version": registry_schema_version(),
        "core_flow": list(CORE_FLOW),
        "retired_architecture": list(RETIRED_ARCHITECTURE),
        "owners": owners,
        "capability_count": len(items),
        "repository_status_counts": dict(sorted(repo_counts.items())),
        "maturity_counts": dict(sorted(maturity_counts.items())),
        "open_migration_count": sum(1 for item in items if item.repo_status in {"placeholder", "migrating"}),
    }


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

    if args.command == "capability":
        try:
            item = get_capability(args.capability_id)
        except KeyError:
            print(f"Unknown capability: {args.capability_id}")
            return 1
        if args.as_json:
            print(json.dumps(item.__dict__, indent=2))
        else:
            print(f"ID: {item.id}")
            print(f"Name: {item.name}")
            print(f"Owner: {item.owner}")
            print(f"Kind: {item.kind}")
            print(f"Maturity: {item.maturity}")
            print(f"Repository status: {item.repo_status}")
            print(f"Path: {item.path or '-'}")
            print(f"Note: {item.note}")
        return 0

    if args.command == "context":
        data = _context_data()
        if args.as_json:
            print(json.dumps(data, indent=2))
        else:
            print(data["project"])
            print(data["repository_authority"])
            print(f"Core flow: {' → '.join(data['core_flow'])}")
            print(f"Architecture: {data['architecture_path']}")
            print(f"Registry: {data['registry_path']} (schema {data['registry_schema_version']})")
            print(f"Capabilities: {data['capability_count']}")
            print(f"Open migration entries: {data['open_migration_count']}")
            print("Repository states: " + ", ".join(f"{key}={value}" for key, value in data["repository_status_counts"].items()))
            print("Retired architecture: " + ", ".join(data["retired_architecture"]))
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
