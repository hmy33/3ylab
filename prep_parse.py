import os
from io import StringIO
import datetime
import pandas as pd

def parse_all(db, from_date):
    buy_surplus_datetimes = db.get_dates('daily_buy_sell_surplus')[from_date:].index
    hold_ratio_datetimes = db.get_dates('daily_foreign_hold_ratio')[from_date:].index
    for i_datetime in db.get_daily_dates()[from_date:].index:
        i_date = i_datetime.date()
        if i_datetime not in buy_surplus_datetimes:
            parse_daily_foreign_buy_sell_surplus(i_date, db)
        if i_datetime not in hold_ratio_datetimes:
            parse_daily_foreign_hold_ratio(i_date, db)

    shareholder_classes_datetimes = db.get_dates('weekly_shareholder_classes')[from_date:].index
    for i_datetime in db.get_provided_dates_of_weekly_shareholder_classes()[from_date:].index:
        if i_datetime not in shareholder_classes_datetimes:
            i_date = i_datetime.date()
            for stock_id in db.get_stock_info().index:
                parse_weekly_shareholder_classes(stock_id, i_date, db)


def parse_daily_foreign_buy_sell_surplus(date, db):
    print('parse_daily_foreign_buy_sell_surplus', date)
    datestr = date.strftime('%Y%m%d')
    file_path = os.path.join('download', 'daily_foreign_buy_sell_surplus', str(date.year), datestr + '.csv')
    report_type = '3cols' if date > datetime.date(2017,12,17) else ''
    stock_ids = db.get_stock_info().index
    df = handle_buy_sell_surplus(file_path, report_type, 'foreign', stock_ids)
    if df is not None:
        df['date'] = str(date)
        df = df.set_index(['stock_id', 'date'])
        db.save(df, 'daily_buy_sell_surplus')

def handle_buy_sell_surplus(file_path, report_type, report_name, stock_ids):
    if not os.path.exists(file_path):
        print('**WARRN: does not exist')
        return None
    with open(file_path, 'r', encoding='utf-8-sig') as file:
        content = file.read()

    # delete unused table
    lines = content.split('\n')
    ncols = 13 if report_type == '3cols' else 7
    lines = list(filter(lambda line:len(line.split('",')) == ncols, lines))
    content = "\n".join(lines)
    # delete extra character
    content = content.replace('=', '')
    
    # csv to dataframe
    df = pd.read_csv(StringIO(content))

    # delete unused rows
    df = df.astype(str)
    df['證券代號'] = df['證券代號'].apply(lambda s: s.strip())
    df = df[df['證券代號'].apply(lambda s: s in stock_ids)]
    # reserve used columns
    col_name = '買賣超股數.2' if report_type == '3cols' else '買賣超股數'
    df = df[['證券代號', col_name]]
    df.columns = ['stock_id', report_name]
    # change string to number
    df[report_name] = df[report_name].apply(lambda s: round(int(s.replace(',', '')) / 1000))
    
    return df


def parse_daily_foreign_hold_ratio(date, db):
    print('parse_daily_foreign_hold_ratio', date)
    
    # read file
    datestr = date.strftime('%Y%m%d')
    file_path = os.path.join('download', 'daily_foreign_hold_ratio', str(date.year), datestr + '.csv')
    if not os.path.exists(file_path):
        print('**WARRN: does not exist')
        return None
    with open(file_path, 'r', encoding='utf-8-sig') as file:
        content = file.read()
    
    # delete unused table
    lines = content.split('\n')
    lines = list(filter(lambda line:len(line.split('",')) == 13, lines))
    content = "\n".join(lines)
    # delete extra character
    content = content.replace('=', '')
    
    # csv to dataframe
    df = pd.read_csv(StringIO(content))

    # delete unused rows
    df = df.astype(str)
    df['證券代號'] = df['證券代號'].apply(lambda s: s.strip())
    df = df[df['證券代號'].apply(lambda s: s in db.get_stock_info().index)]
    # reserve used columns
    df = df[['證券代號', '發行股數', '全體外資及陸資持股比率']]
    df.columns = ['stock_id', 'total_amount', 'foreign_ratio']
    # change string to number
    df['total_amount'] = df['total_amount'].apply(lambda s: round(int(s.replace(',', '')) / 1000))
    df['foreign_ratio'] = df['foreign_ratio'].apply(float)
    
    df['date'] = str(date)
    df = df.set_index(['stock_id', 'date'])
    db.save(df, 'daily_foreign_hold_ratio')


def parse_weekly_shareholder_classes(stock_id, date, db):
    print('parse_weekly_shareholder_classes', stock_id, date)
    
    # read file
    datestr = date.strftime('%Y%m%d')
    file_path = os.path.join('download', 'weekly_shareholder_classes', stock_id, datestr + '.csv')
    if not os.path.exists(file_path):
        print('**WARRN: not exist')
        return None
    df = pd.read_csv(file_path, encoding='utf-8')
    
    大戶_人數, 大戶_股數 = list(df.iloc[-1][['人 數', '股 數/單位數']])
    result = {
        'stock_id': stock_id,
        'date': str(date),
        '大戶_人數': 大戶_人數,
        '大戶_張數': int(round(大戶_股數 / 1000)) # 有時round完還是float
    }
    df = pd.DataFrame([result])
    df = df.set_index(['stock_id', 'date'])
    db.save(df, 'weekly_shareholder_classes')