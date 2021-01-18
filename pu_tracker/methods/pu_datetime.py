# -*- coding: utf-8 -*-
import pandas as pd


def to_datetime_from_db(date_time):
    from datetime import datetime
    if type(date_time) == str:
        date_time = date_time[:19]
    if date_time is None:
        date_time = '0000-00-00 00:00:00'
    if date_time == '0000-00-00 00:00:00' or pd.isnull(date_time):
        date_time = datetime.strptime('1900-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    return date_time


def to_datetime_from_db_deleted(date_time):
    from datetime import datetime
    if type(date_time) == str:
        date_time = date_time[:19]
    if date_time is None:
        date_time = '0000-00-00 00:00:00'
    if date_time == '0000-00-00 00:00:00' or pd.isnull(date_time):
        date_time = datetime.strptime('9999-12-31 00:00:00', '%Y-%m-%d %H:%M:%S')
    return date_time
