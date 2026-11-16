"""The layers stay layered: dependencies only point inwards (api, services, domain).

A failing test here means a shortcut that would couple the business rules to
HTTP or to a framework. Fix the import, not the test.
"""

import ast
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parent.parent / "app"

# layer: imports it must never make
FORBIDDEN = {
    "domain": ("flask", "flask_openapi3", "app.api", "app.services", "app.cli", "app.infra"),
    "services": ("flask", "flask_openapi3", "app.api", "app.cli"),
}


def imports_of(path: Path) -> set[str]:
    package = "app." + ".".join(path.relative_to(APP).with_suffix("").parts[:-1])
    found = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:  # relative import: resolve it against the module's package
                base = package.rsplit(".", node.level - 1)[0] if node.level > 1 else package
                found.add(f"{base}.{node.module}" if node.module else base)
            elif node.module:
                found.add(node.module)
    return found


@pytest.mark.parametrize("layer", FORBIDDEN)
def test_layer_does_not_depend_on_outer_layers(layer):
    violations = [
        f"{path.relative_to(APP)} imports {name}"
        for path in sorted((APP / layer).glob("*.py"))
        for name in imports_of(path)
        if name.startswith(FORBIDDEN[layer])
    ]
    assert violations == []
