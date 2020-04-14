import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import matplotlib.dates as mdates
import utility as util

def dashboard(stock_id, db):
    mpl.style.use('fivethirtyeight')
    rows, cols, width, height = (11, 1, 10, 6)
    fig, axes = plt.subplots(rows, cols, figsize=(width*cols, height*rows))
    graph_index = -1
    def get_ax():
        nonlocal graph_index
        graph_index += 1
        return axes[graph_index]
    
    stock_name = db.get_stock_name(stock_id)
    df_daily = db.get_daily_price(stock_id)
    df_monthly = db.get_by_stock_id(stock_id, 'monthly_revenue')
    df_quarterly = db.get_by_stock_id(stock_id, 'quarterly_report')
    
    ### 營收
    df_monthly['3月營收'] = df_monthly.當月營收.rolling(3).mean()
    df_monthly['12月營收'] = df_monthly.當月營收.rolling(12).mean()
    df_monthly['3月營收_年增率'] = df_monthly['3月營收'] / df_monthly['3月營收'].shift(12) - 1
    # plot
    df_monthly[['當月營收', '3月營收', '12月營收']].plot(marker='o', grid=True, title=stock_name, ax=get_ax())
    ax = df_monthly[['3月營收_年增率']][-24:].plot(kind='bar', grid=True, ax=get_ax())
    ax.yaxis.set_major_formatter(FuncFormatter('{0:.0%}'.format))
    ax.set_xticklabels(df_monthly.index[-24:].map(lambda x: util.get_month_by_report_date(x)[1]))
    ax.xaxis.set_tick_params(rotation=0)

    xlim=[df_quarterly.index[0], df_quarterly.index[-1]]

    ### 三率、EPS
    df_quarterly['毛利率'] = df_quarterly.毛利 / df_quarterly.營收
    df_quarterly['營益率'] = df_quarterly.營利 / df_quarterly.營收
    df_quarterly['淨利率'] = df_quarterly.稅後淨利 / df_quarterly.營收
    df_quarterly['業外比率'] = (df_quarterly.稅前淨利 - df_quarterly.營利) / df_quarterly.營收
    df_quarterly['EPS4季'] = df_quarterly.EPS.rolling(4).sum()
    df_qoq, df_yoy = get_report_ratio_diff(df_quarterly)
    # plot
    ax = df_quarterly[['毛利率', '營益率', '淨利率']].plot(marker='o', grid=True, xlim=xlim, ax=get_ax())
    ax.yaxis.set_major_formatter(FuncFormatter('{0:.0%}'.format))
    def draw(df, ax):
        # 三率的波動較小，以含括三率的範圍為主
        ymax = max(df.apply(max)[1:4]) * 1.2
        ymin = min(df.apply(min)[1:4]) * 1.2
        df.plot.bar(ylim=(ymin, ymax), grid=True, ax=ax)
        ax.yaxis.set_major_formatter(FuncFormatter('{0:.1%}'.format))
        ax.xaxis.set_tick_params(rotation=0)
        ax.legend(loc='upper left')
    draw(df_qoq, get_ax())
    draw(df_yoy, get_ax())    
    df_quarterly[['EPS4季']].plot(marker='o', grid=True, xlim=xlim, ax=get_ax())
    
    ### ROE
    df_quarterly['ROE'] = df_quarterly.稅後淨利 / df_quarterly.權益
    df_quarterly['ROE4季'] = df_quarterly.ROE.rolling(4).sum()
    # plot
    ax = df_quarterly[['ROE4季']].plot(marker='o', grid=True, xlim=xlim, ax=get_ax())
    ax.yaxis.set_major_formatter(FuncFormatter('{0:.0%}'.format))
    
    ### 淨值
    股數 = df_quarterly.股本 / 10
    df_quarterly['淨值/股'] = df_quarterly.權益 / 股數
    df_quarterly['保留盈餘/股'] = df_quarterly.保留盈餘 / 股數
    df_quarterly['現金/股'] = df_quarterly.現金 / 股數
    # plot
    df_quarterly[['淨值/股', '保留盈餘/股', '現金/股']].plot(marker='o', grid=True, xlim=xlim, ax=get_ax())

    xlim=[df_quarterly.index[0], df_daily.index[-1]]

    ### 股價相對低檔(眼光費、本益比、本淨比)
    util.fill_short_interval_by_long_interval(df_daily, df_quarterly, 'EPS4季')
    util.fill_short_interval_by_long_interval(df_daily, df_quarterly, '淨值/股')

    df_daily['EPS4季'] = df_daily['EPS4季'].map(lambda x: None if ((x != None) and (x < 1)) else x) # EPS小，本益比會太大
    df_daily['本益比'] = df_daily.close / df_daily.EPS4季
    df_daily['本淨比'] = df_daily.close / df_daily['淨值/股']
    df_daily['眼光費'] = (df_daily.close - df_daily['淨值/股']) / df_daily.EPS4季
    df_daily['眼光費'] = df_daily['眼光費'].map(lambda x: None if x < 0 else x) # <淨值不看，看本淨比
    # plot
    df_daily[['本益比', '眼光費']].plot(grid=True, xlim=xlim, ax=get_ax())
    df_daily[['本淨比']].plot(grid=True, xlim=xlim, ax=get_ax())

    ### 股價
    close_show = df_daily['close'].loc[df_quarterly.index[0]:]
    ylim = [close_show.min(), close_show.max()]
    df_daily[['close']].plot(grid=True, xlim=xlim, ylim=ylim, ax=get_ax())

    
def get_report_ratio_diff(df):  
    df = df[-10:].copy()
    df.index = df.index.map(lambda date: date.date())
    df['營收_季增率'] = df['營收'] / df['營收'].shift(1) - 1
    df['毛利率_季增'] = df['毛利率'] - df['毛利率'].shift(1)
    df['營益率_季增'] = df['營益率'] - df['營益率'].shift(1)
    df['淨利率_季增'] = df['淨利率'] - df['淨利率'].shift(1)
    df['業外比率_季增'] = df['業外比率'] - df['業外比率'].shift(1)
    df['EPS_季增'] = df['EPS'] - df['EPS'].shift(1)

    df['營收_年增率'] = df['營收'] / df['營收'].shift(4) - 1
    df['毛利率_年增'] = df['毛利率'] - df['毛利率'].shift(4)
    df['營益率_年增'] = df['營益率'] - df['營益率'].shift(4)
    df['淨利率_年增'] = df['淨利率'] - df['淨利率'].shift(4)
    df['業外比率_年增'] = df['業外比率'] - df['業外比率'].shift(4)
    df['EPS_年增'] = df['EPS'] - df['EPS'].shift(4)
     
    df_qoq = df[['營收_季增率', '毛利率_季增', '營益率_季增', '淨利率_季增', '業外比率_季增', 'EPS_季增']][-6:]
    df_yoy = df[['營收_年增率', '毛利率_年增', '營益率_年增', '淨利率_年增', '業外比率_年增', 'EPS_年增']][-6:]
    return (df_qoq, df_yoy)