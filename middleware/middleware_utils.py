""" Module intended to use AWS RDS database as a middleware caching layer between
    Dashboard calls and the various sources like Simplicate, Yuki and Google Maps.
    Also intended for future use in more interactive Dashboard. """
import sys
from pathlib import Path

from hplib import dbClass

scriptpath = Path(__file__).resolve().parent
middleware_db = None


def get_middleware_db():
    global middleware_db
    if not middleware_db:
        middleware_db = dbClass.from_inifile(scriptpath / '..' / 'sources' / 'credentials.ini', section='aws-dashboard')
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
