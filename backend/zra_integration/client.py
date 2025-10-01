# zra_integration/client.py
import httpx
from schemas import ZRAInvoiceSubmission

class ZRAClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {"api-key": api_key}

    def submit_invoice(self, invoice_data: ZRAInvoiceSubmission):
        """
        Submits an invoice to the ZRA API.
        Returns the response JSON on success, raises an exception on failure.
        """
        url = f"{self.base_url}/v1/invoices/submit"
        try:
            with httpx.Client() as client:
                response = client.post(
                    url,
                    json=invoice_data.model_dump(),
                    headers=self.headers,
                    timeout=10.0 # Set a reasonable timeout
                )
                response.raise_for_status() # Raises HTTPError for 4xx/5xx responses
                return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            print(f"An error occurred while requesting {e.request.url!r}.")
            raise