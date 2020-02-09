import os
from layout.block import TextBlock, Page, Grid, VBlock
from layout.table import Table
from layout.basic_layout import headersize, midsize
from layout.chart import ScatterChart, ChartConfig
from model.productiviteit import tuple_of_productie_users, billable_trend_person


def render_billable_page():
    users = tuple_of_productie_users()
    cols = 3
    rows = len(users) // cols + 1
    grid = Grid(rows, cols)
    row = 0
    col = 0
    for user in users:
        chartdata = [{'x': rec['datum'].strftime('%Y-%m-%d'), 'y': rec['hours']} for rec in billable_trend_person(user)]
        chart = ScatterChart(
            chartdata,
            ChartConfig(
                width=400,
                height=220,
                colors=['#6666cc', '#ddeeff'],
                min_y_axis=0,
                max_y_axis=40,  # Max 40 billable hours per week
                x_type='date',
            ),
        )
        user_block = VBlock([TextBlock(user, font_size=midsize), chart])
        grid.set_cell(row, col, user_block)
        col += 1
        if col == cols:
            col = 0
            row += 1

    page = Page(
        [
            TextBlock('Billable uren', headersize),
            TextBlock(
                'Billable uren per week het afgelopen half jaar gemeten in blokken van twee weken.', color="gray"
            ),
            grid,
        ]
    )
    page.render('output/billable.html')


if __name__ == '__main__':
    os.chdir('..')
    render_billable_page()
