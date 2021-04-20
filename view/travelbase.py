import math
import os
from pathlib import Path

from layout.basic_layout import headersize
from layout.block import TextBlock, Page
from layout.table import Table, TableConfig
from layout.chart import StackedBarChart, ChartConfig, MultiScatterChart
from model.travelbase import BRANDS, get_bookings_per_week, update_bookings_per_day

CHART_COLORS = [['#6666cc', '#ddeeff'], ['#66cc66', '#eeffdd'], ['#cc6666', '#ffddee'], ['#ccc66', '#ffffdd']]
BAR_COLORS = ['#6666cc', '#66cc66', '#cc6666', '#cccc66']


def render_travelbase_page(output_folder):
    update_bookings_per_day()
    bookings = get_bookings_per_week()
    totals = [(brand, bookings[brand].sum()) for brand in BRANDS]
    totals_table = Table(totals, TableConfig(aligns=['left', 'right'], formats=['', '0'], totals=[0, 1]))
    page = Page(
        [
            TextBlock('Travelbase', headersize),
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
    max_value = max([max(series) for series in chartdata])
    max_value = 100 * math.ceil(max_value / 100)
    chart_config = ChartConfig(
        width=width,
        height=height,
        colors=BAR_COLORS,
        min_y_axis=0,
        max_y_axis=max_value,
        y_axis_max_ticks=5,
        labels=BRANDS,
        bottom_labels=data['week'].tolist(),
    )
    return StackedBarChart(chartdata, chart_config)


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.dirname(__file__)))
    render_travelbase_page(Path('/Users/hp/MT/Dashboard'))
