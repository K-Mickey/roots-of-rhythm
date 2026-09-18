"""Architecture import-boundary guardrails for the modular monolith.

Static AST scan of ``backend/src`` (no new dependencies):

- R1: a bounded context or Discovery never imports infrastructure of a foreign context.
- R2: public readers import only their owning context (plus shared root helpers).
- R3: domain imports only its own context's domain (plus shared text length constants).
- R4: application never imports any context infrastructure.

Composition roots (``entrypoints``, ``seed``) are allowed to touch foreign infrastructure.

Bounded contexts are derived from the filesystem, not hard-coded: a top-level
directory is a context when it contains a ``domain/`` or ``infrastructure/``
subdirectory. Shared root modules (``application``, ``infrastructure``,
``presentation``) and composition roots are not contexts.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterable

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT = _PROJECT_ROOT / "src" / "roots_of_rhythm"

_COMPOSITION_ROOTS = frozenset({"entrypoints", "seed"})
_SHARED_ROOT_HELPERS = frozenset(
    {
        "roots_of_rhythm.application",
        "roots_of_rhythm.config",
        "roots_of_rhythm.infrastructure.service_columns",
        "roots_of_rhythm.utils",
    }
)
_DOMAIN_ALLOWED_ROOT = frozenset({"roots_of_rhythm.utils"})
_PACKAGE = "roots_of_rhythm"


def _contexts() -> frozenset[str]:
    found = {
        entry.name
        for entry in _SRC_ROOT.iterdir()
        if entry.is_dir() and ((entry / "domain").is_dir() or (entry / "infrastructure").is_dir())
    }
    return frozenset(found)


def _imports(path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append((node.lineno, node.module))
    return imports


def _violations(contexts: frozenset[str]) -> list[str]:
    problems: list[str] = []
    for file in _SRC_ROOT.rglob("*.py"):
        relative = file.relative_to(_SRC_ROOT)
        top_layer = relative.parts[0]
        own_context = next((part for part in relative.parts if part in contexts), None)
        own_layer = relative.parts[1] if own_context is not None else top_layer
        if top_layer in _COMPOSITION_ROOTS:
            continue
        for lineno, imported in _imports(file):
            if not imported.startswith(_PACKAGE):
                continue
            problem = _check(file, own_context, own_layer, lineno, imported, contexts)
            if problem:
                problems.append(problem)
    return problems


def _is_part_of(imported: str, roots: Iterable[str]) -> bool:
    return any(imported == root or imported.startswith(f"{root}.") for root in roots)


def _check(
    file: Path,
    own_context: str | None,
    own_layer: str,
    lineno: int,
    imported: str,
    contexts: frozenset[str],
) -> str | None:
    parts = imported.split(".")
    imported_context = parts[1] if len(parts) >= 2 and parts[1] in contexts else None
    layer = parts[2] if len(parts) >= 3 else None
    location = f"{file}:{lineno}: imports {imported}"

    if own_layer == "domain":
        if imported_context is None:
            if not _is_part_of(imported, _DOMAIN_ALLOWED_ROOT):
                return f"{location} — R3: domain imports non-context root module"
            return None
        if imported_context != own_context or layer != "domain":
            return f"{location} — R3: domain imports outside own context"
        return None

    if own_layer == "application":
        if imported_context is not None and layer == "infrastructure":
            return f"{location} — R4: application imports infrastructure of context {imported_context}"
        return None

    if (
        imported_context is not None
        and layer == "infrastructure"
        and (own_context != imported_context or own_layer != "infrastructure")
    ):
        return f"{location} — R1: {own_layer} imports infrastructure of context {imported_context}"

    if own_layer == "public":
        if imported_context is None:
            if not _is_part_of(imported, _SHARED_ROOT_HELPERS):
                return f"{location} — R2: public reader imports non-shared root module"
            return None
        if imported_context != own_context:
            return f"{location} — R2: public reader imports foreign context {imported_context}"

    return None


def test_import_boundaries() -> None:
    contexts = _contexts()
    problems = _violations(contexts)
    assert not problems, "Architecture import violations:\n" + "\n".join(problems)
