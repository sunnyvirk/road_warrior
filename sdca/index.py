import plot
import utils
import fetch
import pandas as pd
import numpy as np
from rich import print
from rich.text import Text
from rich.table import Table

import scipy.stats as stats

from indicators import fundamentalIndicators, technicalIndicators, setimentIndicators

def fetchIndicatorZScore(indicator, feature, type):
    df = fetch.indicatorData(indicator)

    df = utils.normaliseDataFrame(df)
    df = df.dropna()
    
    df = df[df['date'] >= '2017']
    
    std_dev, mean, mode_value, median = utils.getStandardDeviationAndMeanValues(df[feature])
    last_value, z_score, skewness, current_data_point, date = utils.calculateZScore(df, indicator['zscoreDataPoint'], mean, std_dev)
    
    # plot.visual(f'{indicator['title']} - {type}', df[feature], df['logPrice'], df['date'])
    # plot.histogram(f'{indicator['title']} - {type}', df, feature, std_dev, mean, skewness, current_data_point, last_value, z_score)
    
    return last_value, z_score, skewness, current_data_point, date

PRIMARY = "#00BCD4"
SECONDARY = "#FF4081"

def report(title, df):
    table = Table(title=f'SDCA - {title}')
    table.add_column("Indicator", style=PRIMARY, justify="right", width=120)
    table.add_column("Data value", style=PRIMARY, justify="right")
    table.add_column("Skewness", style=PRIMARY, justify="right")
    table.add_column("Z Score", style=PRIMARY, justify="right")
    table.add_column("Date", style=SECONDARY, justify="right") 

    for _, row in df.iterrows():

        zscore = Text(str(row['Z Score']), style=PRIMARY)
        if row['Z Score'] < 0:
            zscore = Text(str(row['Z Score']), style=SECONDARY)

        date = Text(str(row['Date']), style=PRIMARY)
        if row['Date'] != pd.to_datetime('today').strftime('%Y-%m-%d'):
            date = Text(str(row['Date']), style=SECONDARY)


        row_cells = [

            zscore if column == 'Z Score' else

            date if column == 'Date' else

            str(row[column])
            for column in df.columns
        ]

        table.add_row(*row_cells)

    return table

def main():

    global fundamentalReport
    global technicalReport
    global sentimentReport

    columns = ['Indicator', 'Data value', 'Skewness', 'Z Score', 'Date']

    fundamentalReport = pd.DataFrame(columns=columns)
    technicalReport = pd.DataFrame(columns=columns)
    sentimentReport = pd.DataFrame(columns=columns)
    
    def runIndicators(type, indicators):        
        for indicator in indicators:
            global fundamentalReport
            global technicalReport
            global sentimentReport
            
            last_value, z_score, skewness, current_data_point, date = fetchIndicatorZScore(indicator, 'valueNormal', 'Normalised')
            
            date = pd.to_datetime(date).strftime('%Y-%m-%d')
            new_row = pd.DataFrame({'Indicator': f'{indicator['title']}\n {indicator['webpageUrl']}\n', 'Data value': current_data_point, 'Skewness': skewness, 'Z Score': z_score, 'Date': date }, index=[0])

            new_row = new_row.dropna(axis=1, how='all')

            if type == 'Fundamental':
                fundamentalReport = fundamentalReport.dropna(axis=1, how='all')
                fundamentalReport = pd.concat([fundamentalReport, new_row], ignore_index=True)
            elif type == 'Technical':
                technicalReport = technicalReport.dropna(axis=1, how='all')
                technicalReport = pd.concat([technicalReport, new_row], ignore_index=True)
            elif type == 'Sentiment':
                sentimentReport = sentimentReport.dropna(axis=1, how='all')
                sentimentReport = pd.concat([sentimentReport, new_row], ignore_index=True)

    runIndicators('Fundamental', fundamentalIndicators)
    runIndicators('Technical', technicalIndicators)
    runIndicators('Sentiment', setimentIndicators)

    fundamental_title = 'Fundamental Report'
    fundamental_table = report(fundamental_title, fundamentalReport)
    print(fundamental_table)

    technical_title = 'Technical Report'
    technical_table = report(technical_title, technicalReport)
    print(technical_table)

    sentiment_title = 'Sentiment Report'
    sentiment_table = report(sentiment_title, sentimentReport)
    print(sentiment_table)

    # Aggregate Z Score values for each report
    fundamental_z_scores = fundamentalReport['Z Score'].dropna().values
    technical_z_scores = technicalReport['Z Score'].dropna().values
    sentiment_z_scores = sentimentReport['Z Score'].dropna().values
    all_z_scores = np.concatenate((fundamental_z_scores, technical_z_scores, sentiment_z_scores))

    average_z_score = np.mean(all_z_scores)

    average_z_score_title = 'Average Z Score'
    average_z_score_table = report(average_z_score_title, pd.DataFrame({
        'Indicator': 'Average Z Score',
        'Data value': '',
        'Skewness': '',
        'Z Score': round(average_z_score, 2) * -1,
        'Date': pd.to_datetime('today').strftime('%Y-%m-%d')
    }, index=[0]))
    print(average_z_score_table)

main()