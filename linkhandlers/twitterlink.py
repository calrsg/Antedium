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
    def ignore(self) -> List[str]:
        return  ["fxtwitter.com", "vxtwitter.com"]

    @property
    def replace(self) -> List[str]:
        """Return links to replace."""
        return ["twitter.com", "x.com", "nitter.net"]
    
    @property
    def pattern(self) -> str:
        """Return the regex pattern for the Twitter link.
        Matches Twitter, X, and Nitter links with status and photo components."""
        return r"(https?:\/\/)((?:www\.)?twitter\.com|x\.com|nitter\.net)(\/[-a-zA-Z0-9()@:%_\+.~#?&=]*)(\/status\/[-a-zA-Z0-9()@:%_\+.~#?&=]*)(\/photo\/[0-9]*)?"