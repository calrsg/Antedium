"""The Health Report: what the latest run of Provider Health Checks found.

The provider-health workflow saves it into HEALTH_RESULTS_DIR after every run,
and the bot reads it back to tell users which Embed Providers are working.
"""
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from linkhandlers.linkinterface import LinkInterface
from linkhandlers.outages import KNOWN_OUTAGES

REPORT_FILE = "health.json"
# Two runs of the 6-hourly provider-health workflow
STALE_AFTER = timedelta(hours=12)

WORKING = "working"
DOWN = "down"
PARTIAL = "partly working"
KNOWN_OUTAGE = "known outage"
UNCHECKED = "not checked yet"


def results_dir() -> str:
    """Where the Health Report lives, mounted from the server in production."""
    return os.environ.get("HEALTH_RESULTS_DIR", "health")


@dataclass(frozen=True)
class Check:
    """One Provider Health Check as recorded in the report."""
    handler: str
    provider: str
    # Whether the provider was the handler's current one when checked
    current: bool
    # What the Canary Post stands for, e.g. "videos" or "pin.it links"
    label: str
    ok: bool
    detail: str


@dataclass
class HealthReport:
    checked_at: datetime
    checks: List[Check]

    def stale(self, now: Optional[datetime] = None) -> bool:
        return (now or datetime.now(timezone.utc)) - self.checked_at > STALE_AFTER


def save_report(directory: str, report: HealthReport):
    """Write the report so a reader never sees a half written file."""
    os.makedirs(directory, exist_ok=True)
    contents = {
        "checked_at": report.checked_at.isoformat(),
        "checks": [asdict(check) for check in report.checks],
    }
    fd, temp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as file:
            json.dump(contents, file, indent=4)
        # The bot runs as a different user, so the default 0600 would lock it out
        os.chmod(temp, 0o644)
        os.replace(temp, os.path.join(directory, REPORT_FILE))
    except BaseException:
        os.unlink(temp)
        raise


def load_report(directory: str) -> Optional[HealthReport]:
    """Read the report back, or None if there is no usable one."""
    try:
        with open(os.path.join(directory, REPORT_FILE)) as file:
            contents = json.load(file)
        return HealthReport(
            datetime.fromisoformat(contents["checked_at"]),
            [Check(**check) for check in contents["checks"]],
        )
    except (OSError, ValueError, KeyError, TypeError):
        return None


@dataclass(frozen=True)
class ProviderStatus:
    """How a Link Handler's current Embed Provider is doing, as users see it."""
    handler: str
    provider: str
    state: str
    note: str = ""


def provider_status(handler: LinkInterface, report: Optional[HealthReport]) -> ProviderStatus:
    # Only checks of the provider in use now count, a switch since the last run
    # leaves the new one unchecked rather than showing the old one's health
    checks = [c for c in report.checks if c.handler == handler.name and c.provider == handler.link] if report else []
    if not checks:
        return ProviderStatus(handler.name, handler.link, UNCHECKED)
    failing = [c.label for c in checks if not c.ok]
    if not failing:
        return ProviderStatus(handler.name, handler.link, WORKING)
    if handler.link in KNOWN_OUTAGES:
        return ProviderStatus(handler.name, handler.link, KNOWN_OUTAGE, KNOWN_OUTAGES[handler.link])
    if len(failing) == len(checks):
        return ProviderStatus(handler.name, handler.link, DOWN)
    return ProviderStatus(handler.name, handler.link, PARTIAL, f"{', '.join(failing)} not embedding")
