import os
from layout.block import TextBlock, Page
from layout.table import Table, TableConfig
from layout.basic_layout import headersize
from model.resultaat import debiteuren_leeftijd_analyse


def render_debiteuren_page():
    page = Page(
        [
            TextBlock('Debiteuren', headersize),
            Table(
                debiteuren_leeftijd_analyse(),
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

    page.render('output/debiteuren.html')


if __name__ == '__main__':
    os.chdir('..')
    render_debiteuren_page()
