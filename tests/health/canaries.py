from dataclasses import dataclass


@dataclass(frozen=True)
class Canary:
    """A stable public post whose Fixed Link should always embed."""
    source: str
    # "image" or "video", the media Discord must show
    kind: str


CANARIES = [
    Canary("https://x.com/kani_kani_kany/status/2108632914737131556/photo/1", "image"),
    Canary("https://x.com/pianhangx/status/2090246911995597084/video/1", "video"),
    Canary("https://www.instagram.com/p/Dd01U2Wkv6x/", "image"),
    Canary("https://www.instagram.com/reels/DefcOIGBCoN/", "video"),
    Canary("https://www.tiktok.com/@fairviewfarmvalais/video/7683192754012310797", "video"),
    Canary("https://vt.tiktok.com/ZSgNDhUMN/", "video"),
    Canary("https://au.pinterest.com/pin/669206825885255454/", "image"),
    Canary("https://pin.it/2jPT2dQ9U", "image"),
]
