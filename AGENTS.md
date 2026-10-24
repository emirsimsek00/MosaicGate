# Working on MosaicGate

The source of truth is `docs/SPEC.md`. Read `docs/VERIFICATION_LOG.md` for current
status, assumptions, actual check results, and outstanding prerequisites. Work
in this existing checkout; preserve user files. Do not create another repository
or checkout. The current build is authorized through validation and publication;
plans and step gates are internal records, never user review gates.

## Setup

Python 3.12, uv, and Tesseract with English language data are required.

```sh
# macOS (when missing)
brew install uv tesseract
uv sync --locked
```

This macOS session repeatedly marked the generated editable-install `.pth`
file hidden, including before MCP subprocess startup. A regular wheel install
avoids dependence on that path file. For this session use the following after
source changes, and add `--no-editable` to each `uv run` gate command:

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv sync --locked --offline --no-editable --reinstall-package mosaicgate
UV_CACHE_DIR="$PWD/.cache/uv" uv run --locked --no-editable pytest
```

On Debian/Ubuntu install `tesseract-ocr` and `tesseract-ocr-eng` with apt.
For a sandbox-local Python installation/cache in this checkout:

```sh
export UV_PYTHON_INSTALL_DIR="$PWD/.tools/python"
export UV_CACHE_DIR="$PWD/.cache/uv"
uv sync --locked
```

## Full gate commands

Run all three gates after every numbered milestone, record observed results,
commit, and push to origin before starting the next milestone:

```sh
uv run --locked pytest
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
```

## Implementation constraints

- All side effects are local simulations. Never send email or touch real data.
- Never enable billing or use a paid model tier. Live calls require a credential
  for a confirmed free/unbilled project. Never make model API calls in CI.
- Preserve native MCP image blocks. Keep transport independent from inspection.
- Every eventual controller tool call must go through the authorizer, including
  reads. Gemini automatic function execution must remain disabled.
- No raw content or credentials in default logs. Any published evidence must be
  synthetic. Never print `.env` or secret values.
- Split evaluation cases before creating variants; freeze holdout before tuning.
- Do not claim a test, integration, result, or recording exists without running
  or inspecting it. Distinguish deterministic results from live model behavior.
- If a step fails, preserve diagnostics and restore only agent-owned uncommitted
  implementation changes to the last green revision; retry a smaller increment.
  Record three repeated failures of an approach before changing approach.

## Current state

Step 1 is complete and pushed (`c59e9a8`): seven actual MCP integration tests,
Ruff, formatting, and strict mypy passed. Diagnostics are available as:

```sh
uv run --locked mosaicgate doctor
uv run --locked mosaicgate smoke --modality text
uv run --locked mosaicgate smoke --modality image
```

Step 2 native-image feasibility passed with Gemini 3.6 Flash. The key and user
confirmation of Free tier/billing disabled are in ignored `.env`. Six pilot
requests include three failed sessions and one complete two-request success;
all evidence is in `docs/evidence/feasibility.jsonl`. Fourteen offline tests pass.
The current model is `gemini-3.6-flash`, with model-default sampling and low
thinking. Preserve full returned model content and IDs; function responses use
role `user` and native image bytes. Automatic tool execution stays disabled.

Next is Step 3 (bounded inspector); then follow the sequential log checklist.
GitHub SSH pushes work; GitHub CLI is unauthenticated, so release visibility
management still needs authentication. See the verification log for evidence.
