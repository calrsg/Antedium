from linkhandlers.pinterestlink import PinterestLink
from tests.rewrite.cases import Case, Seed

HANDLER = PinterestLink

# pin.it short code -> pin id, standing in for the network lookup
PIN_IT = {"abc123": "111"}

CASES = [
    Case("geo", "https://au.pinterest.com/pin/669206825885255454/", ["https://pinterestez.com/pin/669206825885255454/"]),
    Case("www", "https://www.pinterest.com/pin/669206825885255454/", ["https://pinterestez.com/pin/669206825885255454/"]),
    Case("slug", "https://pinterest.com/pin/some-slug--669206825885255454/", ["https://pinterestez.com/pin/669206825885255454/"]),
    Case("shared", "https://www.pinterest.com/pin/669206825885255454/sent/?invite_code=abc&sfo=1",
         ["https://pinterestez.com/pin/669206825885255454/"]),
    Case("pin-it", "https://pin.it/abc123", ["https://pinterestez.com/pin/111/"]),
    Case("pin-it-unresolvable", "https://pin.it/nothere"),
    Case("profile-ignored", "https://www.pinterest.com/someuser/"),
    Case("already-fixed", "https://pinterestez.com/pin/669206825885255454/"),
]

SEEDS = [
    Seed("https://au.pinterest.com/pin/669206825885255454/", "669206825885255454"),
    Seed("https://pinterest.com/pin/some-slug--222/", "222"),
    Seed("https://pin.it/abc123", "111"),
]
