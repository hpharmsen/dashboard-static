import os
from pathlib import Path

from layout.basic_layout import HEADER_SIZE, MID_SIZE
from layout.block import Page, TextBlock, VBlock
from layout.chart import StackedBarChart, ChartConfig
from model.booked import booked
from model.utilities import Day, Period
from settings import get_output_folder, GREEN, BLUE, RED, ORANGE, GRAY, LIGHT_GRAY


def render_booked_page(output_folder: Path):
    periods = []
    until = Day().last_monday()
    for _ in range(3):
        start = until.plus_days(-7)
        periods += [Period(start, until)]
        until = start

    page_content = [
        VBlock(
            [
                TextBlock(f"Uren van week {period.fromday.week_number()}", MID_SIZE),
                booked_chart(period),
            ]
        )
        for period in periods
    ]

    page = Page([TextBlock("Geboekte uren", HEADER_SIZE)] + page_content)
    page.render(output_folder / "booked.html")


def booked_chart(period: Period):
    name_labels, series = booked(period)

    chartdata = series.values()
    chart_config = ChartConfig(
        horizontal=True,
        width=800,
        height=1200,
        colors=[GREEN, RED, BLUE, ORANGE, GRAY, LIGHT_GRAY],
        max_x_axis=50,
        labels=series.keys(),
        series_labels=name_labels,
    )
    return StackedBarChart(chartdata, chart_config)


if __name__ == "__main__":
    os.chdir("..")

    render_booked_page(get_output_folder())
