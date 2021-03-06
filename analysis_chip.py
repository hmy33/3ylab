import matplotlib as mpl
import matplotlib.pyplot as plt
import datetime
import pandas as pd
import numpy as np
import utility as util

def dashboard(stock_id, db, num_of_data, from_date=None):
    mpl.style.use('fivethirtyeight')
    ### get stock data
    price = db.get_daily_price(stock_id)[['close']]
    buy_surplus = db.get_by_stock_id(stock_id, 'daily_buy_sell_surplus')
    buy_surplus.columns = ['foreign_buy_surplus']
    hold_ratio = db.get_by_stock_id(stock_id, 'daily_foreign_hold_ratio')
    major_holder = db.get_by_stock_id(stock_id, 'weekly_shareholder_classes')

    df = pd.merge(buy_surplus, hold_ratio, left_index=True, right_index=True)
    df = pd.merge(df, price, left_index=True, right_index=True)
    util.fill_short_interval_by_long_interval(df, major_holder, '大戶_張數')
    df['major_ratio'] = df['大戶_張數'] / df['total_amount'] * 100
    
    # ### 均線
    periods = {'週線':5, '雙週線':10, '月線':20,
            '季線':60, '半年線':120, '年線':240}
    overlays = {}
    for p in periods:
        overlays[p] = df.foreign_buy_surplus.rolling(periods[p]).sum()
    overlays = pd.DataFrame(overlays)
    overlay_titles = [['週線', '雙週線'], ['月線', '季線'], ['半年線', '年線']]
    
    # ### 日k -> 周k, 月k
    df = df[['close', 'foreign_ratio', 'major_ratio']]
    dfs = [df, reduce_to_long_interval(df, 5), reduce_to_long_interval(df, 20)]
    for df in dfs:
        df['other_major_ratio'] = df.major_ratio - df.foreign_ratio
        df['foreign_ratio_diff'] = df.foreign_ratio - df.foreign_ratio.shift(1)
        df['other_major_ratio_diff'] = df.other_major_ratio - df.other_major_ratio.shift(1)
        
    ### plot
    plot(dfs, overlays, overlay_titles, num_of_data, from_date)
 

def reduce_to_long_interval(df, num):
    return df[::-num][::-1]


def plot(dfs, overlays, overlay_titles_list, num, from_date):    
    rows, cols, width, height = (3, 3, 6, 6)
    fig, axes = plt.subplots(rows, cols, figsize=(width*cols, height*rows))
    
    for period_index, (df_all, overlay_titles) in enumerate(zip(dfs, overlay_titles_list)):
        df = df_all[-num:] if from_date is None else df_all.loc[from_date:]

        graph_index = -1
        def get_ax():
            nonlocal graph_index
            graph_index += 1
            return axes[graph_index, period_index]
        
        ### plot buy_surplus
        ax = get_ax()
        # overlays
        for title in overlay_titles:
            overlay = df.join(overlays[title])[[title]]
            overlay.plot(ax=ax, title='外資買超')
        # grid
        ax.grid(True, axis='y')
        
        if period_index == 0:
            continue

        ### plot hold_ratio diff
        ax=get_ax()
        df[['foreign_ratio_diff', 'other_major_ratio_diff']].plot(ax=ax)
        
        ### plot hold_ratio
        ax=get_ax()
        df[['foreign_ratio']].plot(ax=ax)
        df[['other_major_ratio']].plot(grid=True, color='orangered', ax=ax.twinx())
        