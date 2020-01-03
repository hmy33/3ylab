import sqlite3
import pandas as pd
import os
import io
import requests
import datetime
import utility as util

class DB():
    def __init__(self):
        self.conn = sqlite3.connect(os.path.join('db', "data.db"))
        self.curs = self.conn.cursor()
        self.stock_info = get_target_stocks()
        self.daily_price = {}

    def __del__(self):
        self.curs.close()
        self.conn.close()

    def save(self, df, table_name):
        df.to_sql(table_name, self.conn, if_exists='append')

    def delete_by_date(self, date, table_name):
        sql = f'DELETE FROM {table_name} WHERE date = "{str(date)}"'
        print(sql)
        self.curs.execute(sql)
        self.conn.commit()

    def get_stock_info(self):
        return self.stock_info

    def get_stock_name(self, stock_id):
        return self.stock_info.loc[stock_id, 'stock_name']

    def get_daily_price(self, stock_id, force=False):
        if force or stock_id not in self.daily_price:
            self.daily_price[stock_id] = crawl_price(stock_id)
        return self.daily_price[stock_id]
    
    def get_daily_dates(self):
        price = self.get_daily_price(util.DEFAULT_STOCK_ID)
        return pd.DataFrame(price.index).set_index('Date')

    def get_provided_dates_of_weekly_shareholder_classes(self):
        return get_provided_dates_of_weekly_shareholder_classes()

    def get_downloaded_dates_of_weekly_shareholder_classes(self):
        return get_downloaded_dates_of_weekly_shareholder_classes()
        
    def query_and_index_date(self, sql):
        df = pd.read_sql(sql, self.conn, index_col=['date'], parse_dates=['date']).sort_index()
        if len(df) == 0:
            raise Exception(sql)
        return df

    def get_by_stock_id(self, stock_id, table_name):
        sql = f'SELECT * FROM {table_name} WHERE stock_id = {stock_id}'
        df = self.query_and_index_date(sql)
        return df.drop('stock_id', axis=1)

    def get_dates(self, table_name):
        sql = f'SELECT DISTINCT(date) FROM {table_name}'
        df = pd.read_sql(sql, self.conn, parse_dates=['date']).sort_values(by='date')
        return pd.DataFrame(df['date']).set_index('date')

    def get_accumulated_income(self, stock_id, year):
        sql = f'SELECT sum(營收) as 營收, sum(毛利) as 毛利, sum(營利) as 營利, sum(稅前淨利) as 稅前淨利, sum(稅後淨利) as 稅後淨利, sum(EPS) as EPS FROM quarterly_report WHERE stock_id = "{stock_id}" AND date in ("{year}-05-15", "{year}-08-14", "{year}-11-14")'
        df = pd.read_sql(sql, self.conn)
        return df

def crawl_price(stock_id):
    # print('crawl price: ' + stock_id)
    stock_id = stock_id + '.TW'
    now = int(datetime.datetime.now().timestamp()) + 86400
    url = "https://query1.finance.yahoo.com/v7/finance/download/" + stock_id + "?period1=0&period2=" + str(now) + "&interval=1d&events=history&crumb=hP2rOschxO0"

    response = requests.post(url)

    f = io.StringIO(response.text)
    df = pd.read_csv(f, index_col='Date', parse_dates=['Date']).sort_index()
    df = df.dropna()
    df = df.rename(columns={col: col.lower() for col in df.columns})
    return df

def get_target_stocks():
    df = pd.read_csv('target.csv', encoding='utf-8', dtype={'stock_id': str})
    df = df.set_index('stock_id')
    return df[~df.index.isin(util.NEW_STOCK_ID)]

import ast
def get_provided_dates_of_weekly_shareholder_classes():
    url = 'https://www.tdcc.com.tw/smWeb/QryStockAjax.do'
    payload = {'REQ_OPR': 'qrySelScaDates'}
    res = requests.post(url, data=payload, headers=util.HTTP_HEADERS)
    datestrs = ast.literal_eval(res.text)
    return pd.DataFrame({'date': pd.to_datetime(datestrs)}).set_index('date').sort_index()

import time
def get_downloaded_dates_of_weekly_shareholder_classes():
    path = os.path.join('download', 'weekly_shareholder_classes', util.DEFAULT_STOCK_ID)
    dates = []
    for filename in os.listdir(path):
        datestr = filename.replace('.csv', '')
        date = datetime.datetime.fromtimestamp(time.mktime(time.strptime(datestr, '%Y%m%d'))) 
        dates.append(date) 
    return pd.DataFrame({'date': dates}).set_index('date').sort_index()