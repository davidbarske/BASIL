from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .registry import load_capabilities


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str


def find_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "pyproject.toml").exists() and (candidate / "AGENTS.md").exists():
            return candidate
    # Installed-package fallback: this is diagnostic, not proof of a git checkout.
    return Path(__file__).resolve().parents[2]


def run_doctor(root: Path | None = None) -> list[Check]:
    repo = find_repo_root(root)
    checks: list[Check] = []
    required = [
        "README.md",
        "AGENTS.md",
        "docs/architecture/CURRENT_ARCHITECTURE.md",
        "docs/governance/AUTHORITY_AND_EVIDENCE.md",
        "docs/repository/GITHUB_AND_DRIVE.md",
        "THIRD_PARTY_NOTICES.md",
    ]
    for rel in required:
        path = repo / rel
        checks.append(Check(rel, path.exists(), "present" if path.exists() else "missing"))

    try:
        capabilities = load_capabilities()
        checks.append(Check("capability registry", True, f"{len(capabilities)} entries validated"))
    except Exception as exc:  # diagnostic surface: report rather than hide
        checks.append(Check("capability registry", False, f"{type(exc).__name__}: {exc}"))
        return checks

    for cap in capabilities:
        if cap.path:
            path = repo / cap.path
            checks.append(Check(f"capability:{cap.id}", path.exists(), cap.path if path.exists() else f"missing {cap.path}"))

    return checks


def healthy(checks: list[Check]) -> bool:
    return all(c.passed for c in checks)
