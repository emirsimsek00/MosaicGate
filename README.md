# MosaicGate

Task-grant enforcement on every agent tool call is MosaicGate's intended
prevention layer. A separate content inspector will examine untrusted text and
OCR-visible image text from MCP results.

**Status: foundation and native-image feasibility implemented; security enforcement and evaluation pending.**
This repository currently verifies a real local MCP boundary and simulated
side effects. It does not yet claim to prevent prompt injection. The native-image feasibility pilot passed with Gemini 3.6 Flash on a user-confirmed
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

## What is implemented

- Locked Python 3.12 package with the official MCP SDK, Google GenAI SDK, Pillow,
  pytest, Ruff, and strict mypy configuration.
- A local MCP server exposing `read_report`, `send_email`, and `write_note`.
- Native text and PNG report results; the startup configuration selects format.
- An isolated in-memory ledger. Email and note actions are **SIMULATIONS**;
  no external service is contacted. Email fixtures require reserved `.test` addresses.
- Offline diagnostic CLI, synthetic smoke fixtures, and reproducible rendering.

The fixture server is deliberately not an authorization boundary. Baseline
experiments will need to demonstrate simulated unauthorized actions. The future
controller will enforce the trusted task grant independently of that server.

## Remaining milestones

The bounded content inspector, task grants,
controller, scripted/live agent adapters, 48-case evaluation, comparison report,
and release recording remain unimplemented. The public `inspect`, `demo`, `eval`,
and `report` commands will arrive with those milestones. No attack-success,
false-positive, or prevention-rate measurements exist yet. One live native-image
pilot passed; this is feasibility evidence, not an injection-defense evaluation.

The scope excludes real email, private input data, paid model usage, audio,
steganography, general MCP proxying, and production authorization claims.

## Project records

- [Specification](docs/SPEC.md) — supplied implementation contract.
- [Verification log](docs/VERIFICATION_LOG.md) — plan, assumptions, checks, blockers.
- [Agent instructions](AGENTS.md) — setup and exact validation commands.
- [Synthetic fixture convention](fixtures/README.md).
- [Dependency and API references](docs/DEPENDENCY_NOTES.md).

MIT licensed. Development remains local and in the existing GitHub repository;
publication follows final validation.
