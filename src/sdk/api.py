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

if not CLIENT_ID:
    raise ValueError("TL_CLIENT_ID not in Environment Variables")
if not CLIENT_SECRET:
    raise ValueError("TL_CLIENT_SECRET not in Environment Variables")
if not KID:
    raise ValueError("TL_KID not in Environment Variables")

with open("ec512-private.pem") as f:
    PRIVATE_KEY = f.read()

if not PRIVATE_KEY:
    raise ValueError("ec512-private.pem file could not be found")

# the base url to use
TL_BASE_URL: str = "t7r.dev"

client = BackendApplicationClient(client_id=CLIENT_ID)
oauth = OAuth2Session(client=client)
token = oauth.fetch_token(
    token_url=f"https://auth.{TL_BASE_URL}/connect/token",
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET)


def do_api_request(method: HttpMethod, path: str, json_body: Optional[Any], query: Optional[Dict[str, str]]):
    url = f"https://api.{TL_BASE_URL}{path}"
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
