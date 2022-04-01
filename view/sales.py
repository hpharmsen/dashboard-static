import os
from pathlib import Path

from layout.basic_layout import HEADER_SIZE, MID_SIZE, DEF_SIZE
from layout.block import HBlock, VBlock, TextBlock, Page
from layout.table import Table, TableConfig
from model.resultaat import top_x_klanten_laatste_zes_maanden
from model.sales import sales_waarde_details, top_x_sales
from settings import get_output_folder, GRAY


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


def sales_waarde_block():
    minimal_interesting_amount = 25000
    top_sales = top_x_sales(minimal_amount=minimal_interesting_amount)
    return VBlock(
        [
            TextBlock(f"Top {len(top_sales)} sales kansen", MID_SIZE),
            TextBlock(
                f"Met een verwachte waarde van minimaal € {minimal_interesting_amount}.",
                color=GRAY,
            ),
            Table(
                top_sales,
                TableConfig(headers=[], aligns=["left", "right"], formats=["", "€"]),
            ),
        ],
        link="sales.html",
    )


def klanten_block():
    klanten = VBlock(
        [
            TextBlock("Klanten", MID_SIZE),
            TextBlock("Top 3 klanten laatste 6 maanden", DEF_SIZE, padding=10, color=GRAY),
            Table(
                top_x_klanten_laatste_zes_maanden(3),
                TableConfig(
                    headers=[],
                    aligns=["left", "right", "right"],
                    formats=["", "€", "%"],
                    totals=[0, 0, 1],
                ),
            ),
        ],
        link="clients.html",
    )
    return klanten


if __name__ == '__main__':
    os.chdir('..')
    render_sales_page(get_output_folder())
