import math
import os
from pathlib import Path

from layout.basic_layout import headersize, midsize, defsize
from layout.block import Block, VBlock, HBlock, TextBlock, Page
from layout.table import Table, TableConfig
from layout.chart import StackedBarChart, ChartConfig, MultiScatterChart
from model.travelbase import BRANDS, get_bookings
from sources.database import get_db

CHART_COLORS = [['#6666cc', '#ddeeff'], ['#66cc66', '#eeffdd'], ['cc#6666', '#ffddee']]
BAR_COLORS = ['#6666cc', '#66cc66']  # ['cc#6666'


def render_travelbase_page(output_folder):
    bookings = get_bookings()
    totals = [(brand, bookings[brand].sum()) for brand in BRANDS]
    totals_table = Table(totals, TableConfig(aligns=['left', 'right'], formats=['', '0'], totals=[0, 1]))
    page = Page([TextBlock('Travelbase', headersize), chart(bookings, 600, 400), totals_table])

    page.render(output_folder / 'travelbase.html')


def scatterchart(data, width, height):
    # Get data from DB
    # db = get_db()
    # query = 'select `date`'
    # for brand in BRANDS:
    #     query += f", sum(if(trendline='travelbase_{brand}', value, 0)) as {brand} "
    # query += 'from trends where trendline like "travelbase%" group by `date`'
    # data = db.execute(query)

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


def chart(data, width, height):
    # Get data from DB
    # db = get_db()
    # query = 'select `date`'
    # for brand in BRANDS:
    #     query += f", sum(if(trendline='travelbase_{brand}', value, 0)) as {brand} "
    # query += 'from trends where trendline like "travelbase%" group by `date`'
    # data = db.execute(query)

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
        bottom_labels=data['week'].tolist(),  # [d.strftime('%Y-%m-%d') for d in data['day'].tolist()]
    )
    return StackedBarChart(chartdata, chart_config)


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.dirname(__file__)))
    render_travelbase_page(Path('/Users/hp/MT/Dashboard'))
