from linkhandlers.twitterlink import TwitterLink
from tests.rewrite.cases import Case, Seed

HANDLER = TwitterLink

CASES = [
    Case("x", "https://x.com/user/status/123", ["https://fxtwitter.com/user/status/123"]),
    Case("twitter", "https://twitter.com/user/status/123", ["https://fxtwitter.com/user/status/123"]),
    Case("twitter-www", "https://www.twitter.com/user/status/123", ["https://fxtwitter.com/user/status/123"]),
    Case("nitter", "https://nitter.net/user/status/123", ["https://fxtwitter.com/user/status/123"]),
    Case("http", "http://x.com/user/status/123", ["http://fxtwitter.com/user/status/123"]),
    Case("i-status", "https://x.com/i/status/123", ["https://fxtwitter.com/i/status/123"]),
    Case("photo-kept", "https://x.com/user/status/123/photo/2", ["https://fxtwitter.com/user/status/123/photo/2"]),
    # fxtwitter embeds the video from the status alone
    Case("video-dropped", "https://x.com/user/status/123/video/1", ["https://fxtwitter.com/user/status/123"]),
    Case("query-kept", "https://x.com/user/status/123?s=20&t=abc", ["https://fxtwitter.com/user/status/123?s=20&t=abc"]),
    Case("in-sentence", "look at this https://x.com/user/status/123 lol", ["https://fxtwitter.com/user/status/123"]),
    Case("spoiler", "||https://x.com/user/status/123||", ["||https://fxtwitter.com/user/status/123||"]),
    Case("two-links", "https://x.com/a/status/1 https://x.com/b/status/2",
         ["https://fxtwitter.com/a/status/1", "https://fxtwitter.com/b/status/2"]),
    Case("profile-ignored", "https://x.com/user"),
    Case("already-fixed", "https://fxtwitter.com/user/status/123"),
    Case("candidate-provider-ignored", "https://fixupx.com/user/status/123"),
    Case("twitter-and-x", "https://twitter.com/a/status/1 https://x.com/b/status/2",
         ["https://fxtwitter.com/a/status/1", "https://fxtwitter.com/b/status/2"]),
    Case("fixed-and-unfixed", "https://fxtwitter.com/a/status/1 https://x.com/b/status/2",
         ["https://fxtwitter.com/b/status/2"]),
    Case("one-spoiler", "||https://x.com/a/status/1|| https://x.com/b/status/2",
         ["||https://fxtwitter.com/a/status/1||", "https://fxtwitter.com/b/status/2"]),
    Case("www-x", "https://www.x.com/user/status/123", ["https://fxtwitter.com/user/status/123"]),
    Case("mobile-twitter", "https://mobile.twitter.com/user/status/123", ["https://fxtwitter.com/user/status/123"]),
]

SEEDS = [
    Seed("https://x.com/user/status/123", "123"),
    Seed("https://twitter.com/user/status/456", "456"),
    Seed("https://nitter.net/user/status/789", "789"),
]
