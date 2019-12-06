import matplotlib as mpl
import matplotlib.pyplot as plt
import datetime
import pandas as pd
import numpy as np
from talib import abstract

def dashboard(stock_id, db):
    mpl.style.use('fivethirtyeight')
    
    price = db.get_daily_price(stock_id)

    ### 日k -> 周k, 月k
    prices = [price, combine_price(price, 5), combine_price(price, 20)]

    ### 均線
    periods = {'週線':5, '雙週線':10, '月線':20,
            '季線':60, '半年線':120, '年線':240,
            '三年線':720, '五年線':1200, '十年線':2400}
    overlays = {}
    for p in periods:
        overlays[p] = abstract.SMA(price, periods[p])
    overlays = pd.DataFrame(overlays)
    overlay_titles = [['週線', '雙週線', '月線'], ['季線', '半年線', '年線'], ['三年線', '五年線', '十年線']]

    ### plot
    plot(prices, overlays, overlay_titles, 60)


def combine_price(price, num):
    result = []
    for i in range(len(price) - num, 0, -num):
        df = price.iloc[i : i + num]
        date = df.index[-1]
        open = df.iloc[0]['open']
        close = df.iloc[-1]['close']
        high = df['high'].max()
        low = df['low'].min()
        volume = df['volume'].sum()
        result.append({'date': date, 'open': open, 'high': high, 'low': low, 'close': close, 'volume': volume})

    df_new = pd.DataFrame(result)
    df_new.set_index('date', inplace=True)
    df_new.sort_index(inplace=True)
    return df_new


def plot(prices, overlays, overlay_titles_list, num):
    rows, cols, width, height = (3, 3, 6, 4)
    fig, axes = plt.subplots(rows, cols, figsize=(width*cols, height*rows))
    
    for period_index, (price_all, overlay_titles) in enumerate(zip(prices, overlay_titles_list)):
        price = price_all[-num:]
        graph_index = -1
        def get_ax():
            nonlocal graph_index
            graph_index += 1
            return axes[graph_index, period_index]
        
        ### plot price
        ax = get_ax()
        # candle
        x = np.arange(len(price))
        open_close_min = pd.concat([price.open, price.close], axis=1).min(axis=1)
        open_close_max = pd.concat([price.open, price.close], axis=1).max(axis=1)
        def candle_color(index, open, close):
            return 'g' if open[index] > close[index] else 'r'
        candle_colors = [candle_color(i, price.open, price.close) for i in x]
        ax.bar(x, open_close_max - open_close_min, bottom=open_close_min, color=candle_colors, linewidth=0)
        ax.vlines(x, price.low, price.high, color=candle_colors, linewidth=1)
        # x ticks
        ticks = [date.strftime('%Y-%m-%d') for date in price.index]
        space = int(len(ticks) / 4)
        for i, t in enumerate(ticks):
            ticks[i] = t if i % space == 0 else ''
        ax.set_xticks(x)
        ax.set_xticklabels(ticks)
        # overlays
        for title in overlay_titles:
            overlay = price.join(overlays[title])[title]
            ax.plot(x, overlay, label=title)
        ax.legend()   
        # grid
        ax.grid(True, axis='y')

#         ### plot volume
#         ax = get_ax()
#         # bar
#         volume = price.volume
#         if volume.max() > 1000000000: #股
#             volume_scale = 'M' #張
#             scaled_volume = volume / 1000000000 #張
#         elif volume.max() > 1000000:
#             volume_scale = 'K'
#             scaled_volume = volume / 1000000
#         else:
#             volume_scale = None
#             scaled_volume = volume
#         def volume_color(index, close):
#             return 'g' if close[index] < close[index - 1] else 'r'
#         volume_colors = [volume_color(i, price.close) for i in x]
#         ax.bar(x, scaled_volume, color=volume_colors)
#         # title 
#         volume_title = f'Volume ({volume_scale})' if volume_scale else 'Volume'
#         ax.set_title(volume_title)
#         # grid
#         ax.set_xticks(x)
#         ax.set_xticklabels(ticks)
#         ax.grid(True, axis='y')
    
        ### plot technical indicators
        def plot_indicator(data, title, ax):
            # plot
            for col in data.columns:
                ax.plot(x, data[col], label=col)
            # title
            ax.set_title(title)
            # grid
            ax.grid(True, axis='y')
            ax.set_xticks(x)
            ax.set_xticklabels(ticks)
            ax.legend()
        ## MACD    
        ax = get_ax()
        MACD = abstract.MACD(price_all[-num-50:])[-num:]
        MACD.columns = ['DIFF', 'DEM', 'D-M']
        plot_indicator(MACD, 'MACD', ax)
        ylim = MACD.abs().max().max()
        ax.set_ylim(-ylim, ylim)
        ## KD
        ax = get_ax()
        KD = abstract.STOCH(price_all[-num-50:])[-num:]
        KD.columns = ['K', 'D']
        plot_indicator(KD, 'KD', ax)