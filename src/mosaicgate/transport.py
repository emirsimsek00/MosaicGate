"""Lifecycle of the real, local stdio MCP connection; no model integration."""

import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp import Client, StdioServerParameters

from mosaicgate.smoke_fixtures import Modality


@asynccontextmanager
async def fixture_client(modality: Modality = Modality.TEXT) -> AsyncIterator[Client]:
    """Start an isolated subprocess with a bounded MCP response wait."""
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mosaicgate.fixture_server", "--modality", modality.value],
        env={"PYTHONUNBUFFERED": "1"},
    )
    async with Client(parameters, read_timeout_seconds=15) as client:
        yield client
