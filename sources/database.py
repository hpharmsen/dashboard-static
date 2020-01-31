from pathlib import Path
from hplib.dbclass import dbClass  # pip3 install git+https://github.com/hpharmsen/hplib
import pandas as pd

scriptpath = Path(__file__).resolve().parent

DB = None


def get_db():
    global DB
    return DB or dbClass.from_inifile(scriptpath / 'db.ini')


# def dict_list(query):
#     return get_db().execute(query)


def value(query):
    res = get_db().execute(query)[0]
    return float(res[list(res.keys())[0]])


def dataframe(query):
    return pd.read_sql_query(query, get_db().db)


def table(query):
    return dataframe(query).to_dict(orient='records')
