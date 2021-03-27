import os
from pathlib import Path

from layout.basic_layout import headersize, midsize
from layout.block import VBlock, TextBlock, Page
from layout.table import Table, TableConfig
from model.organisatie import vrije_dagen_overzicht
from model.utilities import fraction_of_the_year_past


def render_vrije_dagen_page(output_folder: Path):

    table = VBlock(
        [
            Table(
                vrije_dagen_overzicht(),
                TableConfig(
                    headers=['Naam', 'Vorig jaar', 'Dit jaar nieuw', 'Dit jaar beschikbaar', 'Totaal', 'Pool'],
                    aligns=['left', 'right', 'right', 'right', 'right', 'right'],
                    formats=['', '.5', '.5', '.5', '.5', '.5'],
                    totals=[0, 0, 0, 0, 0, 1],
                ),
            ),
        ]
    )

    page = Page(
        [
            TextBlock('Vrije dagen', headersize),
            table,
            TextBlock(
                f'Pool = Dagen van vorig jaar + Dagen dit jaar * deel van het jaar dat is geweest ({fraction_of_the_year_past()*100:.0f}%).'
            ),
        ]
    )
    page.render(output_folder / 'freedays.html')


if __name__ == '__main__':
    os.chdir('..')
    render_vrije_dagen_page(Path('/Users/hp/MT/Dashboard'))
