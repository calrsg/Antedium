from linkhandlers.instagramlink import InstagramLink
from tests.rewrite.cases import Case, Seed

HANDLER = InstagramLink

CASES = [
    Case("post", "https://www.instagram.com/p/ABC123/", ["https://oginstagram.com/p/ABC123/"]),
    Case("post-no-www", "https://instagram.com/p/ABC123/", ["https://oginstagram.com/p/ABC123/"]),
    Case("post-no-slash", "https://www.instagram.com/p/ABC123", ["https://oginstagram.com/p/ABC123"]),
    Case("reel", "https://www.instagram.com/reel/ABC123/", ["https://oginstagram.com/reel/ABC123/"]),
    Case("reels", "https://www.instagram.com/reels/ABC123/", ["https://oginstagram.com/reels/ABC123/"]),
    Case("query-kept", "https://www.instagram.com/reel/ABC123/?igsh=xyz", ["https://oginstagram.com/reel/ABC123/?igsh=xyz"]),
    Case("profile-ignored", "https://www.instagram.com/someuser/"),
    Case("story-ignored", "https://www.instagram.com/stories/someuser/123/"),
    Case("already-fixed", "https://oginstagram.com/p/ABC123/"),
    Case("candidate-provider-ignored", "https://kkinstagram.com/p/ABC123/"),
]

SEEDS = [
    Seed("https://www.instagram.com/p/ABC123/", "ABC123"),
    Seed("https://instagram.com/reel/DEF456/", "DEF456"),
    Seed("https://www.instagram.com/reels/GHI789/", "GHI789"),
]
