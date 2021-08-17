import os
from layout.basic_layout import headersize, midsize
from layout.block import HBlock, VBlock, TextBlock, Page
from layout.table import Table, TableConfig
from pathlib import Path

from model.winstgevendheid import (
    winst_per_project,
    winst_per_klant,
    PRODUCTIVITEIT,
    OVERIGE_KOSTEN_PER_FTE_PER_MAAND,
    winst_per_persoon,
)
from settings import get_output_folder
from view.dashboard import GRAY


def render_winstgevendheid_page(output_folder: Path):

    client_data = winst_per_klant()
    per_client = VBlock(
        [
            TextBlock('Per klant', midsize),
            Table(
                client_data,
                TableConfig(
                    id="winst_per_klant",
                    headers=list(client_data.columns),
                    aligns=['left', 'right', 'right', 'right', 'right', 'right', 'right', 'right'],
                    formats=['', '.', '€', '€', '€', '€', '€', '€'],
                    totals=[False, True, True, True, True, True, False, False],
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
                    headers=list(project_data.columns),
                    aligns=['left', 'left', 'right', 'right', 'right', 'right', 'right', 'right', 'right'],
                    formats=['', '', '.', '€', '€', '€', '€', '€', '€'],
                    totals=[False, False, True, True, True, True, True, False, False],
                ),
            ),
        ]
    )

    person_data = winst_per_persoon()
    per_person = VBlock(
        [
            TextBlock('Per persoon (voorlopig)', midsize),
            Table(
                person_data,
                TableConfig(
                    id="winst_per_persoon",
                    headers=list(person_data.columns),
                    aligns=['left', 'right', 'right', 'right'],
                    formats=['', '.', '€', '€'],
                    totals=[False, True, True, True],
                ),
            ),
        ]
    )

    page = Page(
        [
            TextBlock('Winstgevendheid', headersize),
            TextBlock(
                f'''Uitgaande van een productiviteit van {PRODUCTIVITEIT*100:.0f}% 
                               en €{OVERIGE_KOSTEN_PER_FTE_PER_MAAND} per persoon per maand bureaukosten.''',
                color=GRAY,
            ),
            HBlock([per_client, per_project, per_person]),
        ]
    )
    page.render(output_folder / 'winstgevendheid.html')


if __name__ == '__main__':
    os.chdir('..')
    render_winstgevendheid_page(get_output_folder())
