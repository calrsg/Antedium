"""Rewrite Checks that already-fixed links are skipped by their host, not just
because a handler's pattern happens not to match them."""
from linkhandlers.rewrite import rewrite
from linkhandlers.twitterlink import TwitterLink
from tests.rewrite.support import check_fixed_link


class GreedyTwitterLink(TwitterLink):
    """A Twitter handler whose pattern also matches Embed Provider hosts."""

    @property
    def pattern(self) -> str:
        return r"(https?:\/\/)([a-z]*twitter\.com\/\S*)"


async def fixed_links(message):
    results = await rewrite(message, [GreedyTwitterLink()])
    return [link for result in results for link in result.links]


async def test_already_fixed_link_is_not_refixed():
    assert await fixed_links("https://fxtwitter.com/a/status/1") == []


async def test_already_fixed_link_beside_source_link():
    links = await fixed_links("https://vxtwitter.com/a/status/1 https://twitter.com/b/status/2")
    assert links == ["https://fxtwitter.com/b/status/2"]
    check_fixed_link(links[0], GreedyTwitterLink())
