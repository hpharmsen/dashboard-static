import os
from decimal import Decimal
from functools import partial

from settings import get_output_folder, MAANDEN
from model.caching import clear_cache
from layout.block import TextBlock, Block, Page, VBlock, HBlock, Grid
from layout.basic_layout import defsize, midsize
from model.log import log
from model.resultaat import (
    onderhanden_werk,
    omzet_begroot,
    omzet_tm_maand,
    omzet_tm_nu,
    bruto_marge_werkelijk,
    kosten_werkelijk,
    winst_begroot,
    winst_werkelijk,
    projectkosten_tm_nu,
    laatste_geboekte_maand,
    projectkosten_tm_maand,
    kosten_boekhoudkundig_tm_maand,
    kosten_begroot_na_maand,
)
from pathlib import Path

# from model.resultaat_vergelijking import MAANDEN


def line(key, value, format='K', url='', tooltip=''):
    block = Block()
    block.add_absolute_block(0, 0, TextBlock(key, defsize, color='gray', url=url, tooltip=tooltip))
    block.add_absolute_block(150, 0, TextBlock(value, defsize, format=format, url=url, tooltip=tooltip))
    return block


def add_row(grid, *args, header=False, bold=False, coloring=None):
    row = []
    style = 'font-weight:bold' if bold else ''
    for idx, arg in enumerate(args):
        if not isinstance(arg, Block):
            format = url = ''
            if isinstance(arg, tuple):
                arg, url = arg
            if isinstance(arg, int) or isinstance(arg, Decimal) or isinstance(arg, float):
                format = '.'
            colorfunc = (
                partial(coloring, idx) if coloring else None
            )  # Convert function with idx, value as function to value as function
            arg = TextBlock(arg, defsize, style=style, format=format, url=url, color=colorfunc)
        row += [arg]
    grid.add_row(row)


def winst_berekening_block():
    grid = Grid(cols=5, aligns=['left', 'right', 'right', 'right', 'right'], has_header=True)

    laatste_maand = laatste_geboekte_maand()
    naam_laatste_maand = MAANDEN[laatste_maand - 1]
    naam_huidige_maand = MAANDEN[laatste_maand]
    yuki_omzet_url = 'https://oberon.yukiworks.nl/domain/aspx/Finances.aspx?app=FinReports.aspx'
    begroting_url = (
        'https://docs.google.com/spreadsheets/d/1KsVEIBcnlntGR9dHYn_gSREmpoidWUUZoGlCN7ck7Zo/edit#gid=2127576386'
    )

    add_row(grid, '', 'Boekhouding (Yuki)', 'Correctie', 'Totaal nu', 'Begroot', bold=True)

    omzet_tm_laatste_maand = omzet_tm_maand(laatste_maand)
    log(f'Yuki omzet tm {naam_laatste_maand}', omzet_tm_laatste_maand)
    add_row(grid, f'Omzet t/m {naam_laatste_maand}', (omzet_tm_laatste_maand, yuki_omzet_url))

    projectkosten_tm_laatste_maand = projectkosten_tm_maand(laatste_maand)
    log(f'Yuki projectkosten tm {naam_laatste_maand}', projectkosten_tm_laatste_maand)
    add_row(grid, f'Projectkosten t/m {naam_laatste_maand}', (-projectkosten_tm_maand(laatste_maand), yuki_omzet_url))

    omzet_nu = omzet_tm_nu()
    log('Yuki omzet tm nu', omzet_nu)
    add_row(
        grid,
        f'Omzet vanaf {naam_huidige_maand}',
        '',
        (omzet_nu - omzet_tm_laatste_maand, yuki_omzet_url),
        '',
        '',
    )

    add_row(
        grid,
        f'Projectkosten vanaf {naam_huidige_maand}',
        '',
        (-projectkosten_tm_nu() + projectkosten_tm_maand(laatste_maand), yuki_omzet_url),
    )

    onderhanden = onderhanden_werk()
    log('Simplicate onderhanden werk', onderhanden)
    add_row(grid, f'Onderhanden werk nu (Simplicate)', '', (onderhanden, 'onderhanden.html'), '', '')

    begroot = omzet_begroot()
    log('Begroot', begroot)
    werkelijk = bruto_marge_werkelijk()
    log('Bruto marge (omz-proj+onderh)', werkelijk)
    add_row(
        grid,
        f'Opbrengsten',
        omzet_tm_laatste_maand - projectkosten_tm_laatste_maand,
        '',
        werkelijk,
        begroot,
        bold=True,
    )
    add_row(grid)

    kosten_tm_laatste_maand = kosten_boekhoudkundig_tm_maand(laatste_maand)
    log(f'Kosten tm {naam_laatste_maand}', kosten_tm_laatste_maand)
    add_row(
        grid,
        f'Kosten t/m {naam_laatste_maand}',
        (kosten_tm_laatste_maand, yuki_omzet_url),
        '',
        '',
        '',
    )

    begroot = kosten_begroot_na_maand(laatste_maand)
    log(f'Kosten begroot vanaf {naam_huidige_maand}', begroot)
    add_row(
        grid,
        f'Begrote kosten vanaf {naam_huidige_maand}',
        '',
        (begroot, begroting_url),
        '',
        '',
    )

    add_row(
        grid,
        f'Kosten',
        kosten_tm_laatste_maand,
        '',
        kosten_werkelijk(),
        kosten_tm_laatste_maand + begroot,
        bold=True,
    )
    add_row(grid)

    yuki_winst = omzet_tm_laatste_maand - projectkosten_tm_laatste_maand - kosten_tm_laatste_maand
    werkelijk = winst_werkelijk()
    begroot = winst_begroot()
    log('Yuki winst', yuki_winst)
    log('Winst werkelijk', werkelijk)
    log('Winst begroot', begroot)
    add_row(
        grid,
        'Winst',
        yuki_winst,
        '',
        werkelijk,
        begroot,
        bold=True,
    )
    return VBlock([TextBlock('Winstberekening', midsize), grid], id="Winstberekening")


def render_resultaat_berekening(output_folder: Path):

    page = Page([HBlock([winst_berekening_block()])])
    page.render(output_folder / 'resultaat_berekening.html')


if __name__ == '__main__':
    os.chdir('..')
    clear_cache()
    render_resultaat_berekening(get_output_folder())
