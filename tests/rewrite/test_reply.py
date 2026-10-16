"""Rewrite Checks for the reply text built from a message's Fixed Links."""
from linkhandlers.rewrite import INVITE_FOOTER, build_reply, default_handlers, rewrite


async def test_single_link():
    results = await rewrite("https://x.com/user/status/123", default_handlers())
    assert build_reply(results) == "https://fxtwitter.com/user/status/123\n" + INVITE_FOOTER


async def test_links_from_one_handler_share_a_block():
    results = await rewrite("https://x.com/a/status/1 https://x.com/b/status/2", default_handlers())
    assert build_reply(results) == (
        "https://fxtwitter.com/a/status/1\n"
        "https://fxtwitter.com/b/status/2\n"
        + INVITE_FOOTER
    )


async def test_handlers_are_listed_in_reverse_with_a_gap_between():
    results = await rewrite("https://x.com/a/status/1 https://www.instagram.com/p/ABC/", default_handlers())
    assert build_reply(results) == (
        "https://oginstagram.com/p/ABC/\n"
        "\n"
        "https://fxtwitter.com/a/status/1\n"
        + INVITE_FOOTER
    )


async def test_nothing_to_fix():
    assert await rewrite("no links here", default_handlers()) == []
