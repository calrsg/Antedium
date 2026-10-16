import asyncio
import time
from dataclasses import dataclass
from typing import List, Optional, Set, Tuple

import aiohttp

from linkhandlers.linkinterface import LinkInterface
from linkhandlers.rewrite import default_handlers, find_fixable_handlers, rewrite
from tests.health.canaries import Canary

# Discord unfurls links a few seconds after the message is posted
EMBED_WAIT = 15
POLL_INTERVAL = 2
# Current providers get retries before alerting, candidates are only reported
ATTEMPTS = 3
BACKOFF = 10
# Discord component type for a media gallery
MEDIA_GALLERY = 12
# Post without pinging anyone in the probe channel
SUPPRESS_NOTIFICATIONS = 1 << 12


@dataclass
class Result:
    canary: Canary
    handler: str
    provider: str
    active: bool
    ok: bool
    detail: str


class WebhookProbe:
    """Posts links through a Discord webhook and reads back the embeds."""

    def __init__(self, session: aiohttp.ClientSession, webhook_url: str):
        self.session = session
        self.url = webhook_url.rstrip("/")

    async def request(self, method: str, url: str, **kwargs):
        """Make a webhook request, waiting out rate limits."""
        while True:
            async with self.session.request(method, url, **kwargs) as response:
                if response.status == 429:
                    await asyncio.sleep((await response.json()).get("retry_after", 1))
                    continue
                response.raise_for_status()
                return await response.json() if response.status != 204 else None

    async def embeds_for(self, link: str) -> List[dict]:
        """Post a link and return the embeds Discord attaches to it."""
        message = await self.request("POST", f"{self.url}?wait=true", json={
            "content": link,
            "flags": SUPPRESS_NOTIFICATIONS,
            "allowed_mentions": {"parse": []},
        })
        try:
            deadline = time.monotonic() + EMBED_WAIT
            embeds = message.get("embeds", [])
            while not embeds and time.monotonic() < deadline:
                await asyncio.sleep(POLL_INTERVAL)
                embeds = (await self.request("GET", f"{self.url}/messages/{message['id']}")).get("embeds", [])
            return embeds
        finally:
            await self.request("DELETE", f"{self.url}/messages/{message['id']}")


def gallery_media(component: dict) -> Set[str]:
    """Media kinds in the media galleries of a components style embed."""
    kinds = set()
    if component.get("type") == MEDIA_GALLERY:
        for item in component.get("items", []):
            kinds.add(item.get("media", {}).get("content_type", "").split("/")[0])
    for child in component.get("components", []):
        kinds |= gallery_media(child)
    return kinds


def media_kinds(embed: dict) -> Set[str]:
    """Media kinds ("image", "video") an embed shows."""
    if embed.get("type") == "components":
        # The section thumbnail is the poster's avatar, so only galleries count
        return set().union(*(gallery_media(c) for c in embed.get("components", [])))
    kinds = {"image"} if "image" in embed or "thumbnail" in embed else set()
    return kinds | ({"video"} if "video" in embed else set())


def judge(embeds: List[dict], kind: str) -> Optional[str]:
    """Return why the embeds are not a Working Embed, or None if they are."""
    if not embeds:
        return "no embed"
    kinds = set().union(*(media_kinds(embed) for embed in embeds))
    if kind == "video" and "video" not in kinds:
        return f"embed has no video: {describe(embeds)}"
    if not kinds:
        return f"embed has no image: {describe(embeds)}"
    return None


def describe(embeds: List[dict]) -> str:
    """Name what Discord did show, usually the provider's error title."""
    embed = embeds[0]
    return embed.get("title") or embed.get("description", "")[:80] or embed.get("type", "unknown")


def cache_bust(link: str) -> str:
    """Make the link unique so Discord cannot answer from its embed cache."""
    return f"{link}{'&' if '?' in link else '?'}_={int(time.time() * 1000)}"


async def fixed_link_for(canary: Canary) -> Tuple[LinkInterface, Optional[str]]:
    """Run a canary through the real Rewrite, network lookups included."""
    handler = find_fixable_handlers(canary.source, default_handlers())[0]
    results = await rewrite(canary.source, [handler])
    return handler, results[0].links[0] if results else None


async def check_provider(probe: WebhookProbe, canary: Canary, handler: LinkInterface,
                         fixed: str, provider: str) -> Result:
    link = fixed.replace(handler.link, provider, 1)
    active = provider == handler.link
    detail = "unchecked"
    for attempt in range(ATTEMPTS if active else 1):
        if attempt:
            await asyncio.sleep(BACKOFF * attempt)
        try:
            detail = judge(await probe.embeds_for(cache_bust(link)), canary.kind)
        except aiohttp.ClientError as e:
            detail = f"webhook error: {e}"
        if detail is None:
            return Result(canary, handler.name, provider, active, True, "ok")
    return Result(canary, handler.name, provider, active, False, detail)


async def check_canary(probe: WebhookProbe, canary: Canary, candidates: bool = True) -> List[Result]:
    """Check a canary on its handler's current provider and, optionally, its candidates."""
    handler, fixed = await fixed_link_for(canary)
    if fixed is None:
        return [Result(canary, handler.name, handler.link, True, False, "source link did not rewrite")]
    providers = handler.candidates if candidates else [handler.link]
    # The current provider always comes first so its result is the headline
    providers = [handler.link] + [p for p in providers if p != handler.link]
    return [await check_provider(probe, canary, handler, fixed, provider) for provider in providers]
