import time
import hmac
import hashlib
import requests
import os
from indicators import generate_signal
from supabase_client import get_demo_balance, update_demo_balance, log_operation

API_KEY = os.environ.get("BINGX_API_KEY")
API_SECRET = os.environ.get("BINGX_API_SECRET")
BASE_URL = "https://open-api.bingx.com"

MODO = os.environ.get("BOT_MODE", "demo")
SYMBOL = "BTC-USDT"
RIESGO_PCT = 0.05
SL_PCT = 0.01
TP_PCT = 0.015
CHECK_INTERVAL = 60

def get_klines(symbol=SYMBOL, interval="5m", limit=100):
    path = "/openApi/spot/v2/market/kline"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    r = requests.get(BASE_URL + path, params=params)
    data = r.json()
    closes = [float(c[4]) for c in data["data"]]
    closes.reverse()
    return closes

def procesar_demo(price, signal):
    balance = get_demo_balance()
    usdt = float(balance["usdt"])
    btc = float(balance["btc"])
    stop_loss = balance.get("stop_loss")
    take_profit = balance.get("take_profit")
    entry_price = balance.get("entry_price")

    if btc > 0:
        if price <= stop_loss or price >= take_profit or signal == "VENDER":
            usdt_final = btc * price
            pnl = usdt_final - (btc * entry_price)
            update_demo_balance(usdt + usdt_final, 0, None, None, None)
            motivo = "SL/TP" if (price <= stop_loss or price >= take_profit) else "señal"
            log_operation("demo", SYMBOL, "SELL", price, btc, pnl, motivo)
            print(f"[DEMO] VENTA a {price} | PnL: {pnl:.2f} USDT")
        else:
            print(f"[DEMO] En posición | Precio: {price} | SL: {stop_loss:.2f} | TP: {take_profit:.2f}")
    elif signal == "COMPRAR":
        monto = usdt * RIESGO_PCT
        cantidad = monto / price
        nuevo_sl = price * (1 - SL_PCT)
        nuevo_tp = price * (1 + TP_PCT)
        update_demo_balance(usdt - monto, cantidad, price, nuevo_sl, nuevo_tp)
        log_operation("demo", SYMBOL, "BUY", price, cantidad, None, "señal EMA/RSI")
        print(f"[DEMO] COMPRA a {price} | Cantidad: {cantidad:.6f} BTC")
    else:
        print(f"[DEMO] Sin posición | Señal: {signal} | Precio: {price}")

if __name__ == "__main__":
    print(f"=== Bot BingX iniciado en modo {MODO.upper()} ===")
    while True:
        try:
            closes = get_klines()
            price = closes[-1]
            signal = generate_signal(closes)
            if MODO == "demo":
                procesar_demo(price, signal)
            else:
                print("Modo REAL aún no implementado")
        except Exception as e:
            print(f"Error en el loop: {e}")
        time.sleep(CHECK_INTERVAL)
