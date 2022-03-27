''' Various global settings for colors and paths '''

from configparser import ConfigParser
from pathlib import Path

ini = ConfigParser()
ini.read(Path(__file__).resolve().parent / 'sources' / 'credentials.ini')


def get_output_folder():
    return Path(ini['output']['folder'])


def get_monthly_folder():
    return Path(ini['output']['monthly'])


GREEN = 'green'  #'#7C7'
YELLOW = '#FD0'
ORANGE = '#FFA500'
RED = '#c00'
BLUE = 'blue'  # '#77c'
BLACK = '#000'
GRAY = 'gray'
BOLD = 'font-weight:bold;'
ITALIC = 'font-style:italic;'
TOPLINE = 'border-top:2px solid #999;'
DOUBLE_TOPLINE = 'border-top-style:double;border-top-color:#999'
DATE_FORMAT = '%Y-%m-%d'

EFFECTIVITY_GREEN = 65
EFFECTIVITY_RED = 60
CORRECTIONS_RED = 0.05  # Red at > 5% corrections
CORRECTIONS_GREEN = 0.02  # Green at < 1 % corrections
TURNOVER_GREEN = 69000  # Omzet per week
TURNOVER_RED = 59000  # Nog geen rekening houdend met het feit dat er meer omzet is dan hours turnover


def dependent_color(value, red_treshold, green_treshold):
    # Returns color GREEN, BLACK, RED depending on value
    if red_treshold < green_treshold:
        return RED if value < red_treshold else GREEN if value > green_treshold else BLACK
    return RED if value > red_treshold else GREEN if value < green_treshold else BLACK


MAANDEN = ["Jan", "Feb", "Mrt", "Apr", "Mei", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dec"]
