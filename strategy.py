import pandas as pd
import utility as util

def prepare_stock_data(db):
    stock_data = {}
    for stock_id in db.get_stock_info().index:
        df_quarterly = db.get_by_stock_id(stock_id, 'quarterly_report')
        df_quarterly['EPS4季'] = df_quarterly.EPS.rolling(4).sum()
        股數 = df_quarterly.股本 / 10
        df_quarterly['淨值/股'] = df_quarterly.權益 / 股數

        df_daily = db.get_daily_price(stock_id)
        util.fill_short_interval_by_long_interval(df_daily, df_quarterly, 'EPS4季')
        util.fill_short_interval_by_long_interval(df_daily, df_quarterly, '淨值/股')
        df_daily['本益比'] = df_daily.close / df_daily.EPS4季
        df_daily['本淨比'] = df_daily.close / df_daily['淨值/股']
        df_daily['眼光費'] = (df_daily.close - df_daily['淨值/股']) / df_daily.EPS4季
        stock_data[stock_id] = df_daily[['close', '淨值/股', 'EPS4季', '本益比', '本淨比', '眼光費']].dropna()
    return stock_data


def get_stock_data_by_date(stock_info, stock_data, date):
    data_dict = {}
    for stock_id in stock_info.index:
        try:
            data_dict[stock_id] = stock_data[stock_id].loc[date]
        except:
            print('**WARN: ' + stock_id + ' data missing')
            
    df = pd.DataFrame(data_dict).transpose()
    df = pd.merge(stock_info, df, left_index=True, right_index=True)
    df[['淨值/股', '本益比', '本淨比', '眼光費']] = df[['淨值/股', '本益比', '本淨比', '眼光費']].applymap(lambda x: float("{:.2f}".format(x)))
    return df


### backtest
### 買入：本益比<10，眼光費<2
def draw_backtest(stock_info, stock_data):
    for stock_id in stock_info.index:
        stock_name = stock_info.loc[stock_id, 'stock_name'] + ',' + stock_id
        df_daily = stock_data[stock_id]
        region = []
        get = False
        for i in range(len(df_daily.index)):
            if df_daily.iloc[i]['buy_label']:
                if not get:
                    region.append([df_daily.index[i]])
                    get = True
                continue
            if get:
                region[-1].append(df_daily.index[i - 1])
                get = False

        if len(region) > 0:
            if len(region[-1]) == 1:
                region[-1].append(df_daily.index[-1])
            ax = df_daily[['close']].plot(grid=True, title=stock_name, figsize=(10,4))
            for xmin, xmax in region:
                ax.axvspan(xmin, xmax, color='red', alpha=0.5)


