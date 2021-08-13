import os
from layout.basic_layout import headersize, midsize
from layout.block import HBlock, VBlock, TextBlock, Page
from layout.table import Table, TableConfig
from pathlib import Path

from model.winstgevendheid import winst_per_project, winst_per_klant #, winst_per_persoon


def render_winstgevendheid_page(output_folder: Path):

    client_data = winst_per_klant()
    per_client = VBlock(
        [
            TextBlock('Per klant', midsize),
            Table(
                client_data,
                TableConfig(
                    id="winst_per_klant",
                    headers = list(client_data.columns),
                    aligns=['left', 'right', 'right', 'right', 'right', 'right', 'right', 'right'],
                    formats=['', '.', '€', '€', '€', '€', '€', '€'],
                    totals=[False, True, True, True, True, True, False, False]
                ),
            ),
        ]
    )


    project_data = winst_per_project()
    per_project = VBlock(
        [
            TextBlock('Per project', midsize),
            Table(
                project_data,
                TableConfig(
                    id="winst_per_project",
                    headers = list(project_data.columns),
                    aligns = ['left', 'left', 'right', 'right', 'right', 'right', 'right', 'right', 'right'],
                    formats = ['', '', '.', '€', '€', '€', '€', '€', '€'],
                    totals = [False, False, True, True, True, True, True, False, False]
                ),
            ),
        ]
    )

    page = Page([TextBlock('Winstgevendheid', headersize), HBlock([per_client, per_project])])
    page.render(output_folder / 'winstgevendheid.html')


if __name__ == '__main__':
    os.chdir('..')
    render_winstgevendheid_page(Path('/Users/hp/My Drive/MT/Dashboard'))
