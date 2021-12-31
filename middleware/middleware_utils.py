''' Module intended to use AWS RDS database as a middleware caching layer between
    Dashboard calls and the various sources like Simplicate, Yuki and Google Maps.
    Also intended for future use in more interactive Dashboard. '''

from hplib import dbClass

from sources.database import scriptpath

middleware_db = None


def get_middleware_db():
    global middleware_db
    if not middleware_db:
        middleware_db = dbClass.from_inifile(scriptpath / 'credentials.ini', section='aws-dashboard')
    return middleware_db


def singleton(class_):
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return getinstance


if __name__ == '__main__':
    pass
