import requests
import pandas as pd

from rich.prompt import Prompt, IntPrompt, FloatPrompt
from rich.progress import track
from rich.console import Console

console = Console()

import styles

headers = {
    "accept": "application/json",
    "x-cg-pro-api-key": "CG-ttQ98WX4hmX15dHUVz7hgxNo"
}

def defaultSettings(cat):

    if cat == 'meme-token':
        return 500
    elif cat == 'artificial-intelligence':
        return 500
    
    return 300

def fetchCoinMetaData(cat):

    default = defaultSettings(cat)

    console.print('\n')
    console.print('COINS', style=f"bold {styles.SECONDARY}")
    length = IntPrompt.ask("How many coins do you want to fetch?", default=default)

    url = "https://pro-api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc"

    if cat:
        url += f"&category={cat}"

    url += "&page="

    coins = pd.DataFrame(columns=['id', 'symbol', 'market_cap_rank'])

    for i in track(range(1, length // 100 + 1), description=f"Fetching metadata for [bold {styles.SECONDARY}]{length}[/bold {styles.SECONDARY}] coins from coingecko..."):

        url_with_page = url + str(i)
        response = requests.get(url_with_page, headers=headers)

        data = response.json()

        for symbol in data:
            new_row = pd.DataFrame({'id': symbol['id'], 'symbol': symbol['symbol'], 'market_cap_rank': symbol['market_cap_rank'] }, index=[0])
            coins = pd.concat([coins, new_row], ignore_index=True)

    coins = coins.drop_duplicates(subset=['id', 'symbol', 'market_cap_rank'])
    coins = coins[~coins['id'].str.contains('opacity')]

    return coins

def ohlc(coin_id, days):

    url = f"https://pro-api.coingecko.com/api/v3/coins/{coin_id}/ohlc?vs_currency=usd&days={days}&interval=daily"

    response = requests.get(url, headers=headers)
    data = response.json()

    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close'])

    return df

def marketData(coin_id, days):

    url = f"https://pro-api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={days}&interval=daily"

    response = requests.get(url, headers=headers)
    data = response.json()

    df_marketcap = pd.DataFrame(data['market_caps'], columns=['timestamp', 'marketcap'])
    df_volume = pd.DataFrame(data['total_volumes'], columns=['timestamp', 'volume'])
    df_close = pd.DataFrame(data['prices'], columns=['timestamp', 'close'])

    df = pd.merge(df_marketcap, df_volume, on='timestamp')
    df = pd.merge(df, df_close, on='timestamp')

    return df

def createCloseOnlyDataFrame(coin_id, days = 600):

    df = marketData(coin_id, days)

    # df = df.iloc[:-1]
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')

    df = df.drop('timestamp', axis=1)
    df.set_index('date', inplace=True)
    df['return'] = df['close'].pct_change() * 100

    df = df[df.index.time == pd.Timestamp('00:00:00').time()]

    return df

def createDataFrame(coin_id, days = 180):

    valid_days = [1, 7, 14, 30, 60, 90, 180]
    days = str(min([d for d in valid_days if d >= days], default='max'))

    df = ohlc(coin_id, 180)

    # df = df.iloc[:-1]
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')

    df = df.drop('timestamp', axis=1)
    df.set_index('date', inplace=True)

    return df


def fetch_coin_data(id):
    
    url = f"https://pro-api.coingecko.com/api/v3/coins/{id}"

    response = requests.get(url, headers=headers)

    data = response.json()

    return data

def fetchContractInfo(id):

    data = fetch_coin_data(id)

    return data['platforms']
