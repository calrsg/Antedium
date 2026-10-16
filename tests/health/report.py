"""Run every Provider Health Check and alert if a current provider is down.

    python -m tests.health.report

Reads HEALTH_PROBE_WEBHOOK_URL (where links are posted to see if they embed)
and, optionally, HEALTH_WEBHOOK_URL (where alerts go). Exits non-zero if any
handler's current provider failed; Candidate Providers are only reported.
"""
import asyncio
import os
import sys
from itertools import groupby
from typing import List

import aiohttp

from tests.health.canaries import CANARIES
from tests.health.probe import Result, WebhookProbe, check_canary

# Discord rejects messages longer than this
MESSAGE_LIMIT = 2000


def table(results: List[Result]) -> str:
    lines = []
    for handler, group in groupby(results, key=lambda r: r.handler):
        lines.append(f"**{handler}**")
        for r in group:
            mark = "✅" if r.ok else "❌"
            current = " (current)" if r.active else ""
            lines.append(f"{mark} `{r.provider}`{current} {r.canary.kind}: {r.detail} <{r.canary.source}>")
    return "\n".join(lines)


async def alert(session: aiohttp.ClientSession, webhook_url: str, results: List[Result]):
    down = sorted({r.provider for r in results if r.active and not r.ok})
    # Show every provider for the handlers that need a new one
    handlers = {r.handler for r in results if r.active and not r.ok}
    body = f"Embed provider down: {', '.join(down)}\n" + table([r for r in results if r.handler in handlers])
    if len(body) > MESSAGE_LIMIT:
        body = body[:MESSAGE_LIMIT - 1] + "…"
    async with session.post(webhook_url, json={"content": body, "allowed_mentions": {"parse": []}}) as response:
        response.raise_for_status()


async def main() -> int:
    probe_url = os.environ["HEALTH_PROBE_WEBHOOK_URL"]
    alert_url = os.environ.get("HEALTH_WEBHOOK_URL")
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        probe = WebhookProbe(session, probe_url)
        results = []
        for canary in CANARIES:
            results += await check_canary(probe, canary)
        results.sort(key=lambda r: r.handler)

        print(table(results))
        if all(r.ok for r in results if r.active):
            return 0
        if alert_url:
            await alert(session, alert_url, results)
        return 1


if __name__ == "__main__":
    # The table has emoji, which a Windows console cannot encode by default
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(asyncio.run(main()))
