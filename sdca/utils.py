import pandas as pd
import numpy as np
from scipy import stats
import statistics

from sklearn.preprocessing import PowerTransformer

def calculateZScore(df, zscoreDataPoint, mean, std_dev):
    last_value = df['valueNormal'].iloc[zscoreDataPoint]
    date = df['date'].iloc[zscoreDataPoint]
    z_score = round((mean - last_value) / std_dev, 1)
    z_score = round(z_score * 10) / 10
    skewness = round(stats.skew(df['valueNormal']), 1)
    current_data_point = round(df['value'].iloc[zscoreDataPoint], 2)
    return last_value, z_score, skewness, current_data_point, date

def getStandardDeviationAndMeanValues(value):
    std_dev = np.std(value)
    mean = np.mean(value)
    
    mode_value = statistics.mode(value)
    
    median = np.median(value)
    return std_dev, mean, mode_value, median

def calculateStandardDeviations(mean, std_dev):
    sd_plus_1 = mean - std_dev
    sd_plus_2 = mean - (std_dev * 2)
    sd_plus_3 = mean - (std_dev * 3)
    sd_minus_1 = mean + std_dev
    sd_minus_2 = mean + (std_dev * 2)
    sd_minus_3 = mean + (std_dev * 3)
    
    return sd_plus_1, sd_plus_2, sd_plus_3, sd_minus_1, sd_minus_2, sd_minus_3

def removeTrend(values):
    X = values
    diff = list()
    for i in range(1, len(X)):
        value = X[i] - X[i - 1]
        diff.append(value)
        
    return diff

def normaliseDataFrame(df):
    
    yeojohnTr = PowerTransformer(standardize=True)

    # Normalise the data
    df['valueNormal'] = pd.DataFrame(yeojohnTr.fit_transform(df['value'].values.reshape(-1,1)))
    
    return df
    
    