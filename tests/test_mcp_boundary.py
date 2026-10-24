"""Integration tests use real stdio subprocesses, with no Gemini/API credentials."""

import base64
import json
from io import BytesIO

from mcp.types import ImageContent, TextContent, TextResourceContents
from PIL import Image

from mosaicgate.smoke_fixtures import REPORT_TEXT, Modality
from mosaicgate.transport import fixture_client


async def test_real_text_result_round_trip() -> None:
    async with fixture_client() as client:
        result = await client.call_tool("read_report", {"report_id": "q3"})
    assert not result.is_error
    assert len(result.content) == 1
    block = result.content[0]
    assert isinstance(block, TextContent)
    assert block.text == REPORT_TEXT


async def test_real_native_image_round_trip() -> None:
    async with fixture_client(Modality.IMAGE) as client:
        result = await client.call_tool("read_report", {"report_id": "q3"})
    assert not result.is_error
    assert len(result.content) == 1
    block = result.content[0]
    assert isinstance(block, ImageContent)
    assert block.mime_type == "image/png"
    with Image.open(BytesIO(base64.b64decode(block.data, validate=True))) as image:
        assert image.format == "PNG"
        assert image.size == (1200, 420)
        image.verify()


async def test_tools_have_expected_argument_schemas() -> None:
    async with fixture_client() as client:
        listed = await client.list_tools()
    schemas = {tool.name: tool.input_schema for tool in listed.tools}
    assert set(schemas) == {"read_report", "send_email", "write_note"}
    assert schemas["read_report"]["required"] == ["report_id"]
    assert set(schemas["send_email"]["required"]) == {"to", "body"}
    assert set(schemas["send_email"]["properties"]) == {"to", "body"}
    assert schemas["write_note"]["required"] == ["body"]


async def test_simulated_actions_record_only_in_the_server_ledger() -> None:
    async with fixture_client() as client:
        email = await client.call_tool(
            "send_email", {"to": "analyst@example.test", "body": "Synthetic summary"}
        )
        note = await client.call_tool("write_note", {"body": "Synthetic note"})
        ledger = await client.read_resource("simulation://ledger")
    assert not email.is_error and not note.is_error
    block = ledger.contents[0]
    assert isinstance(block, TextResourceContents)
    data = json.loads(block.text)
    assert data["simulation"] is True
    assert data["events"] == [
        {
            "sequence": 1,
            "tool": "send_email",
            "arguments": {"to": "analyst@example.test", "body": "Synthetic summary"},
            "simulation": True,
        },
        {
            "sequence": 2,
            "tool": "write_note",
            "arguments": {"body": "Synthetic note"},
            "simulation": True,
        },
    ]


async def test_ledger_is_isolated_between_server_processes() -> None:
    async with fixture_client() as first:
        await first.call_tool("write_note", {"body": "Must not leak to a new server"})
    async with fixture_client() as second:
        ledger = await second.read_resource("simulation://ledger")
    block = ledger.contents[0]
    assert isinstance(block, TextResourceContents)
    assert json.loads(block.text) == {"simulation": True, "events": []}


async def test_missing_report_is_an_error_not_a_successful_execution() -> None:
    async with fixture_client() as client:
        result = await client.call_tool("read_report", {"report_id": "missing"})
        ledger = await client.read_resource("simulation://ledger")
    assert result.is_error
    assert isinstance(result.content[0], TextContent)
    block = ledger.contents[0]
    assert isinstance(block, TextResourceContents)
    assert json.loads(block.text)["events"] == []


async def test_non_test_recipient_is_rejected_without_ledger_effect() -> None:
    async with fixture_client() as client:
        result = await client.call_tool("send_email", {"to": "invalid", "body": "Synthetic"})
        ledger = await client.read_resource("simulation://ledger")
    assert result.is_error
    block = ledger.contents[0]
    assert isinstance(block, TextResourceContents)
    assert json.loads(block.text)["events"] == []
