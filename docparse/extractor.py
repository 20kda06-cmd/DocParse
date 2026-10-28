"""Send a PDF or image to Claude and get a validated Invoice back."""
from __future__ import annotations

import base64
import os
from pathlib import Path

import anthropic

from .schema import Invoice

MODEL = os.environ.get("DOCPARSE_MODEL", "claude-sonnet-5-5")
TOOL_NAME = "record_invoice"

SYSTEM_PROMPT = """You extract structured data from business documents (invoices, receipts, credit notes).

Rules:
- Copy values exactly as printed. Never calculate, correct or guess a number.
- If a field is not present in the document, leave it null (or an empty list).
- Amounts are plain numbers: no currency symbols, no thousands separators.
- Dates are ISO 8601 (YYYY-MM-DD). Currency is an ISO 4217 code.
- List every field you are unsure about in uncertain_fields.
"""

SUPPORTED = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


def _document_block(path: Path) -> dict:
    media_type = SUPPORTED.get(path.suffix.lower())
    if media_type is None:
        raise ValueError(f"Unsupported file type: {path.suffix or '(none)'}")
    data = base64.standard_b64encode(path.read_bytes()).decode("ascii")
    kind = "document" if media_type == "application/pdf" else "image"
    return {"type": kind, "source": {"type": "base64", "media_type": media_type, "data": data}}


def extract_invoice(path: Path, client: anthropic.Anthropic | None = None) -> Invoice:
    client = client or anthropic.Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        tools=[
            {
                "name": TOOL_NAME,
                "description": "Record the data extracted from the document.",
                "input_schema": Invoice.model_json_schema(),
            }
        ],
        tool_choice={"type": "tool", "name": TOOL_NAME},
        messages=[
            {
                "role": "user",
                "content": [_document_block(path), {"type": "text", "text": "Extract this document."}],
            }
        ],
    )
    if response.stop_reason == "max_tokens":
        raise RuntimeError("Output was cut off; the document may be too long for one pass.")
    for block in response.content:
        if block.type == "tool_use" and block.name == TOOL_NAME:
            return Invoice.model_validate(block.input)
    raise RuntimeError("The model did not return structured data.")
