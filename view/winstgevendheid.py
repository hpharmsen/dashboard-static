import os
from pathlib import Path

from layout.basic_layout import HEADER_SIZE, MID_SIZE
from layout.block import HBlock, VBlock, TextBlock, Page
from layout.table import Table, TableConfig
from middleware.employee import OVERIGE_KOSTEN_PER_FTE_PER_UUR, PRODUCTIVITEIT
from model.utilities import Period, Day
from model.winstgevendheid import (
    winst_per_project,
    winst_per_klant,
    winst_per_persoon,
)
from settings import get_output_folder, GRAY


def render_winstgevendheid_page(output_folder: Path, period=None):
    if period:
        period_description = f'Van {period.fromday} tot {period.untilday if period.untilday else "nu"}'
    else:
        period = Period(Day().plus_months(-12))  # Laatste 12 maanden
        period_description = 'De laatste 12 maanden.'
    client_data = winst_per_klant(period)
    per_client = VBlock(
        [
            TextBlock('Per klant', MID_SIZE),
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

    project_data = winst_per_project(period)
    per_project = VBlock(
        [
            TextBlock('Per project', MID_SIZE),
            Table(
                project_data,
                TableConfig(
                    id="winst_per_project",
                    headers=list(project_data.columns),
                    aligns=['left', 'left', 'right', 'right', 'right', 'right', 'right', 'right', 'right'],
                    formats=['', '', '.', '€', '€', '€', '€', '€', '€'],
                    totals=[False, False, True, True, True, True, True, True, False],
                ),
            ),
        ]
    )

    person_data = winst_per_persoon(period)
    per_person = VBlock(
        [
            TextBlock('Per persoon', MID_SIZE),
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
            TextBlock('Winstgevendheid', HEADER_SIZE),
            TextBlock(
                f'''{period_description} uitgaande van een productiviteit van {PRODUCTIVITEIT * 100:.0f}% 
                               en €{OVERIGE_KOSTEN_PER_FTE_PER_UUR * 45 * 40 / 12:.0f} per persoon per maand bureaukosten.''',
                color=GRAY,
            ),
            HBlock([per_client, per_project, per_person]),
        ]
    )
    page.render(output_folder / 'winstgevendheid.html')


if __name__ == '__main__':
    os.chdir('..')
    period = Period('2022-01-01')
    render_winstgevendheid_page(get_output_folder(), period)
