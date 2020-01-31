import os
from layout.basic_layout import midsize, headersize
from layout.block import VBlock, TextBlock, Page
from model.trendline import trends


def render_tmp():

    chart = trends.chart('billable', 100, 60)

    billable = VBlock([TextBlock('Billable', midsize), chart])

    page = Page([TextBlock('Trends', headersize), billable])

    page.render('output/tmp.html')


if __name__ == '__main__':
    os.chdir('..')
    render_tmp()
