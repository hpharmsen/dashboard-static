import os
from layout.basic_layout import headersize, midsize
from layout.block import HBlock, VBlock, TextBlock, Page
from layout.table import Table
from model.winstgevendheid import winst_per_persoon, winst_per_project


def render_winstgevendheid_page():

    per_persoon = VBlock(
        [
            TextBlock('Per persoon', midsize),
            Table(
                winst_per_persoon(),
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
        ]
    )

    wp = winst_per_project()
    per_project = VBlock(
        [
            TextBlock('Per project', midsize),
            Table(
                wp,
                id="winst_per_project",
                aligns=['left', 'left', 'right', 'right', 'right', 'right'],
                formats=['', '', '.', '€', '€', '€'],
            ),
        ]
    )

    page = Page([TextBlock('Winstgevendheid', headersize), HBlock([per_persoon, per_project])])

    page.render('output/winstgevendheid.html')


if __name__ == '__main__':
    os.chdir('..')
    render_winstgevendheid_page()
