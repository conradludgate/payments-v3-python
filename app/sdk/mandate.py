import json
from app.sdk.api import do_api_request
from app.sdk.models import CreateMandateRequest
from truelayer_signing import HttpMethod

def create_mandate(mandate: CreateMandateRequest):
    res = do_api_request(HttpMethod.POST, "/mandates", mandate, None)

    try:
        res.raise_for_status()
        return res.json()
    except Exception:
        print(res.content.decode())

def get_mandate(mandate_id: str):
    res = do_api_request(HttpMethod.GET, f"/mandates/{mandate_id}", None, None)

    try:
        res.raise_for_status()
        return res.json()
    except Exception:
        print(res.content.decode())
