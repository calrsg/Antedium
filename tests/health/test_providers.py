"""Provider Health Checks for each handler's current provider, for local runs.

    HEALTH_PROBE_WEBHOOK_URL=... pytest -m network

The scheduled workflow runs tests.health.report instead, which also checks
Candidate Providers and sends the alert.
"""
import os

import aiohttp
import pytest

from tests.health.canaries import CANARIES, KNOWN_OUTAGES
from tests.health.probe import WebhookProbe, check_canary

PROBE_URL = os.environ.get("HEALTH_PROBE_WEBHOOK_URL")

pytestmark = [
    pytest.mark.network,
    pytest.mark.skipif(not PROBE_URL, reason="HEALTH_PROBE_WEBHOOK_URL is not set"),
]


@pytest.mark.parametrize("canary", CANARIES, ids=lambda c: f"{c.kind}-{c.source}")
async def test_current_provider_embeds(canary):
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
        [result] = await check_canary(WebhookProbe(session, PROBE_URL), canary, candidates=False)
    if not result.ok and result.provider in KNOWN_OUTAGES:
        pytest.xfail(f"known outage: {KNOWN_OUTAGES[result.provider]}")
    assert result.ok, f"{result.provider}: {result.detail}"
