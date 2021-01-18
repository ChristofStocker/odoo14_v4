# -*- coding: utf-8 -*-

import pandas as pd
import pyhdb


class st_mysql_login:
    def __init__(self):
        self.sql_hostname = None
        self.sql_username = None
        self.sql_password = None
        self.sql_port = None


def get_db_login():
    login = st_mysql_login()
    login.sql_hostname = 's4psgc1.stasto.local'
    login.sql_username = 'SAPABAP1'
    login.sql_password = 's4SAPadm'
    login.sql_port = 30215
    return login


def get_data(self, query) -> object:
    login = get_db_login()
    conn = pyhdb.connect(
        host=login.sql_hostname,
        port=login.sql_port,
        user=login.sql_username,
        password=login.sql_password)

    data = pd.read_sql_query(query, conn)
    data = data.where(pd.notnull(data), None)
    # print(data)
    conn.close()
    return data


def db_execute(self, query) -> object:
    login = get_db_login()
    conn = pyhdb.connect(
        host=login.sql_hostname,
        port=login.sql_port,
        user=login.sql_username,
        password=login.sql_password)

    with conn.cursor() as cur:
        cur.execute(query)
        conn.commit()
        conn.close()
