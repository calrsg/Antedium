# Glossary

**Link Handler**
The unit that knows how to recognise one platform's links and turn them into Fixed Links. There is one per supported platform (Twitter, Instagram, TikTok, Pinterest).

**Source Link**
A link to a supported platform as a user posted it, e.g. `https://x.com/user/status/123`.

**Fixed Link**
A Source Link rewritten to point at an Embed Provider, e.g. `https://fxtwitter.com/user/status/123`. This is what the bot replies with.

**Embed Provider**
A third-party service that serves a Discord-friendly embed for a platform's posts (e.g. fxtwitter, kktiktok). Each Link Handler targets exactly one Embed Provider at a time.

**Candidate Provider**
An Embed Provider a Link Handler could switch to if its current one stops producing Working Embeds. Distinct from providers the bot merely recognises as already-fixed links, which may include dead services.

**Rewrite**
The process of turning a message's Source Links into Fixed Links. Our code alone determines its outcome.

**Rewrite Check**
An automated check that a given Source Link (or message) rewrites to the expected Fixed Link(s). Rewrite Checks are deterministic and gate deploys.

**Provider Health Check**
An automated check that an Embed Provider currently serves a Working Embed for a Canary Post. Failures reflect a third party, so they alert rather than gate deploys, and only a Link Handler's current Embed Provider alerts; Candidate Providers are reported for information.

**Canary Post**
A stable, public post on a supported platform, used by Provider Health Checks as a known-good input.

**Working Embed**
An embed Discord actually renders for a Fixed Link, showing the post's image or, for a video post, its video. Judged by what Discord shows, not by what the Embed Provider returns to anyone else.
