import os
from datetime import datetime
from model.caching import reportz
from model.resultaat import (
    BEGROTING_SHEET,
    BEGROTING_TAB,
    RESULTAAT_TAB,
    RESULTAAT_INKOMSTEN_ROW,
    BEGROTING_INKOMSTEN_ROW,
    BEGROTING_WINST_ROW,
    RESULTAAT_WINST_ROW,
    RESULTAAT_FACTUREN_VORIG_JAAR_ROW,
    BEGROTING_WINST_VORIG_JAAR_ROW,
    BEGROTING_INKOMSTEN_VORIG_JAAR_ROW,
)
from sources.googlesheet import sheet_tab, sheet_value

MAANDEN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def to_int(s):
    if not s:
        return 0
    return int(s.replace('.', ''))


@reportz(hours=24)
def omzet_per_maand():
    tab = sheet_tab(BEGROTING_SHEET, RESULTAAT_TAB)
    if not tab:
        return 0  # Error in the spreadsheet
    res = [to_int(s) for s in tab[RESULTAAT_INKOMSTEN_ROW - 1][2:14] if to_int(s) > 0]
    return res


@reportz(hours=1000)
def omzet_vorig_jaar_per_maand():
    y = datetime.today().year
    tab = sheet_tab(BEGROTING_SHEET, BEGROTING_TAB)
    if not tab:
        return 0  # Error in the spreadsheet
    return [to_int(s) for s in tab[BEGROTING_INKOMSTEN_VORIG_JAAR_ROW - 1][2:14]]


@reportz(hours=200)
def omzet_begroot_per_maand():
    tab = sheet_tab(BEGROTING_SHEET, BEGROTING_TAB)
    if not tab:
        return 0  # Error in the spreadsheet
    return [1000 * to_int(s) for s in tab[BEGROTING_INKOMSTEN_ROW - 1][2:14]]


@reportz(hours=24)
def winst_per_maand():
    tab = sheet_tab(BEGROTING_SHEET, RESULTAAT_TAB)
    if not tab:
        return 0  # Error in the spreadsheet
    return [to_int(s) for s in tab[RESULTAAT_WINST_ROW - 1][2:14] if to_int(s) != 0]


@reportz(hours=1000)
def winst_vorig_jaar_per_maand():
    y = datetime.today().year
    tab = sheet_tab(BEGROTING_SHEET, BEGROTING_TAB)
    if not tab:
        return 0  # Error in the spreadsheet
    return [to_int(s) for s in tab[BEGROTING_WINST_VORIG_JAAR_ROW - 1][2:14]]


@reportz(hours=24)
def winst_begroot_per_maand():
    tab = sheet_tab(BEGROTING_SHEET, BEGROTING_TAB)
    if not tab:
        return 0  # Error in the spreadsheet
    return [1000 * to_int(s) for s in tab[BEGROTING_WINST_ROW - 1][2:14]]


if __name__ == '__main__':
    os.chdir('..')

    print("\n", omzet_per_maand())
    print("\n", omzet_vorig_jaar_per_maand())
    print("\n", omzet_begroot_per_maand())
