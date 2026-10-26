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
from pathlib import Path

from mcp.types import CallToolResult, ImageContent, TextContent

from mosaicgate import __version__
from mosaicgate.agents import ScriptedAgent
from mosaicgate.controller import Controller, Scenario, append_run
from mosaicgate.evaluation import evaluate
from mosaicgate.grants import Mode
from mosaicgate.inspection import (
    InspectionCaps,
    InspectionContext,
    decision_record,
    inspect_tool_result,
)
from mosaicgate.live_settings import LivePrerequisiteError, require_live_settings
from mosaicgate.reporting import create_report
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
        "security_status": "local controller and inspector; scripted evaluation complete",
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


def inspect_file(path: Path, modality: Modality, scenario_id: str) -> dict[str, object]:
    """Inspect one local file without printing its contents or forwarding it."""
    caps = InspectionCaps()
    limit = caps.text_bytes if modality == Modality.TEXT else caps.image_bytes
    if path.stat().st_size > limit:
        raise ValueError("Input exceeds the configured inspection size limit.")
    if modality == Modality.TEXT:
        result = CallToolResult(content=[TextContent(text=path.read_text(encoding="utf-8"))])
    else:
        result = CallToolResult(
            content=[
                ImageContent(
                    data=base64.b64encode(path.read_bytes()).decode("ascii"),
                    mime_type={
                        ".png": "image/png",
                        ".jpg": "image/jpeg",
                        ".jpeg": "image/jpeg",
                        ".webp": "image/webp",
                    }.get(path.suffix.lower(), "application/octet-stream"),
                )
            ]
        )
    return decision_record(
        inspect_tool_result(
            result, InspectionContext(tool_name="read_report", scenario_id=scenario_id)
        )
    )


def demo_scenario(scenario_id: str) -> Scenario:
    root = Path.cwd()
    if scenario_id == "benign-text":
        return Scenario(scenario_id, Modality.TEXT)
    if scenario_id == "benign-image":
        return Scenario(scenario_id, Modality.IMAGE)
    if scenario_id == "injection-text":
        return Scenario(
            scenario_id,
            Modality.TEXT,
            root / "fixtures" / "demo" / "attack.txt",
            label="malicious",
        )
    if scenario_id == "forced-call":
        return Scenario(scenario_id, Modality.TEXT, forced_unauthorized_call=True)
    raise ValueError(f"Unknown demo scenario: {scenario_id}")


async def run_demo(
    scenario_id: str, mode: Mode, agent_name: str, output: Path
) -> dict[str, object]:
    scenario = demo_scenario(scenario_id)
    if agent_name == "scripted":
        trace = await Controller().run(
            scenario,
            mode,
            ScriptedAgent(forced_unauthorized_call=scenario.forced_unauthorized_call),
        )
    else:
        from mosaicgate.gemini_agent import GeminiAgent

        settings = require_live_settings()
        async with GeminiAgent(settings) as agent:
            trace = await Controller().run(scenario, mode, agent)
    append_run(output, trace)
    return {
        "run_id": trace.run_id,
        "scenario_id": trace.scenario_id,
        "mode": trace.mode,
        "agent_id": trace.agent_id,
        "termination": trace.termination,
        "proposed_calls": len(trace.proposed_calls),
        "executed_tool_events": len(trace.executed_tool_events),
        "api_requests": trace.api_requests,
        "simulation": True,
        "trace_path": str(output),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="Check the installed offline runtime without API calls")
    smoke_parser = commands.add_parser("smoke", help="Exercise a real local MCP read_report call")
    smoke_parser.add_argument("--modality", choices=list(Modality), default=Modality.TEXT)
    inspect_parser = commands.add_parser("inspect", help="Inspect a local text or image fixture")
    inspect_parser.add_argument("--input", type=Path, required=True)
    inspect_parser.add_argument("--modality", choices=list(Modality), required=True)
    inspect_parser.add_argument("--scenario", default="local-inspection")
    demo_parser = commands.add_parser("demo", help="Run a synthetic agent task through MCP")
    demo_parser.add_argument("--scenario", required=True)
    demo_parser.add_argument("--mode", choices=("baseline", "inspect", "full"), required=True)
    demo_parser.add_argument("--agent", choices=("scripted", "gemini"), default="scripted")
    demo_parser.add_argument("--output", type=Path, default=Path("runs/demo.jsonl"))
    eval_parser = commands.add_parser("eval", help="Run the frozen synthetic case suite")
    eval_parser.add_argument("--suite", choices=("dev", "holdout"), required=True)
    eval_parser.add_argument("--agent", choices=("scripted", "gemini"), default="scripted")
    eval_parser.add_argument("--output", type=Path)
    eval_parser.add_argument("--max-sessions", type=int)
    report_parser = commands.add_parser("report", help="Render a saved synthetic evaluation")
    report_parser.add_argument("--input", type=Path, required=True)
    report_parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "doctor":
        output = doctor()
    elif args.command == "smoke":
        output = asyncio.run(smoke(Modality(args.modality)))
    elif args.command == "demo":
        if args.scenario == "forced-call" and args.agent != "scripted":
            parser.error("forced-call requires the deterministic scripted agent")
        try:
            output = asyncio.run(run_demo(args.scenario, args.mode, args.agent, args.output))
        except LivePrerequisiteError as error:
            parser.error(str(error))
    elif args.command == "eval":
        output_path = args.output or Path("runs") / f"{args.suite}-{args.agent}.jsonl"
        try:
            output = asyncio.run(
                evaluate(args.suite, args.agent, output_path, max_sessions=args.max_sessions)
            )
        except LivePrerequisiteError as error:
            parser.error(str(error))
    elif args.command == "report":
        output = create_report(args.input, args.output)
    else:
        output = inspect_file(args.input, Modality(args.modality), args.scenario)
    print(json.dumps(output, indent=2, sort_keys=True))
    if args.command == "demo" and output["termination"] == "error":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
