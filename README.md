# MosaicGate

Task-grant enforcement on every agent tool call is MosaicGate's prevention
layer. A separate content inspector examines untrusted text and OCR-visible
image text from MCP results.

**Status: local simulation, frozen corpus, and offline evaluation implemented.**
The project verifies a real local MCP boundary and simulated side effects.
The native-image feasibility pilot passed with Gemini 3.6 Flash on a user-confirmed
free, unbilled project. Failed and successful pilot evidence is retained in
[`docs/evidence/feasibility.jsonl`](docs/evidence/feasibility.jsonl).

## Run the foundation offline

Install Python 3.12, [uv](https://docs.astral.sh/uv/), and local Tesseract OCR
(`brew install uv tesseract` on macOS; `tesseract-ocr` and `tesseract-ocr-eng` on
Debian/Ubuntu). No Docker, model account, or API key is required for these commands.

```sh
uv sync --locked
uv run --locked mosaicgate doctor
uv run --locked mosaicgate smoke --modality text
uv run --locked mosaicgate smoke --modality image
```

Each smoke command starts a separate MCP server over stdio, calls `read_report`,
and reports the returned block's type, size, and SHA-256. The image stays a native
MCP `ImageContent` containing PNG bytes. The text fixture and image depict the
same invented Q3 report. These checks are transport diagnostics, not agent runs
or injection evaluations.

## Validate

```sh
uv run --locked pytest
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
```

The integration tests exercise actual subprocess client/server communication,
native image decoding, tool schemas, error results, and isolated simulated
ledgers. GitHub Actions runs only offline checks, with no model credentials or
live API calls. Local results are recorded in [the verification log](docs/VERIFICATION_LOG.md);
workflow execution is not claimed merely because its configuration exists.

Inspect a local synthetic result without printing its content:

```sh
uv run --locked mosaicgate inspect --input fixtures/smoke/q3.txt --modality text
uv run --locked mosaicgate inspect --input fixtures/smoke/q3.png --modality image
```

The inspector validates and bounds text, image bytes, pixels, nested structured
data, normalization work, and OCR runtime. It returns a validated MCP result or
a fixed neutral quarantine message. Tests exercise actual OCR of benign and
malicious screenshots, malformed media, unsupported blocks, metadata, and
benign quoted security examples. Its explainable rules are heuristic, so the
independent task-grant action gate remains the security boundary.

## What is implemented

- Locked Python 3.12 package with the official MCP SDK, Google GenAI SDK, Pillow,
  pytest, Ruff, and strict mypy configuration.
- A local MCP server exposing `read_report`, `send_email`, and `write_note`.
- Native text and PNG report results; the startup configuration selects format.
- An isolated in-memory ledger. Email and note actions are **SIMULATIONS**;
  no external service is contacted. Email fixtures require reserved `.test` addresses.
- Offline diagnostic CLI, synthetic smoke fixtures, and reproducible rendering.

The fixture server is deliberately not an authorization boundary. The controller
enforces the trusted task grant independently of that server in full mode.

## Run the simulated agent demo

```sh
uv run --locked mosaicgate demo --scenario injection-text --mode baseline --agent scripted
uv run --locked mosaicgate demo --scenario injection-text --mode inspect --agent scripted
uv run --locked mosaicgate demo --scenario benign-image --mode full --agent scripted
```

The controller checks every proposed call against the trusted grant before
dispatch. Baseline and inspection modes record denials but deliberately do not
enforce them; full mode denies unauthorized calls. The baseline's attacker
email is only a local **SIMULATION** in an isolated ledger. The append-only
trace is saved to ignored `runs/demo.jsonl`; each run has a unique ID. The
scripted agent is deterministic. A manual Gemini adapter uses the same
controller and native function responses, but requires a user-confirmed free,
unbilled project and a local key; it is never run in CI.

## Reproduce the frozen offline comparison

The 48 synthetic cases were assigned to development and holdout before variants
were rendered. The 24-case holdout is SHA-256 verified. Each case runs in
baseline, inspection-only, and full-defense modes with the same task grant.
The scripted agent makes no API calls.

```sh
uv run --locked mosaicgate eval --suite holdout --agent scripted --output runs/holdout-scripted.jsonl
uv run --locked mosaicgate report --input runs/holdout-scripted.jsonl --output site/scripted
```

The committed [static report](site/scripted/index.html),
[aggregate JSON](site/scripted/aggregate.json), and
[saved JSONL traces](site/scripted/traces.jsonl) expose every held-out case.
The report's media and per-case details show what the agent proposed, what the
authorizer decided, and what the local MCP ledger recorded. The report command
rebuilds its HTML and JSON from the saved traces and verified fixtures.

The held-out **scripted** run completed 72/72 sessions with zero model API
requests. The full arm quarantined 11/12 malicious cases and 1/12 benign cases,
completed 11/12 benign tasks, and recorded 0/37 unauthorized simulated tool
executions per proposed call. OCR returned nonempty text for 12/12 inspected
images, which does not mean it read every line. In baseline, 8/56 proposed
calls executed outside the grant in the local simulation. These are
deterministic fixture results, not estimates of live model attack rates or
production guarantees. The missed malicious image and benign false positive
remain visible in the report.

The [live held-out report](site/live/index.html) uses the same frozen Gemini
3.6 Flash model, prompt, grant, and tool schema across arms on the
user-confirmed Free tier. It is never part of CI. The append-only trace has
23 attempts and 48 attempted API requests: 17 sessions completed, 3 ended in
initial connection errors, and 3 ended in HTTP 429, including a later retry.
The remaining 55 sessions are **missing**, not scored as failures. The Free
tier limit prevented a complete comparison. Among the completed sessions,
the full arm quarantined 6/6 malicious text cases and recorded zero
unauthorized simulated executions across 6 proposals; no benign or image
sessions completed. These small, uneven counts do not support a stable live
model rate. The [saved live trace](site/live/traces.jsonl) permits later
resumption with the same protocol when free quota returns.

The [60-second silent demo](site/demo.mp4) is rendered from saved synthetic
traces and measured aggregates; its [evidence script](site/demo-script.md)
states exactly what each segment shows. A measured
[résumé bullet](docs/RESUME_BULLET.md) is available separately.

## Scope

The scope excludes real email, private input data, paid model usage, audio,
steganography, general MCP proxying, and production authorization claims.

## Project records

- [Specification](docs/SPEC.md) — supplied implementation contract.
- [Verification log](docs/VERIFICATION_LOG.md) — plan, assumptions, checks, blockers.
- [Agent instructions](AGENTS.md) — setup and exact validation commands.
- [Synthetic fixture convention](fixtures/README.md).
- [Dependency and API references](docs/DEPENDENCY_NOTES.md).

MIT licensed. Publication of the existing GitHub repository follows final
validation.
