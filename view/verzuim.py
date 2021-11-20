import datetime
import os
from pathlib import Path

from settings import get_output_folder, GRAY, dependent_color
from layout.basic_layout import HEADER_SIZE, MID_SIZE, DEF_SIZE
from layout.block import VBlock, TextBlock, Page, HBlock
from layout.table import Table, TableConfig
from model.organisatie import (
    verzuim_from_day,
    verzuim_list,
    verzuim_normal_hours,
    verzuim_absence_hours,
    verzuimpercentage,
)


def render_verzuim_page(output_folder: Path):
    start = verzuim_from_day()
    today = datetime.datetime.today().strftime('%Y-%m-%d')
    table = VBlock(
        [
            Table(
                verzuim_list(start),
                TableConfig(
                    headers=['Naam', 'Dag', 'soort', 'Uren'],
                    aligns=['left', 'left', 'left', 'right'],
                    formats=[
                        '',
                        '',
                        '',
                        '.0',
                    ],
                    totals=[0, 0, 0, 1],
                ),
            ),
        ]
    )

    verzuim = verzuimpercentage()
    verzuim_color = dependent_color(verzuim, 3, 1.5)
    page = Page(
        [
            TextBlock('Vrije dagen', HEADER_SIZE),
            TextBlock(f'Van {start} tot {today}', color=GRAY),
            HBlock(
                [
                    VBlock(
                        [
                            TextBlock('Geboekte uren', DEF_SIZE, color='gray', padding=5),
                            TextBlock('Verzuim uren', DEF_SIZE, color='gray'),
                            TextBlock('Verzuimopercentage', DEF_SIZE, color='gray'),
                        ]
                    ),
                    VBlock(
                        [
                            TextBlock(verzuim_normal_hours(start), DEF_SIZE, format='0', padding=5),
                            TextBlock(verzuim_absence_hours(start), DEF_SIZE, format='0'),
                            TextBlock(verzuim, verzuim_color, format='%1'),
                        ]
                    ),
                ]
            ),
            table,
        ]
    )
    page.render(output_folder / 'absence.html')


if __name__ == '__main__':
    os.chdir('..')
    render_verzuim_page(get_output_folder())
