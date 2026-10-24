"""Offline foundation diagnostics. Security and evaluation commands arrive later."""

import argparse
import asyncio
import base64
import hashlib
import importlib.metadata
import json
import shutil
import subprocess
import sys
from collections.abc import Sequence

from mcp.types import ImageContent, TextContent

from mosaicgate import __version__
from mosaicgate.smoke_fixtures import Modality
from mosaicgate.transport import fixture_client


def doctor() -> dict[str, object]:
    executable = shutil.which("tesseract")
    ocr: dict[str, object] = {"available": executable is not None}
    if executable is not None:
        try:
            version = subprocess.run(
                [executable, "--version"], capture_output=True, text=True, timeout=5, check=True
            )
            languages = subprocess.run(
                [executable, "--list-langs"], capture_output=True, text=True, timeout=5, check=True
            )
            ocr["version"] = version.stdout.splitlines()[0]
            ocr["english_available"] = "eng" in languages.stdout.splitlines()
        except (OSError, subprocess.SubprocessError, IndexError) as error:
            ocr = {"available": False, "error_type": type(error).__name__}
    return {
        "mosaicgate": __version__,
        "python": sys.version.split()[0],
        "packages": {
            name: importlib.metadata.version(name) for name in ("mcp", "google-genai", "pillow")
        },
        "ocr": ocr,
        "live_api_requests": 0,
        "security_status": "foundation only; enforcement not yet implemented",
    }


async def smoke(modality: Modality) -> dict[str, object]:
    """One fixed trusted read for transport validation; not an agent run."""
    async with fixture_client(modality) as client:
        result = await client.call_tool("read_report", {"report_id": "q3"})
        if result.is_error or len(result.content) != 1:
            raise RuntimeError("Fixture server returned an unexpected result")
        block = result.content[0]
        if isinstance(block, ImageContent):
            raw = base64.b64decode(block.data, validate=True)
            content_type = block.mime_type
        elif isinstance(block, TextContent):
            raw = block.text.encode("utf-8")
            content_type = "text/plain"
        else:
            raise RuntimeError("Fixture server returned an unsupported smoke result")
        return {
            "simulation": True,
            "check": "real MCP stdio round trip; not a security evaluation",
            "modality": modality.value,
            "content_type": content_type,
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "is_error": result.is_error,
            "live_api_requests": 0,
        }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="Check the installed offline runtime without API calls")
    smoke_parser = commands.add_parser("smoke", help="Exercise a real local MCP read_report call")
    smoke_parser.add_argument("--modality", choices=list(Modality), default=Modality.TEXT)
    args = parser.parse_args(argv)
    output = doctor() if args.command == "doctor" else asyncio.run(smoke(Modality(args.modality)))
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
