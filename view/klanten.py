import os
from pathlib import Path

from model.resultaat import omzet_per_klant_laatste_zes_maanden

# from model.winstgevendheid import winst_per_klant
from layout.basic_layout import headersize, midsize
from layout.block import VBlock, TextBlock, Page
from layout.table import Table, TableConfig


def render_klant_page(output_folder: Path):

    omzet = VBlock(
        [
            TextBlock('Omzet laatste 6 maanden', midsize),
            Table(
                omzet_per_klant_laatste_zes_maanden(),
                TableConfig(aligns=['left', 'right', 'right'], formats=['', '€', '%']),
            ),
        ]
    )

    # winst = VBlock(
    #     [
    #         TextBlock('Winstgevendheid', midsize),
    #         Table(
    #             winst_per_klant(),
    #             id="winst_per_klant",
    #             headers=['klant', 'uren', 'gefactureerd', 'kosten', 'winst'],
    #             aligns=['left', 'right', 'right', 'right', 'right'],
    #             formats=['', '.', '€', '€', '€'],
    #         ),
    #     ],
    # )

    page = Page([TextBlock('Klanten', headersize), omzet])
    page.render(output_folder / 'clients.html')


if __name__ == '__main__':
    os.chdir('..')
    render_klant_page(Path('/Users/hp/My Drive/MT/Dashboard'))
