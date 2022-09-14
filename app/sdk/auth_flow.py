import json
from app.sdk.api import do_api_request
from truelayer_signing import HttpMethod

def start_auth_flow(mandate_id, req):
    res = do_api_request(HttpMethod.POST, f"/mandates/{mandate_id}/authorization-flow", req, None)

    try:
        res.raise_for_status()
        return res.json()
    except Exception:
        print(res.content.decode())
