import atexit
import datetime
import os
import pickle
from functools import wraps, partial

CACHE_FILE = ''
cache_dict = {}
use_cache = True  # Default but can be overwritten for debug purposes


def load_cache():
    global cache_dict
    try:
        with open(CACHE_FILE, 'rb') as cachefile:
            cache_dict = pickle.load(cachefile)
        print('Loaded cache')
    except:
        cache_dict = {}
        print('New cache')


def save_cache():
    global cache_dict
    with open(CACHE_FILE, 'wb') as cachefile:
        pickle.dump(cache_dict, cachefile)


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


def cache(func=None, *, hours=0.1):
    if func is None:
        return partial(cache, hours=hours)

    @wraps(func)
    def wrapper(*args, **kwargs):
        global use_cache

        def make_str(arg):
            s = str(arg)
            splitted = s.split()
            if len(splitted) == 4 and splitted[1] == 'object':
                return splitted[0][1:]
            return s

        # getting the parameters sorted out in a string
        args_str = ', '.join([make_str(arg) for arg in args])
        kwargs_str = ', '.join([':'.join([str(j) for j in i]) for i in kwargs.items()])
        all_args = args_str + (', ' if args_str and kwargs_str else '') + kwargs_str
        func_str = func.__name__ + (f'({all_args})' if all_args else '')

        if use_cache:
            # Executing the function unless it's in the cache
            try:
                value, timestamp = cache_dict[func_str]
                diff = datetime.datetime.now() - timestamp
                dh = diff.seconds / 3600
                if dh < hours:
                    return value
                else:
                    del cache_dict[func_str]
            except KeyError:
                pass

        # No cache hit, calculate..
        before = datetime.datetime.now()

        # --- Run the actual function ---
        value = func(*args, **kwargs)
        # -------------------------------

        excution_time = datetime.datetime.now() - before
        cache_dict[func_str] = (value, datetime.datetime.now())
        printable_func_str = func_str[:77].split('\n')[0]
        if printable_func_str != func_str:
            printable_func_str += '...'
        print(f'{excution_time.seconds} {printable_func_str}')  #  = {doFormat(value)}
        return value

    return wrapper


CACHE_FILE = os.path.dirname(__file__) + '/cache.tmp'
print(CACHE_FILE)
atexit.register(save_cache)
