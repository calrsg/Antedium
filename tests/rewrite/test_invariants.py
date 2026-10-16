"""Shape Rewrite Checks: every seed Source Link, posted in every message shape,
must produce exactly one well formed Fixed Link."""
import pytest

from tests.rewrite.support import CASE_MODULES, check_fixed_link, fixed_links

# Ways people post a link. Each takes the source link and returns a message.
SHAPES = {
    "bare": lambda url: url,
    "in-sentence": lambda url: f"look at this {url} lol",
    "on-own-line": lambda url: f"look at this\n{url}\nlol",
    "end-of-sentence": lambda url: f"look at this {url}.",
    "parenthesised": lambda url: f"look at this ({url})",
    "spoiler": lambda url: f"||{url}||",
    "no-embed": lambda url: f"<{url}>",
    "http": lambda url: url.replace("https://", "http://", 1),
    "query": lambda url: url + ("&" if "?" in url else "?") + "utm_source=share",
}

TRAILING_PUNCTUATION = "Punctuation straight after a link is captured into the fixed link (#11)"

# Shapes that hit a known bug: shape -> (bug, handlers it affects)
BUGGY_SHAPES = {
    "end-of-sentence": (TRAILING_PUNCTUATION, {"TwitterLink", "InstagramLink", "TiktokLink"}),
    "parenthesised": (TRAILING_PUNCTUATION, {"TwitterLink", "InstagramLink", "TiktokLink"}),
}


def params():
    out = []
    for module in CASE_MODULES:
        for seed in module.SEEDS:
            for name, shape in SHAPES.items():
                bug, affected = BUGGY_SHAPES.get(name, (None, set()))
                marks = [pytest.mark.xfail(reason=bug, strict=True)] if module.HANDLER.__name__ in affected else []
                out.append(pytest.param(module.HANDLER(), seed, shape(seed.source),
                                        id=f"{module.HANDLER.__name__}-{seed.source}-{name}", marks=marks))
    return out


@pytest.mark.parametrize("handler, seed, message", params())
async def test_one_well_formed_link(handler, seed, message):
    links = await fixed_links(message)
    assert len(links) == 1, f"expected one fixed link, got {links}"
    check_fixed_link(links[0], handler, seed.post_id)
