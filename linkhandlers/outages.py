# Current providers known to be down with nowhere better to switch to:
# provider -> why. They are still checked and reported, but do not alert.
# The provider-health alert says when one recovers, so the entry can be removed.
KNOWN_OUTAGES = {
    "pinterestez.com": "fails to parse full pinterest.com links, no working alternative (pin.it still works)",
}
