import os
from settings import get_output_folder
from layout.basic_layout import HEADER_SIZE, MID_SIZE
from layout.block import HBlock, VBlock, TextBlock, Page
from layout.table import Table, TableConfig
from model.sales import sales_waarde_details
from pathlib import Path


def render_sales_page(output_folder: Path):

    sales_trajecten = VBlock(
        [
            TextBlock('Actieve&nbsp;salestrajecten', MID_SIZE),
            Table(
                sales_waarde_details(),
                TableConfig(
                    headers=['klant', 'project', 'grootte', 'kans', 'fase', 'waarde', 'bron'],
                    aligns=['left', 'left', 'right', 'right', 'left', 'right', 'left'],
                    formats=['', '', '€', '%', '', '€', ''],
                    totals=[0, 0, 1, 0, 0, 1, 0],
                ),
            ),
        ]
    )

    pijplijn = VBlock(
        [
            TextBlock('Werk&nbsp;in&nbsp;de&nbsp;pijplijn', MID_SIZE),
            TextBlock('Moet uit Simplicate komen'),
            # Table(
            #     werk_in_pijplijn_details(),
            #     TableConfig(
            #         headers=['klant', 'project', '% af', 'onderhanden', 'eigenaar'],
            #         aligns=['left', 'left', 'right', 'right', 'left'],
            #         formats=['', '', '%', '€', ''],
            #         totals=[0, 0, 0, 1, 0],
            #     ),
            # ),
        ]
    )

    page = Page([TextBlock('Sales', HEADER_SIZE), HBlock([sales_trajecten, pijplijn])])

    page.render(output_folder / 'sales.html')


if __name__ == '__main__':
    os.chdir('..')
    render_sales_page(get_output_folder())
