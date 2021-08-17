import datetime
import os

# ERROR LOGGING #
# Very basic implementation of errorlogging through the system. Will get more features by time.
from decimal import Decimal


def log_error(file: str, function: str, message: str):
    global _errors
    print('ERROR: ' + message)
    _errors += [locals()]


def get_errors():
    global _errors
    return _errors


# CALCULATION LOGGING #
def init_log():
    line = '=========='
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    log('\n' + line + ' ' + timestamp + ' ' + line)


def log(key: str, value=''):
    if type(value) in (Decimal, float):
        value = str(round(value, 0)).rjust(7)
    elif type(value) == int:
        value = str(value).rjust(7)

    if not os.path.isfile((LOG_FILE)):
        with open(LOG_FILE, 'w') as f:
            pass
    with open(LOG_FILE, 'a') as f:
        f.write(key.ljust(31) + value + '\n')


LOG_FILE = os.path.dirname(__file__) + '/log.txt'
_errors = []
