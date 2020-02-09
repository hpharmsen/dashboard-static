import os
from layout.basic_layout import headersize, midsize
from layout.block import HBlock, VBlock, TextBlock, Page
from layout.table import Table, TableConfig
from model.sales import sales_waarde_details, werk_in_pijplijn_details


def render_sales_page():

    sales_trajecten = VBlock(
        [
            TextBlock('Actieve&nbsp;salestrajecten', midsize),
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
            TextBlock('Werk&nbsp;in&nbsp;de&nbsp;pijplijn', midsize),
            Table(
                werk_in_pijplijn_details(),
                TableConfig(
                    headers=['klant', 'project', '% af', 'onderhanden', 'eigenaar'],
                    aligns=['left', 'left', 'right', 'right', 'left'],
                    formats=['', '', '%', '€', ''],
                    totals=[0, 0, 0, 1, 0],
                ),
            ),
        ]
    )

    page = Page([TextBlock('Sales', headersize), HBlock([sales_trajecten, pijplijn])])

    page.render('output/sales.html')
    page.render('output/limited/sales.html', limited=1)


if __name__ == '__main__':
    os.chdir('..')
    render_sales_page()
