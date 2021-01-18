# -*- coding: utf-8 -*-
import pandas as pd


def to_datetime_from_db(date_time):
    from datetime import datetime
    if date_time == '0000-00-00 00:00:00' or pd.isnull(date_time):
        date_time = datetime.strptime('1900-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    return date_time


def to_datetime_from_db_deleted(date_time):
    from datetime import datetime
    if date_time == '0000-00-00 00:00:00' or pd.isnull(date_time):
        date_time = datetime.strptime('9999-12-31 00:00:00', '%Y-%m-%d %H:%M:%S')
    return date_time


def to_date_from_hdb(date_string):
    from datetime import datetime
    if date_string == '00000000' or pd.isnull(date_string):
        date = datetime.strptime('1900-01-01', '%Y-%m-%d')
    else:
        date = datetime.strptime(f'{date_string[0:4]}-{date_string[4:6]}-{date_string[6:8]}', '%Y-%m-%d')
    return date


def to_sapdate(date):
    result = str(date.year) + ("00" + str(date.month))[-2:] + ("00" + str(date.day))[-2:]
    return result
