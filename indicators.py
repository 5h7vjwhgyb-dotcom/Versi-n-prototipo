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

def sma(values, period):
    return [sum(values[i - period + 1:i + 1]) / period for i in range(period - 1, len(values))]

def true_range(highs, lows, closes):
    trs = [highs[0] - lows[0]]
    for i in range(1, len(closes)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1])
        )
        trs.append(tr)
    return trs

def atr(highs, lows, closes, period=14):
    trs = true_range(highs, lows, closes)
    atr_values = [sum(trs[:period]) / period]
    for tr in trs[period:]:
        atr_values.append((atr_values[-1] * (period - 1) + tr) / period)
    return atr_values

def adx(highs, lows, closes, period=14):
    plus_dm = [0.0]
    minus_dm = [0.0]
    for i in range(1, len(highs)):
        up_move = highs[i] - highs[i - 1]
        down_move = lows[i - 1] - lows[i]
        plus_dm.append(up_move if (up_move > down_move and up_move > 0) else 0.0)
        minus_dm.append(down_move if (down_move > up_move and down_move > 0) else 0.0)

    trs = true_range(highs, lows, closes)

    def wilder_smooth(values, period):
        smoothed = [sum(values[:period])]
        for v in values[period:]:
            smoothed.append(smoothed[-1] - (smoothed[-1] / period) + v)
        return smoothed

    smoothed_tr = wilder_smooth(trs, period)
    smoothed_plus_dm = wilder_smooth(plus_dm, period)
    smoothed_minus_dm = wilder_smooth(minus_dm, period)

    plus_di = [100 * (pdm / tr) if tr != 0 else 0 for pdm, tr in zip(smoothed_plus_dm, smoothed_tr)]
    minus_di = [100 * (mdm / tr) if tr != 0 else 0 for mdm, tr in zip(smoothed_minus_dm, smoothed_tr)]

    dx = [100 * abs(p - m) / (p + m) if (p + m) != 0 else 0 for p, m in zip(plus_di, minus_di)]

    adx_values = [sum(dx[:period]) / period]
    for d in dx[period:]:
        adx_values.append((adx_values[-1] * (period - 1) + d) / period)

    return adx_values
