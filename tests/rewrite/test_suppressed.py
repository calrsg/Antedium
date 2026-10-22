"""Rewrite Checks that Suppressed Links are left alone, while the other links
in the same message are still fixed."""
import pytest

from tests.rewrite.support import all_seeds, fixed_links


@pytest.mark.parametrize("source", [
    pytest.param(seed.source, id=f"{module.HANDLER.__name__}-{seed.source}")
    for module, seed in all_seeds()
])
async def test_suppressed_seed_is_not_fixed(source):
    assert await fixed_links(f"<{source}>") == []


@pytest.mark.parametrize("message", [
    "<https://x.com/a/status/1>",
    "||<https://x.com/a/status/1>||",
    "[a post](<https://x.com/a/status/1>)",
    "<https://x.com/a/status/1.>",
    # Discord suppresses the whole URL, even where a handler's pattern stops
    # matching before its end
    "<https://x.com/a/status/1/>",
    "<https://x.com/a/status/1/video/1>",
    "<https://x.com/a/status/1!>",
    "<https://www.instagram.com/p/abc,d/>",
    "<https://www.tiktok.com/@u/video/1?x=a,b>",
    "<https://pin.it/abc123/>",
    "<https://pin.it/abc123?x=1>",
    "<https://example.com/?u=https://x.com/a/status/1>",
])
async def test_suppressed_link_is_not_fixed(message):
    assert await fixed_links(message) == []


@pytest.mark.parametrize("message, expected", [
    ("<https://x.com/a/status/1> https://x.com/b/status/2", ["https://fxtwitter.com/b/status/2"]),
    ("<https://www.instagram.com/p/A/> https://x.com/b/status/2", ["https://fxtwitter.com/b/status/2"]),
    ("<https://www.tiktok.com/@u/video/1> https://x.com/b/status/2", ["https://fxtwitter.com/b/status/2"]),
    ("<https://pin.it/abc123> https://x.com/b/status/2", ["https://fxtwitter.com/b/status/2"]),
])
async def test_suppressed_link_beside_source_link(message, expected):
    assert await fixed_links(message) == expected


async def test_same_link_suppressed_and_bare_is_fixed_once():
    links = await fixed_links("<https://x.com/a/status/1> https://x.com/a/status/1")
    assert links == ["https://fxtwitter.com/a/status/1"]


@pytest.mark.parametrize("message", [
    "< https://x.com/a/status/1 >",
    "<https://x.com/a/status/1",
    "https://x.com/a/status/1>",
    "<https://x.com/a/status/1 >",
])
async def test_half_suppressed_link_is_still_fixed(message):
    assert await fixed_links(message) == ["https://fxtwitter.com/a/status/1"]
