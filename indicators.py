def ema(values, period):
    k = 2 / (period + 1)
    ema_values = [values[0]]
    for price in values[1:]:
        ema_values.append(price * k + ema_values[-1] * (1 - k))
    return ema_values

def rsi(values, period=14):
    gains, losses = [], []
    for i in range(1, len(values)):
        change = values[i] - values[i - 1]
        gains.append(max(change, 0))
        losses.append(max(-change, 0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    rsi_values = []
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        rs = avg_gain / avg_loss if avg_loss != 0 else 999
        rsi_values.append(100 - (100 / (1 + rs)))
    return rsi_values

def generate_signal(closes):
    ema9 = ema(closes, 9)
    ema21 = ema(closes, 21)
    rsi14 = rsi(closes, 14)
    if len(rsi14) < 2:
        return "ESPERAR"
    cross_up = ema9[-2] <= ema21[-2] and ema9[-1] > ema21[-1]
    cross_down = ema9[-2] >= ema21[-2] and ema9[-1] < ema21[-1]
    current_rsi = rsi14[-1]
    if cross_up and current_rsi < 70:
        return "COMPRAR"
    elif cross_down and current_rsi > 30:
        return "VENDER"
    return "ESPERAR"
