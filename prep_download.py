import os
from io import StringIO
import time
import requests
import random
import re
import datetime
import pandas as pd
import utility as util

def download_daily(db, from_date):
    for i_datetime in db.get_daily_dates()[from_date:].index:
        i_date = i_datetime.date()
        download_daily_foreign_buy_sell_surplus(i_date)
        download_daily_foreign_hold_ratio(i_date)

def download_weekly(db, from_date):
    for i_datetime in db.get_provided_dates_of_weekly_shareholder_classes()[from_date:].index:
        i_date = i_datetime.date()
        for stock_id in db.get_stock_info().index:
            download_weekly_shareholder_classes(stock_id, i_date)

def download_monthly(from_date):
    for i_datetime in util.get_todo_months(from_date):
        i_date = i_datetime.date()
        download_monthly_revenue(i_date)

def download_quarterly(db, from_date):
    for i_date in util.get_todo_quarters(from_date):
        year, quarter = util.get_quarter_by_report_date(i_date)
        for stock_id in db.get_stock_info().index:
            if year < 2019:
                download_quarterly_report(stock_id, year, quarter)
            else:
                move_quarterly_report(stock_id, year, quarter)


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


def download_monthly_revenue(date):
    print('download_monthly_revenue', date)
    
    year, month = util.get_month_by_report_date(date)

    # check if directory exists
    directory = os.path.join('download', 'monthly_revenue', str(year))
    util.check_directory(directory)

    # if file already downloaded, pass
    file_path = os.path.join(directory, str(year) + '-' + str(month).zfill(2) + '.html')
    if os.path.exists(file_path):
        print('**WARRN: already exists')
        return
    
    # send request
    year -= 1911
    postfix = '_0.html' if year > 98 else '.html'
    filename = str(year) + '_' + str(month) + postfix
    url = 'https://mops.twse.com.tw/nas/t21/sii/t21sc03_' + filename  
    try:
        time.sleep(5)
        response = requests.get(url, util.HTTP_HEADERS)
    except:
        print('**WARRN: requests cannot get html')
        return
    if len(response.text) < 1000:
        print('**WARRN: no report', filename)
        return
    response.encoding = 'big5'

    # save file
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write('<meta charset="UTF-8">\n')
        file.write(response.text)


def move_quarterly_report(stock_id, year, quarter):
    print('move_quarterly_report', stock_id, year, quarter)

    path = os.path.join('download', 'quarterly_report', stock_id, str(year) + 'q' + str(quarter) + '.html')
    
    # if file already downloaded, pass
    if os.path.exists(path):
        print('**WARRN: already exists')
        return
    
    # move file
    old_path = os.path.join('download', 'temp', 'tifrs-' + str(year) + 'Q' + str(quarter), 
                            'tifrs-fr1-m1-ci-cr-' + stock_id + '-' + str(year) + 'Q' + str(quarter) + '.html')
    os.rename(old_path, path)

def download_quarterly_report(stock_id, year, quarter):
    print('download_quarterly_report', stock_id, year, quarter)

    path = os.path.join('download', 'quarterly_report', stock_id, str(year) + 'q' + str(quarter) + '.html')
    
    # if file already downloaded, pass
    if os.path.exists(path):
        print('**WARRN: already exists')
        return
    
    # send request
    url = ('http://mops.twse.com.tw/server-java/t164sb01?step=1&CO_ID='
            + stock_id + '&SYEAR=' + str(year) + '&SSEASON=' + str(quarter) + '&REPORT_ID=')
    response = get_quarterly_report(url, 'C', util.HTTP_HEADERS)
    if response == None:
        response = get_quarterly_report(url, 'A', util.HTTP_HEADERS)
        if response == None:
            return
    response.encoding = 'big5'
    
    # save file
    with open(path, 'w', encoding='utf-8') as file:
        file.write('<meta charset="UTF-8">\n')
        file.write(response.text)

def get_quarterly_report(url, report_type, headers):
    try:
        time.sleep(random.uniform(5, 10))
        response = requests.get(url + report_type, headers=headers)
    except:
        print('**WARRN: requests cannot get report_type', report_type)
        return None
    if len(response.text) < 10000:
        print('**WARRN: no report', report_type)
        return None
    return response