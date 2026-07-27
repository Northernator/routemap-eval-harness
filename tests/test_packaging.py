from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def test_public_package_metadata_and_extras_are_declared() -> None:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = config["project"]

    assert project["version"] == "0.1.0"
    assert project["readme"] == "README.md"
    assert project["dependencies"] == ["numpy>=1.24,<3"]
    assert set(project["optional-dependencies"]) == {"api", "benchmark", "dev", "matrix"}
    assert project["scripts"]["routemap-harness"] == "routemap_harness.__main__:main"


def test_bundled_schema_matches_canonical_schema() -> None:
    canonical = ROOT / "schemas" / "harness_decision_v1.schema.json"
    bundled = ROOT / "src" / "routemap_harness" / "schemas" / canonical.name

    assert json.loads(bundled.read_text(encoding="utf-8")) == json.loads(
        canonical.read_text(encoding="utf-8")
    )


def test_runtime_package_data_is_declared() -> None:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    package_data = config["tool"]["setuptools"]["package-data"]["routemap_harness"]
    legacy_modules = set(config["tool"]["setuptools"]["py-modules"])

    assert package_data == ["schemas/*.json", "web/*.html"]
    assert legacy_modules == {
        "dr_checker_code_v1",
        "dr_checker_framework_v1",
        "dr_checker_schema_v1",
        "dr_generate_corpus_v1",
        "dr_output_extraction_v1",
        "dr_repair_wrapper_v1",
        "dr_residue_engine_v1",
        "dr_verifier_v1",
        "llm_output_parsing",
    }
    assert (ROOT / "src" / "routemap_harness" / "web" / "app.html").is_file()


def test_package_imports_do_not_depend_on_unshipped_top_level_modules() -> None:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    shipped_modules = set(config["tool"]["setuptools"]["py-modules"])
    source_root = ROOT / "src"
    root_modules = {path.stem for path in source_root.glob("*.py")}
    package_files = {
        path
        for package_init in source_root.glob("*/__init__.py")
        for path in package_init.parent.rglob("*.py")
    }
    package_files.update(source_root / f"{module}.py" for module in shipped_modules)

    referenced_modules: set[str] = set()
    for path in package_files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = {alias.name.partition(".")[0] for alias in node.names}
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                imported = {node.module.partition(".")[0]}
            else:
                continue
            referenced_modules.update(imported & root_modules)

    assert referenced_modules <= shipped_modules
