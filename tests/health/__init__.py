"""Provider Health Checks.

Each Canary Post's Source Link is run through the real Rewrite, then the Fixed
Link is posted to Discord through a probe webhook so Discord itself decides
whether it embeds. Embed providers vary too much (redirects to raw media,
ActivityPub, serving Discord's IPs differently) to judge from their responses.

These checks never gate a deploy. A provider going down is a third party's
outage, and blocking deploys would also block the commit that switches a
handler to a working provider. They run on a schedule and alert instead; see
.github/workflows/provider-health.yml.
"""
