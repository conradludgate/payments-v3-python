import json
from app.sdk.api import do_api_request
from truelayer_signing import HttpMethod

def create_payment(payment):
    res = do_api_request(HttpMethod.POST, "/payments", payment, None)

    try:
        res.raise_for_status()
        return res.json()
    except Exception:
        print(res.content.decode())

def get_payment(payment_id: str):
    res = do_api_request(HttpMethod.GET, f"/payments/{payment_id}", None, None)

    try:
        res.raise_for_status()
        return res.json()
    except Exception:
        print(res.content.decode())
