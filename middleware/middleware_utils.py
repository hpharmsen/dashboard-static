""" Module intended to use AWS RDS database as a middleware caching layer between
    Dashboard calls and the various sources like Simplicate, Yuki and Google Maps.
    Also intended for future use in more interactive Dashboard. """
import sys
from pathlib import Path

import pymysql
from hplib import dbClass

middleware_db = None


def get_middleware_db():
    global middleware_db
    if not middleware_db:
        try:
            middleware_db = dbClass.from_inifile(scriptpath / '..' / 'sources' / 'credentials.ini',
                                                 section='aws-dashboard')
        except pymysql.err.OperationalError:
            panic("middleware_utils.py get_middleware_db() Can't connect to MySQL server on AWS.")

    return middleware_db


def singleton(class_):
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return getinstance


def panic(message: str):
    print(message)
    sys.exit(1)


if __name__ == '__main__':
    pass
scriptpath = Path(__file__).resolve().parent
