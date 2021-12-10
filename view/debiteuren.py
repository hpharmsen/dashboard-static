import os
from pathlib import Path

import pandas as pd

from layout.basic_layout import HEADER_SIZE
from layout.block import TextBlock, Page
from layout.table import Table, TableConfig
from model.finance import debiteuren_leeftijd_analyse
from settings import get_output_folder


def render_debiteuren_page(output_folder: Path):
    debiteuren = debiteuren_leeftijd_analyse()
    if not isinstance(debiteuren, pd.DataFrame):
        return  # Error occurred, no use to proceed
    page = Page(
        [
            TextBlock('Debiteuren', HEADER_SIZE),
            Table(
                debiteuren,
                TableConfig(
                    headers=['klant', 'openstaand', '<30 dg', '30-60 dg', '60-90 dg', '> 90 dg'],
                    aligns=['left', 'right', 'right', 'right', 'right', 'right'],
                    formats=['', '.', '.', '.', '.', '.'],
                    totals=[0, 1, 1, 1, 1, 1],
                    row_linking=lambda line, value: 'https://oberview.oberon.nl/facturen/openstaand',
                ),
            ),
        ]
    )
    page.render(output_folder / 'debiteuren.html')


if __name__ == '__main__':
    os.chdir('..')

    render_debiteuren_page(get_output_folder())
