import streamlit as st
import requests
import pandas as pd
from supabase_client import supabase, get_demo_balance

st.set_page_config(page_title="Bot BingX - Panel", page_icon="📊", layout="centered")

BASE_URL = "https://open-api.bingx.com"
SYMBOL = "BTC-USDT"

def get_precio_actual():
    path = "/openApi/spot/v2/market/kline"
    params = {"symbol": SYMBOL, "interval": "5m", "limit": 1}
    r = requests.get(BASE_URL + path, params=params)
    data = r.json()
    return float(data["data"][0][4])

st.title("📊 Bot BingX - Panel de Control")
st.caption("Modo DEMO — fondos virtuales, precios reales")

if st.button("🔄 Actualizar"):
    st.rerun()

try:
    precio = get_precio_actual()
    balance = get_demo_balance()
    usdt = float(balance["usdt"])
    btc = float(balance["btc"])
    valor_btc = btc * precio
    total = usdt + valor_btc

    col1, col2, col3 = st.columns(3)
    col1.metric("USDT libres", f"${usdt:,.2f}")
    col2.metric("BTC en posición", f"{btc:.6f}")
    col3.metric("Valor total", f"${total:,.2f}")

    st.metric("Precio BTC/USDT actual", f"${precio:,.2f}")

    if btc > 0:
        entry = float(balance.get("entry_price") or 0)
        sl = float(balance.get("stop_loss") or 0)
        tp = float(balance.get("take_profit") or 0)
        st.info(f"📈 En posición | Entrada: ${entry:,.2f} | SL: ${sl:,.2f} | TP: ${tp:,.2f}")
    else:
        st.info("⏳ Sin posición abierta")

except Exception as e:
    st.error(f"Error al obtener datos en vivo: {e}")

st.divider()
st.subheader("Historial de operaciones")

try:
    r = supabase.table("operaciones").select("*").order("created_at", desc=True).limit(50).execute()
    df = pd.DataFrame(r.data)
    if not df.empty:
        df = df[["created_at", "side", "price", "quantity", "pnl", "signal_source"]]
        df.columns = ["Fecha", "Tipo", "Precio", "Cantidad", "PnL", "Origen"]
        st.dataframe(df, use_container_width=True, hide_index=True)

        pnl_total = df["PnL"].dropna().sum()
        cerradas = df["PnL"].dropna().shape[0]
        ganadoras = df[df["PnL"] > 0].shape[0]
        winrate = (ganadoras / cerradas * 100) if cerradas > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("PnL acumulado", f"${pnl_total:,.2f}")
        col2.metric("Operaciones cerradas", cerradas)
        col3.metric("Win rate", f"{winrate:.1f}%")
    else:
        st.write("Todavía no hay operaciones registradas.")
except Exception as e:
    st.error(f"Error al leer historial: {e}")
