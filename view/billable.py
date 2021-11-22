import os
from pathlib import Path

from layout.basic_layout import HEADER_SIZE, MID_SIZE
from layout.block import TextBlock, Page, Grid, VBlock
from layout.chart import ChartConfig, BarChart
from maandrapportage.maandrapport import HoursData
from model.productiviteit import tuple_of_productie_users, billable_trend_person_week
from model.utilities import Day
from settings import get_output_folder


def render_billable_page(output_folder: Path):
    users = sorted(tuple_of_productie_users())
    untilday = Day()
    fromday = Day().plus_months(-6)
    cols = 3
    rows = len(users) // cols + 1
    grid = Grid(rows, cols)
    row = 0
    col = 0
    for user in users:
        labels, hours = billable_trend_person_week(user, startweek=0)  # {weekno: hours} dict
        hours_data = HoursData(fromday, untilday, user)
        chart = BarChart(
            hours,
            ChartConfig(
                width=400,
                height=220,
                colors=['#ddeeff'],
                bottom_labels=labels,
                max_y_axis=hours_data.rooster,
                y_axis_max_ticks=5,
            ),
        )
        user_block = VBlock(
            [
                TextBlock(
                    f'{user} {hours_data.effectivity():.0f}%  / {hours_data.billable_perc():.0f}%', font_size=MID_SIZE
                ),
                chart,
            ]
        )
        grid.set_cell(row, col, user_block)
        col += 1
        if col == cols:
            col = 0
            row += 1

    page = Page(
        [
            TextBlock('Billable uren', HEADER_SIZE),
            TextBlock(
                'Billable uren per week het afgelopen halfjaar.<br/><br/>'
                + 'Grafiek toont uren gewerkt op billable projecten zonder rekening te houden met correcties.<br/>'
                + 'Percentage is na correcties.',
                color="gray",
            ),
            grid,
        ]
    )
    page.render(output_folder / 'billable.html')


if __name__ == '__main__':
    os.chdir('..')

    render_billable_page(get_output_folder())
