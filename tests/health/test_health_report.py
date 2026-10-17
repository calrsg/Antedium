"""How a Health Report turns into what /providers tells users. Offline."""
from datetime import datetime, timedelta, timezone

from linkhandlers.healthreport import (DOWN, KNOWN_OUTAGE, PARTIAL, UNCHECKED, WORKING, Check,
                                       HealthReport, load_report, provider_status, save_report)
from linkhandlers.outages import KNOWN_OUTAGES
from linkhandlers.pinterestlink import PinterestLink
from linkhandlers.twitterlink import TwitterLink

NOW = datetime(2026, 10, 17, 12, tzinfo=timezone.utc)
TWITTER = TwitterLink()


def report(*checks: Check, checked_at: datetime = NOW) -> HealthReport:
    return HealthReport(checked_at, list(checks))


def check(label: str, ok: bool, provider: str = "fxtwitter.com", handler: str = "Twitter") -> Check:
    return Check(handler, provider, provider == "fxtwitter.com", label, ok, "ok" if ok else "no embed")


def test_every_canary_passing_is_working():
    status = provider_status(TWITTER, report(check("images", True), check("videos", True)))
    assert (status.provider, status.state) == ("fxtwitter.com", WORKING)


def test_every_canary_failing_is_down():
    assert provider_status(TWITTER, report(check("images", False), check("videos", False))).state == DOWN


def test_some_canaries_failing_names_what_fails():
    status = provider_status(TWITTER, report(check("images", True), check("videos", False)))
    assert (status.state, status.note) == (PARTIAL, "videos not embedding")


def test_candidate_providers_do_not_count():
    status = provider_status(TWITTER, report(check("images", True), check("images", False, "vxtwitter.com")))
    assert status.state == WORKING


def test_a_switched_provider_is_unchecked_until_the_next_run():
    status = provider_status(TWITTER, report(check("images", False, "oldprovider.com")))
    assert (status.provider, status.state) == ("fxtwitter.com", UNCHECKED)


def test_no_report_is_unchecked():
    assert provider_status(TWITTER, None).state == UNCHECKED


def test_known_outage_shows_its_reason():
    pinterest = PinterestLink()
    status = provider_status(pinterest, report(
        check("pinterest.com links", False, pinterest.link, pinterest.name),
        check("pin.it links", True, pinterest.link, pinterest.name),
    ))
    assert (status.state, status.note) == (KNOWN_OUTAGE, KNOWN_OUTAGES[pinterest.link])


def test_recovered_known_outage_is_working():
    pinterest = PinterestLink()
    status = provider_status(pinterest, report(check("pin.it links", True, pinterest.link, pinterest.name)))
    assert status.state == WORKING


def test_stale_after_two_missed_runs():
    assert not report(checked_at=NOW - timedelta(hours=12)).stale(NOW)
    assert report(checked_at=NOW - timedelta(hours=13)).stale(NOW)


def test_round_trip(tmp_path):
    saved = report(check("images", True), check("videos", False, "vxtwitter.com"))
    save_report(str(tmp_path), saved)
    assert load_report(str(tmp_path)) == saved
    assert [p.name for p in tmp_path.iterdir()] == ["health.json"]


def test_missing_or_broken_report_loads_as_none(tmp_path):
    assert load_report(str(tmp_path)) is None
    (tmp_path / "health.json").write_text("{not json")
    assert load_report(str(tmp_path)) is None
