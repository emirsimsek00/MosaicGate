"""Offline Gemini payload tests; CI never makes a model request."""

import base64

from mcp.types import CallToolResult, ImageContent, TextContent

from mosaicgate.agents import ProposedCall
from mosaicgate.gemini_agent import function_response, tool_declarations
from mosaicgate.smoke_fixtures import report_png


def test_native_image_function_response_preserves_bytes_and_call_identity() -> None:
    raw = report_png()
    proposal = ProposedCall("read_report", {"report_id": "q3"}, "synthetic-id")
    result = CallToolResult(
        content=[ImageContent(data=base64.b64encode(raw).decode(), mime_type="image/png")]
    )
    part = function_response(proposal, result)
    response = part.function_response
    assert response is not None
    assert response.id == "synthetic-id"
    assert response.name == "read_report"
    assert response.response is not None
    assert response.response["image_count"] == 1
    assert response.parts is not None
    image = response.parts[0].inline_data
    assert image is not None and image.data == raw and image.mime_type == "image/png"
    assert image.display_name is None


def test_neutral_denial_is_text_only() -> None:
    proposal = ProposedCall("send_email", {"to": "attacker@example.test", "body": "x"})
    result = CallToolResult(content=[TextContent(text="Tool call denied.")], is_error=True)
    response = function_response(proposal, result).function_response
    assert response is not None
    assert response.response is not None
    assert response.response["is_error"] is True
    assert response.response["text"] == ["Tool call denied."]
    assert response.parts == []


def test_all_three_tool_schemas_are_exposed_to_model() -> None:
    tools = tool_declarations()
    assert len(tools) == 1 and tools[0].function_declarations is not None
    assert {declaration.name for declaration in tools[0].function_declarations} == {
        "read_report",
        "send_email",
        "write_note",
    }
