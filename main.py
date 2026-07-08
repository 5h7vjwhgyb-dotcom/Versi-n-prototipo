import time
import hmac
import hashlib
import requests
import os

API_KEY = os.environ.get("BINGX_API_KEY")
API_SECRET = os.environ.get("BINGX_API_SECRET")
BASE_URL = "https://open-api.bingx.com"

def sign(params: dict) -> str:
    query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
    return hmac.new(
        API_SECRET.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

def get_balance():
    path = "/openApi/spot/v1/account/balance"
    params = {
        "timestamp": int(time.time() * 1000),
        "recvWindow": 5000
    }
    params["signature"] = sign(params)
    headers = {"X-BX-APIKEY": API_KEY}
    r = requests.get(BASE_URL + path, params=params, headers=headers)
    return r.json()

def get_btc_price():
    path = "/openApi/spot/v1/ticker/price"
    params = {"symbol": "BTC-USDT"}
    r = requests.get(BASE_URL + path, params=params)
    return r.json()

if __name__ == "__main__":
    print("=== Test de conexión BingX ===")
    print("\n--- Precio BTC/USDT (público) ---")
    print(get_btc_price())
    print("\n--- Balance de cuenta (privado) ---")
    print(get_balance())
