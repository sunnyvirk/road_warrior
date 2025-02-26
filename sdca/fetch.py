import requests
import datetime
import json
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

import re
import pandas as pd
from bs4 import BeautifulSoup
import ast
import random
import numpy as np

userAgentStrings = [
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.2227.0 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.3497.92 Safari/537.36',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
]

def on_chain_dataframe(date, value, price):

    df = pd.DataFrame(date, columns=['date'])
    df['value'] = pd.Series(value)
    df['price'] = pd.Series(price)

    df['value'] = df['value'].astype(float)
    df['price'] = df['price'].astype(float)
  
    return df

def indicatorData(indicator):
    global prices
    global timeSeriesData
    global dates
    global df

    # if indicator['source'] == 'lookIntoBitCoin':
    #     payload = {
    #         "output":"chart.figure",
    #         "outputs":{
    #             "id":"chart",
    #             "property":"figure"
    #         },
    #         "inputs":[
    #             {
    #                 "id":"url",
    #                 "property":"pathname",
    #                 "value": indicator['payload']
    #             }
    #         ],
    #         "changedPropIds":[
    #             "url.pathname"
    #         ]
    #     }

    #     response = requests.post(indicator['dataUrl'], json=payload)
        
    #     response = json.loads(response.text)
        
    #     prices = response['response']['chart']['figure']['data'][indicator['priceDataIndex']]['y']
    #     timeSeriesData = response['response']['chart']['figure']['data'][indicator['dataIndex']]['y']
    #     dataDates = response['response']['chart']['figure']['data'][indicator['dataIndex']]['x'][:len(timeSeriesData)]

    #     df = on_chain_dataframe(dataDates, timeSeriesData, prices)
        
    # elif indicator['source'] == 'cryptoQuant':

    #     # Create a timestamp variable using today's date
    #     timestamp = int(datetime.datetime.now().timestamp() * 1000)
    #     url = f'{indicator['dataUrl']}{timestamp}&limit=70000'

    #     priceUrl = f'https://live-api.cryptoquant.com/api/v2/assets/61712eb35a176168a02409e8/price?window=DAY&from=1085353200000&to={timestamp}&limit=70000'
        
            
    #     with sync_playwright() as p:
    #         browser = p.chromium.launch(headless=False)
    #         context = browser.new_context()
    #         page = context.new_page()
            
    #         page.goto(url)
            
    #         page_content = page.content()
            
    #         pattern = r'<pre>(.*?)</pre>'
    #         match = re.search(pattern, page_content)
    #         if match:
    #             response = match.group(1)
    #         else:
    #             response = None
            
    #         response = json.loads(response)
    #         response = response['result']['data']
    #         timeSeriesData = pd.DataFrame(response, columns=['date', 'value'])
    #         timeSeriesData['date'] = pd.to_datetime(timeSeriesData['date'], unit='ms')
            
    #         page.goto(priceUrl)
    #         page_content = page.content()
    #         match = re.search(pattern, page_content)
    #         if match:
    #             response = match.group(1)
    #         else:
    #             response = None
            
    #         response = json.loads(response)

    #         response = response['data']
    #         prices = pd.DataFrame(response, columns=['date', 'price'])
    #         prices['date'] = pd.to_datetime(prices['date'], unit='ms')
            
    #         df = pd.merge(prices, timeSeriesData, on='date')

    if indicator['source'] == 'coingecko':

        headers = {
            "accept": "application/json",
            "x-cg-pro-api-key": "CG-ttQ98WX4hmX15dHUVz7hgxNo"
        }

        url = "https://pro-api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=max&interval=daily"

        response = requests.get(url, headers=headers)
        data = response.json()

        df = pd.DataFrame(data['prices'][:-1], columns=['timestamp', 'close'])
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms').dt.strftime('%Y-%m-%d')
        df.drop(columns=['timestamp'], inplace=True)

        df['returns'] = df['close'].pct_change() * 100
        if indicator['type'] == 'sharpe_ratio':
            df['ratio'] = df['returns'].rolling(window=365).apply(lambda x: x.mean() / x.std() * np.sqrt(365))
        elif indicator['type'] == 'sortino_ratio':
            df['ratio'] = df['returns'].rolling(window=365).apply(lambda x: x.mean() / x[x < 0].std() * np.sqrt(365))
        elif indicator['type'] == 'omega_ratio':
            df['ratio'] = df['returns'].rolling(window=365).apply(lambda x: x[x > 0].mean() / -x[x < 0].mean())

        prices = df['close'].values
        values = df['ratio'].values
        dates = df['date'].values


        df = on_chain_dataframe(dates, values, prices)
            
    elif indicator['source'] == 'alternative':
        
        response = requests.get(indicator['dataUrl'])
        response = json.loads(response.text)['data']
        
        values = [int(item['value']) for item in response][::-1]
        
        prices = [0] * len(values)
        
        dates = [datetime.datetime.fromtimestamp(int(item['timestamp'])).strftime('%Y-%m-%d') for item in response][::-1]

        df = on_chain_dataframe(dates, values, prices)
        
    elif indicator['source'] == 'augmento':
        
        response1 = requests.get(indicator['dataUrl'])
        response = json.loads(response1.text)['props']['children'][0]['props']['children'][0]['props']['figure']['data'][4]['text']

        numbers = []
        for string in response:
            pattern = r'\d+\.\d+'  # Regular expression pattern to match the number
            matches = re.findall(pattern, string)
            numbers.extend([float(num) for num in matches])
        
        dataDates = json.loads(response1.text)['props']['children'][0]['props']['children'][0]['props']['figure']['data'][4]['x']
        
        prices = [0] * len(numbers)        

        df = on_chain_dataframe(dataDates, timeSeriesData, prices)        
        
    elif indicator['source'] == 'checkonchain':

        response = requests.get(indicator['webpageUrl'])
        html_content = response.text
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find the script tag
        script_tag = soup.find_all('script')
        script_tag = script_tag[2].text
        trimmed = script_tag.replace('\n', '').replace(' ', '')

        pattern = r'Plotly\.newPlot\("([^"]+)",\s*(\[.*?\])\s*,\s*({.*?})\)'

        match = re.search(pattern, trimmed)

        array_content = match.group(2)
        array_content = json.loads(array_content)

        # print('fetching: ', indicator['title'])
        # for item in array_content:
        #     print('prices: ', item['name'])
        
        prices = array_content[indicator['priceDataIndex']]['y']
        
        if isinstance(indicator['dataIndex'], list):
            data_frames = []
            for index in indicator['dataIndex']:
                time_series = array_content[index]['y']

                time_series = pd.Series(time_series)
                if data_frames:
                    data_frames[0] = data_frames[0].combine_first(time_series)
                else:
                    data_frames.append(time_series)

            timeSeriesData = pd.concat(data_frames, ignore_index=True)
            dataDates = array_content[1]['x'][:len(timeSeriesData)]
        else:
            timeSeriesData = array_content[indicator['dataIndex']]['y']
            dataDates = array_content[indicator['dataIndex']]['x'][:len(timeSeriesData)]
        
        prices = prices[:len(timeSeriesData)]

        df = on_chain_dataframe(dataDates, timeSeriesData, prices)
    
    elif indicator['source'] == 'bitbo':            
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)

            user_agent = random.choice(userAgentStrings)
            
            context = browser.new_context(user_agent=user_agent)
            page = context.new_page()
            
            stealth_sync(page)
            
            page.wait_for_timeout(3000)
            
            page.goto(indicator['webpageUrl'])
            page.wait_for_timeout(3000)

            page_content = page.content()
            soup = BeautifulSoup(page_content, 'html.parser')
            
            script_tags = soup.find_all('script')
            js_code = script_tags[5].text
            
            
            trace1_match = re.search(r'var trace1 = ({.*?});', js_code, re.DOTALL)
            trace1_str = trace1_match.group(1) if trace1_match else ''
            prices = re.search(r'y: (\[.*?\])', trace1_str, re.DOTALL).group(1)
            prices = ast.literal_eval(prices)
            
            # Replace empty strings with a default value (e.g., 0)
            prices = [val for val in prices if val != '']
            
            trace2_match = re.search(r'var trace2 = ({.*?});', js_code, re.DOTALL)
            trace2_str = trace2_match.group(1) if trace2_match else ''
            timeSeriesData = re.search(r'y: (\[.*?\])', trace2_str, re.DOTALL).group(1)
            timeSeriesData = ast.literal_eval(timeSeriesData)
            
            today = datetime.date.today().strftime('%Y-%m-%d')
            dates = pd.date_range(end=today, periods=len(timeSeriesData)).strftime('%Y-%m-%d').tolist()
            
            df = on_chain_dataframe(dataDates, timeSeriesData, prices)

    return df
