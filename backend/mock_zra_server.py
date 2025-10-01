# mock_zra_server.py
import random
import uuid
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field
from typing import List, Optional

app = FastAPI(title="Mock ZRA E-Invoicing Server")

# --- Mock Schemas ---
class InvoiceItem(BaseModel):
    item_name: str
    quantity: int
    price: float

class InvoiceSubmission(BaseModel):
    transaction_id: str
    total_amount: float
    tax_amount: float
    items: List[InvoiceItem]

class InvoiceResponse(BaseModel):
    zra_invoice_id: str = Field(..., description="The unique ID from ZRA")
    qr_code_data: str = Field(..., description="Data to be encoded into a QR code")
    status: str = "SUBMITTED"


@app.post("/v1/invoices/submit", response_model=InvoiceResponse)
async def submit_invoice(
    invoice: InvoiceSubmission, 
    api_key: Optional[str] = Header(None)
):
    """
    Mock endpoint to simulate submitting an invoice to the tax authority.
    """
    print(f"Received invoice submission: {invoice.model_dump()}")
    if not api_key or api_key != "test_api_key":
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")

    # Simulate a chance of failure
    if random.random() < 0.1: # 10% chance of failure
        raise HTTPException(status_code=503, detail="ZRA Service Unavailable")

    zra_id = f"ZRA-{uuid.uuid4().hex[:8].upper()}"
    qr_data = f"https://verify.zra.gov.zm/inv?id={zra_id}&tid={invoice.transaction_id}"
    
    return InvoiceResponse(zra_invoice_id=zra_id, qr_code_data=qr_data)