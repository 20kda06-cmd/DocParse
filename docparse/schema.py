"""Pydantic models describing what we extract from a document."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class Party(BaseModel):
    name: str | None = Field(None, description="Legal or trading name, exactly as printed.")
    address: str | None = Field(None, description="Postal address on a single line.")
    tax_id: str | None = Field(None, description="VAT / tax / registration number, as printed.")


class LineItem(BaseModel):
    description: str = Field(description="Item or service description, as printed.")
    quantity: Decimal | None = None
    unit_price: Decimal | None = None
    tax_rate: Decimal | None = Field(None, description="Tax rate for this line in percent, e.g. 20 for 20%.")
    total: Decimal | None = Field(None, description="Line total exactly as printed.")


class Invoice(BaseModel):
    document_type: Literal["invoice", "credit_note", "receipt", "other"] = Field(
        description="What kind of document this is."
    )
    invoice_number: str | None = None
    issue_date: date | None = Field(None, description="ISO date (YYYY-MM-DD).")
    due_date: date | None = Field(None, description="ISO date (YYYY-MM-DD).")
    currency: str | None = Field(None, description="ISO 4217 code, e.g. USD, EUR, GBP.")
    vendor: Party = Field(default_factory=Party, description="Who issued the document.")
    customer: Party = Field(default_factory=Party, description="Who it is billed to.")
    line_items: list[LineItem] = Field(default_factory=list)
    subtotal: Decimal | None = Field(None, description="Total before tax, as printed.")
    tax_total: Decimal | None = Field(None, description="Total tax amount, as printed.")
    total: Decimal | None = Field(None, description="Grand total, as printed.")
    uncertain_fields: list[str] = Field(
        default_factory=list,
        description=(
            "Dotted names of fields you were not confident about "
            "(blurry, ambiguous, partially hidden), e.g. 'total' or 'vendor.tax_id'."
        ),
    )
