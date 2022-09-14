from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4
import json

# third-party imports
import requests
from truelayer_signing import HttpMethod, sign_with_pem

from auth import KID, PRIVATE_KEY, TL_BASE_URL, token

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
