from __future__ import annotations

import json
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Iterable


_ALLOWED_MATURITY = {
    "architectural",
    "documented",
    "designed",
    "built",
    "tested",
    "operational",
    "candidate",
    "planned",
    "historical",
    "recovery-pending",
}

_ALLOWED_REPO_STATUS = {"placeholder", "migrating", "canonical", "retired"}


@dataclass(frozen=True)
class Capability:
    id: str
    name: str
    owner: str
    kind: str
    maturity: str
    repo_status: str
    path: str | None
    note: str


def _registry_path() -> Path:
    return Path(str(files("basil.data").joinpath("capabilities.json")))


def _load_registry_document() -> dict:
    raw = json.loads(_registry_path().read_text(encoding="utf-8"))
    if not isinstance(raw.get("schema_version"), int):
        raise ValueError("registry schema_version must be an integer")
    if not isinstance(raw.get("capabilities"), list):
        raise ValueError("registry capabilities must be a list")
    return raw


def registry_schema_version() -> int:
    return int(_load_registry_document()["schema_version"])


def load_capabilities() -> list[Capability]:
    raw = _load_registry_document()
    items = [Capability(**item) for item in raw["capabilities"]]
    validate_capabilities(items)
    return items


def get_capability(capability_id: str) -> Capability:
    target = capability_id.strip().casefold()
    for item in load_capabilities():
        if item.id.casefold() == target:
            return item
    raise KeyError(capability_id)


def validate_capabilities(items: Iterable[Capability]) -> None:
    seen: set[str] = set()
    for item in items:
        if item.id in seen:
            raise ValueError(f"duplicate capability id: {item.id}")
        seen.add(item.id)
        if item.maturity not in _ALLOWED_MATURITY:
            raise ValueError(f"invalid maturity for {item.id}: {item.maturity}")
        if item.repo_status not in _ALLOWED_REPO_STATUS:
            raise ValueError(f"invalid repo status for {item.id}: {item.repo_status}")
        if not item.owner.strip():
            raise ValueError(f"missing owner for {item.id}")


def filter_capabilities(*, owner: str | None = None, maturity: str | None = None, repo_status: str | None = None) -> list[Capability]:
    items = load_capabilities()
    if owner:
        items = [x for x in items if x.owner.lower() == owner.lower()]
    if maturity:
        items = [x for x in items if x.maturity.lower() == maturity.lower()]
    if repo_status:
        items = [x for x in items if x.repo_status.lower() == repo_status.lower()]
    return items
