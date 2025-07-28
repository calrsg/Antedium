from typing import List
from linkhandlers.linkinterface import LinkInterface

class TiktokLink(LinkInterface):
    """Class to handle Tiktok links."""

    @property
    def name(self) -> str:
        return "Tiktok"

    @property
    def link(self) -> str:
        return "tnktok.com"

    @property
    def ignore(self) -> List[str]:
        return  ["tnktok.com"]

    @property
    def replace(self) -> List[str]:
        """Return links to replace."""
        return ["vt.tiktok.com"]
    
    @property
    def pattern(self) -> str:
        """Return the regex pattern for the Tiktok link.
        Matches Tiktok links with reel and post components."""
        return r"(https?:\/\/)(vt\.tiktok\.com\/)([-a-zA-Z0-9()@:%_\+.~#&=\/]*\/)"