import os
from layout.block import TextBlock, Page
from layout.table import Table, TableConfig
from layout.basic_layout import headersize
from model.productiviteit import corrections_all
from view.dashboard import GRAY, dependent_color
from pathlib import Path


def render_correcties_page(output_folder: Path):
    def row_linking(rowindex, full_line):
        project_id = full_line[2]
        return f'https://oberon.simplicate.com/projects/{project_id}/hours'

    corrections = corrections_all()
    corrections_table = Table(
        corrections,
        TableConfig(
            headers=['Klant', 'Project', 'Uren', 'Correcties'],
            aligns=['left', 'left', 'right', 'right'],
            totals=[0, 0, 0, 1],
            row_linking=row_linking,
            hide_columns=[2],  # project_id
        ),
    )

    page = Page(
        [
            TextBlock('Correcties', headersize),
            TextBlock('Alle correcties dit jaar<br/>Tabel toont uren en gecorrigeerde uren.', color=GRAY),
            corrections_table,
        ]
    )

    page.render(output_folder / 'corrections.html')


if __name__ == '__main__':
    os.chdir('..')
    from main import output_folder

    render_correcties_page(output_folder)
