import logging
from pathlib import Path
from hplib.dbclass import dbClass  # pip3 install git+https://github.com/hpharmsen/hplib
import pandas as pd
from pymysql import OperationalError

from model.log import log_error

scriptpath = Path(__file__).resolve().parent

db = None
travelbase_db = None


def get_db():
    global db
    try:
        return db or dbClass.from_inifile(scriptpath / 'credentials.ini')
    except OperationalError:
        log_error('database.py', 'get_db()', 'Could not connect to database')
        return


def get_travelbase_db():
    global travelbase_db
    return travelbase_db or dbClass.from_inifile(scriptpath / 'credentials.ini', section='travelbase')


def value(query, database=None):
    if not database:
        database = get_db()
    if not database:
        return 0
    res = database.execute(query)[0]
    res = res[list(res.keys())[0]]
    if res:
        return float(res)
    else:
        return 0


def dataframe(query, database=None):
    if not database:
        database = get_db()
    if not database:
        return None
    try:
        return pd.read_sql_query(query, database.db)
    except ConnectionResetError:
        log_error('database.py', 'dataframe', 'Database connection reset')
        return None


def table(query):
    df = dataframe(query)
    if type(df) != pd.DataFrame:
        return []
    return df.to_dict(orient='records')
