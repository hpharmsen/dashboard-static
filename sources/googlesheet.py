import os
import sys
from collections import defaultdict

import gspread  # https://github.com/burnash/gspread
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.service_account import Credentials

from model import log


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


# @cache(hours=2)
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


class HeaderSheet:
    """Headersheet reads a Google Sheet with headers in the first row and in the first column.
    Pass (1-based) parameters header_row and header_col when the header data are not in the first row or col.

    After initialization the data is addressable as headersheet['Turnover','January']
    Passing non-existing headers returns None
    WARNING: sheets with duplicate headers lead to mayhem!
    """

    def __init__(self, sheetname, tabname, header_row=1, header_col=1):
        self.raw_data = sheet_tab(sheetname, tabname)
        self.data = defaultdict(dict)
        column_headers = self.raw_data[header_row - 1]
        for row in self.raw_data[header_row:]:
            row_header = row[header_col - 1]
            if not row_header:
                continue
            for idx, value in enumerate(row):
                if idx < header_col:
                    continue  # Header, hadden we al
                column_header = column_headers[idx]
                if not column_header:
                    continue
                self.data[row_header][column_header] = value
                pass

    def __getitem__(self, key):
        row, col = key
        try:
            return self.data[row][col]
        except:
            return None


if __name__ == '__main__':
    os.chdir('..')
    s = HeaderSheet('Begroting 2021', 'Begroting', header_row=2, header_col=2)
    a = s['Medewerkers', 'Apr']
    pass
