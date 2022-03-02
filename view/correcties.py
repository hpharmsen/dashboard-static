import os
from pathlib import Path

from layout.basic_layout import HEADER_SIZE
from layout.block import TextBlock, Page
from layout.table import Table, TableConfig
from model.productiviteit import corrections_list, corrections_count
from model.utilities import Day, Period
from settings import get_output_folder, GRAY


def render_correcties_page(output_folder: Path):
    end_day = Day().plus_days(-2).last_monday()
    start_day = end_day.plus_weeks(-4)
    period = Period(start_day, end_day)
    page = Page(
        [
            TextBlock('Correcties', HEADER_SIZE),
            TextBlock(f'correcties op uren van {start_day} tot en met {end_day.plus_days(-1)}.', color=GRAY),
            corrections_last_month_table(period),
            TextBlock('Alle correcties dit jaar<br/>Tabel toont uren en gecorrigeerde uren.', color=GRAY),
            corrections_all_table(),
        ]
    )

    page.render(output_folder / 'corrections.html')


def corrections_last_month_table(period: Period):
    return Table(
        corrections_count(period),
        TableConfig(
            headers=['Project', 'Correcties'],
            aligns=['left', 'right'],
        ),
    )


def corrections_all_table():
    def row_linking(rowindex, full_line):
        project_id = full_line[2]
        return f'https://oberon.simplicate.com/projects/{project_id}/hours'

    period = Period(Day('2022-1-1'))
    # corr = corrections_list(period)
    return Table(
        corrections_list(period),
        TableConfig(
            headers=['Klant', 'Project', 'Uren', 'Correcties'],
            aligns=['left', 'left', 'right', 'right'],
            totals=[0, 0, 0, 1],
            row_linking=row_linking,  # project_id
        ),
    )


if __name__ == '__main__':
    os.chdir('..')

    render_correcties_page(get_output_folder())
