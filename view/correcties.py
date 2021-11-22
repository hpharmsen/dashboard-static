import os
from pathlib import Path

from layout.basic_layout import HEADER_SIZE
from layout.block import TextBlock, Page
from layout.table import Table, TableConfig
from model.productiviteit import corrections_list, corrections_count
from model.utilities import Day
from settings import get_output_folder, GRAY


def render_correcties_page(output_folder: Path):
    untilday = Day().plus_weeks(-1)
    fromday = untilday.plus_weeks(-5)
    page = Page(
        [
            TextBlock('Correcties', HEADER_SIZE),
            TextBlock('correcties op uren tussen 1 week geleden en 5 weken geleden.', color=GRAY),
            corrections_last_month_table(fromday, untilday),
            TextBlock('Alle correcties dit jaar<br/>Tabel toont uren en gecorrigeerde uren.', color=GRAY),
            corrections_all_table(),
        ]
    )

    page.render(output_folder / 'corrections.html')


def corrections_last_month_table(fromday: Day, untilday: Day):
    return Table(
        corrections_count(fromday, untilday),
        TableConfig(
            headers=['Project', 'Correcties'],
            aligns=['left', 'right'],
        ),
    )


def corrections_all_table():
    def row_linking(rowindex, full_line):
        project_id = full_line[2]
        return f'https://oberon.simplicate.com/projects/{project_id}/hours'

    untilday = Day()
    fromday = Day('2021-1-1')
    return Table(
        corrections_list(fromday, untilday),
        TableConfig(
            headers=['Klant', 'Project', 'Uren', 'Correcties'],
            aligns=['left', 'left', 'right', 'right'],
            totals=[0, 0, 0, 1],
            row_linking=row_linking,
            hide_columns=[2],  # project_id
        ),
    )


if __name__ == '__main__':
    os.chdir('..')

    render_correcties_page(get_output_folder())
