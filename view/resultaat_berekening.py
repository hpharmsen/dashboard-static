import os
from decimal import Decimal
import datetime

from model.caching import load_cache, clear_cache
from layout.block import TextBlock, Block, Page, VBlock, HBlock, Grid
from layout.basic_layout import defsize, midsize, headersize
from model.resultaat import (
    onderhanden_werk,
    # kosten_boekhoudkundig_tm_vorige_maand,
    kosten_begroot_tm_maand,
    omzet_begroot,
    omzet_tm_maand,
    omzet_tm_nu,
    bruto_marge_werkelijk,
    omzet_verschil,
    omzet_verschil_percentage,
    kosten_werkelijk,
    winst_begroot,
    winst_werkelijk,
    winst_verschil,
    winst_verschil_percentage,
    # virtuele_maand,
    virtuele_dag,
    # begroting_maandomzet,
    # kosten_begroot_deze_maand,
    # projectkosten_tm_vorige_maand,
    projectkosten_tm_nu,
    laatste_geboekte_maand,
    projectkosten_tm_maand,
    kosten_boekhoudkundig_tm_maand,
    kosten_begroot_na_maand,
)
from pathlib import Path

# from model.resultaat_vergelijking import MAANDEN
MAANDEN = ["Jan", "Feb", "Mrt", "Apr", "Mei", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dec"]


def line(key, value, format='K', url='', tooltip=''):
    block = Block()
    block.add_absolute_block(0, 0, TextBlock(key, defsize, color='gray', url=url, tooltip=tooltip))
    block.add_absolute_block(150, 0, TextBlock(value, defsize, format=format, url=url, tooltip=tooltip))
    return block


def omzet_block():
    vm = virtuele_maand()
    vorigemaand = MAANDEN[vm - 2]
    # huidigemaand = MAANDEN[vm - 1]
    h = begroting_maandomzet(vm)
    v = begroting_maandomzet(vm - 1)
    vd = virtuele_dag()  # Dag van de maand maar doorgeteld als de vorige maand nog niet is ingevuld in de boekhouding
    begroot_deze_maand_tot_nu = vd / 30 * (h - v)

    omzet = VBlock(
        [
            TextBlock('Omzet', headersize),
            line(f'Omzet begroot t/m {vorigemaand}', v),
            line(f'begroot deze maand tot nu', begroot_deze_maand_tot_nu),
            line('omzet begrooot nu', omzet_begroot()),
            line('omzet werkelijk', bruto_marge_werkelijk()),
            line('omzet verschil', omzet_verschil(), format='+K'),
            line('percentueel', omzet_verschil_percentage(), format='+%'),
        ]
    )
    return omzet


def winst_block():
    winst = VBlock(
        [
            TextBlock('Winst', headersize),
            line('winst begrooot', winst_begroot()),
            line('winst werkelijk', winst_werkelijk()),
            line('winst verschil', winst_verschil(), format='+K'),
            line('percentueel', winst_verschil_percentage(), format='+%'),
        ]
    )
    return winst


def add_row(grid, *args, header=False, bold=False):
    row = []
    style = 'font-weight:bold' if bold else ''
    for arg in args:
        if not isinstance(arg, Block):
            format = url = ''
            if isinstance(arg, tuple):
                arg, url = arg
            if isinstance(arg, int) or isinstance(arg, Decimal) or isinstance(arg, float):
                format = '.'
            arg = TextBlock(arg, defsize, style=style, format=format, url=url)
        row += [arg]
    grid.add_row(row)


def winst_berekening_block():
    grid = Grid(cols=5, aligns=['left', 'right', 'right', 'right', 'right'], has_header=True)

    # huidige_maand = datetime.datetime.today().month
    laatste_maand = laatste_geboekte_maand()
    naam_laatste_maand = MAANDEN[laatste_maand - 1]
    naam_huidige_maand = MAANDEN[laatste_maand]
    yuki_omzet_url = 'https://oberon.yukiworks.nl/domain/aspx/Finances.aspx?app=FinReports.aspx'
    begroting_url = (
        'https://docs.google.com/spreadsheets/d/1KsVEIBcnlntGR9dHYn_gSREmpoidWUUZoGlCN7ck7Zo/edit#gid=2127576386'
    )

    add_row(grid, '', 'Boekhouding (Yuki)', 'Correctie', 'Totaal nu', 'Begroot', bold=True)
    add_row(grid, f'Omzet t/m {naam_laatste_maand}', (omzet_tm_maand(laatste_maand), yuki_omzet_url))
    add_row(grid, f'Projectkosten t/m {naam_laatste_maand}', (-projectkosten_tm_maand(laatste_maand), yuki_omzet_url))
    add_row(
        grid,
        f'Omzet vanaf {naam_huidige_maand}',
        '',
        (omzet_tm_nu() - omzet_tm_maand(laatste_maand), yuki_omzet_url),
        '',
        '',
    )
    add_row(
        grid,
        f'Projectkosten vanaf {naam_huidige_maand}',
        '',
        (-projectkosten_tm_nu() + projectkosten_tm_maand(laatste_maand), yuki_omzet_url),
    )
    add_row(grid, f'Onderhanden werk nu (Simplicate)', '', (onderhanden_werk(), 'onderhanden.html'), '', '')
    add_row(
        grid,
        f'Opbrengsten',
        omzet_tm_maand(laatste_maand) - projectkosten_tm_maand(laatste_maand),
        '',
        bruto_marge_werkelijk(),
        omzet_begroot(),
        bold=True,
    )
    add_row(grid)

    # huidige_maand = virtuele_maand()  # 1 based
    # naam_vorige_maand = MAANDEN[huidige_maand - 2]
    # naam_huidige_maand = MAANDEN[huidige_maand - 1]

    add_row(
        grid,
        f'Kosten t/m {naam_laatste_maand}',
        (kosten_boekhoudkundig_tm_maand(laatste_maand), yuki_omzet_url),
        '',
        '',
        '',
    )
    # add_row(grid, f'Ntb bonussen t/m {naam_vorige_maand}', '', bonussen_tm_vorige_maand(), '', '')
    add_row(
        grid,
        f'Begrote kosten vanaf {naam_huidige_maand}',
        '',
        (kosten_begroot_na_maand(laatste_maand), begroting_url),
        '',
        '',
    )
    add_row(
        grid,
        f'Kosten',
        kosten_boekhoudkundig_tm_maand(laatste_maand),
        '',
        kosten_werkelijk(),
        kosten_boekhoudkundig_tm_maand(laatste_maand) + kosten_begroot_na_maand(laatste_maand),
        bold=True,
    )
    add_row(grid)
    add_row(
        grid,
        'Winst',
        omzet_tm_maand(laatste_maand)
        - projectkosten_tm_maand(laatste_maand)
        - kosten_boekhoudkundig_tm_maand(laatste_maand),
        '',
        winst_werkelijk(),
        winst_begroot(),
        bold=True,
    )
    return VBlock([TextBlock('Winstberekening', midsize), grid], id="Winstberekening")


def tor_block():
    return None
    # te_factureren = min(TOR_MAX_BUDGET, gedaan_werk_tor()) / 2
    # tor_grid = Grid(cols=2, aligns=['left', 'right'], has_header=True)
    # add_row(tor_grid, 'TOR Facturatie')
    # add_row(tor_grid, 'Werk gedaan', gedaan_werk_tor())
    # add_row(tor_grid, f'Te factureren (50% van max {TOR_MAX_BUDGET})', te_factureren)
    # add_row(tor_grid, 'Gefactureerd', invoiced_tor())
    # add_row(tor_grid, 'Nog te factureren', te_factureren - invoiced_tor(), bold=True)
    # add_row(tor_grid)
    # # add_row(tor_grid, 'Werk gedaan dit jaar', gedaan_werk_tor_dit_jaar())
    # add_row(tor_grid, 'Activeren (50% van te factureren)', te_factureren / 2)
    # add_row(tor_grid, 'Nog te factureren', te_factureren - invoiced_tor())
    # add_row(tor_grid, 'Tor onderhanden vorig jaar', -tor_onderhanden_2019)
    # add_row(tor_grid, 'Onderhandenwerk TOR dit jaar', onderhanden_werk_tor(), bold=True)
    #
    # return VBlock([TextBlock('TOR 3', midsize), tor_done_block(), tor_grid])


def render_resultaat_berekening(output_folder: Path):

    page = Page([HBlock([winst_berekening_block()])])
    page.render(output_folder / 'resultaat_berekening.html')


if __name__ == '__main__':
    os.chdir('..')
    clear_cache()

    # load_cache()
    render_resultaat_berekening(Path('/Users/hp/MT/Dashboard'))
