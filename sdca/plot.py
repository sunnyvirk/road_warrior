import matplotlib.pyplot as plt
from matplotlib.dates import YearLocator
import numpy as np
import utils
import time
import scipy.stats as stats

def visual(title, value, price, date):    
    # Create a Visualisation of the df    
    fig, ax1 = plt.subplots()
    
    ax1.set_title(f'{title} Visualisation')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Value', color="black")
    ax1.plot(date, value, color="lightBlue")
    ax1.tick_params(axis='y', labelcolor="black")
    ax1.xaxis.set_major_locator(YearLocator(base=1))
    
    ax2 = ax1.twinx()
    ax2.set_ylabel('Price (Log)', color="black")
    ax2.plot(date, price, color="black")
    ax2.tick_params(axis='y', labelcolor="black")
    ax2.xaxis.set_major_locator(YearLocator(base=2))
    
    fig.tight_layout()  # otherwise the right y-label is slightly clipped

    mng = plt.get_current_fig_manager()    
    mng.set_window_title(title)
    mng.resize(*mng.window.maxsize())

    plt.show()
    
def histogram(title, df, feature, std_dev, mean, skewness, current_data_point, last_value, z_score):
    
    sd_plus_1, sd_plus_2, sd_plus_3, sd_minus_1, sd_minus_2, sd_minus_3 = utils.calculateStandardDeviations(mean, std_dev)

    # Create a histogram using the data
    plt.title(f'${title} Histogram')
    plt.hist(df[feature], bins=30, color='skyblue', edgecolor='black', density=True)
    plt.ylabel('Frequency')
    
    # Define the positions and labels for your custom x-axis
    x_positions = [sd_plus_3, sd_plus_2, sd_plus_1, mean, sd_minus_1, sd_minus_2, sd_minus_3]
    x_labels = ['3', '2', '1', '0', '-1', '-2', '-3']
    plt.xticks(x_positions, x_labels)
    
    # Generate values for the normal distribution
    x = np.linspace(sd_plus_3, sd_minus_3, 100)
    y = (1 / (std_dev * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mean) / std_dev) ** 2)

    plt.plot(x, y, color='red', label=f'Normal Distribution - Skewness: {skewness}')
    
    plt.axvline(x=mean, color='blue', linestyle='--', label='Mean')

    plt.axvline(x=last_value, color='red', linestyle='--', label=f'Current Data Point {current_data_point} (Z-Score: {z_score})')
    
    plt.legend(loc='upper left')
   
    mng = plt.get_current_fig_manager()
    mng.set_window_title(f'{title} Histogram')
    mng.resize(*mng.window.maxsize())

    plt.show()
