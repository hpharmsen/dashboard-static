import math
import os

import pandas as pd

from layout.basic_layout import HEADER_SIZE
from layout.block import TextBlock, Page
from layout.chart import StackedBarChart, ChartConfig, MultiScatterChart
from layout.table import Table, TableConfig
from model.travelbase import BRANDS, get_bookings_per_week
from settings import get_output_folder

CHART_COLORS = [
    ['#6666cc', '#ddeeff'],
    ['#66cc66', '#eeffdd'],
    ['#cc6666', '#ffddee'],
    ['#ccc66', '#ffffdd'],
    ['#cc66cc', '#ffddff'],
]
BAR_COLORS = ['#6666cc', '#66cc66', '#cc6666', '#cccc66', '#cc66cc']


def render_travelbase_page(output_folder):
    bookings = get_bookings_per_week(booking_type='bookings')
    if not isinstance(bookings, pd.DataFrame):
        return  # An error occurred, no use to proceed
    totals = [(brand, bookings[brand].sum()) for brand in BRANDS]
    totals_table = Table(totals, TableConfig(aligns=['left', 'right'], formats=['', '0'], totals=[0, 1]))
    page = Page(
        [
            TextBlock('Travelbase', HEADER_SIZE),
            TextBlock('Aantal boekingen per week. Weken lopen van maandag t/m zondag.', color='gray'),
            bar_chart(bookings, 600, 400),
            totals_table,
        ]
    )

    page.render(output_folder / 'travelbase.html')


def scatterchart(data, width, height):
    chartdata = []
    for brand_index in range(len(BRANDS)):
        xy = []
        for _, row in data.iterrows():
            x = row['day']
            y = 0
            for j in range(brand_index + 1):
                brand = BRANDS[j]
                y += row[brand]
            xy += [{'x': x, 'y': y}]
        chartdata += [xy]
    max_value = max([xy['y'] for xy in chartdata[-1]])
    max_value = 100 * math.ceil(max_value / 100)
    chart_config = ChartConfig(
        width=width,
        height=height,
        colors=CHART_COLORS,
        x_type='date',
        min_y_axis=0,
        max_y_axis=max_value,
        y_axis_max_ticks=5,
    )
    return MultiScatterChart(chartdata, chart_config)


def bar_chart(data, width, height):
    chartdata = []
    for brand in BRANDS:
        values = [int(row[brand]) for _, row in data.iterrows()]
        chartdata += [values]
    z = list(zip(*chartdata))
    max_value = max([sum(series) for series in zip(*chartdata)])
    max_value = 100 * math.ceil(max_value / 100)
    chart_config = ChartConfig(
        width=width,
        height=height,
        colors=BAR_COLORS,
        min_y_axis=0,
        max_y_axis=max_value,
        y_axis_max_ticks=5,
        labels=BRANDS,
        series_labels=data['week'].tolist(),
    )
    return StackedBarChart(chartdata, chart_config)


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.dirname(__file__)))
    render_travelbase_page(get_output_folder())
