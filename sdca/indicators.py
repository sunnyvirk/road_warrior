# Get Fundamental Indicators data
fundamentalIndicators = [
    # Fundamental Indicators
    # {
    #     'source': 'lookIntoBitCoin',
    #     'url': 'https://www.lookintobitcoin.com/charts/advanced-nvt-signal/',
    #     'dataUrl': 'https://www.lookintobitcoin.com/django_plotly_dash/app/nvts/_dash-update-component',
    #     'payload': '/charts/advanced-nvt-signal/',
    #     'title': 'Bitcoin: Advanced NVT Signal',
    #     'zscoreDataPoint': -1,
    #     'priceDataIndex': 0,
    #     'dataIndex': 1
    # },
    {
        'source': 'checkonchain',
        'webpageUrl': 'https://charts.checkonchain.com/btconchain/lifespan/vddmultiple/vddmultiple_light.html',
        'title': 'Bitcoin Value Days Destroyed Multiple',
        'zscoreDataPoint': -1,
        'priceDataIndex': 1,
        'dataIndex': 6
    },

    {
        'source': 'checkonchain',
        'webpageUrl': 'https://charts.checkonchain.com/btconchain/unrealised/nupl/nupl_light.html',
        'title': 'Bitcoin: Net Unrealized Profit/Loss (NUPL)',
        'zscoreDataPoint': -1,
        'priceDataIndex': 0,
        'dataIndex': [1, 2, 3, 4, 5]
    },
    {
        'source': 'checkonchain',
        'webpageUrl': 'https://charts.checkonchain.com/btconchain/realised/sopr/sopr_light.html',
        'title': 'Bitcoin: SOPR',
        'zscoreDataPoint': -1,
        'priceDataIndex': 4,
        'dataIndex': 6,
    },
    {
        'source': 'checkonchain',
        'webpageUrl': 'https://charts.checkonchain.com/btconchain/realised/lthsopr_indicator/lthsopr_indicator_light.html',
        'title': 'Long term holder LTH MVRV Indicator',
        'zscoreDataPoint': -1,
        'priceDataIndex': 0,
        'dataIndex': 5      
    },
    {
        'source': 'checkonchain',
        'webpageUrl': 'https://charts.checkonchain.com/btconchain/stablecoins/stablecoins_ssr_oscillator/stablecoins_ssr_oscillator_light.html',
        'title': 'Bitcoin: Stablecoin Supply Ratio Oscillator',
        'zscoreDataPoint': -1,
        'priceDataIndex': 2,
        'dataIndex': 7,
    },
    {
        'source': 'checkonchain',
        'webpageUrl': 'https://charts.checkonchain.com/btconchain/unrealised/mvrv_aviv_zscore/mvrv_aviv_zscore_light.html',
        'title': 'Bitcoin: AVIV Ratio',
        'zscoreDataPoint': -1,
        'priceDataIndex': 0,
        'dataIndex': 2,
    },
    {
        'source': 'checkonchain',
        'webpageUrl': 'https://charts.checkonchain.com/btconchain/mining/difficultyregression/difficultyregression_light.html',
        'title': 'Bitcoin: Difficulty Regression Model (Avg cost of production)',
        'zscoreDataPoint': -1,
        'priceDataIndex': 0,
        'dataIndex': 2,
    }
]

# Get Technical Indicators data

technicalIndicators = [
    # Technical Indicators
    # {
    #     'source': 'lookIntoBitCoin',
    #     'webpageUrl': 'https://www.lookintobitcoin.com/charts/pi-cycle-top-bottom-indicator/',
    #     'dataUrl': 'https://www.lookintobitcoin.com/django_plotly_dash/app/pi_cycle_top_bottom_indicator/_dash-update-component',
    #     'payload': '/charts/pi-cycle-top-bottom-indicator/',            
    #     'title': 'Bitcoin: Pi Cycle Top/Bottom Indicator',
    #     'zscoreDataPoint': -1,
    #     'priceDataIndex': 4,
    #     'dataIndex': 7
    # },
    {
        'source': 'checkonchain',
        'webpageUrl': 'https://charts.checkonchain.com/btconchain/pricing/pricing_mayermultiple_zscore/pricing_mayermultiple_zscore_light.html',
        'title': 'Bitcoin: Mayer Multiple Z-Score',
        'zscoreDataPoint': -1,
        'priceDataIndex': 6,
        'dataIndex': 4,
    },
    {
        'source': 'coingecko',
        'webpageUrl': 'https://www.coingecko.com/en',
        'type': 'sharpe_ratio',
        'title': 'Bitcoin: Sharpe Ratio',
        'zscoreDataPoint': -1,
    },
    {
        'source': 'coingecko',
        'webpageUrl': 'https://www.coingecko.com/en',
        'type': 'sortino_ratio',
        'title': 'Bitcoin: Sortino Ratio',
        'zscoreDataPoint': -1,
    },
    {
        'source': 'coingecko',
        'webpageUrl': 'https://www.coingecko.com/en',
        'type': 'omega_ratio',
        'title': 'Bitcoin: Omega Ratio',
        'zscoreDataPoint': -1,
    }
]


# Get Sentiment Indicators data
setimentIndicators = [
    # Sentiment Indicators
    {
        'source': 'alternative',
        'webpageUrl': 'https://alternative.me/crypto/fear-and-greed-index/',
        'dataUrl': 'https://api.alternative.me/fng/?limit=0',
        'title': 'Bitcoin: Fear & Greed Index',
        'zscoreDataPoint': -1,
        'priceDataIndex': 0,
        'dataIndex': 1
    },
    # {
    #     'source': 'lookIntoBitCoin',
    #     'webpageUrl': 'https://www.lookintobitcoin.com/charts/active-address-sentiment-indicator/',
    #     'dataUrl': 'https://www.lookintobitcoin.com/django_plotly_dash/app/bitcoin_sentiment/_dash-update-component',
    #     'payload': '/charts/active-address-sentiment-indicator/',
    #     'title': 'Bitcoin: Active Address Sentiment Indicator',
    #     'zscoreDataPoint': -1,
    #     'priceDataIndex': 0,
    #     'dataIndex': 2
    # },
    {
        'source': 'augmento',
        'webpageUrl': 'https://www.augmento.ai/bitcoin-sentiment/',
        'dataUrl': 'https://bitcoin-sentiment.augmento.ai/graph/_dash-layout',
        'title': 'Bitcoin sentiment - Bull & Bear Index',
        'zscoreDataPoint': -1,
        'priceDataIndex': 0,
        'dataIndex': 1
    }
]