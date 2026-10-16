import re
from dataclasses import dataclass
from typing import List
from urllib.parse import urlsplit

from linkhandlers.instagramlink import InstagramLink
from linkhandlers.linkinterface import LinkInterface
from linkhandlers.pinterestlink import PinterestLink
from linkhandlers.tiktoklink import TiktokLink
from linkhandlers.twitterlink import TwitterLink

# Small-text invite line appended beneath the fixed links in every reply
INVITE_FOOTER = "-# [Invite Antedium to your server](<https://antedium.glky.net>)"


def default_handlers() -> List[LinkInterface]:
    """Return a fresh instance of every link handler the bot runs, in order."""
    return [TwitterLink(), InstagramLink(), TiktokLink(), PinterestLink()]


@dataclass
class HandlerResult:
    """The fixed links one handler produced for a message."""
    handler: LinkInterface
    links: List[str]


def find_fixable_handlers(content: str, handlers: List[LinkInterface]) -> List[LinkInterface]:
    """
    Preliminary check for links that may match link handlers.

    Parameters
    ----------
    content : str
        The message content to check for fixable links.

    handlers : [LinkInterface]
        The link handlers to check against.

    Returns
    -------
    [LinkInterface]
        A list of link handlers that can fix the links in the message.
    """
    # Already-fixed links are skipped one by one in fix_links, so one in the
    # message must not stop the others being fixed
    return [handler for handler in handlers if any(link in content for link in handler.replace)]


async def fix_links(content: str, handler: LinkInterface) -> List[str]:
    """
    Rewrite the links in a message that a handler matches into fixed links.

    Parameters
    ----------
    content : str
        The message content to fix.

    handler : LinkInterface
        The link handler to use for fixing the message.

    Returns
    -------
    [str]
        The fixed links, in the order they appear in the message. Empty if no
        links were fixed.
    """
    new_urls = []
    # Use handler regex to identify links
    for match in re.finditer(handler.pattern, content):
        # Rebuild the URL from the regex match
        original_url = trim_trailing_punctuation("".join(match.groups(default="")))
        # Skip links already pointing at an Embed Provider
        if is_already_fixed(original_url, handler):
            continue
        spoiler = spoiler_check(content, match.start())

        # Let the handler expand short-form links, which may need a request
        new_url = await handler.resolve(original_url)
        # Skip links the handler could not resolve
        if new_url is None:
            continue

        for link in handler.replace:
            # If the link is in the URL, replace
            if link in original_url:
                new_url = new_url.replace(link, handler.link)
                # Remove www. if present
                new_url = new_url.replace("www.", "")
                # Add spoiler tags for links originally spoilered
                if spoiler:
                    new_url = "||" + new_url + "||"
                if handler.status is not None:
                    new_url += "\n" + handler.status
                new_urls.append(new_url)
    return new_urls


async def rewrite(content: str, handlers: List[LinkInterface]) -> List[HandlerResult]:
    """
    Rewrite every fixable link in a message.

    Parameters
    ----------
    content : str
        The message content to fix.

    handlers : [LinkInterface]
        The link handlers to fix the message with.

    Returns
    -------
    [HandlerResult]
        The fixed links for each handler that fixed at least one link, in the
        order the handlers are given.
    """
    results = []
    for handler in find_fixable_handlers(content, handlers):
        links = await fix_links(content, handler)
        if links:
            results.append(HandlerResult(handler, links))
    return results


def build_reply(results: List[HandlerResult]) -> str:
    """
    Build the reply text for a message's fixed links.

    Parameters
    ----------
    results : [HandlerResult]
        The fixed links for each handler, as returned by rewrite.

    Returns
    -------
    str
        The reply, with the invite footer beneath the links.
    """
    fixed = ""
    # We read links top down so default message is reversed
    for result in reversed(results):
        fixed += "".join(f"{link}\n" for link in result.links) + "\n"
    # Links already end in a newline, so trim before adding the footer
    return fixed.rstrip() + "\n" + INVITE_FOOTER


def is_already_fixed(url: str, handler: LinkInterface) -> bool:
    """
    Check if a link already points at one of a handler's ignored domains.

    Parameters
    ----------
    url : str
        The URL matched by the handler's pattern.

    handler : LinkInterface
        The link handler whose ignore list to check against.

    Returns
    -------
    bool
        True if the URL's host is an ignored domain or a subdomain of one,
        False otherwise.
    """
    host = urlsplit(url).hostname or ""
    return any(host == domain or host.endswith("." + domain) for domain in handler.ignore)


def spoiler_check(content: str, position: int) -> bool:
    """
    Check if a position in the message is inside spoiler tags.

    Parameters
    ----------
    content : str
        The message content to check for spoiler tags.

    position : int
        The index in the message to check, such as the start of a link.

    Returns
    -------
    bool
        True if the position is between an opening and closing pair of spoiler
        tags, False otherwise.
    """
    # An odd number of tags before the position means a spoiler is open
    opened = content.count("||", 0, position) % 2 == 1
    return opened and "||" in content[position:]


def trim_trailing_punctuation(url: str) -> str:
    """
    Trim punctuation the link patterns capture from the text after a link.

    Parameters
    ----------
    url : str
        The URL matched by a handler's pattern.

    Returns
    -------
    str
        The URL without trailing sentence punctuation, or a closing bracket
        that has no opening bracket in the URL.
    """
    while url:
        if url[-1] in ".,:;!?":
            url = url[:-1]
        # Keep a closing bracket that pairs with one inside the URL
        elif url[-1] == ")" and url.count(")") > url.count("("):
            url = url[:-1]
        else:
            break
    return url
