"""Render a sixty-second silent demo from saved, synthetic trace evidence."""

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT = 1280, 720
INK = "#103e50"
MUTED = "#53717d"
TEAL = "#147e8f"
PAPER = "#f5f8fa"


@dataclass(frozen=True)
class Slide:
    eyebrow: str
    title: str
    lines: tuple[str, ...]
    footer: str


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    path = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
    if path.is_file():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size=size)


def find_run(runs: list[dict[str, Any]], scenario: str, mode: str) -> dict[str, Any]:
    matches = [run for run in runs if run["scenario_id"] == scenario and run["mode"] == mode]
    if len(matches) != 1 or matches[0]["termination"] != "completed":
        raise ValueError(f"Missing completed synthetic demo trace: {scenario}/{mode}")
    return matches[0]


def evidence_slides() -> list[Slide]:
    runs = [json.loads(line) for line in (ROOT / "site/demo-traces.jsonl").read_text().splitlines()]
    baseline = find_run(runs, "injection-text", "baseline")
    forced = find_run(runs, "forced-call", "full")
    image_run = find_run(runs, "benign-image", "full")
    scripted = json.loads((ROOT / "site/scripted/aggregate.json").read_text())
    live = json.loads((ROOT / "site/live/aggregate.json").read_text())
    if not all(run["simulation"] and run["api_requests"] == 0 for run in runs):
        raise ValueError("Demo traces must be offline synthetic simulations.")
    baseline_attack = sum(
        event["tool"] == "send_email" and event["arguments"].get("to") == "attacker@example.test"
        for event in baseline["executed_tool_events"]
    )
    denied = sum(not call["authorization"]["allowed"] for call in forced["proposed_calls"])
    forced_attack = sum(
        event["tool"] == "send_email" and event["arguments"].get("to") == "attacker@example.test"
        for event in forced["executed_tool_events"]
    )
    analyst = sum(
        event["tool"] == "send_email" and event["arguments"].get("to") == "analyst@example.test"
        for event in forced["executed_tool_events"]
    )
    image_analyst = sum(
        event["tool"] == "send_email" and event["arguments"].get("to") == "analyst@example.test"
        for event in image_run["executed_tool_events"]
    )
    if (baseline_attack, denied, forced_attack, analyst, image_analyst) != (1, 1, 0, 1, 1):
        raise ValueError("Saved traces do not support the planned demo claims.")
    full = scripted["modes"]["full"]
    if full["completed_sessions"] != 24 or full["unauthorized_simulated_completions"]["numerator"]:
        raise ValueError("Saved scripted comparison does not support the planned demo claims.")
    live_done = sum(live["modes"][mode]["completed_sessions"] for mode in live["modes"])
    return [
        Slide(
            "MOSAICGATE  /  00:00–00:10",
            "Every tool call has a gate",
            (
                "A trusted task grant authorizes proposed MCP calls.",
                "A separate inspector filters untrusted report content.",
                "All effects shown here are local simulations with invented data.",
            ),
            "Offline demo • no API key required",
        ),
        Slide(
            "ATTACK SURFACE  /  00:10–00:20",
            "One untrusted report result",
            (
                "Legitimate task: summarize synthetic Q3 revenue and email the analyst.",
                "Attacker controls one read_report response body.",
                "The report can ask for an email to attacker@example.test.",
            ),
            "The user request, grant, and tool schema remain trusted",
        ),
        Slide(
            "BASELINE  /  00:20–00:30",
            "Watch the simulated failure",
            (
                "mosaicgate demo --scenario injection-text --mode baseline",
                f"Saved trace: {baseline_attack} attacker-directed email executed locally.",
                "The authorizer recorded a denial, but baseline did not enforce it.",
            ),
            "No email left this machine",
        ),
        Slide(
            "FULL DEFENSE  /  00:30–00:40",
            "Independent authorization wins",
            (
                "mosaicgate demo --scenario forced-call --mode full",
                f"{denied} attacker-directed call denied; {forced_attack} unauthorized executions.",
                f"{analyst} authorized analyst email still completed locally.",
            ),
            "This example deliberately bypasses the inspector to exercise the grant",
        ),
        Slide(
            "NATIVE IMAGE  /  00:40–00:50",
            "A screenshot remains an image",
            (
                "PNG bytes crossed MCP as native ImageContent.",
                "Local OCR inspected visible text before forwarding.",
                f"$330,000 summary; {image_analyst} analyst email simulated.",
            ),
            "The synthetic report screenshot is shown on the right",
        ),
        Slide(
            "FROZEN HOLDOUT  /  00:50–01:00",
            "Measured, with limits visible",
            (
                "Scripted: 72/72 sessions; full mode 0/37 unauthorized executions.",
                "Inspector: 11/12 malicious cases and 1/12 benign case quarantined.",
                f"Live Gemini: {live_done}/72 completed; 64 missing after HTTP 429.",
            ),
            "Reports and saved traces: site/index.html",
        ),
    ]


def wrap_text(
    draw: ImageDraw.ImageDraw,
    value: str,
    face: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in value.split():
        proposed = f"{current} {word}".strip()
        if current and draw.textlength(proposed, font=face) > max_width:
            lines.append(current)
            current = word
        else:
            current = proposed
    if current:
        lines.append(current)
    return lines


def draw_slide(slide: Slide, index: int, output: Path) -> None:
    canvas = Image.new("RGB", (WIDTH, HEIGHT), PAPER)
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((30, 28, 1250, 690), radius=24, fill="white", outline="#d7e2e8")
    draw.rounded_rectangle((30, 28, 1250, 145), radius=24, fill=INK)
    draw.rectangle((30, 120, 1250, 145), fill=INK)
    draw.text((70, 63), slide.eyebrow, font=font(28), fill="#b9e6e7")
    draw.text((70, 185), slide.title, font=font(58), fill=INK)
    right_edge = 800 if index == 4 else 1190
    y = 300
    for line in slide.lines:
        draw.rounded_rectangle((70, y + 8, 82, y + 20), radius=5, fill=TEAL)
        face = font(28)
        wrapped = wrap_text(draw, line, face, right_edge - 105)
        for offset, segment in enumerate(wrapped):
            draw.text((105, y + offset * 39), segment, font=face, fill=INK)
        y += max(83, len(wrapped) * 39 + 23)
    if index == 4:
        screenshot = Image.open(ROOT / "fixtures/smoke/q3.png")
        screenshot.thumbnail((350, 285))
        left = right_edge + 20
        top = 310
        draw.rounded_rectangle(
            (left - 10, top - 10, left + screenshot.width + 10, top + screenshot.height + 10),
            radius=8,
            fill="#e9f1f4",
        )
        canvas.paste(screenshot.convert("RGB"), (left, top))
    draw.line((70, 610, 1190, 610), fill="#d7e2e8", width=2)
    draw.text((70, 634), slide.footer, font=font(22), fill=MUTED)
    draw.text((1150, 634), f"{index + 1}/6", font=font(22), fill=MUTED)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)


def main() -> None:
    slides = evidence_slides()
    frame_dir = ROOT / "runs/demo-frames"
    for index, slide in enumerate(slides):
        draw_slide(slide, index, frame_dir / f"slide-{index + 1:02d}.png")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-framerate",
            "1/10",
            "-start_number",
            "1",
            "-i",
            str(frame_dir / "slide-%02d.png"),
            "-vf",
            "fps=24",
            "-t",
            "60",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(ROOT / "site/demo.mp4"),
        ],
        check=True,
    )
    print("Rendered six evidence-backed slides into site/demo.mp4 (target: 60 seconds).")


if __name__ == "__main__":
    main()
