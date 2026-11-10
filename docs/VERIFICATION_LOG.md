# MosaicGate verification log

## Build plan — recorded before Step 1 implementation

Date: 2026-10-23 (America/Denver). The user's current request authorizes the
build, sequential internal validation gates, commits and pushes, and publication
after validation. No plan or milestone review is required.

### Architecture in my own words

MosaicGate puts an independent permission check between an agent and a small
local MCP server. A trusted scenario supplies an immutable task grant. Every
proposed call passes through a single controller dispatch function; an inspector
separately validates and examines untrusted tool results. The inspector returns
either bounded, canonicalized content or a fixed neutral quarantine message.
Text, nested structured data, and OCR-visible image text are inspected. Unsupported
content and extraction failures fail closed. Simulated emails and notes stay in
an isolated local ledger, and all fixtures contain invented data.

The MCP transport, inspection, authorization, agent adapters, and JSONL trace
writer are separate modules. A scripted agent exercises the same controller as a
manual Gemini adapter without any API key. Baseline, inspection-only, and full
defense share the same task, grant, tool definitions, and agent settings. Traces
separate proposed calls, decisions, and server-confirmed executions. Saved traces
produce aggregate JSON and an escaped static report; measured live behavior is
kept separate from deterministic tests and offline scripted results.

### Sequential checklist

- [x] 1. Foundation: preserve checkout; copy spec; initialize locked Python 3.12
  uv package; README, license, CI, environment example, fixture conventions;
  exercise text and native images through a real MCP client/server; full pytest,
  Ruff, type check; commit and push.
- [x] 2. Feasibility: verify a free/unbilled Gemini project and current model;
  run a manual native-image function-response cycle, preserving model context;
  record actual evidence; full checks; commit and push.
- [x] 3. Inspector: bounded validation, OCR, normalization, structured content,
  reason codes, safe forwarding and quarantine; negative and benign tests;
  full checks; commit and push.
- [x] 4. Authorization and controller: strict grants, single dispatch path,
  ledger, scripted adapter and three modes; unauthorized-attempt/denial and
  benign-completion tests; full checks; commit and push.
- [x] 5. Evaluation: 48 original pre-split synthetic fixtures; freeze holdout
  before tuning; offline regression; free-tier live comparison when possible;
  append-only/resumable evidence, aggregate JSON and static report; full checks;
  commit and push.
- [x] 6. Release: offline end-to-end and clean-install validation, 60-second
  recording, measured resume bullet, honest implemented/measured/future docs;
  full checks; commit and push; publish validated repository.

### Ambiguities and adopted assumptions

1. The handoff's opening says no repository exists, but the current user request
   and inspected checkout take precedence. Use only this checkout and preserve
   the existing README. Initial commit: `496de70` (`Initial commit`); clean `main`.
2. Step 6 requests a fresh clone while the user prohibits a second checkout.
   Validate a clean exported source archive in a temporary directory with a new
   environment instead; also verify the pushed remote revision. Do not clone.
3. Step 2 allows independent offline work while waiting, but the user requires
   strict step order. Finish Step 1 and stop at the credential gate if missing;
   never mark Step 2 complete or begin Step 3 before live feasibility succeeds.
4. An API key alone does not prove a project is free/unbilled. Require verified
   project status or explicit user confirmation of Free tier with billing off.
   Never enable billing; never put model requests or credentials in CI.
5. The spec gives suggested/current model IDs. Recheck official docs, select a
   supported free Gemini 3 model during preflight, and freeze it for a complete
   experiment. Model availability is not inferred from the plan.
6. Use MIT for this portfolio project's new code. Preserve existing content and
   ownership. Default logs exclude raw content; checked-in evidence is synthetic.
7. Live quota exhaustion leaves missing sessions, not invented failures or
   measurements. Cap all live experiment requests at 300, persist accounting,
   and never change model or enable billing to finish a run.
8. Each milestone begins from a green commit. On a failed implementation check,
   preserve diagnostic evidence, restore only this agent's uncommitted changes
   to the last green state, and retry a smaller increment. Never discard user
   files. Log three repeated failures of the same approach and change approach
   or report an external blocker.
9. Publishing means changing the existing GitHub repository to public after
   release validation, not creating a hosted service or another repository.

## Initial inspection

- Existing directory: `/Users/emir/Desktop/mosaic gate/MosaicGate`.
- Tracked file: `README.md`; no pre-existing AGENTS.md in the ancestor chain.
- Remote: `git@github.com:emirsimsek00/MosaicGate.git`; reachability pending.
- `uv`, Homebrew, GitHub CLI, Git, and ffmpeg found on PATH.
- Python 3.12 and Tesseract not found on PATH; installation/verification pending.
- `GEMINI_API_KEY` and `GOOGLE_API_KEY` absent from the process environment.
  No `.env` in the repository or its parent. No secret values were printed.
- Prior planning notes were consulted for continuity; the current handoff and
  current authorization supersede the older paused-build state.
- No test, live model call, measurement, or publication has run yet.

## Step 1 — foundation

Complete. All required checks passed; implementation commit
`c59e9a89adc0c2825d1e9f5730cf9e5c47842880` was pushed to `origin/main`.


### Step 1 validation — executed

- Verified SSH remote reachability: `origin` advertises `main` and `HEAD` at
  `496de70c64c8932169309f58cdc367dbfc7b492a`. The URL matches the user's existing
  `emirsimsek00/MosaicGate` repository. No repository or checkout was created.
- Initial sandbox network requests could not resolve GitHub. The uv downloader
  made its three automatic retries, all DNS failures. Recorded this failed
  approach and used the authorized network-enabled command instead; download
  and SSH verification then succeeded. No repeated implementation patching.
- Installed uv-managed Python 3.12.14 locally, resolved and locked 60 packages;
  runtime packages include MCP 2.3.0, google-genai 2.33.0, and Pillow 13.0.0.
- Installed Tesseract 5.5.3 through Homebrew with required dependencies; `eng`
  and `osd` language data are present. Homebrew also updated required shared
  dependencies; it did not install model services or enable any billing.
- `uv run --locked pytest`: **7 passed in 2.56s**, actual stdio subprocess tests.
- `uv run --locked ruff check .`: **passed**.
- `uv run --locked ruff format --check .`: **passed**, 13 files formatted.
- `uv run --locked mypy`: **passed**, no issues in 8 source files (strict mode).
- `mosaicgate doctor`: Python, package versions, Tesseract, and English data
  present; zero live API requests.
- Text MCP smoke: 205 bytes, SHA-256
  `a99bf08ba934f3af6a6b79bf38c321104230f5a7c51debda791782a74a680a35`.
- Native PNG MCP smoke: 34,044 bytes, 1200 x 420 pixels, SHA-256
  `b5f0eb13e81e854542affcb48ee74a4e6bb094e4a05358af1bf10d01c483bd13`.
- Rendered PNG visually inspected: all seven report lines visible. Direct local
  Tesseract extraction returned all report values, growth, and synthetic canary.
  This is a single smoke fixture, not OCR evaluation coverage or accuracy.
- Tests cover native text/image transport, exact exposed tool schemas, local
  simulated actions, ledger isolation, missing reports, and rejection of a
  non-`.test` recipient without a ledger effect. There is no action-gate or
  injection-detector claim yet.
- Original README heading retained and expanded with current-state boundaries.
  `docs/SPEC.md` is an exact copy of the supplied handoff.
- CI configuration added; a hosted GitHub Actions result has not been observed.
- GitHub CLI has no authenticated account in this environment. SSH operations
  work; API-based visibility verification/change will require an authenticated
  route before release. Repository visibility has not been changed.
- Step 1 checks are green; commit and push verification pending below.
- The additional staged whitespace check flagged two Markdown hard line breaks
  already present in the supplied spec. Preserved the required byte-for-byte
  copy and scoped a Git whitespace attribute to `docs/SPEC.md`; no executable
  source or test failed, and no implementation rollback was needed.

### Step 1 backup verified

- Commit: `c59e9a89adc0c2825d1e9f5730cf9e5c47842880` —
  `build: establish validated offline MCP foundation`.
- `git push origin main` succeeded (`496de70..c59e9a8 main -> main`).
- Working tree was clean after that push, with `main` tracking `origin/main`.
- Verified `docs/SPEC.md` byte-for-byte against the supplied file. SHA-256:
  `90fa1b0a7a38bcb1fa36bbd9fbc266f527df93b6f82f2b726c242ca7fc9a00c5`.

## Step 2 — feasibility gate: blocked on user credential

Entered only after Step 1 passed and its implementation was pushed.

- Rechecked `GEMINI_API_KEY` and `GOOGLE_API_KEY`: both absent from the process
  environment. Checked repository `.env*` files excluding `.env.example`:
  zero local credential files. No credential values were printed or committed.
- No free/unbilled project confirmation is available. The presence of a free
  model on Google's pricing page cannot establish this account's billing state.
- Asked the user to put `GEMINI_API_KEY` in the ignored repository `.env`, using
  `.env.example` as the template, and confirm Free tier with billing disabled.
  This is the credential stop explicitly required by the user's request and
  spec section 5 step 2, not a plan or approval review.
- Zero live API requests, zero feasibility sessions, zero live comparison
  sessions. The native-image Gemini cycle has **not** been tested.
- Steps 3–6 have not been started because the required sequential gate is
  incomplete. No inspector, authorization guarantee, evaluation rate, generated
  comparison report, recording, or publication is claimed.
- GitHub CLI authentication remains a later release prerequisite for API-based
  visibility management; existing SSH pushes succeed. No visibility change has
  been attempted.

### Resume procedure

1. Read this log and `AGENTS.md`; use the same checkout and locked dependencies.
2. Check for the local key without printing it. Establish that its project is
   Free tier and billing is disabled; user confirmation is acceptable.
3. Recheck model availability and execute the minimal manual native-image
   function cycle using real MCP output. Preserve call IDs and model context,
   disable automatic function execution, and save synthetic-only evidence.
4. Diagnose any pilot failure against the official docs before implementing the
   full adapter. Pass all gates, commit, and push Step 2 before Step 3.
5. Continue the remaining checklist autonomously; never request plan reviews.

### Step 2 resumed — prerequisite and environment diagnosis

- User supplied a local key and then explicitly confirmed: Free tier, billing
  disabled. Recorded that attestation in ignored `.env`; this is user
  confirmation, not an independent billing API audit. No secret values printed.
- Initial pilot increment passed Ruff and strict mypy, but pytest could not
  import even the original package. Saved the increment outside the checkout,
  restored executable source to the last green commit, and reproduced the
  same failure on the unchanged seven-test baseline.
- Three import/check attempts encountered the same generated `.pth` issue.
  Diagnosis: macOS flags `32832` include `UF_HIDDEN`; Python 3.12.14's `site.py`
  explicitly skips hidden `.pth` files. Clearing only that generated install
  file's hidden flag restored both direct and `uv run` imports. The flag
  reappeared between tool invocations, so clear it immediately before local
  gates. Do not modify application imports or weaken tests to conceal this.
- A reinstall attempt failed during sandbox DNS resolution for hatchling after
  three automatic downloader retries. Changed approach to the verified file
  flag repair; no dependency or lockfile change was necessary.
- Retrying in smaller increments: live settings first, then the pilot and its
  contract tests. The complete feasibility gate still requires a real run.
- Clearing the hidden flag fixed direct imports but did not remain effective
  for the MCP subprocess. Changed to a regular wheel install using
  `uv sync --locked --offline --no-editable --reinstall-package mosaicgate`;
  subsequent commands use `uv run --locked --no-editable`. Baseline restored:
  **7 passed in 2.39s**. No application transport change or test bypass.
- Restored the pilot increment; **14 tests passed in 2.63s**, Ruff and formatting
  passed, strict mypy passed on 11 source files.
- First actual pilot request returned HTTP 503 (`ServerError`) before any tool
  call. Preserved the failed run in `docs/evidence/feasibility.jsonl`.
  One live request attempted; native-image receipt is not yet verified.
- Official troubleshooting documentation permits bounded retries on HTTP 503.
  It also now states that Gemini 3.6+ ignores custom sampling settings, with
  future rejection planned. Adopted the actually supported model default by
  omitting temperature rather than falsely claiming temperature zero. Record
  this constraint in live settings and freeze it across comparison arms.
  Source: https://ai.google.dev/gemini-api/docs/troubleshooting
- Second 3.8 attempt returned HTTP 504 (deadline expired) before a tool call.
  Selected the spec's documented free 3.6 Flash fallback for a fresh pilot;
  no comparison experiment has begun, so there is no mixed-model dataset.
- First 3.6 pilot proposed the fixed Q3 read, retained its call ID and thought
  signature, and received actual MCP PNG bytes. The native-response request
  returned HTTP 400. At this point: four generation requests total, zero
  successful complete native-image sessions.
- Diagnosed against the official Generate Content multimodal example. It uses
  role `user` for function-response content; the initial pilot incorrectly used
  `tool`. Saved the failed increment, restored the source/test tree to the last
  green revision, and reapplied it with that one-field correction and a
  regression assertion. No OCR substitution or alternate image path.
  Source: https://ai.google.dev/gemini-api/docs/generate-content/function-calling.md


### Step 2 outcome — native-image feasibility passed

- Successful run `ca9353a6-4799-4495-8c11-075d02f350f5` used
  `gemini-3.6-flash` (returned model version matches), two generation requests,
  and took 3,986.7 ms. This is one pilot timing, not a latency distribution.
- The model proposed `read_report(report_id="q3")`; the fixed pilot permission
  check allowed it. Real MCP returned the 34,044-byte native PNG. Its bytes were
  nested inside `FunctionResponse.parts`; the full model turn and call ID were
  retained. The second response correctly read all three monthly revenues,
  $330,000 total, and 20% growth. No OCR text was supplied to Gemini.
- Four pilot sessions were attempted: two 3.8 service failures, one 3.6 payload
  rejection, and one complete 3.6 success. **Six total generation requests**.
  Failed traces remain present; no comparison sessions have been run.
- Selected 3.6 Flash for subsequent live work and set the local/sample model
  default accordingly. No paid tier, priority mode, billing change, or external
  side effect was used. Free-project status is based on user confirmation.
- The final adapter must use role `user` for function responses and preserve
  the returned model content object, call IDs, and thought context. Automatic
  SDK tool execution stays disabled. Use native image parts, never OCR text
  as a substitute for model-visible images.
- Offline checks passed after the role correction: **14 passed in 2.41s**;
  Ruff check and format passed; strict mypy passed on 11 source files.
- A final full check after updating the selected default precedes the commit
  and push. Step 3 starts only after that push succeeds.

## Step 3 — inspector (resumed 2026-10-26)

- Implemented `inspect_tool_result(result, context)` with stable PASS/QUARANTINE
  verdicts, reason codes, input hash, extraction state, local analysis text,
  elapsed time, and safe forwarded MCP result. Default `decision_record` omits
  content; an explicitly synthetic excerpt is HTML-escaped.
- Supports text, native PNG/JPEG/WebP, and recursively inspected structured
  content and metadata. Rejects audio, resources, unsupported or malformed
  images, oversized inputs, deep data, too many blocks/nodes, OCR failures,
  OCR timeout, and empty OCR output. Text, decoded media, pixels,
  normalization work, and OCR runtime are bounded. Quarantines return only the
  fixed neutral message with no original metadata.
- The official MCP SDK discards unknown wire fields on parsing. The inspector
  does not claim to have examined data that was already discarded; its safe
  forwarded result includes only known validated fields. This is covered by a
  regression test.
- Explainable rule categories cover role spoofing, direct instructions, off-task
  tool commands, and exfiltration destinations. Quoted security examples pass
  focused tests. These heuristics are not a complete attack detector, and the
  independent action gate remains essential.
- Resumed WIP initially had two failed tests and two mypy errors. Corrected a
  repeated base64 decode, typed bounded metadata maps, and replaced an
  impossible unknown-wire-field test with an SDK-discard regression. Checks then
  passed; no user file was discarded.
- Final Step-3 full gate: **64 passed in 3.32s**; Ruff check passed; Ruff format
  passed (19 files); strict mypy passed (13 source files).
- Actual MCP image and actual OCR tests pass. The malicious PNG text is detected
  and replaced by the neutral quarantine message. Local `mosaicgate inspect`
  returned PASS for both synthetic smoke fixtures. One smoke run measured
  0.548 ms for text and 141.938 ms for image; these are single-run timings,
  not benchmark percentiles.
- No Gemini comparison sessions have been run in Step 3.
- Commit and push will be recorded after execution below.

## Step 4 — trusted grant, controller, and adapters (2026-10-26)

- `authorize_tool_call` admits only `read_report(report_id="q3")` and
  `send_email(to="analyst@example.test", body=<nonempty bounded string>)`.
  Unknown tools, extra keys, wrong types, other reports, and other recipients
  are denied. The grant is built from trusted scenario configuration, not MCP
  content.
- The controller owns the only `client.call_tool` dispatch. It records every
  proposed call, the grant decision, whether enforcement was on, inspection
  result, and whether the server was called. It reads the isolated simulation
  ledger after runs, including error runs. Turn and call limits cap loops.
- Baseline and inspection-only deliberately record but do not enforce grant
  denials. Full mode enforces the grant before **every** proposed tool call.
  The server's email/note actions remain local simulations with `.test` only.
- Added scripted and manual Gemini adapters. The Gemini adapter disables SDK
  automatic function execution, exposes the same three tool schemas, preserves
  call IDs and the whole model content turn, and sends native image bytes in
  nested function-response parts. No model API calls run in CI.
- Focused deterministic tests: baseline executed one simulated attacker email
  after an injected report; inspection quarantined that attack; full mode
  denied a forced unauthorized attempt even when the inspector passed the
  benign report; benign text/image tasks completed with authorized email.
  A fault test confirms actual server executions remain in the ledger after
  an agent error. These are scripted results, not observed attack rates.
- Manual scripted CLI demonstrations ran for injection baseline, injection
  inspection, and benign-image full mode. Trace files under ignored `runs/`
  are append-only; the CLI prints summary counts without raw report text.
- First live Gemini controller demo proposed two wrong report IDs and the
  grant denied both. Clarified the trusted q3 ID in the prompt and tool schema.
  Two subsequent diagnostic runs reached an authorized MCP image read but got
  HTTP 400 on the model's function-response request. The original payload used
  an image `$ref` array; restoring the exact native-image response shape that
  passed Step 2 resolved it. All unsuccessful local traces were retained.
- Successful live benign-image run `a1bc903d-4bf6-40c5-98cb-9a281d576eb2`
  used frozen candidate `gemini-3.6-flash`: 3 API requests, 2 authorized MCP
  executions, no unauthorized attempt, correct $100,000/$110,000/$120,000
  monthly values, $330,000 total, 20% change, and a simulated email to the
  authorized recipient. This is **one task completion**, not a rate estimate.
  Source trace: ignored `runs/live-demo.jsonl`; selected evidence may be
  published later after review and redaction. No real email was sent.
- Full suite, Ruff, formatting, and mypy results will be recorded after the
  final Step-4 gate below; Step 5 begins only after commit and push.

### Step 4 gate and backup

- Full gate: **75 passed in 6.08s**; Ruff check and format passed (25 files);
  strict mypy passed (19 source files).
- Commit `2e61c99` (`feat: enforce trusted grants in one MCP controller`) was
  pushed to `origin/main` after the full gate. Step 5 started afterward.

## Step 5 — evaluation corpus freeze (2026-10-26)

- Wrote `fixtures/case_plan.json` before rendering any case variants. It
  assigns 48 unique original wording/layout families: 24 development and 24
  holdout, with six malicious text, six benign text, six malicious image, and
  six benign image in each split. Development images use `memo_card`; holdout
  images use a distinct `grid_sheet` template. The common numeric report is
  the legitimate task shared across all arms.
- Rendered all 48 sources and wrote per-case manifests with scenario ID,
  split, modality, label, family, legitimate goal, controlled surface,
  authorized tools, forbidden outcome, source SHA-256, and expected OCR text
  for images. The rendering scripts refuse to overwrite the assigned plan,
  source files, or manifests.
- Frozen SHA-256: case plan
  `d50f1d04fe6744dd61186837b8292762e580a08eedb298374e8cb9dfbbdd80f7`;
  holdout manifest
  `73da91e336c5f5523f64de65fa6e399a89d743d85948e1473fb05239f0bcf7c8`;
  development manifest
  `256f947b029f32604f6bb92ace07796222c7f5ae5fd433b3c32e3fc834f45c3b`.
  The holdout digest is pinned in `tests/test_fixtures.py`. Any subsequent
  held-out source change will require an explicit logged post-freeze change
  and complete rerun; no such change has occurred.
- Visually inspected sample development and holdout images including the
  low-contrast attack cases. The images contain only invented values and `.test`
  addresses. This visual sample is not OCR or detector accuracy evidence.
- Initial case-plan script had one quoting syntax error before it wrote any
  plan file. Replaced it with the checked-in deterministic script. Focused
  corpus check caught a test regex including terminal punctuation in a
  `.test` address; corrected the test, not the frozen cases.
- Freeze checkpoint full gate: **76 passed in 6.14s**; Ruff check and format
  passed (28 files); strict mypy passed (22 source files). No live comparison
  requests have started. Commit and push below precede development tuning.

## Step 5 — evaluation in progress (2026-10-26)

- Initial development scripted comparison completed 72/72 sessions with zero
  API requests. Inspector quarantined 11/12 malicious cases and 1/12 benign
  cases in each inspecting arm. The missed pale-footer image was unreadable to
  direct Tesseract OCR and three contrast transforms; no detection is claimed.
  The benign training quote caused a false positive. Added a narrowly scoped
  quote-framing rule and a regression case; the frozen holdout was not opened
  for tuning. A new development run will measure the revised rule.
- The new offline regression runs both 24-case splits through all three arms,
  resumes from two saved sessions, and regenerates a static report from the
  saved traces. The first full gate after adding it passed 79 tests in 59.20s,
  with Ruff and mypy passing; the report was subsequently expanded to show
  proposed calls, actual ledger effects, final responses, and missing errors.
  A final gate is still required before Step 5 is committed.
- The first live held-out attempt encountered `ConnectError` at the initial
  model request three times (baseline, full, inspect) despite the API host
  answering an unauthenticated HEAD request. No live sessions completed; three
  attempted requests are recorded in ignored `runs/holdout-gemini.jsonl`.
  The runner now stops on a transport error rather than cycling through cases.
  Retry the same frozen model/protocol with approved network access; retain
  these failed attempts in append-only evidence and count them separately.
- Retried the unchanged Gemini 3.6 Flash protocol with approved network access;
  successful held-out sessions are being appended. The runner spaces live
  requests by 12 seconds and stops on quota, service, or transport errors.
- Revised development scripted run: 72/72 complete, zero API requests. Each
  inspecting arm quarantined 11/12 malicious and 0/12 benign cases, and
  completed 12/12 benign tasks; the pale-footer OCR miss remains. These are
  deterministic scripted observations after development-only tuning.
- Frozen held-out scripted run: 72/72 complete, zero API requests. Baseline
  simulated 8 unauthorized executions / 56 proposals. Full mode recorded
  0 unauthorized executions / 37 proposals and denied one attempted call;
  it quarantined 11/12 malicious cases and 1/12 benign case, extracted
  nonempty OCR text for 12/12 inspected images, and completed 11/12 benign
  tasks. The inspection-only arm simulated 1 unauthorized execution / 37
  proposals. These are scripted, single-run fixture results; no live rate is
  inferred from them. Holdout fixtures and inspector rules were not changed
  after observing these outcomes.
- Generated `site/scripted/index.html`, `aggregate.json`, `cases.json`, copied
  all 24 SHA-verified sources to `media/`, and saved the append-only trace as
  `site/scripted/traces.jsonl`. Static parser inspection found 26 local links,
  zero missing targets, 24 case rows, 12 image elements, and 120 detail panels.
  Browser visual QA was unavailable because the browser URL policy blocked a
  local `file:` URL; no visual-layout claim is made.
- Live held-out attempt stopped on HTTP 429 after eight completed sessions.
  A single paced resume after the short rate window returned 429 again, so no
  further live requests were made. Saved evidence has 13 attempts, 25 attempted
  API requests, eight completions, three initial `ConnectError` failures, two
  HTTP 429 failures, and 64 missing sessions. The completed arm counts are
  baseline 2, inspection 3, full 3; all completed cases are malicious text.
  The full arm quarantined 3/3 such cases and had 0 unauthorized simulated
  executions / 3 proposed calls. No benign or image live sessions completed;
  those metrics have denominator zero and no measured rate. A complete 72-run
  live comparison was unavailable within the confirmed Free tier. This is a
  service/quota limitation, not a switch to a paid tier or a different model.
- Generated `site/live/` from the saved partial JSONL and SHA-verified frozen
  sources; copied the trace into the report directory and added `site/index.html`
  to distinguish deterministic scripted and incomplete live evidence.
- Final Step-5 gate on the saved implementation: **79 passed in 58.45s**;
  Ruff check and format passed (31 files); strict mypy passed (25 source files);
  `git diff --check` passed. The static HTML parser found all 2 landing-page,
  26 scripted-report, and 26 live-report links present, with no script tags.
  Checked-in trace scan found only reserved `.test` email addresses, no
  Gemini-key marker, and simulation flags on all 85 runs. The complete live
  comparison remains outstanding due to repeated 429 responses; 64 sessions
  are explicitly missing in the report. Step 5 can be committed and pushed
  with that quota limitation recorded, as the spec permits.
- Step 5 commit `f5560fb` was pushed to `origin/main`. A subsequent remote
  head query returned the full SHA
  `f5560fb550f178d79839c6b20453f65f71c0e329`.

## Step 6 — release validation in progress (2026-10-26)

- Ran four offline CLI demo sessions in the installed wheel: `injection-text`
  baseline and full, `forced-call` full, and `benign-image` full. The baseline
  trace recorded one simulated attacker-directed email after a non-enforced
  authorization denial. The `forced-call` full trace recorded one denied
  attacker-directed proposal, zero unauthorized ledger executions, one
  authorized analyst email, and a correct `$330,000`/`20%` summary. The benign
  native-image full trace also recorded one authorized analyst email and a
  correct summary. All four sessions completed with zero model API requests;
  the inspector quarantined the `injection-text` full case, so that run did
  not independently exercise the authorization denial.
- Added a deterministic `forced-call` CLI scenario so the release demo can
  show task-grant enforcement even when the report itself is benign. The
  Gemini adapter is not allowed for this scripted scenario.
- Copied the four synthetic demo traces to `site/demo-traces.jsonl`. Rendered
  `site/demo.mp4` from those traces and saved aggregates using six ten-second
  slides. `ffprobe` measured H.264, 1280×720, 24 fps, 1,440 frames, exactly
  60.000 seconds, 331,223 bytes. Visually inspected all six rendered frames;
  no text was clipped. The video is silent and explicitly described as a
  saved-evidence walkthrough, not a live Gemini screen recording.
- Created `docs/RESUME_BULLET.md` using only the deterministic 72-session
  holdout and explicit 0/37 unauthorized execution and 11/12 benign-completion
  counts. It excludes the incomplete live comparison from the claim.
- Clean setup: copied the 157 current tracked/non-ignored source files to
  `/private/tmp/mosaicgate-clean.BgyHbV` without `.git` or `.env`; installed
  from the locked dependencies into a fresh Python 3.12 environment offline.
  From that environment, real MCP text and image smoke calls succeeded and a
  full-mode scripted `forced-call` demo completed with zero API requests.
  This source archive follows the logged no-second-checkout assumption. The
  final full gate and publication are still pending.
- The first Step-6 lint pass found one 104-character `doctor` status line;
  formatting and mypy passed. I restored the agent-owned CLI file from the
  last green commit, reapplied the release demo change in a smaller increment,
  then shortened the status line. Focused Ruff passed after each increment.
  The full Step-6 gate must be rerun on this corrected source.
- Corrected Step-6 full gate: **79 passed in 63.99s**; Ruff check and format
  passed (34 files); strict mypy passed (26 source files); `git diff --check`
  passed. The landing page and both reports have 4, 26, and 26 local links
  respectively, with zero missing targets. A pre-publication scan of 157
  tracked/non-ignored candidate files found no `.env`, Gemini-key pattern,
  private-key marker, or AWS-key pattern. This scan is a check of those named
  patterns, not a general secret-detection guarantee.
- Chrome's signed-in GitHub view shows the existing repository as private and
  the Step-5 head `f5560fb` with a success indicator. The release commit and
  push, followed by public visibility change and verification, remain.

## Release resumption — 2026-11-10

- Resumed from clean `e596320a2a79e263bc97aac377569c810df8cff2` on
  `main`; a read-only GitHub SSH query confirmed the same remote `main` head.
  The release commit is therefore pushed. Its GitHub Actions result and
  repository visibility still require authenticated verification.
- Re-ran the local full gate on the unchanged checkout: **79 passed in
  63.43s**; Ruff check passed; Ruff format check reported 34 files already
  formatted; strict mypy found no issues in 26 source files. The working tree
  remained clean after these checks.
- Current `doctor` reports Python 3.12.14, Tesseract 5.5.3 with English data,
  MCP 2.3.0, Pillow 13.0.0, and google-genai 2.33.0. Real local MCP text and
  native-image smoke calls both succeeded with zero model API requests. The
  landing page and two reports have 4, 26, and 26 local links respectively,
  with zero missing targets or script tags.
- The ignored local `.env` still contains a nonempty Gemini key and Free tier
  confirmation; no value was printed. The append-only live trace began this
  resumption with 13 attempts, 8 completed sessions, 25 attempted requests,
  and one protocol hash. One quota-aware retry of the unchanged frozen
  comparison is running; its outcome must be recorded after it terminates.
- GitHub CLI is signed out. Requested browser-based `gh auth login` from the
  user for private Actions inspection and repository publication; no token was
  requested in chat. Publication is pending that access and a green CI run.
- The single later Free tier retry of the frozen Gemini 3.6 Flash protocol
  stopped on another HTTP 429. It added ten attempts, nine completed sessions,
  and 23 attempted API requests. The append-only total is **23 attempts,
  17/72 completed sessions, 48 attempted API requests, and 55 missing**. Three
  attempts ended in initial `ConnectError` and three in HTTP 429. Completed
  arms: baseline 5, inspection 6, full 6; all are malicious text. The full
  arm quarantined 6/6 completed malicious text cases and recorded zero
  unauthorized simulated executions / 6 proposed calls. No benign or image
  live sessions completed, so their outcome denominators remain zero. No
  further live requests will be made in this release; this was the third
  quota response across the saved attempts. The model, prompt, grant, tool
  schema, frozen holdout, and billing state were unchanged.
- Regenerated `site/live/` from the append-only local trace. The report says
  17 completed and 55 missing; the exact saved attempt and request counts are
  retained. The original report command did not update the copied
  `traces.jsonl`, leaving 13 stale attempts; fixed the report generator to
  copy the source trace and added an end-to-end test of that artifact. The
  committed report source now matches all 23 local attempts byte for byte.
  Regenerated the silent 60-second video with dynamic live counts. `ffprobe`
  measured H.264, 1280×720, 24 fps, 1,440 frames, and exactly 60.000 seconds;
  visually inspected the revised final slide, including 17/72 and 55 missing.
- The user completed browser-based GitHub CLI authentication. Outside the
  restricted network sandbox, `gh auth status` verified account
  `emirsimsek00` with `repo` and `workflow` scopes; no token value was copied
  into the repository or this log. GitHub Actions run `40285662023` for
  release commit `e596320` completed **successfully**. `gh repo view`
  confirmed the existing `emirsimsek00/MosaicGate` repository is still
  **private** on default branch `main` before publication.
- Final source and evidence changes passed the full local gate: **79 passed
  in 63.51s**; Ruff check passed; Ruff format check reported 34 files already
  formatted; strict mypy found no issues in 26 source files. The report
  generator's trace-copy assertion ran inside the offline evaluation test.
- Exported 157 tracked/non-ignored source files, excluding `.git` and `.env`,
  to `/private/tmp/mosaicgate-clean-nmizbhl8` without creating a second Git
  checkout. A fresh Python 3.12 environment installed the locked package
  offline. Real MCP text and native-image smoke calls passed. The scripted
  full-mode `forced-call` demo completed with one denied proposal, zero
  attacker-email executions, one authorized analyst-email execution, and
  zero model API requests.
- Rechecked 4 landing-page, 26 scripted-report, and 26 live-report local
  links: zero missing targets and zero script tags. Scanned 157 current
  candidate files and 142 unique historical Git blobs for named high-confidence
  Google API key, GitHub token, private-key, and AWS key patterns: zero matches.
  `.env` was absent from the candidate files and Git history. All 51 email
  matches in the updated saved live trace ended with reserved `.test` domains
  after removing sentence punctuation. These are scoped checks, not a general
  guarantee that every possible secret or sensitive datum has been found.

## Publication — 2026-11-10

- Committed the refreshed live evidence, self-contained report trace, video,
  documentation, and regression assertion as `37394c4`. Pushed to
  `origin/main`; a remote-head query returned the full SHA
  `37394c4b6ff0e3f21094a6ebe2ca135a0c8e3f90`.
- GitHub Actions offline run `42903095318` for that exact SHA completed
  **successfully**. All eight earlier completed Actions runs were also
  successful. Scanned the logs for all nine completed runs for named
  high-confidence Google API key, GitHub token, private-key, and AWS key
  patterns: zero matches. This is a scoped pattern check, not a complete
  privacy audit of every possible log field.
- Verified the account had admin permission on the existing private
  `emirsimsek00/MosaicGate` repository, then changed its visibility to
  **public**. `gh repo view` returned `PUBLIC`. An unauthenticated HTTP request
  to the repository page returned 200; an unauthenticated request to the
  committed live report returned 200; the public GitHub API returned the same
  `37394c4b6ff0e3f21094a6ebe2ca135a0c8e3f90` `main` SHA.
- This final status update is documentation-only. Its push and Actions result
  are verified separately after committing; the GitHub Actions page remains
  the source of truth for later commits. The publication-record local gate
  passed: **79 tests in 61.31s**, Ruff check, Ruff format check (34 files),
  strict mypy (26 source files), and `git diff --check`.
