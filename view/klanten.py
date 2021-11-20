import os
from pathlib import Path

from model.resultaat import omzet_per_klant_laatste_zes_maanden

from settings import get_output_folder
from layout.basic_layout import HEADER_SIZE, MID_SIZE
from layout.block import VBlock, TextBlock, Page
from layout.table import Table, TableConfig


def render_klant_page(output_folder: Path):

    omzet = VBlock(
        [
            TextBlock('Omzet laatste 6 maanden', MID_SIZE),
            Table(
                omzet_per_klant_laatste_zes_maanden(),
                TableConfig(aligns=['left', 'right', 'right'], formats=['', '€', '%']),
            ),
        ]
    )

    page = Page([TextBlock('Klanten', HEADER_SIZE), omzet])
    page.render(output_folder / 'clients.html')


if __name__ == '__main__':
    os.chdir('..')
    render_klant_page(get_output_folder())
