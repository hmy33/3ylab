import os
from io import StringIO
import datetime
import re
import pandas as pd
import utility as util

def parse_daily(db, from_date, check_exist=True):
    db_buy_surplus_datetimes = db.get_dates('daily_buy_sell_surplus')[from_date:].index if check_exist else []
    db_hold_ratio_datetimes = db.get_dates('daily_foreign_hold_ratio')[from_date:].index if check_exist else []
    for i_datetime in db.get_daily_dates()[from_date:].index:
        i_date = i_datetime.date()
        if i_datetime not in db_buy_surplus_datetimes:
            parse_daily_foreign_buy_sell_surplus(i_date, db)
        if i_datetime not in db_hold_ratio_datetimes:
            parse_daily_foreign_hold_ratio(i_date, db)

def parse_weekly(db, from_date, check_exist=True):
    db_shareholder_classes_datetimes = db.get_dates('weekly_shareholder_classes')[from_date:].index if check_exist else []
    for i_datetime in db.get_downloaded_dates_of_weekly_shareholder_classes()[from_date:].index:
        if i_datetime not in db_shareholder_classes_datetimes:
            i_date = i_datetime.date()
            for stock_id in db.get_stock_info().index:
                parse_weekly_shareholder_classes(stock_id, i_date, db)

def parse_monthly(db, from_date, check_exist=True):
    db_monthly_revenue_datetimes = db.get_dates('monthly_revenue')[from_date:].index if check_exist else []
    for i_datetime in util.get_todo_months(from_date):
        if i_datetime not in db_monthly_revenue_datetimes:
            i_date = i_datetime.date()
            parse_monthly_revenue(i_date, db)

def parse_quarterly(db, from_date, check_exist=True):
    db_quarterly_report_datetimes = db.get_dates('quarterly_report')[from_date:].index if check_exist else []
    db_quarterly_report_dates = [dt.date() for dt in db_quarterly_report_datetimes]
    for i_date in util.get_todo_quarters(from_date):
        if i_date not in db_quarterly_report_dates:
            for stock_id in db.get_stock_info().index:
                parse_quarterly_report(stock_id, i_date, db)


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
        return
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
        return
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


def parse_monthly_revenue(date, db):
    print('parse_monthly_revenue', date)

    year, month = util.get_month_by_report_date(date)

    file_path = os.path.join('download', 'monthly_revenue', str(year), str(year) + '-' + str(month).zfill(2) + '.html')
    if not os.path.exists(file_path):
        print('**WARRN: not exist')
        return
    dfs = pd.read_html(file_path, encoding='utf-8')
    
    # deal with different types of report
    if dfs[0].shape[0] > 500: # single big table (row > 500)
        df = dfs[0].copy() 
    else: # small tables => combine all
        df = pd.concat([df for df in dfs])
        print('get small tables...')

    # select column 0~9
    df = df[list(range(0,10))]
    # set column index
    df.columns = df[df[0] == '公司代號'].iloc[0]
    # delete unused rows
    df['當月營收'] = pd.to_numeric(df['當月營收'], errors='coerce')
    df = df.dropna(subset=['當月營收'])
    df = df[df['公司代號'] != '合計']
    # add column
    df['date'] = str(date)
    # set dataframe index
    df = df.rename(columns={'公司代號':'stock_id'})
    df = df.set_index(['stock_id'])
    # reserve used columns
    df = df.loc[:, ['date', '當月營收']]
    # reserve target stocks
    df = df[df.index.isin(db.get_stock_info().index)]
    
    db.save(df, 'monthly_revenue')


def parse_quarterly_report(stock_id, date, db):
    print('parse_quarterly_report', stock_id, date)

    # read file
    year, quarter = util.get_quarter_by_report_date(date)
    file_path = os.path.join('download', 'quarterly_report', stock_id, str(year) + 'q' + str(quarter) + '.html')
    if not os.path.exists(file_path):
        print('**WARRN: not exist')
        return
    dfs = pd.read_html(file_path, encoding='utf-8')

    result = {'stock_id':stock_id, 'date':str(date)}

    # pre-processing for year >= 2019
    if year >= 2019:
        dfs = [pd.DataFrame(), patch2019(dfs[0]), patch2019(dfs[1]), patch2019(dfs[2])]
    
    # balance sheet
    df = dfs[1].copy()
    df = df.set_index(0)
    columns = {
        '現金':['現金及約當現金總額', '現金及約當現金合計', '現金及約當現金'],
        '股本':'股本合計',
        '保留盈餘':'保留盈餘合計',
        '權益':['歸屬於母公司業主之權益合計','權益總額','權益總計']
    }
    if not getValues(df, columns, result):
        return

    # income statement
    df = dfs[2].copy()
    df = df.set_index(0)
    columns = {
        '營收':['營業收入合計','淨收益'],
        '毛利':'營業毛利（毛損）',
        '營利':'營業利益（損失）',#,'繼續營業單位稅前損益','繼續營業單位稅前淨利（淨損）'
        '稅前淨利':'繼續營業單位稅前淨利（淨損）',
        '稅後淨利':['母公司業主（淨利／損）','本期淨利（淨損）'],
        'EPS':'基本每股盈餘合計'
    } 
    if not getValues(df, columns, result):
        return

    df = pd.DataFrame([result])
    df = df.set_index(['stock_id', 'date'])
    df = df.apply(lambda s:pd.to_numeric(s, errors='coerce'))
    
    if quarter == 4:
        df_accumulated_income = db.get_accumulated_income(stock_id, year)
        for column in df_accumulated_income.columns:
            df.ix[0, column] = df.ix[0, column] - df_accumulated_income.ix[0, column]
    
    db.save(df, 'quarterly_report')

def getValues(df, columns, result):
    for key, value in columns.items():
        if type(value) == str:
            try:
                result[key] = df.loc[value][1]
            except:
                print('can not get', value)
                return False
        else: # list
            for name in value:
                try:
                    result[key] = df.loc[name][1]
                    break
                except:
                    continue
            if key not in result:
                print('can not get', value)
                return False
    return True

def patch2019(df):
    df = df.copy()
    df = df.iloc[:, 1:] #移除第一欄
    df.columns = range(df.shape[1]) #重設column index
    df = df.dropna() #NaN欄位在re時不符合字串型態
    df[0] = df[0].map(lambda s: re.sub(r'[a-zA-Z(),\-]', '', s).strip()) #移除英文、()、,、-、空白
    df[1] = df[1].map(lambda s: '-' + s[1:-1].replace(',', '') if s[0] == '(' else s) #處理負值格式
    return df
