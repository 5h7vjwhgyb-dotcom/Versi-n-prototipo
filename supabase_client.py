import os
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_demo_balance():
    r = supabase.table("demo_balance").select("*").eq("id", 1).execute()
    return r.data[0]

def update_demo_balance(usdt, btc, entry_price=None, stop_loss=None, maximo=None, tp_parcial=False, pnl_acumulado=0):
    supabase.table("demo_balance").update({
        "usdt": usdt,
        "btc": btc,
        "entry_price": entry_price,
        "stop_loss": stop_loss,
        "maximo": maximo,
        "tp_parcial": tp_parcial,
        "pnl_acumulado": pnl_acumulado
    }).eq("id", 1).execute()

def log_operation(modo, symbol, side, price, quantity, pnl=None, signal_source=None):
    supabase.table("operaciones").insert({
        "modo": modo,
        "symbol": symbol,
        "side": side,
        "price": price,
        "quantity": quantity,
        "pnl": pnl,
        "signal_source": signal_source
    }).execute()
