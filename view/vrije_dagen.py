import os
from pathlib import Path

from layout.basic_layout import headersize, midsize
from layout.block import VBlock, TextBlock, Page
from layout.table import Table, TableConfig
from model.organisatie import vrije_dagen_overzicht


def render_vrije_dagen_page(output_folder: Path):

    omzet = VBlock(
        [
            Table(
                vrije_dagen_overzicht(),
                TableConfig(
                    headers=['Naam', 'Vorig jaar', 'Dit jaar', 'Beschikbaar', 'Pool'],
                    hide_columns=[4],
                    aligns=['left', 'right', 'right', 'right', 'right'],
                    formats=['', '.5', '.5', '.5', '.5'],
                    totals=[0, 0, 0, 0, 1],
                ),
            ),
        ]
    )

    page = Page([TextBlock('Vrije dagen', headersize), omzet])
    page.render(output_folder / 'freedays.html')


if __name__ == '__main__':
    os.chdir('..')
    render_vrije_dagen_page()
