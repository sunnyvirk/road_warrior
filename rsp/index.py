import pandas as pd

from rich import print
from rich.prompt import IntPrompt
from rich.panel import Panel
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.layout import Layout
from rich import box

console = Console()

import coingecko 
import data
import styles

import requests
import time

def selectMajor():

    major_coins = [
        {
            'id': 'bitcoin',
            'symbol': 'btc',
        }, 
        {
            'id': 'ethereum',
            'symbol': 'eth'
        },
        {
            'id': 'solana',
            'symbol': 'sol'
        },
    ]

    console.print('\n')
    console.print("MAJOR:", style=f"bold {styles.SECONDARY}")
    for idx, coin in enumerate(major_coins, start=1):
        print(f"{idx}. {coin['symbol'].upper()} - ({coin['id']})")

    choice = IntPrompt.ask("Enter a number to select the highest peforming major: ", default=1)

    major_coin = major_coins[choice - 1]

    return major_coin['id']

def selectCat():

    catergorys = [
        {
            'id': False,
            'name': 'RSP',
        },
        {
            'id': 'meme-token',
            'name': 'Meme Tokens',
        },
        {
            'id': 'artificial-intelligence',
            'name': 'Artificial Intelligence (AI)',
        }
    ]

    console.log('\n')
    console.log("SYSTEM", style=f"bold {styles.SECONDARY}")
    for idx, cat in enumerate(catergorys, start=1):
        print(f"{idx}. {cat['name']}")

    choice = IntPrompt.ask("Enter a number to select a category: ", default=1)

    cat = catergorys[choice - 1]

    return cat['id']

# Function to create a layout for a single asset
def create_asset_layout(asset_data, matric_score, contract):
    layout = Layout()

    layout.size = 15

    layout.split_column(
        Layout(name="upper"),
        Layout(name="lower")
    )

    layout["upper"].split_column(
        Layout(name="asset"),
        Layout(name="ratio"),
        Layout(name="trends"),
    )

    layout["upper"].size = 6
    layout["lower"].size = 9


    layout["asset"].split_row(
        Layout(name="id"),
        Layout(name="asset_name"),
        Layout(name="length"),
        Layout(name="marketcap"),
        Layout(name="score"),
        Layout(name="matrix")
    )

    layout["ratio"].split_row(
        Layout(name="beta"),
        Layout(name="alpha"),
        Layout(name="volatility"),
        Layout(name="sharpe"),
        Layout(name="sortino"),
        Layout(name="omega"),
    )

    layout["trends"].split_row(
    Layout(name="usd_trend"),
    Layout(name="usd_regime"),
    Layout(name="major_trend"),
    Layout(name="major_regime"),
    Layout(name="empty_3"),
    Layout(name="empty_4"),
    )

    layout["lower"].split_row(
    Layout(name="rugcheck"),
    Layout(name="contracts"),
    )


    # Populate the layout with data
    # Asset Section
    layout["asset"]["id"].update(Text(f"ID: {asset_data['id']}", style="cyan"))
    layout["asset"]["asset_name"].update(Text(f"Symbol: {asset_data['symbol']}", style="cyan"))
    layout["asset"]["length"].update(Text(f"Length: {asset_data['len']}", style="cyan"))
    layout["asset"]["marketcap"].update(Text(f"Market Cap: ${asset_data['marketcap']:.2f}", style="cyan"))
    layout["asset"]["score"].update(Text(f"Score: {asset_data['score']:.0f}", style="cyan"))
    layout["asset"]["matrix"].update(Text(f"Matrix: {matric_score:.0f}", style="cyan"))

    # # Ratio Section
    layout["ratio"]["beta"].update(Text(f"Beta: {asset_data['beta']:.2f}", style="white"))
    layout["ratio"]["alpha"].update(Text(f"Alpha: {asset_data['alpha']:.2f}", style="white"))
    layout["ratio"]["volatility"].update(Text(f"Volatility: {asset_data['volatility']:.2f}", style="white"))
    layout["ratio"]["sharpe"].update(Text(f"Sharpe: {asset_data['sharpe_ratio']:.2f}", style="white"))
    layout["ratio"]["sortino"].update(Text(f"Sortino: {asset_data['sortino_ratio']:.2f}", style="white"))
    layout["ratio"]["omega"].update(Text(f"Omega: {asset_data['omega_ratio']:.2f}", style="white"))

    # Trends Section
    layout["trends"]["usd_trend"].update(Text(f"vs USD: {asset_data['vs_USD']:.1f}", style="green"))
    layout["trends"]["usd_regime"].update(Text(f"USD Regime: {asset_data['vs_USD_regime']}", style="green"))
    layout["trends"]["major_trend"].update(Text(f"vs MAJOR: {asset_data['vs_MAJOR']:.1f}", style="green"))
    layout["trends"]["major_regime"].update(Text(f"MAJOR Regime: {asset_data['vs_MAJOR_regime']}", style="green"))
    layout["trends"]["empty_3"].update(Text(f"", style="green"))
    layout["trends"]["empty_4"].update(Text(f"", style="green"))

    # Info Section - Rug Check

    rug_check_score = ""

    coin_data = coingecko.fetch_coin_data(asset_data['id'])

    if 'Solana Ecosystem' in coin_data['categories']:

        tokenMint = coin_data['platforms']['solana']

        time.sleep(5)

        rugResponse = requests.get("https://api.rugcheck.xyz/v1/tokens/" + tokenMint + "/report", {
            'timeout': 10000,
        })

        if rugResponse.status_code != 200:
            print(f"Failed to fetch rug check data for {id}. Status code: {rugResponse.status_code}")

        data = rugResponse.json()

        tokenReport = data

        token = tokenReport['token'] if tokenReport.get('token') else None

        if token is not None:
            
            mintAuthority = token['mintAuthority']
            freezeAuthority = token['freezeAuthority']
            isInitialized = token['isInitialized']
            # supply = token['supply']
            # decimals = token['decimals']
            tokenMeta = tokenReport['tokenMeta']
            # tokenName = tokenMeta['name']
            # tokenSymbol = tokenMeta['symbol']
            tokenMutable = tokenMeta['mutable']
            topHolders = tokenReport['topHolders']
            marketsLength = len(tokenReport['markets']) if tokenReport['markets'] else 0
            totalLPProviders = tokenReport['totalLPProviders']
            totalMarketLiquidity = tokenReport['totalMarketLiquidity']
            isRugged = tokenReport['rugged']
            rugScore = tokenReport['score']
            rugRisks = tokenReport['risks'] if tokenReport['risks'] else [
                {
                    'name': "Good",
                    'value': "",
                    'description': "",
                    'score': 0,
                    'level': "good",
                },
            ]

            # Update topholders if liquidity pools are excluded
            markets = tokenReport['markets']
            if markets:
                # Safely extract liquidity addresses from markets
                liquidity_addresses = [
                    addr
                    for market in (markets or [])
                    for addr in (market['liquidityA'], market['liquidityB'])
                    if addr
                ]

                # Filter out topHolders that match any of the liquidity addresses
                topHolders = [
                    holder
                    for holder in topHolders
                    if holder['address'] not in liquidity_addresses
                ]


            legacy_not_allowed = [
                "Low Liquidity",
                "Freeze Authority still enabled",
                "Single holder ownership",
                "High holder concentration",
                "Freeze Authority still enabled",
                "Large Amount of LP Unlocked",
                "Copycat token",
                "Low amount of LP Providers",
            ],

            # Set conditions
            conditions = [
                {
                    'check': mintAuthority is not None,
                    'message': "🚫 Mint authority should be null"
                },
                {
                    'check': not isInitialized,
                    'message': "🚫 Token is not initialized"
                },
                {
                    'check': freezeAuthority is not None,
                    'message': "🚫 Freeze authority should be null"
                },
                {
                    'check': tokenMutable is not False,
                    'message': "🚫 Mutable should be false"
                },
                {
                    'check': any(holder['insider'] for holder in topHolders),
                    'message': "🚫 Insider accounts should not be part of the top holders"
                },
                {
                    'check': any(holder['pct'] > 30 for holder in topHolders),
                    'message': "🚫 An individual top holder cannot hold more than the allowed percentage of the total supply"
                },
                {
                    'check': totalLPProviders < 0,
                    'message': "🚫 Not enough LP Providers."
                },
                {
                    'check': marketsLength < 0,
                    'message': "🚫 Not enough Markets."
                },
                {
                    'check': totalMarketLiquidity < 10000,
                    'message': "🚫 Not enough Market Liquidity."
                },
                {
                    'check': isRugged,
                    'message': "🚫 Token is rugged"
                },
                # {
                #     'check': tokenSymbol in rug_check_config.block_symbols,
                #     'message': "🚫 Symbol is blocked"
                # },
                # {
                #     'check': tokenName in rug_check_config.block_names,
                #     'message': "🚫 Name is blocked"
                # },
                {
                    'check': (rugScore > 0) and (0 != 0),
                    'message': f"🚫 Rug score too high. {rugScore}"
                },
                {
                    'check': any(risk['name'] in legacy_not_allowed for risk in rugRisks),
                    'message': "🚫 Token has legacy risks that are not allowed."
                },
            ]
        else:
            conditions = [
                {
                    'check': True,
                    'message': "🚫 Token is not registered on rugcheck.xyz"
                }
            ]

        valid = True
    
        # Validate conditions
        for condition in conditions:
            if condition['check']:
                rug_check_score += f"{condition['message']}\n"
                valid = False

        if valid == True:
            rug_check_score += "✅ Solana Rug Check Passed"
        else:
            rug_check_score += "❌ Solana Rug Check Failed"


    layout["lower"]["rugcheck"].update(Text(rug_check_score, style="yellow"))

    contract_text = "\n".join([f"{platform.upper()}: {address}" for platform, address in contract.items()]) + "\n"

    layout["lower"]["contracts"].update(Text(f"Contracts:\n{contract_text}", style="yellow"))

    return layout

def scoring(df, major_id, MAJOR_DF, title):

    BETA_THRESHOLD = 1.3
    MARKET_CAP_THRESHOLD = df['marketcap'].median()
    ALPHA_THRESHOLD = df['alpha'].median()
    SHARPE_THRESHOLD = 1.98
    SORTINO_THRESHOLD = 2.89
    OMEGA_THRESHOLD = 1.30

    df['score'] = (
        (df['marketcap'] < MARKET_CAP_THRESHOLD).astype(int) +
        (df['beta'] > BETA_THRESHOLD).astype(int) +
        (df['alpha'] > ALPHA_THRESHOLD).astype(int) +
        (df['sharpe_ratio'] > SHARPE_THRESHOLD) +
        (df['sortino_ratio'] > SORTINO_THRESHOLD) +
        (df['omega_ratio'] > OMEGA_THRESHOLD)
    )

    df = data.analyse(df, major_id, MAJOR_DF)

    VS_USD_THRESHOLD = 0
    VS_USD_REGIME_THRESHOLD = 'up'
    VS_MAJOR_THRESHOLD = 0
    VS_MAJOR_REGIME_THRESHOLD = 'up'

    if 'score' not in df.columns:
        print('no score')
        print(df, title)

    df['score'] = (
        (df['score']) +
        (df['vs_USD'] > VS_USD_THRESHOLD).astype(int) +
        (df['vs_USD_regime'] == VS_USD_REGIME_THRESHOLD).astype(int) +
        (df['vs_MAJOR'] > VS_MAJOR_THRESHOLD).astype(int) +
        (df['vs_MAJOR_regime'] == VS_MAJOR_REGIME_THRESHOLD).astype(int)
    )

    df = df[df['vs_USD_regime'] != 'down']
    df = df[df['vs_USD_regime'] != 'down s']
    df = df[df['vs_MAJOR_regime'] != 'down']
    df = df[df['vs_MAJOR_regime'] != 'down s']

    df = df.sort_values(by='score', ascending=False)

    if len(df) > 10:
        score_median = df['score'].median()
        df = df[df['score'] >= score_median]

    if len(df) > 1:
        matrix_table = data.matrix(df, f'{title} Matrix')

    contract_df = matrix_table if len(df) > 1 else df

    count = 0

    # List to store all panels
    panels = []

    for _, row in contract_df.iterrows():

    #     cutoff = 10 if title != 'Meme Caps' else 20

    #     # if count == cutoff:
    #     #     break

        matrix_id = row['id']

        contract = coingecko.fetchContractInfo(matrix_id)

        if any(platform in contract for platform in ['solana', 'ethereum', 'base', 'arbitrum-one']):
            count += 1

        matching_row = df[df['id'] == matrix_id].iloc[0]

        asset_layout = create_asset_layout(matching_row, row['score'], contract)

        # Create a panel for the layout
        panel = Panel(
            asset_layout,
            title=f"[bold magenta]Asset: {matching_row['id']}[/bold magenta]",
            border_style="blue",
            box=box.ROUNDED,
            padding=(0, 0),
            height=15
        )

        panels.append(panel)

    return panels

def main():
    pd.options.mode.copy_on_write = True
    pd.set_option('future.no_silent_downcasting', True)

    console.print('\n')
    print(Panel.fit(f"💉 [bold {styles.PRIMARY}]RSP Tournament 💉", padding=(1, 2)))

    cat = selectCat()
    
    COIN_DF = coingecko.fetchCoinMetaData(cat)

    major_id = selectMajor()
    console.print(f'Fetching [bold {styles.SECONDARY}]{major_id}[/bold {styles.SECONDARY}] historical chart data...')
    MAJOR_DF = coingecko.createCloseOnlyDataFrame(major_id)
    MAJOR_DF.to_csv(f'crypto/close/{major_id}.csv', index=True)

    RSP_DF = data.seed(COIN_DF, major_id, MAJOR_DF, cat)

    if len(RSP_DF) > 0:
        CONTRACTS_RSP_DF = scoring(RSP_DF, major_id, MAJOR_DF, 'RSP')
        # Print all panels in one go
        for panel in CONTRACTS_RSP_DF:
            console.print(panel)

if __name__ == "__main__":
    main()