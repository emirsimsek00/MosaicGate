# MosaicGate 60-second demo

[Watch the 60-second video](demo.mp4). It is a silent, six-slide walkthrough
rendered from saved synthetic traces and aggregate results, not a recording of
a live Gemini session. Regenerate it with `uv run --locked python
scripts/render_demo.py` after installing ffmpeg.

| Time | What the video shows |
| --- | --- |
| 0:00–0:10 | The trusted task grant checks every proposed MCP call; the inspector filters returned content. |
| 0:10–0:20 | The attacker can replace one synthetic `read_report` result, not the user task or grant. |
| 0:20–0:30 | The baseline trace records one simulated attacker-directed email after a non-enforced denial. |
| 0:30–0:40 | A forced wrong call reaches the full-mode authorizer, is denied, and the analyst email still completes locally. |
| 0:40–0:50 | A native PNG traverses MCP, local OCR inspects it, and the benign summary completes. |
| 0:50–1:00 | The frozen scripted holdout and incomplete live comparison are shown with their limits. |

The values come from [the demo traces](demo-traces.jsonl),
[the scripted aggregate](scripted/aggregate.json), and
[the live aggregate](live/aggregate.json). No real email was sent.
