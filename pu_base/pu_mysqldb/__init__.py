# -*- coding: utf-8 -*-

import pymysql
import paramiko
import pandas as pd
from paramiko import SSHClient
from sshtunnel import SSHTunnelForwarder


class mysql_login:
    def __init__(self):
        self.mypkey = None
        self.sql_hostname = None
        self.sql_username = None
        self.sql_password = None
        self.sql_main_database = None
        self.sql_port = None
        self.db_server = None
        self.ssh_host = None
        self.ssh_user = None
        self.ssh_port = None


def get_traccar_login():
    login = mysql_login()
    login.mypkey = paramiko.RSAKey.from_private_key_file("/opt/odoo13/certificates/TraccarKeyPair.pem", password='11admin74x')
    login.sql_hostname = '127.0.0.1'
    login.sql_username = 'traccar'
    login.sql_password = 'traccar123!'
    login.sql_main_database = 'backend'
    login.sql_port = 3306
    login.db_server = 'powgps-legacy-production-cluster.cluster-cbmxbyxhjmft.eu-central-1.rds.amazonaws.com'
    login.ssh_host = 'traccar.powunity.com'
    login.ssh_user = 'ec2-user'
    login.ssh_port = 22
    return login


def get_traccar_data(self, query) -> object:
    login = get_traccar_login()

    with SSHTunnelForwarder(
            (login.ssh_host, login.ssh_port),
            ssh_username=login.ssh_user,
            ssh_pkey=login.mypkey,
            ssh_password=None,
            remote_bind_address=(login.db_server, login.sql_port)) as tunnel:
        conn = pymysql.connect(host=login.sql_hostname, user=login.sql_username,
                               passwd=login.sql_password, db=login.sql_main_database,
                               port=tunnel.local_bind_port)

        data = pd.read_sql_query(query, conn)
        data = data.where(pd.notnull(data), None)
        # print(data)
        conn.close()
    return data


def db_execute(self, query) -> object:
    login = get_traccar_login()

    with SSHTunnelForwarder(
            (login.ssh_host, login.ssh_port),
            ssh_username=login.ssh_user,
            ssh_pkey=login.mypkey,
            ssh_password=None,
            remote_bind_address=(login.db_server, login.sql_port)) as tunnel:
        conn = pymysql.connect(host=login.sql_hostname, user=login.sql_username,
                               passwd=login.sql_password, db=login.sql_main_database,
                               port=tunnel.local_bind_port)
        with conn.cursor() as cur:
            cur.execute(query)
            conn.commit()
        conn.close()

