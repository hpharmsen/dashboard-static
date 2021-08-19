import sys
import os
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import AuthorizedSession
import gspread  # https://github.com/burnash/gspread

from model import log
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


def get_spreadsheet(sheet_name):
    if not SHEETS.get(sheet_name):
        # oAuth authentication. Json file created using explanation at: http://gspread.readthedocs.org/en/latest/oauth2.html
        # Updated call since v2.0: See https://github.com/google/oauth2client/releases/tag/v2.0.0

        # Sheet should be shared with: 859748496829-pm6qtlliimaqt35o8nqcti0h77doigla@developer.gserviceaccount.com
        scopes = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

        # Latest version from: https://stackoverflow.com/questions/51618127/credentials-object-has-no-attribute-access-token-when-using-google-auth-wi
        credentials = Credentials.from_service_account_file('sources/oauth_key.json')
        scoped_credentials = credentials.with_scopes(scopes)
        gc = gspread.Client(auth=scoped_credentials)
        gc.session = AuthorizedSession(scoped_credentials)

        try:
            sheet = gc.open(sheet_name)
        except gspread.exceptions.SpreadsheetNotFound:
            log.log_error('googlesheet.py', 'get_spreasheeet()', 'Could not find ' + sheet_name)
            return None
        except gspread.exceptions.APIError:
            log.log_error('googlesheet.py', 'get_spreasheeet()', 'Could not open ' + sheet_name)
            return None
        SHEETS[sheet_name] = sheet
    return SHEETS[sheet_name]


TABS = {}


@reportz(hours=2)
def sheet_tab(sheetname, tabname):
    key = (sheetname, tabname)
    if not TABS.get(key):
        sheet = get_spreadsheet(sheetname)
        if not sheet:
            return None
        try:
            TABS[key] = sheet.worksheet(tabname).get_all_values()
        except ConnectionError:
            log.log_error('googlesheet.py', 'sheet_tab', f'Could not load {sheetname} - {tabname}')
            return []
    return TABS[key]


def sheet_value(tab, row, col):
    if not tab:
        return 0  # Error in the spreadsheet
    return convert_value(tab[row - 1][col - 1])


def to_float(s):
    if not s:
        return 0
    return float(str(s).replace('€', '').replace('.', '').replace('%', '').replace(' ', '').replace(',', '.'))


def to_int(s):
    return int(round(to_float(s)))


if __name__ == '__main__':
    os.chdir('..')
    get_spreadsheet('Begroting 2020')
