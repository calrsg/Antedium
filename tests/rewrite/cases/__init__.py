"""Rewrite Check case tables, one module per link handler.

Each module defines:

CASES
    Messages and the exact Fixed Links today's code produces for them, across
    every handler, in reply order. A case with ``bug`` set records the output
    we *want*; it is expected to fail until the bug is fixed.
SEEDS
    Source Links paired with the post id their Fixed Link must keep. The
    invariant checks post each seed in several message shapes and check the
    output's shape without needing an exact expectation.
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class Case:
    id: str
    message: str
    expected: List[str] = field(default_factory=list)
    bug: Optional[str] = None


@dataclass(frozen=True)
class Seed:
    source: str
    post_id: str
