import time
import hmac
import hashlib
import requests
import os
from indicators import ema, rsi, atr, adx, sma
from supabase_client import get_demo_balance, update_demo_balance, log_operation

API_KEY = os.environ.get("BINGX_API_KEY")
API_SECRET = os.environ.get("BINGX_API_SECRET")
BASE_URL = "https://open-api.bingx.com"

MODO = os.environ.get("BOT_MODE", "demo")
SYMBOL = "BTC-USDT"
INVERSION_PCT = 0.95
SL_ATR_MULT = 2.5
PARCIAL_TP_ATR_MULT = 3.0
FEE_PCT = 0.001
CHECK_INTERVAL = 900  # 15 minutos (velas diarias, no hace falta más frecuencia)

def sign(params: dict):
    query_string = "&".join([f"{k}={params[k]}" for k in sorted(params.keys())])
    signature = hmac.new(
        API_SECRET.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    return query_string, signature

def get_klines_daily(symbol=SYMBOL, interval="1d", limit=300):
    path = "/openApi/spot/v2/market/kline"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    r = requests.get(BASE_URL + path, params=params)
    data = r.json()["data"]
    data = list(reversed(data))
    highs = [float(c[2]) for c in data]
    lows = [float(c[3]) for c in data]
    closes = [float(c[4]) for c in data]
    volumes = [float(c[5]) for c in data]
    return highs, lows, closes, volumes

def calcular_indicadores(highs, lows, closes, volumes):
    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50)
    ema200 = ema(closes, 200)
    rsi14 = rsi(closes, 14)
    atr14 = atr(highs, lows, closes, 14)
    adx14 = adx(highs, lows, closes, 14)
    vol_sma20 = sma(volumes, 20)
    atr_sma20 = sma(atr14, 20)
    return {
        "ema20": ema20[-1], "ema50": ema50[-1], "ema200": ema200[-1],
        "rsi": rsi14[-1], "atr": atr14[-1], "adx": adx14[-1],
        "vol_actual": volumes[-1], "vol_sma20": vol_sma20[-1],
        "atr_sma20": atr_sma20[-1]
    }

def procesar_demo(price, ind):
    balance = get_demo_balance()
    usdt = float(balance["usdt"])
    btc = float(balance["btc"])
    entry_price = balance.get("entry_price")
    stop = balance.get("stop_loss")
    maximo = balance.get("maximo") or 0
    tp_parcial = balance.get("tp_parcial") or False
    pnl_acumulado = float(balance.get("pnl_acumulado") or 0)

    if btc > 0:
        if price > maximo:
            maximo = price

        nuevo_stop = maximo - (ind["atr"] * SL_ATR_MULT)
        if stop is None or nuevo_stop > stop:
            stop = nuevo_stop

        if not tp_parcial and price >= entry_price + (ind["atr"] * PARCIAL_TP_ATR_MULT):
            vender = btc * 0.5
            dinero = vender * price * (1 - FEE_PCT)
            costo = vender * entry_price
            pnl_parcial = dinero - costo
            pnl_acumulado += pnl_parcial
            usdt += dinero
            btc -= vender
            tp_parcial = True
            stop = entry_price
            update_demo_balance(usdt, btc, entry_price, stop, maximo, tp_parcial, pnl_acumulado)
            log_operation("demo", SYMBOL, "SELL_PARCIAL", price, vender, pnl_parcial, "TP parcial 3xATR")
            print(f"[DEMO] TP PARCIAL a {price} | PnL parcial: {pnl_parcial:.2f}")
            return

        cerrar = False
        motivo = ""
        if price <= stop:
            cerrar = True
            motivo = "TRAILING"
        elif ind["ema20"] < ind["ema50"]:
            cerrar = True
            motivo = "CAMBIO_TENDENCIA"

        if cerrar:
            dinero = btc * price * (1 - FEE_PCT)
            costo = btc * entry_price
            pnl_final = dinero - costo
            pnl_total = pnl_acumulado + pnl_final
            usdt += dinero
            update_demo_balance(usdt, 0, None, None, 0, False, 0)
            log_operation("demo", SYMBOL, "SELL", price, btc, pnl_total, motivo)
            print(f"[DEMO] CIERRE ({motivo}) a {price} | PnL total: {pnl_total:.2f}")
        else:
            update_demo_balance(usdt, btc, entry_price, stop, maximo, tp_parcial, pnl_acumulado)
            print(f"[DEMO] En posición | Precio: {price} | Stop: {stop:.2f} | Parcial tomado: {tp_parcial}")

    else:
        tendencia = ind["ema20"] > ind["ema50"]
        tendencia_larga = price > ind["ema200"]
        fuerza = ind["adx"] > 20
        volumen_ok = ind["vol_actual"] > ind["vol_sma20"]
        rsi_ok = 50 < ind["rsi"] < 70
        volatilidad_ok = ind["atr"] > ind["atr_sma20"]

        if tendencia and tendencia_larga and fuerza and volumen_ok and rsi_ok and volatilidad_ok:
            monto = usdt * INVERSION_PCT
            cantidad = (monto * (1 - FEE_PCT)) / price
            usdt -= monto
            nuevo_stop = price - (ind["atr"] * SL_ATR_MULT)
            update_demo_balance(usdt, cantidad, price, nuevo_stop, price, False, 0)
            log_operation("demo", SYMBOL, "BUY", price, cantidad, None, "V2 ADX+Tendencia+Vol")
            print(f"[DEMO] COMPRA a {price} | Cantidad: {cantidad:.6f}")
        else:
            print(f"[DEMO] Sin posición | Precio: {price} | ADX: {ind['adx']:.1f} | RSI: {ind['rsi']:.1f}")

if __name__ == "__main__":
    print(f"=== Bot BingX V2.0 (diario) iniciado en modo {MODO.upper()} ===")
    while True:
        try:
            highs, lows, closes, volumes = get_klines_daily()
            price = closes[-1]
            ind = calcular_indicadores(highs, lows, closes, volumes)
            if MODO == "demo":
                procesar_demo(price, ind)
            else:
                print("Modo REAL aún no implementado")
        except Exception as e:
            print(f"Error en el loop: {e}")
        time.sleep(CHECK_INTERVAL)
