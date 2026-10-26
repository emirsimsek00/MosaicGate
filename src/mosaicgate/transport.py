"""Lifecycle of the real, local stdio MCP connection; no model integration."""

import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from mcp import Client, StdioServerParameters

from mosaicgate.smoke_fixtures import Modality


@asynccontextmanager
async def fixture_client(
    modality: Modality = Modality.TEXT, payload_file: Path | None = None
) -> AsyncIterator[Client]:
    """Start an isolated subprocess with a bounded MCP response wait."""
    args = ["-m", "mosaicgate.fixture_server", "--modality", modality.value]
    if payload_file is not None:
        args.extend(["--payload-file", str(payload_file.resolve())])
    parameters = StdioServerParameters(
        command=sys.executable,
        args=args,
        env={"PYTHONUNBUFFERED": "1"},
    )
    async with Client(parameters, read_timeout_seconds=15) as client:
        yield client
