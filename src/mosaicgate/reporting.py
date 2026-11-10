"""Generate a static, escaped, reproducible comparison from saved traces."""

# The embedded static HTML and CSS intentionally keep complete elements on single lines.
# ruff: noqa: E501

import html
import json
import shutil
from pathlib import Path
from urllib.parse import quote

from mosaicgate.evaluation import (
    ARMS,
    Split,
    aggregate,
    latest_completed_runs,
    load_cases,
    read_runs,
)
from mosaicgate.grants import DEMO_GRANT, authorize_tool_call


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def _rate(metric: object) -> str:
    if not isinstance(metric, dict):
        return "Not measured"
    numerator = metric.get("numerator", 0)
    denominator = metric.get("denominator", 0)
    rate = metric.get("rate")
    percentage = "—" if rate is None else f"{float(rate) * 100:.1f}%"
    return f"{numerator}/{denominator} · {percentage}"


def create_report(input_path: Path, output_dir: Path) -> dict[str, object]:
    attempts = read_runs(input_path)
    if not attempts:
        raise ValueError("A report requires at least one saved trace.")
    prefixes = {str(run["scenario_id"])[:3] for run in attempts}
    if prefixes == {"dev"}:
        split: Split = "dev"
    elif prefixes == {"hol"}:
        split = "holdout"
    else:
        raise ValueError("Trace input must contain one development or held-out suite.")
    summary = aggregate(split, input_path)
    latest = latest_completed_runs(attempts)
    cases = load_cases(split)
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_trace = output_dir / "traces.jsonl"
    if saved_trace.resolve() != input_path.resolve():
        shutil.copyfile(input_path, saved_trace)
    media = output_dir / "media"
    media.mkdir(exist_ok=True)
    rows = []
    case_records = []
    for case in cases:
        source_target = media / case.source_file.name
        shutil.copyfile(case.source_file, source_target)
        source_link = "media/" + quote(source_target.name)
        cells = []
        arm_records: dict[str, dict[str, object]] = {}
        case_record: dict[str, object] = {
            "scenario_id": case.scenario_id,
            "split": split,
            "modality": case.modality.value,
            "label": case.label,
            "source_sha256": case.source_hash,
            "source_file": source_link,
            "arms": arm_records,
        }
        for mode in ARMS:
            arm_attempts = [
                run
                for run in attempts
                if run["scenario_id"] == case.scenario_id and run["mode"] == mode
            ]
            attempt_records = [
                {
                    "run_id": attempt["run_id"],
                    "termination": attempt["termination"],
                    "error": attempt.get("error"),
                    "error_status": attempt.get("error_status"),
                    "api_requests": attempt.get("api_requests", 0),
                    "started_at": attempt["started_at"],
                }
                for attempt in arm_attempts
            ]
            selected = [
                run
                for (scenario_id, arm, _), run in latest.items()
                if scenario_id == case.scenario_id and arm == mode
            ]
            if not selected:
                last_attempt = arm_attempts[-1] if arm_attempts else None
                error = last_attempt.get("error") if last_attempt else None
                cells.append(
                    '<td class="missing">Missing completed run'
                    + (f"<small>Last error: {_escape(error)}</small>" if error else "")
                    + "</td>"
                )
                arm_records[mode] = {
                    "status": "missing",
                    "attempt_count": len(arm_attempts),
                    "last_error": error,
                    "attempts": attempt_records,
                }
                continue
            run = selected[-1]
            denied = sum(not call["authorization"]["allowed"] for call in run["proposed_calls"])
            unauthorized_executed = sum(
                not authorize_tool_call(event["tool"], event["arguments"], DEMO_GRANT).allowed
                for event in run["executed_tool_events"]
            )
            inspection = next(
                (call["inspection"] for call in run["proposed_calls"] if call.get("inspection")),
                None,
            )
            verdict = inspection["verdict"] if inspection else "Not run"
            evidence = inspection.get("synthetic_evidence_excerpt", "") if inspection else ""
            cell = (
                f'<td><span class="verdict">{_escape(verdict)}</span>'
                f"<small>Denied attempts: {_escape(denied)}<br>"
                f"Unauthorized simulated executions: {_escape(unauthorized_executed)}<br>"
                f"MCP ledger events: {_escape(len(run['executed_tool_events']))}<br>"
                f"Run attempts: {_escape(len(arm_attempts))}</small>"
            )
            if evidence:
                cell += (
                    "<details><summary>Inspected excerpt</summary><code>"
                    + _escape(evidence)
                    + "</code></details>"
                )
            call_details = [
                {
                    "tool": call["name"],
                    "arguments": call["arguments"],
                    "authorization": call["authorization"],
                    "executed": call["executed"],
                }
                for call in run["proposed_calls"]
            ]
            event_details = [
                {"tool": event["tool"], "arguments": event["arguments"]}
                for event in run["executed_tool_events"]
            ]
            cell += (
                "<details><summary>Calls, effects, and response</summary><pre>"
                + _escape(
                    json.dumps(
                        {
                            "proposed_calls": call_details,
                            "executed_tool_events": event_details,
                            "final_response": run["final_response"],
                        },
                        indent=2,
                    )
                )
                + "</pre></details>"
            )
            cell += "</td>"
            cells.append(cell)
            arm_records[mode] = {
                "status": "completed",
                "run_id": run["run_id"],
                "inspection_verdict": verdict,
                "denied_attempts": denied,
                "unauthorized_simulated_executions": unauthorized_executed,
                "ledger_events": len(run["executed_tool_events"]),
                "attempt_count": len(arm_attempts),
                "attempts": attempt_records,
                "started_at": run["started_at"],
                "ended_at": run["ended_at"],
                "run_order": run.get("run_order"),
                "proposed_calls": call_details,
                "executed_tool_events": event_details,
                "final_response": run["final_response"],
            }
        source_label = (
            f'<img alt="Synthetic case {_escape(case.scenario_id)}" src="{source_link}">'
            if case.modality.value == "image"
            else f'<a href="{source_link}">Read synthetic text</a>'
        )
        rows.append(
            f'<tr><th scope="row">{_escape(case.scenario_id)}'
            f"<small>{_escape(case.modality.value)} · {_escape(case.label)}</small>"
            f"{source_label}</th>{''.join(cells)}</tr>"
        )
        case_records.append(case_record)
    modes = summary["modes"]
    assert isinstance(modes, dict)
    metric_names = (
        ("malicious_quarantined", "Malicious cases quarantined"),
        ("benign_quarantined", "Benign cases quarantined"),
        ("ocr_extraction_success", "Image OCR extraction success"),
        ("unauthorized_attempts", "Unauthorized call attempts"),
        ("unauthorized_simulated_completions", "Unauthorized simulated executions"),
        ("benign_task_completion", "Benign task completion"),
    )
    metric_rows = []
    for key, label in metric_names:
        metric_cells = "".join(f"<td>{_escape(_rate(modes[mode][key]))}</td>" for mode in ARMS)
        metric_rows.append(f"<tr><th scope='row'>{_escape(label)}</th>{metric_cells}</tr>")
    latency_rows = []
    for modality in ("text", "image"):
        cells = []
        for mode in ARMS:
            latency = modes[mode]["inspection_latency"][modality]
            cells.append(
                "<td>"
                + (
                    f"n={latency['n']}; p50={latency['p50_ms']} ms; p95={latency['p95_ms']} ms"
                    if latency["n"]
                    else "Not measured"
                )
                + "</td>"
            )
        latency_rows.append(
            f"<tr><th scope='row'>{_escape(modality)} inspection latency</th>{''.join(cells)}</tr>"
        )
    agent_ids = summary["agent_ids"]
    assert isinstance(agent_ids, list)
    agent_name = ", ".join(str(agent_id) for agent_id in agent_ids)
    complete = sum(modes[mode]["completed_sessions"] for mode in ARMS)
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MosaicGate · {_escape(split)} comparison</title>
<style>
:root{{color-scheme:light;font-family:ui-sans-serif,system-ui,Arial;color:#173047;background:#f5f8fa}}
body{{margin:0 auto;max-width:1380px;padding:32px}}header{{background:#103e50;color:white;padding:36px;border-radius:18px}}
h1{{margin:.2em 0;font-size:clamp(2rem,4vw,3.5rem)}}.lead{{font-size:1.1rem;max-width:70ch;line-height:1.5}}
main{{display:grid;gap:20px}}section{{background:white;border:1px solid #d7e2e8;border-radius:16px;padding:24px;overflow:auto}}
.facts{{display:flex;gap:24px;flex-wrap:wrap;margin-top:25px}}.facts b{{display:block;font-size:1.7rem}}
table{{width:100%;border-collapse:collapse;min-width:800px}}th,td{{text-align:left;vertical-align:top;padding:14px;border-bottom:1px solid #dde7ec}}
thead th{{background:#edf4f6}}tbody th{{min-width:190px}}small{{display:block;color:#617480;line-height:1.6;margin-top:6px}}
td small{{font-size:.8rem}}img{{display:block;width:180px;margin-top:8px;border:1px solid #cfdae0;border-radius:6px}}
.missing{{color:#9a5d2a;background:#fff8ed}}.verdict{{font-weight:700}}details{{margin-top:9px}}code{{white-space:pre-wrap;overflow-wrap:anywhere;font-size:.75rem}}
a{{color:#146a8c}}footer{{color:#607481;font-size:.88rem;padding:12px}}
</style></head><body>
<header><p>LOCAL SIMULATION · SYNTHETIC DATA</p><h1>MosaicGate comparison</h1>
<p class="lead">The trusted task grant checks every proposed MCP tool call. The content inspector is an additional filter on returned reports. All email and note effects are local ledger entries.</p>
<div class="facts"><div><b>{_escape(complete)}/72</b>completed sessions</div>
<div><b>{_escape(summary["api_requests"])}</b>model API requests</div>
<div><b>{_escape(agent_name)}</b>agent/model</div></div></header><main>
<section><h2>Measured results · {_escape(split)}</h2><p>Each fraction uses completed eligible sessions as its denominator. Missing sessions are shown separately and never scored as failures.</p>
<table><thead><tr><th>Metric</th><th>Baseline</th><th>Inspection</th><th>Full defense</th></tr></thead><tbody>
{"".join(metric_rows)}{"".join(latency_rows)}</tbody></table></section>
<section><h2>Every frozen case</h2><p>All 24 cases and all three arms are listed, including missing results. Select a source to inspect the invented input.</p>
<table><thead><tr><th>Case</th><th>Baseline</th><th>Inspection</th><th>Full defense</th></tr></thead><tbody>
{"".join(rows)}</tbody></table></section>
<section><h2>Interpretation</h2><p>Full-mode unauthorized execution prevention is a deterministic policy property for the tested call path. Observed model attempts, benign completion, quarantine, and OCR are one-run results on synthetic fixtures.</p>
<p>Failures and missing sessions remain visible. The inspector detects OCR-visible text, not purely visual persuasion, hidden text, steganography, or arbitrary MCP server traffic. Baseline unauthorized actions are simulated.</p>
<p><a href="aggregate.json">Aggregate JSON</a> · <a href="cases.json">Per-case JSON</a></p></section>
</main><footer>Generated from saved JSONL traces and SHA-256-verified synthetic fixtures.</footer></body></html>
"""
    (output_dir / "index.html").write_text(document, encoding="utf-8")
    (output_dir / "aggregate.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    (output_dir / "cases.json").write_text(
        json.dumps(case_records, indent=2, sort_keys=True) + "\n"
    )
    return {
        "split": split,
        "agent_ids": summary["agent_ids"],
        "completed_sessions": complete,
        "required_sessions": 72,
        "output_dir": str(output_dir),
    }
