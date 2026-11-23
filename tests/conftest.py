"""Tests read fixtures and the local EDGAR cache. They do not open the network."""

import urllib.request

import pytest


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    def blocked(*args, **kwargs):
        raise RuntimeError("A test tried to use the network. Use the cache or a fixture.")

    monkeypatch.setattr(urllib.request, "urlopen", blocked)
