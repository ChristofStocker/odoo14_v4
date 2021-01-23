# -*- coding: utf-8 -*-

import pandas as pd
import pyodbc


class st_mysql_login:
    def __init__(self):
        self.sql_hostname = None
        self.sql_username = None
        self.sql_password = None
        self.sql_port = None
        self.sql_database = None


def get_db_login():
    login = st_mysql_login()
    login.sql_hostname = 'tcp:10.10.1.8'
    login.sql_username = 'stastoat'
    login.sql_password = 'ReadSalsys'
    login.sql_database = 'salstasto'
    login.sql_port = 30215
    return login


def get_data(self, query) -> object:
    login = get_db_login()
    conn_string = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=" + login.sql_hostname + \
                  ";DATABASE=" + login.sql_database + \
                  ";UID=" + login.sql_username + ";PWD=" + login.sql_password
    conn = pyodbc.connect(conn_string)

    data = pd.read_sql_query(query, conn)
    data = data.where(pd.notnull(data), None)
    conn.close()
    return data
