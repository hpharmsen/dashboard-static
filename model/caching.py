import os
import atexit
import pickle
import datetime
from functools import wraps, partial
from layout.basic_layout import doFormat

CACHE_FILE = ''
cache = {}
use_cache = True # Default but can be overwritten for debug purposes

def load_cache():
    global cache
    try:
        with open(CACHE_FILE, 'rb') as cachefile:
            cache = pickle.load(cachefile)
        print('Loaded cache')
    except:
        cache = {}
        print('New cache')


def save_cache():
    global cache
    with open(CACHE_FILE, 'wb') as cachefile:
        pickle.dump(cache, cachefile)


def clear_cache():
    print('Removing', CACHE_FILE)
    if os.path.isfile(CACHE_FILE):
        os.remove(CACHE_FILE)


def cache_created_time_stamp():
    if os.path.isfile(CACHE_FILE):
        return datetime.datetime.fromtimestamp(os.stat(CACHE_FILE).st_birthtime)
    else:
        return None


def cache_modified_time_stamp():
    if os.path.isfile(CACHE_FILE):
        # t = os.stat(CACHE_FILE).st_birthtime
        return datetime.datetime.fromtimestamp(os.path.getmtime(CACHE_FILE))  # datetime.datetime.fromtimestamp(t)
    else:
        return datetime.datetime.now()
    # return os.stat(CACHE_FILE).st_mtime


def reportz(func=None, *, hours=0.1):
    if func is None:
        return partial(reportz, hours=hours)

    @wraps(func)
    def wrapper(*args, **kwargs):
        global use_cache

        # getting the parameters sorted out in a string
        args_str = ', '.join([str(arg) for arg in args])
        kwargs_str = ', '.join([':'.join([str(j) for j in i]) for i in kwargs.items()])
        all_args = args_str + (', ' if args_str and kwargs_str else '') + kwargs_str
        func_str = func.__name__ + (f'({all_args})' if all_args else '')

        if use_cache:
            # Executing the function unless it's in the cache
            try:
                value, timestamp = cache[func_str]
                diff = datetime.datetime.now() - timestamp
                dh = diff.seconds / 3600
                if dh < hours:
                    return value
                else:
                    del cache[func_str]
            except KeyError:
                pass

        # No cache hit, calculate..
        before = datetime.datetime.now()

        # --- Run the actual function ---
        value = func(*args, **kwargs)
        # -------------------------------

        excution_time = datetime.datetime.now() - before
        cache[func_str] = (value, datetime.datetime.now())
        printable_func_str = func_str[:77].split('\n')[0]
        if printable_func_str != func_str:
            printable_func_str += '...'
        print(f'{excution_time.seconds} {printable_func_str}')  #  = {doFormat(value)}
        return value

    return wrapper


CACHE_FILE = os.path.dirname(__file__) + '/cache.tmp'
print(CACHE_FILE)
atexit.register(save_cache)
