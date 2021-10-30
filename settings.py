from configparser import ConfigParser
from pathlib import Path


def get_output_folder():
    ini = ConfigParser()
    ini.read(Path(__file__).resolve().parent / 'sources' / 'credentials.ini')
    return Path(ini['output']['folder'])

def get_monthly_folder():
    ini = ConfigParser()
    ini.read(Path(__file__).resolve().parent / 'sources' / 'credentials.ini')
    return Path(ini['output']['monthly'])


ini = ConfigParser()
ini.read(Path(__file__).resolve().parent / 'sources' / 'credentials.ini')
GREEN = 'green'  #'#7C7'
YELLOW = '#FD0'
ORANGE = '#FFA500'
RED = '#c00'
BLACK = '#000'
GRAY = 'gray'
BOLD = 'font-weight:bold;'
TOPLINE = 'border-top:2px solid #999;'
DOUBLE_TOPLINE = 'border-top-style:double;border-top-color:#999'
DATE_FORMAT = '%Y-%m-%d'


def dependent_color(value, red_treshold, green_treshold):
    # Returns color GREEN, BLACK, RED depending on value
    if red_treshold < green_treshold:
        return RED if value < red_treshold else GREEN if value > green_treshold else BLACK
    else:
        return RED if value > red_treshold else GREEN if value < green_treshold else BLACK


MAANDEN = ["Jan", "Feb", "Mrt", "Apr", "Mei", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dec"]