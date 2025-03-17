import pandas as pd
import numpy as np

from rich import print
from rich.progress import track
from rich.console import Console
from rich.table import Table
console = Console()

import coingecko
import indicators

import styles

import warnings
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)
warnings.simplefilter(action='ignore', category=FutureWarning)

def calculate_beta(instrument_returns, benchmark_returns, length):
    instrument_returns = instrument_returns[-length:]

    benchmark_returns = benchmark_returns[-length:]
    
    avg_inst_return = instrument_returns.mean()
    avg_bench_return = benchmark_returns.mean()

    covariance = np.cov(instrument_returns - avg_inst_return, benchmark_returns - avg_bench_return)[0][1]
    variance = benchmark_returns.var()
    
    beta = covariance / variance
    return beta

# Calculate volatility
def calculate_volatility(df, period):
    daily_return = df['return']
    returns_array = np.array(daily_return[-period:])

    return round(np.std(returns_array), 2)


# Calculate alpha
def calculate_alpha(df, base, period, beta):
    # Extract daily returns
    daily_return = df['return']
    daily_base_return = base['return']

    # Ensure the period does not exceed the length of the data
    period = min(period, len(daily_return) - 1, len(daily_base_return) - 1)

    # Convert to numpy arrays
    returns_array = np.array(daily_return[-period:])
    returns_base_array = np.array(daily_base_return[-period:])
    
    if np.sum(returns_array) < 0 or np.sum(returns_base_array) < 0:
        return 0

    # Calculate alpha
    alpha = np.sum(returns_array) - np.sum(returns_base_array) * beta
    alpha = round(np.sqrt(max(alpha, 0)), 2)
    
    return alpha

# Calculate sharpe ratio
def calculate_sharpe_ratio2(df, lookback):
    daily_return = df['return']
    returns_array = np.array(daily_return[-lookback:])

    standard_deviation = np.std(returns_array)
    mean = np.mean(returns_array)

    if standard_deviation == 0:
        return 0

    return round(mean / standard_deviation * np.sqrt(lookback), 2)

# Calculate sortino ratio
def calculate_sortino_ratio(id, df, lookback):
    daily_return = df['return']
    returns_array = np.array(daily_return[-lookback:])

    negative_returns_array = returns_array[returns_array < 0]

    if len(negative_returns_array) == 0:
        standard_deviation = 0
    else:
        standard_deviation = np.std(negative_returns_array)

    mean = np.mean(returns_array)

    if standard_deviation == 0 or np.isnan(standard_deviation):
        return 0

    return round(mean / standard_deviation * np.sqrt(lookback), 2)

# Calculate omega ratio
def calculate_omega_ratio(df, lookback):
    daily_return = df['return']
    negative_returns_array = np.array(daily_return[daily_return < 0])
    positive_returns_array = np.array(daily_return[daily_return > 0])

    postive_area = np.sum(positive_returns_array)
    negative_area = np.sum(negative_returns_array) * (-1)

    if negative_area == 0 or postive_area == 0:
        return 0
    
    return round(postive_area / negative_area, 2)


def seed(coins, major_id, MAJOR_DF, cat):

    print('\n')
    console.print('SEEDING DATA', style=f"bold {styles.SECONDARY}")

    RSP_DF = pd.DataFrame()

    length = 500

    if cat == 'meme-token':
        length = 90
    elif cat == 'artificial-intelligence':
        length = 180

    for index, coin in track(coins.iterrows(), description="Downloading...", total=len(coins)):
        id = coin['id']

        number = f'0{index}' if index < 10 else index
        console.print(f"   .... {number}/{len(coins)} fetching {id}", end='\r')

        df = pd.DataFrame()

        if id == major_id:
            continue

        try:

            df = pd.read_csv(f'crypto/close/{id}.csv')

            if df.empty:

                df = coingecko.createCloseOnlyDataFrame(id)

                df.to_csv(f'crypto/close/{id}.csv', index=True)
            else:
                last_date = pd.to_datetime(df['date'].iloc[-1])
                today = pd.to_datetime('today').normalize()

                if last_date < today:
                    new_data = coingecko.createCloseOnlyDataFrame(id, (today - last_date).days + 1)

                    new_data = new_data.iloc[1:]

                    new_data['date'] = pd.to_datetime(new_data.index, format='%Y-%m-%d')
                    new_data.reset_index(drop=True, inplace=True)

                    # Merge the data
                    df = pd.concat([df, new_data])
                    df = df.reset_index()

                    df.drop(columns=['index'], inplace=True)

                    df['date'] = pd.to_datetime(df['date']).dt.date  
                    df.drop_duplicates(subset=['date'], inplace=True)
                    df.set_index('date', inplace=True)
                    df.to_csv(f'crypto/close/{id}.csv', index=True)

        except FileNotFoundError:
            df = coingecko.createCloseOnlyDataFrame(id)
            df.to_csv(f'crypto/close/{id}.csv', index=True)
            df = pd.read_csv(f'crypto/close/{id}.csv')

        if df.empty:
            continue

        marketcap = df['marketcap'].iloc[-1]

        if marketcap < 10_000_000:
            continue

        def calculations(length):
            beta = round(calculate_beta(df['return'], MAJOR_DF['return'], length), 2)

            volatility = calculate_volatility(df, length)        
            alpha = calculate_alpha(df, MAJOR_DF, length, beta) # SHOULD alpha length be the same as beta length? or less?
            sharpe_ratio = calculate_sharpe_ratio2(df, length)
            sortino_ratio = calculate_sortino_ratio(id, df, length)
            omega_ratio = calculate_omega_ratio(df, length)

            row = pd.DataFrame({
                'id': id,
                'symbol': coin['symbol'],
                'len': len(df),
                'marketcap': df['marketcap'].iloc[-1],
                'beta': beta,
                'alpha': alpha,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'sortino_ratio': sortino_ratio,
                'omega_ratio': omega_ratio
            }, index=[0])

            return row

        if len(df) < length:
            continue

        row = calculations(length)

        RSP_DF = pd.concat([RSP_DF, row], ignore_index=True)
    
    return RSP_DF

def tpiAggregate(df, id):
    rsi_sd_signal = indicators.rsisd(df)
    median_supertrend_signal = indicators.medianSupertrend(df)
    signal, trendingUpSignal, trendingDownSignal = indicators.rolling_vwap(df, id)

    tpi = (rsi_sd_signal + median_supertrend_signal + signal + trendingUpSignal + trendingDownSignal) / 5

    regime = 's'
    if trendingUpSignal == 1:
        regime = 'up'
    elif trendingDownSignal == -1:
        regime = 'down'
    else:
        if signal == 1:
            regime = 'up s'
        elif signal == -1:
            regime = 'down s'

    return tpi, regime

def trendMAJOR(df, MAJOR_DF, id):

    df1 = df[['open', 'high', 'low', 'close', 'volume']]
    df2 = MAJOR_DF[['open', 'high', 'low', 'close', 'volume']]

    min_length = min(len(df1), len(df2))

    df1 = df1.tail(min_length)
    df1 = df1.reset_index(drop=True)
    df2 = df2.tail(min_length)
    df2 = df2.reset_index(drop=True)

    df3 = df1.div(df2.iloc[-1], axis='columns')

    df3 = df1.reset_index(drop=True)/df2.reset_index(drop=True)

    tpi, regime = tpiAggregate(df3, id)

    return tpi, regime

def getOHLC(id):

    try:
        df = pd.read_csv(f'crypto/ohlc/{id}.csv')

        if df.empty:
            df = coingecko.createDataFrame(id)
            df.to_csv(f'crypto/ohlc/{id}.csv', index=True)
            df = pd.read_csv(f'crypto/ohlc/{id}.csv')
        else:
            last_date = pd.to_datetime(df['date'].iloc[-1])
            today = pd.to_datetime('today').normalize()

            if last_date < today:

                new_data = coingecko.createDataFrame(id, (today - last_date).days + 1)
                new_data = new_data.iloc[1:]

                new_data['date'] = pd.to_datetime(new_data.index, format='%Y-%m-%d')
                new_data.reset_index(drop=True, inplace=True)

                # Merge the data
                df = pd.concat([df, new_data])
                df = df.reset_index()

                df.drop(columns=['index'], inplace=True)

                df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')
                
                df.drop_duplicates(subset=['date'], inplace=True)
                df.set_index('date', inplace=True)
                df.to_csv(f'crypto/ohlc/{id}.csv', index=True)
    except FileNotFoundError:
        df = coingecko.createDataFrame(id)
        df.to_csv(f'crypto/ohlc/{id}.csv', index=True)
        df = pd.read_csv(f'crypto/ohlc/{id}.csv')

    return df

def analyse(coins, major_id = None, MAJOR_DF = None):

    if major_id:
        MAJOR_DF_CLOSE = pd.read_csv(f'crypto/close/{major_id}.csv')
        major_df = getOHLC(major_id)
        MAJOR_DF_CLOSE = MAJOR_DF_CLOSE.tail(len(major_df))
        MAJOR_DF_CLOSE.reset_index(drop=True, inplace=True)
        major_df['volume'] = MAJOR_DF_CLOSE['volume']

    RESULT_DF = pd.DataFrame()

    for index, coin in track(coins.iterrows(), description="Downloading...", total=len(coins)):
        id = coin['id']

        number = f'0{index}' if index < 10 else index
        console.print(f"   .... {number}/{len(coins)} fetching {id}", end='\r')

        df = getOHLC(id)

        dfClose = pd.read_csv(f'crypto/close/{id}.csv')
        dfClose = dfClose.tail(len(df))
        dfClose.reset_index(drop=True, inplace=True)

        df['volume'] = dfClose['volume']

        if df.empty or len(df) < 90 or 'date' not in df.columns:
            print(f"   .... {number}/{len(coins)} {id} is empty")
            continue

        vsUSDTPI, vsUSDRegime  = tpiAggregate(df, id)

        if major_id:
            vsMAJORTPI, vsMAJORRegime = trendMAJOR(df, major_df, id)

        row = pd.DataFrame({
            'id': id,
            'symbol': coin['symbol'],
            'len': coin['len'],
            'marketcap': dfClose['marketcap'].iloc[-1],
            'beta': coin['beta'],
            'alpha': coin['alpha'],
            'volatility': coin['volatility'],
            'sharpe_ratio': coin['sharpe_ratio'],
            'sortino_ratio': coin['sortino_ratio'],
            'omega_ratio': coin['omega_ratio'],
            'vs_USD': vsUSDTPI,
            'vs_USD_regime': vsUSDRegime,
        }, index=[0])

        if major_id:
            row['vs_MAJOR'] = vsMAJORTPI
            row['vs_MAJOR_regime'] = vsMAJORRegime

        row['score'] = coin['score']

        RESULT_DF = pd.concat([RESULT_DF, row], ignore_index=True)

    return RESULT_DF


def matrix(df, title):
    print('Creating matrix...')

    matrix = pd.DataFrame(columns=['id', 'asset'] + list(df['id']))

    for i, num in track(df.iterrows(), description="analysing ratios...", total=len(df)):

        numeratorId = num['id']

        numeratorDf = pd.read_csv(f'crypto/ohlc/{numeratorId}.csv')
        numeratorDfClose = pd.read_csv(f'crypto/close/{numeratorId}.csv')
        numeratorDfClose = numeratorDfClose.tail(len(numeratorDf))
        numeratorDfClose.reset_index(drop=True, inplace=True)
        numeratorDf['volume'] = numeratorDfClose['volume']

        numeratorDf = numeratorDf[['open', 'high', 'low', 'close', 'volume']]

        row = {
            'id': numeratorId,
            'asset': num['symbol']
        }

        for j, dem in df.iterrows():
            
            demoninatorId = dem['id']

            ratioID = f'{numeratorId}/{demoninatorId}'
            console.print(f"   .... {ratioID}", end='\r')
            

            if numeratorId == demoninatorId:
                row[demoninatorId] = '-'
                continue

            denominatorDf = pd.read_csv(f'crypto/ohlc/{demoninatorId}.csv')
            denominatorDfClose = pd.read_csv(f'crypto/close/{demoninatorId}.csv')
            denominatorDfClose = denominatorDfClose.tail(len(denominatorDf))
            denominatorDfClose.reset_index(drop=True, inplace=True)
            denominatorDf['volume'] = denominatorDfClose['volume']

            # denominatorDf = pd.read_csv(f'crypto/{demoninatorId}.csv')
            denominatorDf = denominatorDf[['open', 'high', 'low', 'close', 'volume']]

            min_length = min(len(numeratorDf), len(denominatorDf))
            numeratorDf = numeratorDf.tail(min_length)
            numeratorDf = numeratorDf.reset_index(drop=True)
            denominatorDf = denominatorDf.tail(min_length)
            denominatorDf = denominatorDf.reset_index(drop=True)

            ratioDf = numeratorDf.div(denominatorDf.iloc[-1], axis='columns')
            ratioDf = numeratorDf.reset_index(drop=True)/denominatorDf.reset_index(drop=True)

            rsi_sd_signal = indicators.rsisd(ratioDf)

            row[demoninatorId] = rsi_sd_signal

        matrix = pd.concat([matrix, pd.DataFrame([row])], ignore_index=True)

    matrix['score'] = matrix.apply(lambda row: sum(1 for val in row[2:] if isinstance(val, (int, float)) and val > 0), axis=1)

    matrix = matrix.sort_values(by='score', ascending=False)

    return matrix


def list_df(matrix_df, ANALYSED_DF):

    df = pd.DataFrame()

    for index, row in matrix_df.iterrows():
        id = row['id']
        asset = row['asset']
        score = row['score']

        coin = ANALYSED_DF[ANALYSED_DF['id'] == id].iloc[0]
        marketcap = coin['marketcap']
        vs_USD = coin['vs_USD']
        vs_USD_regime = coin['vs_USD_regime']
        vs_MAJOR = coin['vs_MAJOR']

        contract_address = coingecko.fetchContractInfo(id)
        
        row = pd.DataFrame({
            'id': id,
            'asset': asset,
            'matrix_score': score,
            'marketcap': marketcap,
            'vs_USD': vs_USD,
            'vs_USD_regime': vs_USD_regime,
            'vs_MAJOR': vs_MAJOR,
            'contract_address': "\n".join([f"{platform.upper()}: {address}" for platform, address in contract_address.items()])
        }, index=[0])

        df = pd.concat([df, row], ignore_index=True)

    return df


def createTable(df, title):

    table = Table(title=title, header_style=f"bold {styles.SECONDARY}", expand=True, show_lines=True)

    table.add_column("ID", style=f"bold {styles.PRIMARY}")
    table.add_column("Asset", style=f"bold {styles.PRIMARY}")
    table.add_column("Matrix Score", style=f"bold {styles.PRIMARY}")
    table.add_column("Market Cap", style=f"bold {styles.PRIMARY}")
    table.add_column("vs USD", style=f"bold {styles.PRIMARY}")
    table.add_column("vs USD Regime", style=f"bold {styles.PRIMARY}")
    table.add_column("vs MAJOR", style=f"bold {styles.PRIMARY}")
    table.add_column("Contract Address", style=f"bold {styles.PRIMARY}")

    for i, row in df.iterrows():

        table.add_row(
            row['id'],
            row['asset'],
            str(row['matrix_score']),
            f"{row['marketcap']:,}",
            str(row['vs_USD']),
            row['vs_USD_regime'],
            str(row['vs_MAJOR']),
            row['contract_address']
        )

    return table
