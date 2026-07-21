from importlib import import_module
from pathlib import Path

from api.index import app


def test_every_public_api_route_has_a_vercel_function_entrypoint():
    for route in ("health", "ros", "pius", "projects", "mappings", "rob_rubs", "dashboard"):
        module = import_module(f"api.{route}")
        assert module.app is app


def test_nested_vercel_routes_have_physical_entrypoints():
    root = Path(__file__).parents[2]
    for path in (
        "api/rob-rubs.py",
        "api/rob-rubs/filters.py",
        "api/projects/[upc].py",
        "api/projects/[upc]/certification.py",
        "api/dashboard.csv.py",
    ):
        assert (root / path).is_file(), path
