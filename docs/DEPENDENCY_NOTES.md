# Dependency and API verification

Checked 2026-10-23. These notes describe inspected documentation and installed
interfaces, not a completed live integration.

- [Official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
  and [client documentation](https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/client/index.md):
  the current SDK uses `MCPServer` and `Client`. The installed package is 2.3.0.
  Python attributes use snake_case (`structured_content`, `is_error`,
  `mime_type`), while wire JSON retains the protocol's aliases. The foundation
  uses the official stdio subprocess transport.
- [Gemini 3.8 Flash](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash)
  lists text/image input and function calling. It is the preferred preflight
  candidate, not a successfully tested live model.
- [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing) lists free input
  and output for standard Gemini 3.8 Flash. This does not establish that a
  particular user's project has billing disabled. Confirm project status before
  a request. Do not use priority, batch, flex, paid models, or billing upgrades.
- [Function calling](https://ai.google.dev/gemini-api/docs/function-calling)
  documents native multimodal function results for Gemini 3 and requires matching
  call identity and conversation context. The current page emphasizes the
  Interactions API. The installed `google-genai` 2.33.0 also exposes native
  `FunctionResponse.parts`, `id`, `name`, and `response` fields. Step 2 must pilot
  an actual native-image cycle before choosing the final live-adapter design.
  The handoff's `/docs/generate-content/function-calling` URL was unavailable;
  `/docs/function-calling` was successfully read.
- [Rate limits](https://ai.google.dev/gemini-api/docs/rate-limits) are project and
  model dependent. Inspect the user's free-project allowance before evaluation;
  cap requests and retain missing sessions on quota exhaustion.
- [Homebrew Tesseract](https://formulae.brew.sh/formula/tesseract) includes English
  and orientation language data. Installed 5.5.3 and verified `eng` with
  `tesseract --list-langs`.

Exact Python dependency versions and artifact hashes are in `uv.lock`.
Python 3.12.14 was installed into the ignored local `.tools/python` directory.
No Google API calls have been made. No key was present during foundation setup.
