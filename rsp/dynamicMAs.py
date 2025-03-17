import math

# Dynamic Simple Moving Average (SMA)
def SMA(src, length):

    # Initialize variables for the SMA calculation
    sum = 0.0
    count = 0
    
    # Iterate through the length values of `src`
    for i in range(length):
        value = src.iloc[-(i + 1)]  # Access values from the end of the list
        sum += value
        count += 1
    
    # Return the average if there are valid data points, otherwise return None
    if count > 0:
        return sum / count
    else:
        return None

# Dynamic Volume Weighted Moving Average (VWMA)
def VWMA(src, volume, length, id):
    sum_vol_price = 0.0
    sum_vol = 0.0

    for i in range(length):
        price = src.iloc[-(i + 1)]
        vol = volume.iloc[-(i + 1)]
        
        sum_vol_price += price * vol
        sum_vol += vol

    if math.isinf(sum_vol_price) or math.isinf(sum_vol):
        result = 0
    else:
        result = sum_vol_price / sum_vol if sum_vol > 0 else 0
    return result
