import pytest

from linkhandlers.pinterestlink import PinterestLink
from tests.rewrite.cases.pinterest import PIN_IT


@pytest.fixture(autouse=True)
def offline_pin_it(monkeypatch):
    """Resolve pin.it links from a table instead of asking Pinterest."""
    async def expand(self, url):
        return PIN_IT.get(url.rstrip("/").rsplit("/", 1)[-1])

    monkeypatch.setattr(PinterestLink, "expand", expand)
