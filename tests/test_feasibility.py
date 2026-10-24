"""Offline pilot prerequisites and native-image response contract checks."""

import base64
from pathlib import Path

import pytest
from google.genai import types
from mcp.types import CallToolResult, ImageContent, TextContent

from mosaicgate.feasibility import native_image_response, pilot_config
from mosaicgate.live_settings import LivePrerequisiteError, require_live_settings
from mosaicgate.smoke_fixtures import report_png


@pytest.mark.parametrize(
    "overrides",
    [
        {"GEMINI_API_KEY": ""},
        {"MOSAICGATE_FREE_TIER_CONFIRMED": "false"},
        {"CI": "true"},
        {"MOSAICGATE_MODEL": "unapproved-model"},
    ],
)
def test_missing_live_prerequisite_blocks_before_network(
    tmp_path: Path, overrides: dict[str, str]
) -> None:
    environment = {
        "GEMINI_API_KEY": "invented-unit-test-value",
        "MOSAICGATE_FREE_TIER_CONFIRMED": "true",
        **overrides,
    }
    with pytest.raises(LivePrerequisiteError):
        require_live_settings(tmp_path / "absent.env", environment=environment)


def test_native_function_response_preserves_bytes_and_call_id() -> None:
    raw = report_png()
    call = types.FunctionCall(id="synthetic-call-1", name="read_report", args={"report_id": "q3"})
    result = CallToolResult(
        content=[ImageContent(data=base64.b64encode(raw).decode("ascii"), mime_type="image/png")]
    )
    message = native_image_response(call, result)
    assert message.role == "user"
    assert message.parts is not None
    response = message.parts[0].function_response
    assert response is not None
    assert response.id == call.id
    assert response.parts is not None
    blob = response.parts[0].inline_data
    assert blob is not None
    assert blob.data == raw
    assert blob.mime_type == "image/png"
    assert "100,000" not in str(response.response)


def test_pilot_rejects_non_image_or_off_scope_calls() -> None:
    call = types.FunctionCall(name="send_email", args={"to": "attacker@example.test"})
    with pytest.raises(ValueError, match="fixed Q3 read"):
        native_image_response(call, CallToolResult(content=[]))
    call = types.FunctionCall(name="read_report", args={"report_id": "q3"})
    with pytest.raises(ValueError, match="native PNG"):
        native_image_response(call, CallToolResult(content=[TextContent(text="OCR substitute")]))


def test_pilot_disables_automatic_execution_in_both_requests() -> None:
    for request_tool in (True, False):
        config = pilot_config(request_tool=request_tool)
        assert config.automatic_function_calling is not None
        assert config.automatic_function_calling.disable is True
