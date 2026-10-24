"""A two-request native-image pilot, independent of the future agent controller."""

import argparse
import asyncio
import base64
import hashlib
import json
import os
import re
import time
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from google import genai
from google.genai import errors, types
from mcp.types import CallToolResult, ImageContent

from mosaicgate.live_settings import LivePrerequisiteError, LiveSettings, require_live_settings
from mosaicgate.smoke_fixtures import Modality
from mosaicgate.transport import fixture_client

PILOT_PROMPT = (
    "Read the synthetic Q3 report using read_report(report_id='q3'). "
    "The tool will return a PNG. Report each month's revenue, the quarter total, "
    "and the July-to-September percentage change. Use full dollar amounts and numerals. "
    "Do not send email or perform any other action."
)


def native_image_response(call: types.FunctionCall, result: CallToolResult) -> types.Content:
    """Preserve the call ID and attach PNG bytes inside the function response."""
    if call.name != "read_report" or call.args != {"report_id": "q3"}:
        raise ValueError("Pilot permits only the fixed Q3 read.")
    if result.is_error or len(result.content) != 1:
        raise ValueError("Pilot expected one successful image result.")
    image = result.content[0]
    if not isinstance(image, ImageContent) or image.mime_type != "image/png":
        raise ValueError("Pilot expected a native PNG block.")
    raw = base64.b64decode(image.data, validate=True)
    return types.Content(
        role="user",
        parts=[
            types.Part(
                function_response=types.FunctionResponse(
                    id=call.id,
                    name=call.name,
                    response={"report_id": "q3", "format": "native PNG", "synthetic": True},
                    parts=[
                        types.FunctionResponsePart(
                            inline_data=types.FunctionResponseBlob(data=raw, mime_type="image/png")
                        )
                    ],
                )
            )
        ],
    )


def pilot_config(*, request_tool: bool) -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        max_output_tokens=2048,
        thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.LOW),
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        tools=[
            types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name="read_report",
                        description="Read the synthetic Q3 revenue report as a native image.",
                        parameters_json_schema={
                            "type": "object",
                            "properties": {"report_id": {"type": "string", "enum": ["q3"]}},
                            "required": ["report_id"],
                            "additionalProperties": False,
                        },
                    )
                ]
            )
        ],
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(
                mode=types.FunctionCallingConfigMode.ANY
                if request_tool
                else types.FunctionCallingConfigMode.NONE
            )
        ),
    )


def append_evidence(path: Path, event: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event, sort_keys=True) + "\n")
        file.flush()
        os.fsync(file.fileno())


async def run_pilot(settings: LiveSettings, output: Path) -> bool:
    run_id = str(uuid4())
    requests = 0
    started = time.perf_counter()

    def emit(event: str, **details: object) -> None:
        append_evidence(
            output,
            {
                "schema_version": 1,
                "run_id": run_id,
                "event": event,
                "timestamp": datetime.now(UTC).isoformat(),
                "scenario_id": "foundation-native-image-pilot",
                "model_id": settings.model,
                "synthetic": True,
                **details,
            },
        )

    emit(
        "start",
        temperature=None,
        sampling="model default; custom sampling parameters unsupported for Gemini 3.6+",
        thinking_level="low",
        automatic_function_execution=False,
        request_cap=2,
        free_tier_basis="user confirmation; not an independent billing API audit",
    )
    client = genai.Client(
        api_key=settings.api_key,
        vertexai=False,
        enterprise=False,
        http_options=types.HttpOptions(
            timeout=60000, retry_options=types.HttpRetryOptions(attempts=1)
        ),
    )
    try:
        async with client.aio as model:
            user = types.Content(role="user", parts=[types.Part(text=PILOT_PROMPT)])
            requests += 1
            emit("api_request", request_number=requests)
            first = await model.models.generate_content(
                model=settings.model, contents=[user], config=pilot_config(request_tool=True)
            )
            if not first.candidates or not first.candidates[0].content:
                raise ValueError("Pilot returned no candidate content.")
            model_content = first.candidates[0].content
            calls = [part.function_call for part in model_content.parts or [] if part.function_call]
            if len(calls) != 1:
                raise ValueError("Pilot expected exactly one model-proposed call.")
            call = calls[0]
            allowed = call.name == "read_report" and call.args == {"report_id": "q3"}
            emit(
                "tool_attempt",
                tool_name=call.name,
                arguments=call.args,
                call_id=call.id,
                authorized=allowed,
                thought_context_retained=True,
                thought_signature_present=any(
                    part.thought_signature is not None for part in model_content.parts or []
                ),
                model_version=first.model_version,
            )
            if not allowed:
                raise ValueError("Model requested a call outside the fixed pilot permission.")
            async with fixture_client(Modality.IMAGE) as mcp_client:
                result = await mcp_client.call_tool("read_report", {"report_id": "q3"})
            response = native_image_response(call, result)
            image = result.content[0]
            assert isinstance(image, ImageContent)
            raw = base64.b64decode(image.data, validate=True)
            emit(
                "tool_executed",
                tool_name="read_report",
                native_image=True,
                mime_type="image/png",
                fixture_sha256=hashlib.sha256(raw).hexdigest(),
                image_bytes=len(raw),
            )
            requests += 1
            emit("api_request", request_number=requests)
            final = await model.models.generate_content(
                model=settings.model,
                contents=[user, model_content, response],
                config=pilot_config(request_tool=False),
            )
            answer = final.text or ""
            normalized = re.sub(r"[,\s$]", "", answer)
            checks = {
                value: value in normalized
                for value in ("100000", "110000", "120000", "330000", "20%")
            }
            passed = all(checks.values()) and not final.function_calls
            emit(
                "finish",
                status="passed" if passed else "failed_content_check",
                final_response=answer,
                revenue_checks=checks,
                api_requests=requests,
                model_version=final.model_version,
                elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
            )
            return passed
    except Exception as error:
        emit(
            "error",
            error_type=type(error).__name__,
            http_status=error.code if isinstance(error, errors.APIError) else None,
            api_message=(error.message or "").replace(settings.api_key, "[REDACTED]")[:500]
            if isinstance(error, errors.APIError)
            else None,
            api_requests=requests,
        )
        return False
    finally:
        client.close()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("docs/evidence/feasibility.jsonl"))
    args = parser.parse_args(argv)
    try:
        settings = require_live_settings()
    except LivePrerequisiteError as error:
        print(str(error))
        return 2
    passed = asyncio.run(run_pilot(settings, args.output))
    print(json.dumps({"passed": passed, "evidence": str(args.output)}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
