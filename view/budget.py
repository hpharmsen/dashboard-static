import os
from layout.block import TextBlock, Page
from layout.table import Table, TableConfig
from layout.basic_layout import headersize
from model.budget import project_budget_status


def budget_status_coloring(row_index, col_index, value):
    if (col_index == 8 and value > 500) or (col_index == 9 and value >= 10):
        return '#CFC'
    if (col_index == 8 and value < -500) or (col_index == 9 and value <= -10):
        return '#FCC'
    return ''


def budget_status_hovering(row_index, col_index, values):
    if col_index == 6:
        if values[8] == 0:
            return 'In te vullen in pma'
        else:
            return values[8]


def render_budget_status_page():
    data = project_budget_status()
    page = Page(
        [
            TextBlock('Budget status', headersize),
            Table(
                data,
                TableConfig(
                    headers=[
                        'klant',
                        'project',
                        'pm',
                        'type',
                        'uren',
                        'budget',
                        'correctie',
                        'gefactureerd',
                        'verschil',
                        'percentueel',
                        'laatste factuur',
                    ],
                    aligns=[
                        'left',
                        'left',
                        'left',
                        'left',
                        'right',
                        'right',
                        'right',
                        'right',
                        'right',
                        'right',
                        'right',
                    ],
                    hide_columns=[0, 8, 10],
                    cell_coloring=budget_status_coloring,
                    row_linking=lambda l, v: f'https://oberview.oberon.nl/project/{v[0]}',
                    cell_hovering=budget_status_hovering,
                ),
            ),
        ]
    )
    #
    # headers = ['klant', 'openstaand', '<30 dg', '30-60 dg', '60-90 dg', '> 90 dg'],
    # aligns = ['left', 'right', 'right', 'right', 'right', 'right'],
    # formats = ['', '.', '.', '.', '.', '.'],
    # totals = [0, 1, 1, 1, 1, 1],
    # row_linking = lambda line, value: 'https://oberview.oberon.nl/facturen/openstaand'

    page.render('output/budget.html')


if __name__ == '__main__':
    os.chdir('..')
    render_budget_status_page()
