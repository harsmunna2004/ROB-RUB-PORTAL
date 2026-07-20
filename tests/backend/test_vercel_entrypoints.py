from importlib import import_module

from api.index import app


def test_every_public_api_route_has_a_vercel_function_entrypoint():
    for route in ("health", "ros", "pius", "projects", "mappings"):
        module = import_module(f"api.{route}")
        assert module.app is app
