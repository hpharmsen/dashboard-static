import os
from datetime import datetime
from model.caching import reportz
from model.resultaat import DATA_OPBRENGSTEN_ROW, BEGROTING_INKOMSTEN_ROW, BEGROTING_WINST_ROW, DATA_WINST_ROW
from sources.googlesheet import sheet_tab, sheet_value

MAANDEN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def to_int(s):
    return int(s.replace('.', ''))


# @reportz(hours=24)
def omzet_per_maand():
    tab = sheet_tab('Oberon key cijfers', 'Data')
    res = [to_int(s) for s in tab[DATA_OPBRENGSTEN_ROW - 1][2:14] if to_int(s) > 0]
    return res


@reportz(hours=1000)
def omzet_vorig_jaar_per_maand():
    y = datetime.today().year
    tab = sheet_tab('Oberon key cijfers', f'Data_{y-1}')
    return [to_int(s) for s in tab[DATA_OPBRENGSTEN_ROW - 1][2:14]]


@reportz(hours=200)
def omzet_begroot_per_maand():
    tab = sheet_tab('Oberon key cijfers', 'Begroting')
    return [1000 * to_int(s) for s in tab[BEGROTING_INKOMSTEN_ROW - 1][2:14]]


@reportz(hours=24)
def winst_per_maand():
    tab = sheet_tab('Oberon key cijfers', 'Data')
    return [to_int(s) for s in tab[DATA_WINST_ROW - 1][2:14] if to_int(s) != 0]


@reportz(hours=1000)
def winst_vorig_jaar_per_maand():
    y = datetime.today().year
    tab = sheet_tab('Oberon key cijfers', f'Data_{y-1}')
    return [to_int(s) for s in tab[DATA_WINST_ROW - 1][2:14]]


@reportz(hours=24)
def winst_begroot_per_maand():
    tab = sheet_tab('Oberon key cijfers', 'Begroting')
    return [1000 * to_int(s) for s in tab[BEGROTING_WINST_ROW - 1][2:14]]


if __name__ == '__main__':
    os.chdir('..')

    print("\n", omzet_per_maand())
    print("\n", omzet_vorig_jaar_per_maand())
    print("\n", omzet_begroot_per_maand())
