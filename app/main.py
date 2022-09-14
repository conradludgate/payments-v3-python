# std imports
from ctypes import Union
import os
from datetime import datetime, timedelta

from app.sdk.auth_flow import start_auth_flow
from app.sdk.models import Currency, MandateType, PeriodAlignment
from app.sdk.mandate import create_mandate, get_mandate

from truelayer_signing import HttpMethod, extract_jws_header, verify_with_jwks
from truelayer_signing.errors import TlSigningException

import json
import requests
import uvicorn
from fastapi import FastAPI, Request, Header
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

BASE_HOST = os.getenv("BASE_HOST")

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/mandate/{mandate_id}", response_class=HTMLResponse)
async def mandate(request: Request, mandate_id: str):
    return templates.TemplateResponse("index.html", {"request": request, "mandate_id": mandate_id})

@app.get("/callback")
async def callback(mandate_id: str):
    return RedirectResponse(f"/mandate/{mandate_id}", status_code=303)

@app.post("/mandate")
async def post_mandate():
    mandate = create_mandate({
        'mandate': {
            'type': MandateType.sweeping,
            'provider_selection': {
                'type': 'preselected',
                'provider_id': 'ob-natwest-vrp-sandbox'
            },
            'beneficiary': {
                'type': 'external_account',
                'account_holder_name': 'Floob',
                'account_identifier': {
                    'type': "sort_code_account_number",
                    'sort_code': "123456",
                    'account_number': "76543210",
                }
            }
        },
        'currency': Currency.GBP,
        'user': {
            "id": "df69744a-fe8f-4acc-8b89-ba863297234c",
            "email": "conrad@lud.co",
            "name": "Co lu",
        },
        "constraints": {
            "valid_from": datetime.utcnow(),
            "valid_to": datetime.utcnow() + timedelta(days=1),
            "maximum_individual_amount": 5000,
            "periodic_limits": {
                "month": {
                    "maximum_amount": 10000,
                    "period_alignment": PeriodAlignment.consent
                }
            }
        }
    })
    resp = start_auth_flow(mandate["id"], {
        'redirect': {
            'return_uri': f"{BASE_HOST}/callback"
        }
    })
    print(resp)
    return RedirectResponse(resp["authorization_flow"]["actions"]["next"]["uri"], status_code=303)

@app.get("/teapot", status_code=418, response_class=HTMLResponse)
async def teapot():
    return """
When the world is all at odds <br/>
And the mind is all at sea <br/>
Then cease the useless tedium <br/>
And brew a cup of tea. <br/>
There is magic in its fragrance, <br/>
There is solace in its taste; <br/>
And the laden moments vanish <br/>
Somehow into space. <br/>
The world becomes a lovely thing! <br/>
There’s beauty as you’ll see; <br/>
All because you briefly stopped <br/>
To brew a cup of tea.
"""

@app.post("/webhook")
async def webhook(
    request: Request, 
    tl_signature: str = Header(default=None),
    x_tl_webhook_timestamp: str = Header(default=None)
):
    print(await request.json())

    jws_header = extract_jws_header(tl_signature)
    jku = jws_header.jku
    valid_jku = "https://webhooks.t7r.dev/.well-known/jwks"
    if jku != valid_jku:
        raise ValueError(f"Unpermitted jku {jku}")

    res = requests.get(jku)
    res.raise_for_status()
    jwks = res.json()

    verify_with_jwks(jwks, jws_header) \
        .set_method(HttpMethod.POST) \
        .set_path("/webhook") \
        .add_headers({"x-tl-webhook-timestamp": x_tl_webhook_timestamp}) \
        .set_body((await request.body()).decode()) \
        .verify(tl_signature)

def start():
    uvicorn.run(app, port=3000, log_level="info", host="0.0.0.0", proxy_headers=True)
