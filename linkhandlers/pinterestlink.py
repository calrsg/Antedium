import asyncio
import re
from typing import List, Optional

import aiohttp

from linkhandlers.linkinterface import LinkInterface

class PinterestLink(LinkInterface):
    """Class to handle Pinterest links.

    Pinterest links embed poorly. A pin.it short link is not expanded by Discord
    at all, so it does not embed, and a full pinterest.com link only embeds the
    small thumbnail Pinterest puts in its Open Graph tags. Both forms are
    rebuilt against pinterestez.com, which serves a large format image, with
    pin.it links resolved server side first to find the pin they point at.
    """

    # pin.it/<code> -> api.pinterest.com/url_shortener/<code>/redirect/ -> <geo>.pinterest.com/pin/<id>/sent/?invite_code=...
    SHORTENER = "pin.it"
    # Pin paths come as /pin/<id>/ or as /pin/<slug>--<id>/
    PIN_ID_PATTERN = re.compile(r"/pin/(?:[^/?#]*--)?(\d+)")
    # Pinterest serves a bot friendly page to a normal looking client
    USER_AGENT = "Mozilla/5.0 (compatible; Antedium/1.0; +http://bot.glky.net)"
    REQUEST_TIMEOUT = 3
    CACHE_LIMIT = 512

    def __init__(self):
        # Short code -> pin id, so reposts of a link cost no requests
        self.cache = {}

    @property
    def name(self) -> str:
        return "Pinterest"

    @property
    def link(self) -> str:
        return "pinterestez.com"

    @property
    def ignore(self) -> List[str]:
        return ["pinterestez.com"]

    @property
    def replace(self) -> List[str]:
        """Return links to replace."""
        return ["pin.it", "pinterest.com"]

    @property
    def pattern(self) -> str:
        """Return the regex pattern for the Pinterest link.
        Matches pin.it short links and pin links on any Pinterest geo domain."""
        return r"(https?:\/\/)((?:[a-z]{2,4}\.)?pinterest\.com\/pin\/[-a-zA-Z0-9()@:%_\+.~#?&=\/]*|pin\.it\/[a-zA-Z0-9]+)"

    async def resolve(self, url: str) -> Optional[str]:
        """Rebuild a Pinterest link against the fixed embed domain.

        Long form links carry a geo subdomain and, when shared, an invite_code
        and the sharer's Pinterest account id, so the pin id is pulled out and
        the URL rebuilt rather than rewritten in place.

        Parameters
        ----------
        url : str
            The Pinterest link matched by the handler's pattern.

        Returns
        -------
        str or None
            The fixed pin URL, or None if no pin id could be found.
        """
        if self.SHORTENER in url:
            pin_id = await self.expand(url)
        else:
            match = self.PIN_ID_PATTERN.search(url)
            pin_id = match.group(1) if match else None

        if pin_id is None:
            return None
        return f"https://www.{self.link}/pin/{pin_id}/"

    async def expand(self, url: str) -> Optional[str]:
        """Follow a pin.it short link to find the pin it points at.

        Parameters
        ----------
        url : str
            The pin.it short link to expand.

        Returns
        -------
        str or None
            The pin id, or None if the link could not be resolved.
        """
        code = url.rstrip("/").rsplit("/", 1)[-1]
        if code in self.cache:
            return self.cache[code]

        try:
            timeout = aiohttp.ClientTimeout(total=self.REQUEST_TIMEOUT)
            headers = {"User-Agent": self.USER_AGENT}
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                # HEAD is enough, the pin id is in the final URL and the body is never needed
                async with session.head(url, allow_redirects=True) as response:
                    if response.status >= 400:
                        return None
                    final_url = str(response.url)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            print(f"Failed to resolve Pinterest link {url}: {e}")
            return None

        # The page body advertises a canonical URL, but it has been seen to name
        # a different pin than the redirect chain, so trust the redirect
        match = self.PIN_ID_PATTERN.search(final_url)
        if match is None:
            return None

        if len(self.cache) >= self.CACHE_LIMIT:
            self.cache.clear()
        self.cache[code] = match.group(1)
        return match.group(1)
