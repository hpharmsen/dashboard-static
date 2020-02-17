import os
from model.caching import load_cache
from layout.block import TextBlock, Block, Page, VBlock, HBlock, Grid
from layout.table import Table, TableConfig
from layout.basic_layout import defsize, midsize, headersize
from model.resultaat import (
    omzet_tm_vorige_maand,
    omzet_deze_maand,
    uitbesteed_tm_vorige_maand,
    onderhanden_werk,
    subsidie_tm_vorige_maand,
    opbrengsten_tm_vorige_maand,
    kosten_boekhoudkundig_tm_vorige_maand,
    bonussen_tm_vorige_maand,
    kosten_begroot_tm_maand,
    onderhanden_werk_uurbasis_table,
    onderhanden_werk_fixed_table,
    gedaan_werk_tor_table,
    gedaan_werk_tor,
    invoiced_tor,
    onderhanden_werk_tor,
    omzet_begroot,
    omzet_werkelijk,
    omzet_verschil,
    omzet_verschil_percentage,
    kosten_werkelijk,
    winst_begroot,
    winst_werkelijk,
    winst_verschil,
    winst_verschil_percentage,
    virtuele_maand,
    virtuele_dag,
    begroting_maandomzet,
    onderhanden_2019,
    tor_onderhanden_2019,
)
from model.resultaat_vergelijking import MAANDEN


def line(key, value, format='K'):
    block = Block()
    block.add_absolute_block(0, 0, TextBlock(key, defsize, color='gray'))
    block.add_absolute_block(150, 0, TextBlock(value, defsize, format=format))
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
            line(f'omzet begroot t/m {vorigemaand}', v),
            line(f'begroot deze maand tot nu', begroot_deze_maand_tot_nu),
            line('omzet begrooot nu', omzet_begroot()),
            line('omzet werkelijk', omzet_werkelijk()),
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
            arg = TextBlock(arg, defsize, style=style)
        row += [arg]
    grid.add_row(row)


def winst_berekening_block():
    grid = Grid(cols=5, aligns=['left', 'right', 'right', 'right', 'right'], has_header=True)

    huidige_maand = virtuele_maand()  # 1 based
    vorige_maand = huidige_maand - 1
    vd = virtuele_dag()  # Dag van de maand maar doorgeteld als de vorige maand nog niet is ingevuld in de boekhouding
    naam_vorige_maand = MAANDEN[huidige_maand - 2]
    naam_huidige_maand = MAANDEN[huidige_maand - 1]

    # omzet_begroot_tm_huidige_maand = begroting_maandomzet(huidige_maand)
    # omzet_begroot_tm_vorige_maand = begroting_maandomzet(huidige_maand - 1)
    # omzet_begroot_deze_maand_tot_nu = vd / 30 * (omzet_begroot_tm_huidige_maand - omzet_begroot_tm_vorige_maand)
    kosten_begroot_deze_maand_tot_nu = (
        vd / 30 * (kosten_begroot_tm_maand(huidige_maand) - kosten_begroot_tm_maand(vorige_maand))
    )

    add_row(grid, '', f'Boekhouding (t/m {naam_vorige_maand})', 'Correctie', 'Totaal nu', 'Begroot', bold=True)
    add_row(
        grid, f'Omzet t/m {naam_vorige_maand}', omzet_tm_vorige_maand() - onderhanden_2019, '', '', '',
    )
    add_row(grid, f'Uitbesteed werk t/m {naam_vorige_maand}', uitbesteed_tm_vorige_maand(), '', '')
    add_row(grid, f'Subsidie t/m {naam_vorige_maand}', subsidie_tm_vorige_maand(), '', '', '')
    add_row(grid, f'Omzet vanaf {naam_huidige_maand}', '', omzet_deze_maand(), '', '')
    add_row(grid, f'Onderhanden werk', '', onderhanden_werk(), '', '')
    add_row(grid, f'Opbrengsten', '', '', omzet_werkelijk(), omzet_begroot(), bold=True)
    add_row(grid)
    add_row(
        grid, f'Kosten t/m {naam_vorige_maand}', kosten_boekhoudkundig_tm_vorige_maand(), '', '', '',
    )
    add_row(grid, f'Ntb bonussen per nu', '', bonussen_tm_vorige_maand(), '', '')
    add_row(
        grid, f'(Geschatte) kosten vanaf {naam_huidige_maand}', '', kosten_begroot_deze_maand_tot_nu, '', '',
    )
    add_row(
        grid,
        f'Kosten',
        '',
        '',
        kosten_werkelijk(),
        kosten_begroot_tm_maand(huidige_maand - 1) + kosten_begroot_deze_maand_tot_nu,
        bold=True,
    )
    add_row(grid)
    add_row(
        grid, 'Winst', '', '', omzet_werkelijk() - kosten_werkelijk(), winst_begroot(), bold=True,
    )
    return VBlock([TextBlock('Winstberekening', midsize), grid], id="Winstberekening")


def onderhanden_block():
    tor_row = {
        'id': '',
        'name': 'TOR 3',
        'title': 'alles',
        'invoiced': invoiced_tor(),
        'done': gedaan_werk_tor(),
        'onderhanden': onderhanden_werk_tor(),
    }
    data = onderhanden_werk_uurbasis_table().append(onderhanden_werk_fixed_table()).append(tor_row, ignore_index=True)

    return VBlock(
        [
            TextBlock('Onderhanden werk', midsize),
            Table(
                data,
                TableConfig(
                    headers=['Klant', 'Project', 'Gedaan', 'Gefactureerd', 'Onderhanden'],
                    aligns=['left', 'left', 'right', 'right', 'right'],
                    formats=['', '', '€', '€', '€'],
                    totals=[0, 0, 0, 0, 1],
                    row_linking=lambda l, v: f'https://oberview.oberon.nl/project/{v[0]}',
                    hide_columns=[0],  # Hide the id column
                ),
            ),
        ]
    )


def tor_done_block():
    return Table(
        gedaan_werk_tor_table(),
        TableConfig(
            headers=['Onderdeel', 'Gedaan'],
            aligns=['left', 'right'],
            formats=['', '€'],
            totals=[0, 1],
            row_linking=lambda l, v: f'https://oberview.oberon.nl/project/{v[0]}',
            hide_columns=[0],  # Hide the id column
        ),
    )


def tor_block():
    tor_grid = Grid(cols=2, aligns=['left', 'right'], has_header=True)
    add_row(tor_grid, 'TOR Fatuuratie')
    add_row(tor_grid, 'Werk gedaan', gedaan_werk_tor())
    add_row(tor_grid, 'Te factureren (50%)', gedaan_werk_tor() / 2)
    add_row(tor_grid, 'Gefactureerd', invoiced_tor())
    add_row(tor_grid, 'Nog te factureren', gedaan_werk_tor() / 2 - invoiced_tor(), bold=True)
    add_row(tor_grid)
    add_row(tor_grid, 'Activeren (25%)', gedaan_werk_tor() / 4)
    add_row(tor_grid, 'Meegeteld met 2019', -tor_onderhanden_2019)
    add_row(tor_grid, 'Meetellen als onderhanden', onderhanden_werk_tor(), bold=True)

    return VBlock([TextBlock('TOR 3', midsize), tor_done_block(), tor_grid])


def render_resultaat_berekening():

    page = Page([HBlock([winst_berekening_block(), onderhanden_block(), tor_block()])])
    page.render('output/resultaat_berekening.html')


if __name__ == '__main__':
    os.chdir('..')
    load_cache()
    render_resultaat_berekening()
