from importlib import import_module
from pathlib import Path

from backend.app import app


def test_every_public_api_route_has_a_vercel_function_entrypoint():
    for route in ("health", "ros", "pius", "projects", "mappings", "dashboard"):
        module = import_module(f"api.{route}")
        assert module.app is app


def test_nested_vercel_routes_have_physical_entrypoints():
    root = Path(__file__).parents[2]
    for path in (
        "api/rob-rubs.py",
        "api/rob-rubs/filters.py",
        "api/dashboard.csv.py",
    ):
        assert (root / path).is_file(), path


def test_hobby_deployment_has_at_most_twelve_python_functions():
    root = Path(__file__).parents[2]
    function_files = list((root / "api").rglob("*.py"))
    assert len(function_files) <= 12, [str(path.relative_to(root)) for path in function_files]
