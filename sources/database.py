from pathlib import Path
from hplib.dbclass import dbClass  # pip3 install git+https://github.com/hpharmsen/hplib
import pandas as pd

scriptpath = Path(__file__).resolve().parent

db = None
travelbase_db = None


def get_db():
    global db
    return db or dbClass.from_inifile(scriptpath / 'credentials.ini')


def get_travelbase_db():
    global travelbase_db
    return travelbase_db or dbClass(
        'tor-database.cix2oo33paia.eu-west-1.rds.amazonaws.com',
        'analytics',
        'analytics',
        'pg2u032riVERbXgslNszg2IIWkx4',
    )


# dbClass.from_inifile(scriptpath / 'credentials.ini', 'travelbase')

# def dict_list(query):
#     return get_db().execute(query)


def value(query, database=None):
    if not database:
        database = get_db()
    res = database.execute(query)[0]
    res = res[list(res.keys())[0]]
    if res:
        return float(res)
    else:
        return 0


def dataframe(query, database=None):
    if not database:
        database = get_db()
    return pd.read_sql_query(query, database.db)


def table(query):
    return dataframe(query).to_dict(orient='records')
