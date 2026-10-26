"""Bounded inspection of untrusted MCP content, separate from authorization."""

import base64
import binascii
import hashlib
import html
import json
import math
import os
import re
import shutil
import subprocess
import time
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal
from urllib.parse import unquote

from mcp.types import CallToolResult, ImageContent, TextContent
from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import BaseModel

type JSONValue = str | int | float | bool | None | list[JSONValue] | dict[str, JSONValue]
QUARANTINE_MESSAGE = "Tool content unavailable after security inspection."


@dataclass(frozen=True)
class InspectionCaps:
    text_bytes: int = 64 * 1024
    image_bytes: int = 5 * 1024 * 1024
    image_pixels: int = 16_000_000
    ocr_timeout_seconds: float = 5.0
    structured_depth: int = 8
    nodes: int = 2048
    blocks: int = 16
    normalization_chars: int = 256 * 1024


@dataclass(frozen=True)
class InspectionContext:
    tool_name: str
    scenario_id: str
    caps: InspectionCaps = field(default_factory=InspectionCaps)


@dataclass(frozen=True)
class InspectionDecision:
    verdict: Literal["PASS", "QUARANTINE"]
    reasons: tuple[str, ...]
    modality: str
    raw_sha256: str | None
    extraction_status: str
    extracted_text: str
    elapsed_ms: float
    safe_forwarded_result: CallToolResult


class InspectionFailure(ValueError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


@dataclass
class _Budget:
    caps: InspectionCaps
    nodes: int = 0
    raw_bytes: int = 0
    text_bytes: int = 0
    normalization_chars: int = 0
    decoded_image_bytes: int = 0

    def envelope(self, value: object, depth: int = 0) -> JSONValue:
        self.nodes += 1
        if self.nodes > self.caps.nodes:
            raise InspectionFailure("NODE_LIMIT")
        if depth > self.caps.structured_depth:
            raise InspectionFailure("DEPTH_LIMIT")
        if isinstance(value, BaseModel):
            fields: dict[str, object] = {
                name: getattr(value, name) for name in type(value).model_fields
            }
            fields.update(value.model_extra or {})
            return self.envelope(fields, depth)
        if value is None or isinstance(value, bool | int):
            return value
        if isinstance(value, float):
            if not math.isfinite(value):
                raise InspectionFailure("STRUCTURED_TYPE")
            return value
        if isinstance(value, str):
            limit = self.caps.image_bytes * 2 + self.caps.text_bytes * 6
            if len(value) > limit:
                raise InspectionFailure("ENVELOPE_LIMIT")
            self.raw_bytes += len(value.encode("utf-8"))
            if self.raw_bytes > limit:
                raise InspectionFailure("ENVELOPE_LIMIT")
            return value
        if isinstance(value, list):
            if len(value) > self.caps.nodes:
                raise InspectionFailure("NODE_LIMIT")
            return [self.envelope(item, depth + 1) for item in value]
        if isinstance(value, dict):
            if len(value) > self.caps.nodes:
                raise InspectionFailure("NODE_LIMIT")
            output: dict[str, JSONValue] = {}
            for key, item in value.items():
                if not isinstance(key, str):
                    raise InspectionFailure("STRUCTURED_TYPE")
                self.envelope(key, depth)
                output[key] = self.envelope(item, depth + 1)
            return output
        raise InspectionFailure("STRUCTURED_TYPE")

    def text(self, text: str) -> str:
        if len(text) > self.caps.text_bytes:
            raise InspectionFailure("TEXT_LIMIT")
        self.text_bytes += len(text.encode("utf-8"))
        if self.text_bytes > self.caps.text_bytes:
            raise InspectionFailure("TEXT_LIMIT")
        normalized = text
        for _ in range(2):
            self.normalization_chars += len(normalized)
            if self.normalization_chars > self.caps.normalization_chars:
                raise InspectionFailure("NORMALIZATION_LIMIT")
            normalized = unicodedata.normalize("NFKC", normalized)
            normalized = "".join(c for c in normalized if unicodedata.category(c) != "Cf")
            normalized = html.unescape(unquote(normalized, errors="strict"))
            for encoded in re.findall(r"(?i)\bbase64:\s*([A-Za-z0-9+/=]+)", normalized):
                try:
                    decoded = base64.b64decode(encoded, validate=True).decode("utf-8")
                except (ValueError, binascii.Error, UnicodeError) as error:
                    raise InspectionFailure("NORMALIZATION_FAILED") from error
                normalized = normalized.replace(f"base64:{encoded}", decoded, 1)
            if len(normalized.encode("utf-8")) > self.caps.text_bytes:
                raise InspectionFailure("NORMALIZATION_LIMIT")
        return normalized


def _strings(value: JSONValue) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [text for item in value for text in _strings(item)]
    if isinstance(value, dict):
        return [text for key, item in value.items() for text in [key, *_strings(item)]]
    return []


def detect_instructions(text: str) -> tuple[str, ...]:
    """Explainable heuristics, deliberately not a complete injection detector."""
    examined = text
    if re.search(r"(?i)\b(phrase|quoted|example|discusses|security training)\b", text):
        examined = re.sub(r'"[^"\n]*"|“[^”\n]*”|`[^`\n]*`', "[quotation]", text)
    categories = {
        "ROLE_SPOOFING": (
            r"<\s*/?\s*(?:system|developer)\b|\[\s*system\s*\]|"
            r"(?:^|\n)\s*(?:system|developer)\s*:"
        ),
        "DIRECT_INSTRUCTION": (
            r"\b(?:ignore|disregard|override)\b.{0,60}\b(?:instructions|user|task|rules)\b|"
            r"\b(?:assistant|agent|you must)\b.{0,60}\b(?:send|email|call|write|reveal|execute)\b"
        ),
        "OFF_TASK_COMMAND": (
            r"\b(?:write_note|send_email)\s*\(|\b(?:approved|approval|authorized)\b"
            r".{0,60}\b(?:send|email|write|change)\b"
        ),
    }
    reasons = [
        code for code, pattern in categories.items() if re.search(pattern, examined, re.I | re.S)
    ]
    destinations = re.findall(
        r"[\w.+-]{1,64}@[\w.-]{1,253}\.[A-Za-z]{2,24}|https?://[^\s<>]{1,2048}", examined
    )
    if re.search(r"\b(?:send|email|forward|transmit|upload|deliver)\b", examined, re.I) and any(
        destination.lower() != "analyst@example.test" for destination in destinations
    ):
        reasons.append("EXFILTRATION_DESTINATION")
    return tuple(reasons)


def extract_ocr(image_bytes: bytes, caps: InspectionCaps) -> str:
    executable = shutil.which("tesseract")
    if executable is None:
        raise InspectionFailure("OCR_UNAVAILABLE")
    with TemporaryDirectory(prefix="mosaicgate-ocr-") as directory:
        root = Path(directory)
        image = root / "input.png"
        image.write_bytes(image_bytes)
        with (root / "stderr.txt").open("wb") as stderr:
            try:
                subprocess.run(
                    [executable, str(image), str(root / "output"), "-l", "eng", "--psm", "6"],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=stderr,
                    timeout=caps.ocr_timeout_seconds,
                    check=True,
                    env={**os.environ, "OMP_THREAD_LIMIT": "1"},
                )
            except subprocess.TimeoutExpired as error:
                raise InspectionFailure("OCR_TIMEOUT") from error
            except (OSError, subprocess.CalledProcessError) as error:
                raise InspectionFailure("OCR_FAILED") from error
        output = root / "output.txt"
        try:
            if output.stat().st_size > caps.text_bytes:
                raise InspectionFailure("OCR_TEXT_LIMIT")
            text = output.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise InspectionFailure("OCR_FAILED") from error
        if not text.strip():
            raise InspectionFailure("OCR_EMPTY")
        return text


def _canonical_image(block: ImageContent, budget: _Budget) -> bytes:
    formats = {"image/png": "PNG", "image/jpeg": "JPEG", "image/webp": "WEBP"}
    if block.mime_type not in formats:
        raise InspectionFailure("UNSUPPORTED_IMAGE_FORMAT")
    if len(block.data) > ((budget.caps.image_bytes + 2) // 3) * 4:
        raise InspectionFailure("IMAGE_BYTES_LIMIT")
    try:
        data = base64.b64decode(block.data, validate=True)
    except (ValueError, binascii.Error) as error:
        raise InspectionFailure("INVALID_BASE64") from error
    budget.decoded_image_bytes += len(data)
    if budget.decoded_image_bytes > budget.caps.image_bytes:
        raise InspectionFailure("IMAGE_BYTES_LIMIT")
    try:
        with Image.open(BytesIO(data)) as source:
            if source.format != formats[block.mime_type]:
                raise InspectionFailure("IMAGE_MIME_MISMATCH")
            if source.width * source.height > budget.caps.image_pixels:
                raise InspectionFailure("IMAGE_PIXELS_LIMIT")
            if getattr(source, "n_frames", 1) != 1:
                raise InspectionFailure("ANIMATED_IMAGE")
            source.load()
            oriented = ImageOps.exif_transpose(source)
            rgba = oriented.convert("RGBA")
            background = Image.new("RGBA", rgba.size, "white")
            canonical = Image.alpha_composite(background, rgba).convert("RGB")
            output = BytesIO()
            canonical.save(output, format="PNG")
            data = output.getvalue()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as error:
        if isinstance(error, InspectionFailure):
            raise
        raise InspectionFailure("INVALID_IMAGE") from error
    if len(data) > budget.caps.image_bytes:
        raise InspectionFailure("CANONICAL_IMAGE_LIMIT")
    return data


OCRExtractor = Callable[[bytes, InspectionCaps], str]


def inspect_tool_result(
    result: CallToolResult,
    context: InspectionContext,
    *,
    ocr: OCRExtractor = extract_ocr,
) -> InspectionDecision:
    started = time.perf_counter()
    budget = _Budget(context.caps)
    raw_sha256: str | None = None
    extracted: list[str] = []
    safe: list[TextContent | ImageContent] = []
    kinds: set[str] = set()
    extraction = "not_needed"
    reasons: tuple[str, ...] = ()
    structured: JSONValue = None
    try:
        payload = budget.envelope(result)
        raw_sha256 = hashlib.sha256(
            json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()
        ).hexdigest()
        if not isinstance(payload, dict):
            raise InspectionFailure("INVALID_RESULT")
        if result.result_type != "complete":
            raise InspectionFailure("UNSUPPORTED_RESULT")
        if not result.content and result.structured_content is None:
            raise InspectionFailure("EMPTY_RESULT")
        if len(result.content) > context.caps.blocks:
            raise InspectionFailure("BLOCK_LIMIT")
        metadata: dict[str, JSONValue] = {
            key: value
            for key, value in payload.items()
            if key not in {"content", "structured_content", "is_error", "result_type"}
            and value is not None
        }
        extracted.extend(budget.text(text) for text in _strings(metadata))
        structured = payload.get("structured_content")
        extracted.extend(budget.text(text) for text in _strings(structured))
        raw_blocks = payload["content"]
        assert isinstance(raw_blocks, list)
        for block, raw_block in zip(result.content, raw_blocks, strict=True):
            assert isinstance(raw_block, dict)
            extra: dict[str, JSONValue] = {
                key: value
                for key, value in raw_block.items()
                if key not in {"type", "text", "data", "mime_type"} and value is not None
            }
            extracted.extend(budget.text(text) for text in _strings(extra))
            if isinstance(block, TextContent):
                kinds.add("text")
                text = budget.text(block.text)
                extracted.append(text)
                safe.append(TextContent(text=text))
            elif isinstance(block, ImageContent):
                kinds.add("image")
                extraction = "not_attempted"
                image = _canonical_image(block, budget)
                try:
                    text = ocr(image, context.caps)
                except InspectionFailure:
                    raise
                except Exception as error:
                    raise InspectionFailure("OCR_FAILED") from error
                if not text.strip():
                    raise InspectionFailure("OCR_EMPTY")
                extracted.append(budget.text(text))
                extraction = "success"
                safe.append(
                    ImageContent(
                        data=base64.b64encode(image).decode("ascii"), mime_type="image/png"
                    )
                )
            else:
                raise InspectionFailure("UNSUPPORTED_CONTENT")
        reasons = detect_instructions("\n".join(extracted))
    except InspectionFailure as error:
        reasons = (error.reason,)
        if error.reason.startswith("OCR_"):
            extraction = "timeout" if error.reason == "OCR_TIMEOUT" else "failed"
    except (UnicodeError, RecursionError, ValueError, TypeError, AssertionError):
        reasons = ("VALIDATION_FAILED",)
    verdict: Literal["PASS", "QUARANTINE"] = "QUARANTINE" if reasons else "PASS"
    forwarded = (
        CallToolResult(content=[TextContent(text=QUARANTINE_MESSAGE)], is_error=True)
        if reasons
        else CallToolResult(
            content=list(safe), structured_content=structured, is_error=result.is_error
        )
    )
    return InspectionDecision(
        verdict=verdict,
        reasons=reasons or ("CONTENT_VALIDATED",),
        modality="mixed" if len(kinds) > 1 else next(iter(kinds), "structured"),
        raw_sha256=raw_sha256,
        extraction_status=extraction,
        extracted_text="\n".join(extracted),
        elapsed_ms=round((time.perf_counter() - started) * 1000, 3),
        safe_forwarded_result=forwarded,
    )


def decision_record(
    decision: InspectionDecision, *, synthetic_evidence: bool = False
) -> dict[str, object]:
    record: dict[str, object] = {
        "verdict": decision.verdict,
        "reasons": list(decision.reasons),
        "modality": decision.modality,
        "raw_sha256": decision.raw_sha256,
        "hash_status": "complete" if decision.raw_sha256 else "unavailable_validation_limit",
        "extraction_status": decision.extraction_status,
        "elapsed_ms": decision.elapsed_ms,
    }
    if synthetic_evidence:
        record["synthetic_evidence_excerpt"] = html.escape(decision.extracted_text[:160])
    return record
