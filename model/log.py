import datetime
import os

# ERROR LOGGING #
# Very basic implementation of errorlogging through the system. Will get more features by time.
from decimal import Decimal


def log_error(file: str, function: str, message: str):
    global _errors
    print("ERROR: " + message)
    _errors += [locals()]


def get_errors():
    global _errors
    return _errors


_errors = []
