from typing import List
from linkhandlers.linkinterface import LinkInterface

class TwitterLink(LinkInterface):
    """Class to handle Twitter links."""

    @property
    def name(self) -> str:
        return "Twitter"

    @property
    def link(self) -> str:
        return "fxtwitter.com"

    @property
    def candidates(self) -> List[str]:
        return ["fxtwitter.com", "vxtwitter.com", "fixupx.com"]

    @property
    def ignore(self) -> List[str]:
        return  ["fxtwitter.com", "vxtwitter.com"]

    @property
    def replace(self) -> List[str]:
        """Return links to replace."""
        return ["twitter.com", "x.com", "nitter.net"]
    
    @property
    def pattern(self) -> str:
        """Return the regex pattern for the Twitter link.
        Matches Twitter, X, and Nitter links with status and photo components.
        A mobile. subdomain sits outside the groups, so it is dropped when the
        URL is rebuilt from them."""
        return r"(https?:\/\/)(?:mobile\.)?((?:www\.)?(?:twitter|x)\.com|nitter\.net)(\/[-a-zA-Z0-9()@:%_\+.~#?&=]*)(\/status\/[-a-zA-Z0-9()@:%_\+.~#?&=]*)(\/photo\/[0-9]*)?"