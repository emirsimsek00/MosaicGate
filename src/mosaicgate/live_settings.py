"""Fail-closed prerequisites for explicitly requested free-tier live runs."""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import dotenv_values

FREE_MODEL_CANDIDATES = frozenset({"gemini-3.8-flash", "gemini-3.6-flash"})


class LivePrerequisiteError(ValueError):
    """A local requirement is missing; no API request should be attempted."""


@dataclass(frozen=True)
class LiveSettings:
    api_key: str = field(repr=False)
    model: str = "gemini-3.6-flash"


def require_live_settings(
    env_file: Path = Path(".env"), *, environment: Mapping[str, str] | None = None
) -> LiveSettings:
    environment = os.environ if environment is None else environment
    if environment.get("CI", "").lower() not in {"", "0", "false"}:
        raise LivePrerequisiteError("Live model requests are disabled in CI.")
    values = {key: value for key, value in dotenv_values(env_file).items() if value is not None}
    values.update(environment)
    key = (values.get("GEMINI_API_KEY") or values.get("GOOGLE_API_KEY") or "").strip()
    if not key:
        raise LivePrerequisiteError("A local free-tier Gemini credential is required.")
    if values.get("MOSAICGATE_FREE_TIER_CONFIRMED", "").lower() != "true":
        raise LivePrerequisiteError("Confirm Free tier and billing disabled before a live request.")
    model = values.get("MOSAICGATE_MODEL", "gemini-3.6-flash")
    if model not in FREE_MODEL_CANDIDATES:
        raise LivePrerequisiteError("Model is outside the documented free Gemini 3 candidates.")
    return LiveSettings(api_key=key, model=model)
