"""Exact Rewrite Checks: each case's message must produce exactly its Fixed Links."""
import pytest

from tests.rewrite.support import case_params, check_fixed_link, fixed_links


@pytest.mark.parametrize("case", case_params(lambda module, case: (case,)))
async def test_rewrite(case):
    assert await fixed_links(case.message) == case.expected


@pytest.mark.parametrize("handler, case", case_params(lambda module, case: (module.HANDLER(), case), mark_bugs=False))
def test_expected_links_are_well_formed(handler, case):
    """Guards the case tables themselves against typos in expected output."""
    for link in case.expected:
        check_fixed_link(link, handler)
