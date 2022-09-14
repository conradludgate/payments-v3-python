
from src.sdk.api import do_api_request
from models import CreateMandateRequest, Currency, MandateType, PeriodAlignment
from truelayer_signing import HttpMethod

def create_mandate(mandate: CreateMandateRequest):
    res = do_api_request(HttpMethod.POST, "/mandates", mandate, None)

    try:
        res.raise_for_status()
        return res.content.decode()
    except Exception:
        print(res.content.decode())
