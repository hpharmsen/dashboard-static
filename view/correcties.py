import os
from layout.block import TextBlock, Page
from layout.table import Table, TableConfig
from layout.basic_layout import headersize
from model.productiviteit import corrections_all, corrections_last_month
from view.dashboard import GRAY, dependent_color
from pathlib import Path
from settings import get_output_folder

def render_correcties_page(output_folder: Path):

    page = Page(
        [
            TextBlock('Correcties', headersize),
            TextBlock('correcties op uren tussen 1 week geleden en 5 weken geleden.', color=GRAY),
            corrections_last_month_table(),
            TextBlock('Alle correcties dit jaar<br/>Tabel toont uren en gecorrigeerde uren.', color=GRAY),
            corrections_all_table(),
        ]
    )

    page.render(output_folder / 'corrections.html')


def corrections_last_month_table():

    return Table(
        corrections_last_month(),
        TableConfig(
            headers=['Project', 'Correcties'],
            aligns=['left', 'right'],
        ),
    )


def corrections_all_table():
    def row_linking(rowindex, full_line):
        project_id = full_line[2]
        return f'https://oberon.simplicate.com/projects/{project_id}/hours'

    return Table(
        corrections_all(),
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
