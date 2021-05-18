import os
from layout.block import TextBlock, Page, Grid, VBlock
from layout.basic_layout import headersize, midsize
from layout.chart import ChartConfig, BarChart
from model.productiviteit import (
    tuple_of_productie_users,
    billable_trend_person_week,
    billable_perc_user,
    roster_hours_user,
)
from pathlib import Path


def render_billable_page(output_folder: Path):
    users = sorted(tuple_of_productie_users())
    cols = 3
    rows = len(users) // cols + 1
    grid = Grid(rows, cols)
    row = 0
    col = 0
    for user in users:
        labels, hours = billable_trend_person_week(user, startweek=0)  # {weekno: hours} dict
        perc = billable_perc_user(user)
        roster_hours = roster_hours_user(user)
        chart = BarChart(
            hours,
            ChartConfig(
                width=400,
                height=220,
                colors=['#ddeeff'],
                bottom_labels=labels,
                max_y_axis=roster_hours,
                y_axis_max_ticks=5,
            ),
        )
        user_block = VBlock([TextBlock(f'{user} {perc:.0f}%', font_size=midsize), chart])
        grid.set_cell(row, col, user_block)
        col += 1
        if col == cols:
            col = 0
            row += 1

    page = Page(
        [
            TextBlock('Billable uren', headersize),
            TextBlock(
                'Billable uren per week het afgelopen halfjaar.<br/><br/>'
                + 'Grafiek toont uren gewerkt op billablke projecten zonder rekening te houden met correcties.<br/>'
                + 'Percentage is na correcties.',
                color="gray",
            ),
            grid,
        ]
    )
    page.render(output_folder / 'billable.html')


if __name__ == '__main__':
    os.chdir('..')
    from main import output_folder

    render_billable_page(output_folder)
