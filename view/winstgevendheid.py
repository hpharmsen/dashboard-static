import os
from layout.basic_layout import headersize, midsize
from layout.block import HBlock, VBlock, TextBlock, Page
from layout.table import Table, TableConfig
from pathlib import Path

# from model.winstgevendheid import winst_per_persoon, winst_per_project


def render_winstgevendheid_page(output_folder: Path):
    return None
    per_persoon = VBlock(
        [
            TextBlock('Per persoon', midsize),
            Table(
                winst_per_persoon(),
                TableConfig(
                    id='winst_per_persoon',
                    headers=[
                        'persoon',
                        'uren per week',
                        'omzet',
                        'loonkosten',
                        'overige kosten',
                        'kosten per uur',
                        'winst',
                    ],
                    aligns=['left', 'center', 'right', 'right', 'right', 'center', 'right'],
                    formats=['', '.', '€', '€', '€', '€', '€'],
                    totals=[0, 0, 1, 1, 1, 0, 1],
                ),
            ),
        ]
    )

    per_project = VBlock(
        [
            TextBlock('Per project', midsize),
            Table(
                winst_per_project(),
                TableConfig(
                    id="winst_per_project",
                    aligns=['left', 'left', 'right', 'right', 'right', 'right'],
                    formats=['', '', '.', '€', '€', '€'],
                ),
            ),
        ]
    )

    page = Page([TextBlock('Winstgevendheid', headersize), HBlock([per_persoon, per_project])])
    page.render(output_folder / 'winstgevendheid.html')


if __name__ == '__main__':
    os.chdir('..')
    from main import output_folder

    render_winstgevendheid_page(output_folder)
