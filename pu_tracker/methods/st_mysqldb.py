# -*- coding: utf-8 -*-

import pandas as pd
import pymysql


class st_mysql_login:
    def __init__(self):
        self.sql_hostname = None
        self.sql_username = None
        self.sql_password = None
        self.sql_main_database = None
        self.sql_port = None

def get_db_login():
    login = st_mysql_login()
    login.sql_hostname = 'mysqlsrv1.stasto.local'
    login.sql_username = 'webuser'
    login.sql_password = 'e4a1PBeLzWCnHu'
    login.sql_main_database = 'produktdb'
    login.sql_port = 3306
    return login


def get_data(self, query) -> object:
    login = get_db_login()
    conn = pymysql.connect(host=login.sql_hostname, user=login.sql_username,
                           passwd=login.sql_password, db=login.sql_main_database,
                           port=login.sql_port)

    data = pd.read_sql_query(query, conn)
    data = data.where(pd.notnull(data), None)
    # print(data)
    conn.close()
    return data


def db_execute(self, query) -> object:
    login = get_db_login()
    conn = pymysql.connect(host=login.sql_hostname, user=login.sql_username,
                           passwd=login.sql_password, db=login.sql_main_database,
                           port=login.sql_port)
    with conn.cursor() as cur:
        cur.execute(query)
        conn.commit()
        conn.close()

