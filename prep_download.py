import os
from io import StringIO
import time
import requests
import random
import re
import datetime
import pandas as pd
import utility as util

def download_all(db, from_date):
    for i_datetime in db.get_daily_dates()[from_date:].index:
        i_date = i_datetime.date()
        download_daily_foreign_buy_sell_surplus(i_date)
        download_daily_foreign_hold_ratio(i_date)

    for i_datetime in db.get_provided_dates_of_weekly_shareholder_classes()[from_date:].index:
        i_date = i_datetime.date()
        for stock_id in db.get_stock_info().index:
            download_weekly_shareholder_classes(stock_id, i_date)


def download_daily_foreign_buy_sell_surplus(date):
    # check if directory exists
    directory = os.path.join('download', 'daily_foreign_buy_sell_surplus', str(date.year))
    util.check_directory(directory)
    # if file already downloaded, pass
    datestr = date.strftime('%Y%m%d')
    file_path = os.path.join(directory, datestr + '.csv')
    if os.path.exists(file_path):
        return
    print('download_daily_foreign_buy_sell_surplus', date)
    
    # send request
    url = 'http://www.twse.com.tw/fund/TWT38U?response=csv&date=' + datestr
    try:
        time.sleep(random.uniform(5, 10))
        response = requests.get(url, util.HTTP_HEADERS)
    except:
        print('**WARRN: request error')
        return

    if len(response.text) < 10:
        print('**WARRN: no csv file')
        return
    
    # save file
    with open(file_path, 'w', encoding='utf-8-sig') as file:
        file.write(response.text)


def download_daily_foreign_hold_ratio(date):
    # check if directory exists
    directory = os.path.join('download', 'daily_foreign_hold_ratio', str(date.year))
    util.check_directory(directory)
    # if file already downloaded, pass
    datestr = date.strftime('%Y%m%d')
    file_path = os.path.join(directory, datestr + '.csv')
    if os.path.exists(file_path):
        return
    print('download_daily_foreign_hold_ratio', date)
    
    # send request
    url = 'https://www.twse.com.tw/fund/MI_QFIIS?response=csv&selectType=ALLBUT0999&date=' + datestr
    try:
        time.sleep(random.uniform(5, 10))
        response = requests.get(url, util.HTTP_HEADERS)
    except:
        print('**WARRN: request error')
        return

    if len(response.text) < 600:
        print('**WARRN: no csv file')
        return
    
    # save file
    with open(file_path, 'w', encoding='utf-8-sig') as file:
        file.write(response.text)


def download_weekly_shareholder_classes(stock_id, date):
    datestr = date.strftime('%Y%m%d')
    # check if directory exists
    directory = os.path.join('download', 'weekly_shareholder_classes', stock_id)
    util.check_directory(directory) 
    # if file already downloaded, pass
    file_path = os.path.join(directory, datestr + '.csv')
    if os.path.exists(file_path):
        return
    print('download_weekly_shareholder_classes', stock_id, datestr)
    
    # send request
    url = 'https://www.tdcc.com.tw/smWeb/QryStockAjax.do'
    payload = {
        'scaDates': datestr,
        'scaDate': datestr,
        'SqlMethod': 'StockNo',
        'StockNo': stock_id,
        'REQ_OPR': 'SELECT',
        'clkStockNo': stock_id
    }
    time.sleep(random.uniform(5, 10))
    res = requests.post(url, data=payload, headers=util.HTTP_HEADERS)
    
    dfs = pd.read_html(StringIO(res.text))
    df = dfs[-2]
    if len(df.index) == 2:
        print('**WARRN: report date error')
        return
    df.columns = df.iloc[0]
    df = df.iloc[1:16]
    df = df.drop(df.columns[0], axis=1)
    df = df.set_index('持股/單位數分級')

    # save file
    df.to_csv(file_path, encoding='utf-8-sig')