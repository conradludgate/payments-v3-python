from datetime import datetime
import os
from typing import Any, Dict, Optional
from uuid import uuid4
import json

# third-party imports
import requests
from truelayer_signing import HttpMethod, sign_with_pem
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

KID = os.getenv("TL_KID")
CLIENT_ID = os.getenv("TL_CLIENT_ID")
CLIENT_SECRET = os.getenv("TL_CLIENT_SECRET")
PRIVATE_KEY = os.getenv("TL_PRIVATE_KEY")

if not CLIENT_ID:
    raise ValueError("TL_CLIENT_ID not in Environment Variables")
if not CLIENT_SECRET:
    raise ValueError("TL_CLIENT_SECRET not in Environment Variables")
if not KID:
    raise ValueError("TL_KID not in Environment Variables")
if not PRIVATE_KEY:
    raise ValueError("TL_PRIVATE_KEY not in Environment Variables")

print(CLIENT_ID, CLIENT_SECRET)

headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
}
data = {
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'grant_type': 'client_credentials',
    'scope': 'payments recurring_payments:sweeping'
}
token = requests.post("https://auth.t7r.dev/connect/token", headers=headers, data=data).json()

def do_api_request(method: HttpMethod, path: str, json_body: Optional[Any], query: Optional[Dict[str, str]]):
    url = f"https://api.t7r.dev{path}"
    idempotency_key = str(uuid4())

    def datetime_conv(o):
        if isinstance(o, datetime):
            return o.isoformat(timespec='milliseconds')
    body = json.dumps(json_body, default=datetime_conv)

    signature = (
        sign_with_pem(KID, PRIVATE_KEY)
        .set_method(method)
        .set_path(path)
        .add_header("Idempotency-Key", idempotency_key)
        .set_body(body)
        .sign()
    )

    access_token = token["access_token"]
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Idempotency-Key": idempotency_key,
        "Tl-Signature": signature,
    }

    return requests.request(method, url, headers=headers, data=body, params=query)
