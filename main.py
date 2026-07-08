import time
import hmac
import hashlib
import requests
import os
from indicators import generate_signal

API_KEY = os.environ.get("BINGX_API_KEY")
API_SECRET = os.environ.get("BINGX_API_SECRET")
BASE_URL = "https://open-api.bingx.com"

def sign(params: dict):
    query_string = "&".join([f"{k}={params[k]}" for k in sorted(params.keys())])
    signature = hmac.new(
        API_SECRET.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    return query_string, signature

def get_balance():
    path = "/openApi/spot/v1/account/balance"
    params = {"timestamp": int(time.time() * 1000), "recvWindow": 5000}
    query_string, signature = sign(params)
    url = f"{BASE_URL}{path}?{query_string}&signature={signature}"
    headers = {"X-BX-APIKEY": API_KEY}
    r = requests.get(url, headers=headers)
    return r.json()

def get_klines(symbol="BTC-USDT", interval="5min", limit=100):
    path = "/openApi/spot/v2/market/kline"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    r = requests.get(BASE_URL + path, params=params)
    data = r.json()
    print("RAW RESPONSE:", data)
    closes = [float(c[4]) for c in data["data"]]
    closes.reverse()
    return closes

if __name__ == "__main__":
    print("=== Test de señal BTC/USDT (5min) ===")
    closes = get_klines()
    print(f"Últimas {len(closes)} velas obtenidas")
    print(f"Precio actual: {closes[-1]}")
    signal = generate_signal(closes)
    print(f"Señal actual: {signal}")
    print("\n--- Balance de cuenta ---")
    print(get_balance())
