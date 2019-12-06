import os

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
   