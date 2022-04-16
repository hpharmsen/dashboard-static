import pandas as pd
from hplib.dbclass import dbClass  # pip3 install git+https://github.com/hpharmsen/hplib
from pymysql import OperationalError

from middleware.middleware_utils import panic, scriptpath
from model.log import log_error

db = None
travelbase_db = None


def get_db():
    global db
    try:
        return db or dbClass.from_inifile(scriptpath / '..' / 'sources' / 'credentials.ini')
    except OperationalError:
        log_error('database.py', 'get_db()', 'Could not connect to database')
        return


def get_travelbase_db():
    global travelbase_db
    return travelbase_db or dbClass.from_inifile(
        scriptpath / '..' / 'sources' / 'credentials.ini', section='travelbase'
    )


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


def dataframe(query: str, database: dbClass = None) -> pd.DataFrame:
    if not database:
        database = get_db()
    if not database:
        panic(f'dataframe function could not connect to database')
    try:
        return pd.read_sql_query(query.replace('%', '%%'), database.engine)
    except OperationalError:
        panic(f'dataframe function connection reset with query ' + query)


def table(query):
    df = dataframe(query)
    if not isinstance(df, pd.DataFrame):
        return []
    return df.to_dict(orient='records')
