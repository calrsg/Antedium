import re
from dataclasses import dataclass
from typing import List

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
    found = []
    for handler in handlers:
        # FIXME: Multiple links in one message may cause issues
        # Search for valid links
        for link in handler.replace:
            if link in content:
                # Only add if link is not prefixed (assumed pre-fixed URL)
                if not any(x in content for x in handler.ignore):
                    found.append(handler)
    return found


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
    spoiler = spoiler_check(content)
    # Use handler regex to identify links
    for url in re.findall(handler.pattern, content):
        # Rebuild the URL from the regex match
        original_url = "".join(url)

        # Let the handler expand short-form links, which may need a request
        new_url = await handler.resolve(original_url)
        # Skip links the handler could not resolve
        if new_url is None:
            continue

        for link in handler.replace:
            # If the link is in the URL and not in the ignore list, replace
            if link in original_url and not any([x in url for x in handler.ignore]):
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


def spoiler_check(content: str) -> bool:
    """
    Check if the message contains spoiler tags.

    Parameters
    ----------
    content : str
        The message content to check for spoiler tags.

    Returns
    -------
    bool
        True if the message contains spoiler tags, False otherwise.
    """
    return len(content.split("||")) >= 2
