"""Rewrite Checks that Suppressed Links are left alone, while the other links
in the same message are still fixed."""
import pytest

from tests.rewrite.support import CASE_MODULES, fixed_links


@pytest.mark.parametrize("source", [
    pytest.param(seed.source, id=f"{module.HANDLER.__name__}-{seed.source}")
    for module in CASE_MODULES for seed in module.SEEDS
])
async def test_suppressed_seed_is_not_fixed(source):
    assert await fixed_links(f"<{source}>") == []


@pytest.mark.parametrize("message", [
    "<https://x.com/a/status/1>",
    "||<https://x.com/a/status/1>||",
    "[a post](<https://x.com/a/status/1>)",
    "<https://x.com/a/status/1.>",
    "<https://www.instagram.com/p/abc/>",
])
async def test_suppressed_link_is_not_fixed(message):
    assert await fixed_links(message) == []


async def test_suppressed_link_beside_source_link():
    links = await fixed_links("<https://x.com/a/status/1> https://x.com/b/status/2")
    assert links == ["https://fxtwitter.com/b/status/2"]


async def test_same_link_suppressed_and_bare_is_fixed_once():
    links = await fixed_links("<https://x.com/a/status/1> https://x.com/a/status/1")
    assert links == ["https://fxtwitter.com/a/status/1"]


@pytest.mark.parametrize("message", [
    "< https://x.com/a/status/1 >",
    "<https://x.com/a/status/1",
    "https://x.com/a/status/1>",
])
async def test_half_suppressed_link_is_still_fixed(message):
    assert await fixed_links(message) == ["https://fxtwitter.com/a/status/1"]
