import os
from model.resultaat import onderhanden_werk_list
from layout.basic_layout import headersize, midsize
from layout.block import VBlock, TextBlock, Page
from layout.table import Table, TableConfig
from pathlib import Path

def render_onderhanden_werk_page(output_folder: Path):

    onderhanden = VBlock(
        [
            TextBlock('Onderhanden werk', midsize),
            Table(
                onderhanden_werk_list().sort_values("OH", ascending=False),
                TableConfig(
                    headers=['project', 'besteed', 'correctie', 'gefactureerd', 'onderhanden'],
                    aligns=['left', 'right', 'right', 'right', 'right'],
                    formats=['', '€', '€', '€', '€'],
                    totals=[0, 1, 1, 1, 1],
                ),
            ),
        ]
    )

    page = Page([TextBlock('Onderhanden werk', headersize), onderhanden])
    page.render(output_folder / 'onderhanden.html')


if __name__ == '__main__':
    os.chdir('..')
    from main import output_folder
    render_onderhanden_werk_page(output_folder)
