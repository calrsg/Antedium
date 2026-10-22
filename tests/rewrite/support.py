from typing import List, Optional
from urllib.parse import urlsplit

import pytest

from linkhandlers.linkinterface import LinkInterface
from linkhandlers.rewrite import default_handlers, rewrite
from tests.rewrite.cases import instagram, pinterest, tiktok, twitter

CASE_MODULES = [twitter, instagram, tiktok, pinterest]


async def fixed_links(message: str) -> List[str]:
    """Rewrite a message with the bot's handlers, flattened in reply order."""
    results = await rewrite(message, default_handlers())
    return [link for result in results for link in result.links]


def all_seeds():
    """Yield every module's seeds, paired with the module they come from."""
    for module in CASE_MODULES:
        for seed in module.SEEDS:
            yield module, seed


def case_params(build, mark_bugs: bool = True):
    """Turn every module's cases into pytest params, marking known bugs."""
    params = []
    for module in CASE_MODULES:
        for case in module.CASES:
            marks = [pytest.mark.xfail(reason=case.bug, strict=True)] if case.bug and mark_bugs else []
            params.append(pytest.param(*build(module, case), id=f"{module.HANDLER.__name__}-{case.id}", marks=marks))
    return params


def check_fixed_link(link: str, handler: LinkInterface, post_id: Optional[str] = None):
    """Assert a Fixed Link is well formed, whatever its exact text."""
    assert link.startswith("||") == link.endswith("||"), f"unbalanced spoiler: {link}"
    url = link.removeprefix("||").removesuffix("||")

    assert not any(c.isspace() for c in url), f"whitespace in link: {url!r}"
    assert url.count("://") == 1, f"expected exactly one scheme: {url}"
    scheme, rest = url.split("://")
    assert scheme in ("http", "https"), f"bad scheme: {url}"
    assert "//" not in rest, f"doubled slash: {url}"
    assert "\\" not in url, f"backslash: {url}"
    assert "|" not in url, f"stray spoiler bar: {url}"
    assert "www." not in url, f"www. left in: {url}"

    parts = urlsplit(url)
    host = parts.hostname or ""
    assert host == handler.link or host.endswith("." + handler.link), f"host {host} is not {handler.link}: {url}"
    if post_id is not None:
        assert post_id in parts.path, f"post id {post_id} lost: {url}"
    assert not parts.path.endswith((".", ",", ")", "!", "?")), f"trailing punctuation captured: {url}"
