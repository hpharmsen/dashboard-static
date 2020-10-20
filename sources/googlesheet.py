import sys
import gspread  # https://github.com/burnash/gspread
from oauth2client.service_account import ServiceAccountCredentials
from model.caching import reportz


def panic(s):
    print(s)
    sys.exit()


def convert_value(value):
    try:
        return float(value.replace('.', '').replace(',', '.'))
    except:
        pass
    return value


SHEETS = {}

import os
def get_spreadsheet(sheet_name):
    if not SHEETS.get(sheet_name):
        # oAuth authentication. Json file created using explanation at: http://gspread.readthedocs.org/en/latest/oauth2.html
        # Updated call since v2.0: See https://github.com/google/oauth2client/releases/tag/v2.0.0

        # Sheetn should be shared with: 859748496829-pm6qtlliimaqt35o8nqcti0h77doigla@developer.gserviceaccount.com
        scopes = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        print( os.getcwd())
        credentials = ServiceAccountCredentials.from_json_keyfile_name('sources/oauth_key.json', scopes=scopes)
        gc = gspread.authorize(credentials)
        try:
            sheet = gc.open(sheet_name)
        except gspread.exceptions.SpreadsheetNotFound:
            panic('Could not find or open ' + sheet_name)
        SHEETS[sheet_name] = sheet
    return SHEETS[sheet_name]


TABS = {}


@reportz(hours=1)
def sheet_tab(sheetname, tabname):
    key = (sheetname, tabname)
    if not TABS.get(key):
        sheet = get_spreadsheet(sheetname)
        TABS[key] = sheet.worksheet(tabname).get_all_values()
    return TABS[key]


def sheet_value(tab, row, col):
    return convert_value(tab[row - 1][col - 1])


def to_float(s):
    return float(str(s).replace('€', '').replace('.', '').replace('%', '').replace(' ', '').replace(',', '.'))


def to_int(s):
    return int(round(to_float(s)))
