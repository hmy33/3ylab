import os
import datetime
from dateutil.rrule import rrule, MONTHLY 
import pandas as pd

DEFAULT_STOCK_ID = '2317'
HTTP_HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

def check_directory(directory):
    if not os.path.isdir(directory):
        os.mkdir(directory)

def fill_short_interval_by_long_interval(df_short, df_long, column):
    df_short[column] = None
    report_dates = df_long.index
    for i in range(len(report_dates) - 1):
        df_short.loc[report_dates[i]:report_dates[i+1], column] = df_long.loc[report_dates[i], column]
    df_short.loc[report_dates[-1]:, column] = df_long.loc[report_dates[-1], column]

def get_month_by_report_date(date):
    if date.month == 1:
        return date.year - 1, 12
    else:
        return date.year, date.month - 1 

def get_report_date_by_month(year, month):
    if month == 12:
        return datetime.date(year + 1, 1, 10)
    else:
        return datetime.date(year, month + 1, 10)

def get_date_range_of_month(start_date, end_date):
    return pd.date_range(start_date, end_date) & rrule(MONTHLY, dtstart=datetime.date(start_date.year, start_date.month, 10), until=end_date) 

def get_todo_months(start_date):
    if start_date == None:
        path = os.path.join('download', 'monthly_revenue')
        last_year = os.listdir(path)[-1]
        datestr = os.listdir(os.path.join(path, last_year))[-1].replace('.html', '')
        year, month = datestr.split('-')
        start_date = get_report_date_by_month(int(year), int(month)) + datetime.timedelta(days=1)
    end_date = datetime.datetime.now().date()
    return get_date_range_of_month(start_date, end_date)
    
def get_quarter_by_report_date(date):
    if date.month == 5:
        return date.year, 1
    elif date.month == 8:
        return date.year, 2
    elif date.month == 11:
        return date.year, 3
    else:
        return date.year - 1, 4

def get_report_date_by_quarter(year, quarter):
    if quarter == 1:            
        return datetime.date(year, 5, 15)
    elif quarter == 2:
        return datetime.date(year, 8, 14)
    elif quarter == 3:    
        return datetime.date(year, 11, 14)
    else:
        return datetime.date(year + 1, 3, 31)

def get_date_range_of_quarter(start_date, end_date):
    date_range = []
    for year in range(start_date.year, end_date.year + 1):
        date_range += [
            datetime.date(year, 3, 31),
            datetime.date(year, 5, 15),
            datetime.date(year, 8, 14),
            datetime.date(year, 11, 14)
        ]
    return [date for date in date_range if start_date <= date <= end_date]

def get_todo_quarters(start_date):
    if start_date == None:
        path = os.path.join('download', 'quarterly_report', DEFAULT_STOCK_ID)
        check_directory(path)
        file_list = os.listdir(path)
        if len(file_list) == 0:
            start_date = datetime.date(2013, 5, 15)
        else:
            last_quarter = file_list[-1].replace('.html', '')
            year, quarter = last_quarter.split('q')
            start_date = get_report_date_by_quarter(int(year), int(quarter)) + datetime.timedelta(days=1)
    end_date = datetime.datetime.now().date()
    return get_date_range_of_quarter(start_date, end_date)
