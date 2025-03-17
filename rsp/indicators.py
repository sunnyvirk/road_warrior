import pandas as pd
import numpy as np
import talib

import math

import dynamicMAs as DynamicMA

# RSI Standard Deviation
def rsisd(df):

    close = df['close']

    length = 21
    sdLength = 8

    rsiSet = talib.RSI(close, length)
    atrSet = talib.STDDEV(rsiSet, sdLength)

    rsi = rsiSet.iloc[-1]
    atr = atrSet.iloc[-1]

    d = rsi - atr

    L = d > 50
    S = rsi < 50

    signal = 0

    if L and not S:
        signal = 1

    if S:
        signal = -1

    return signal

# Median Super Trend
def medianSupertrend(df):
    high, low, close = df['high'], df['low'], df['close']

    subject = 5
    multiplier = 1.35
    slen = 5

    atr = talib.ATR(high, low, close, timeperiod=subject)

    median = pd.Series(close).rolling(window=slen).median().to_numpy()

    upper_band = median + (multiplier * atr)
    lower_band = median - (multiplier * atr)

    supertrend = pd.Series(np.nan, index=df.index)

    for i in range(1, len(atr.index)):

        l = lower_band.iloc[i]
        u = upper_band.iloc[i]

        pl = lower_band.iloc[i-1]
        pu = upper_band.iloc[i-1]

        l = l if l > pl or close.iloc[i-1] < pl else pl
        u = u if u < pu or close.iloc[i-1] > pu else pu

        d = 0
        pt = supertrend[i-1]

        if np.isnan(atr.iloc[i-1]):
            d = 1
        elif pt == pu:
            d = -1 if close.iloc[i] > u else 1
        else:
            d = 1 if close.iloc[i] < l else -1

        st = l if d == -1 else u

        supertrend.iloc[i] = st
    
    stl = d < 0
    sts = d > 0

    L = stl
    S = sts

    signal = 0

    if L and not S: 
        signal = 1

    if S:
        signal = -1

    return signal

def calcVwVariance(src, volume, length, id):
    maPrice    = DynamicMA.VWMA(src, volume, length, id)

    variance_data = volume * (src - maPrice) ** 2
    sumVar     = DynamicMA.SMA(variance_data, length)
    sumVolume  = DynamicMA.SMA(volume, length)

    if math.isinf(sumVar) or math.isinf(sumVolume):
        return 0

    vwVariance = sumVar / sumVolume
    vwStdDev   = np.sqrt(vwVariance)
    return vwStdDev

# Rolling VWAP
def rolling_vwap(df, id):
    src = df['close']
    volume = df['volume']

    length = 50

    if all(volume == 0.0):
        return 0, 0, 0

    if len(src) < length:
        return 0, 0, 0

    rollingVwap = DynamicMA.VWMA(src, volume, length, id)
    stdevAbs = calcVwVariance(src, volume, length, id)

    upperBandValue1 = rollingVwap + stdevAbs * 0.5
    lowerBandValue1 = rollingVwap - stdevAbs * 0.5

    bullish = src.iloc[-1] > rollingVwap
    bearish = src.iloc[-1] < rollingVwap

    signal = 0

    if bullish:
        signal = 1

    if bearish:
        signal = -1

    trendingUp = src.iloc[-1] > upperBandValue1
    trendingDown = src.iloc[-1] < lowerBandValue1

    trendingUpSignal = 0

    if trendingUp:
        trendingUpSignal = 1
    
    trendingDownSignal = 0

    if trendingDown:
        trendingDownSignal = -1

    return signal, trendingUpSignal, trendingDownSignal
