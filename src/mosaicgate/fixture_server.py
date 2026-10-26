"""Local MCP fixture server. All email/note effects are in-memory simulations."""

import argparse
import base64
import json
import re
from collections.abc import Sequence
from pathlib import Path
from typing import TypedDict

from mcp.server import MCPServer
from mcp.types import CallToolResult, ImageContent, TextContent

from mosaicgate.smoke_fixtures import REPORT_TEXT, Modality, report_png


class SimulatedEvent(TypedDict):
    sequence: int
    tool: str
    arguments: dict[str, str]
    simulation: bool


def create_server(
    modality: Modality = Modality.TEXT, payload_file: Path | None = None
) -> MCPServer[None]:
    """A new server owns its own ledger; no process-global side-effect state."""
    server: MCPServer[None] = MCPServer("MosaicGate synthetic fixture", log_level="ERROR")
    ledger: list[SimulatedEvent] = []
    if payload_file is None:
        report_text = REPORT_TEXT
        report_image = report_png()
    elif modality == Modality.TEXT:
        report_text = payload_file.read_text(encoding="utf-8")
        report_image = b""
    else:
        report_text = ""
        report_image = payload_file.read_bytes()

    def record(tool: str, arguments: dict[str, str]) -> SimulatedEvent:
        event: SimulatedEvent = {
            "sequence": len(ledger) + 1,
            "tool": tool,
            "arguments": arguments,
            "simulation": True,
        }
        ledger.append(event)
        return event

    @server.tool()
    def read_report(report_id: str) -> CallToolResult:
        """Read the invented Q3 report; the server configuration selects its format."""
        if report_id != "q3":
            return CallToolResult(
                content=[TextContent(text="Synthetic report not found.")], is_error=True
            )
        record("read_report", {"report_id": report_id})
        if modality == Modality.IMAGE:
            return CallToolResult(
                content=[
                    ImageContent(
                        data=base64.b64encode(report_image).decode("ascii"), mime_type="image/png"
                    )
                ]
            )
        return CallToolResult(content=[TextContent(text=report_text)])

    @server.tool()
    def send_email(to: str, body: str) -> CallToolResult:
        """SIMULATION: record an invented email in memory; never send real mail."""
        if re.fullmatch(r"[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+\.test", to) is None:
            return CallToolResult(
                content=[TextContent(text="Simulation requires a reserved .test address.")],
                is_error=True,
            )
        event = record("send_email", {"to": to, "body": body})
        return CallToolResult(
            content=[TextContent(text="SIMULATION: email recorded locally.")],
            structured_content={"simulation": True, "event": event},
        )

    @server.tool()
    def write_note(body: str) -> CallToolResult:
        """SIMULATION: record a note in memory; never write to an external service."""
        event = record("write_note", {"body": body})
        return CallToolResult(
            content=[TextContent(text="SIMULATION: note recorded locally.")],
            structured_content={"simulation": True, "event": event},
        )

    @server.resource("simulation://ledger")
    def read_ledger() -> str:
        """Internal observability resource, never offered to the agent as a tool."""
        return json.dumps({"simulation": True, "events": ledger}, sort_keys=True)

    return server


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modality", choices=list(Modality), default=Modality.TEXT)
    parser.add_argument("--payload-file", type=Path)
    args = parser.parse_args(argv)
    create_server(Modality(args.modality), args.payload_file).run(transport="stdio")


if __name__ == "__main__":
    main()
