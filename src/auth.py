import os

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
