# std imports
import os
from datetime import datetime, timedelta
from typing import Union
import urllib
import uuid
from app.sdk.api import GH_CLIENT_ID, GH_CLIENT_SECRET

from app.sdk.auth_flow import start_auth_flow
from app.sdk.models import Currency, MandateType, PeriodAlignment
from app.sdk.mandate import create_mandate, get_mandate

from truelayer_signing import HttpMethod, extract_jws_header, verify_with_jwks
from truelayer_signing.errors import TlSigningException

import json
import requests
import uvicorn
from fastapi import FastAPI, Request, Header, Form, Response, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.sdk.payment import create_payment

BASE_HOST = os.getenv("BASE_HOST")

app = FastAPI()
templates = Jinja2Templates(directory="templates")

class User:
    def __init__(self, name: str):
        self.name = name
        self.payments = []
        self.mandate = None

github_users = {}
users = {}

@app.get("/", response_class=HTMLResponse)
async def root(
    request: Request,
    id: Union[str, None] = Cookie(default=None)
):
    global users, payments
    print(users)
    user = None
    balance = 100000
    if id is not None:
        user = users[id]
        for payment in user.payments:
            for event in payments[payment]:
                if event['type'] == "payment_executed":
                    balance -= 10000

    return templates.TemplateResponse("index.html", {"request": request, 'user': user, 'balance': balance})

@app.get("/login")
async def login():
    query = urllib.parse.urlencode({
        'client_id': GH_CLIENT_ID, 
        'redirect_uri': "https://vrp.conrad.cafe/login/github",
        'state': 'vrp',
        'allow_signup': False,
    })
    return RedirectResponse(f"https://github.com/login/oauth/authorize?{query}", status_code=303)

@app.get("/login/github")
async def auth(code: str, request: Request):
    global users, github_users
    data = {
        'client_id': GH_CLIENT_ID, 
        'client_secret': GH_CLIENT_SECRET, 
        'redirect_uri': "https://vrp.conrad.cafe/login/github",
        'code': code,
    }
    headers = { 'Accept': 'application/json' }
    token = requests.post("https://github.com/login/oauth/access_token", headers=headers, json=data).json()
    
    headers = { 'Authorization': f'Bearer {token["access_token"]}' }
    user = requests.get("https://api.github.com/user", headers=headers).json()

    try:
        id = github_users[user["login"]]
    except:
        id = str(uuid.uuid4())
        github_users[user["login"]] = id
        users[id] = User(user["name"])

    resp = templates.TemplateResponse("redirect.html", {
        "request": request,
		"path": "/",
		"text": "Complete Login",
	})
    resp.set_cookie(key="id", value=id)
    return resp

@app.get("/callback")
async def callback(mandate_id: str):
    return RedirectResponse(f"/", status_code=303)

@app.post("/mandate")
async def post_mandate(id: str = Cookie(default=None)):
    global users
    user = users[id]
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
            "id": id,
            "email": "user@example.com",
            "name": user.name,
        },
        "constraints": {
            "valid_from": datetime.utcnow(),
            "valid_to": datetime.utcnow() + timedelta(days=1),
            "maximum_individual_amount": 10000,
            "periodic_limits": {
                "month": {
                    "maximum_amount": 20000,
                    "period_alignment": PeriodAlignment.consent
                }
            }
        }
    })
    user.mandate = mandate["id"]
    resp = start_auth_flow(mandate["id"], {
        'redirect': {
            'return_uri': f"{BASE_HOST}/callback"
        }
    })
    return RedirectResponse(resp["authorization_flow"]["actions"]["next"]["uri"], status_code=303)

payments = {}

@app.post("/payment", response_class=HTMLResponse)
async def post_payment(id: str = Cookie(default=None)):
    global payments, users
    user = users[id]
    payment = create_payment({
			"amount_in_minor": 10000,
			"currency":      "GBP",
			"payment_method": {
				"type":      "mandate",
				"mandate_id": user.mandate,
			}
    })
    payment_id = payment["id"]
    user.payments.append(payment_id)
    payments[payment_id] = []
    return RedirectResponse(f"/payment/{payment_id}", status_code=303)

@app.get("/payment/{payment_id}", response_class=HTMLResponse)
async def payment(request: Request, payment_id: str):
    global payments
    data = {"request": request}
    events = payments[payment_id]
    if len(events) > 0:
        event = events[len(events)-1]
        if event["type"] == "payment_executed":
            data["executed"] = True
        elif event["type"] == "payment_failed":
            data["failure_reason"] = event["failure_reason"]
        
    return templates.TemplateResponse("payment.html", data)

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
    global payments
    event = await request.json()

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

    try:
        payment_id = event['payment_id']
        payments[payment_id].append(event)
    except:
        pass

def start():
    uvicorn.run(app, port=3000, log_level="info", host="0.0.0.0", proxy_headers=True)
