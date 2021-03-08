import os
from layout.block import TextBlock, Page
from layout.table import Table, TableConfig
from layout.basic_layout import headersize
from model.productiviteit import corrections_all
from view.dashboard import GRAY, dependent_color
from pathlib import Path

def render_correcties_page(output_folder: Path):

    corrections_table = Table(
        corrections_all(),
        TableConfig(
            headers=['Klant', 'Project', 'Uren', 'Correcties'],
            aligns=['left', 'left', 'right', 'right'],
            totals=[0, 0, 1, 1],
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
