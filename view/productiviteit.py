import os
from layout.basic_layout import doFormat, headersize
from layout.block import HBlock, VBlock, TextBlock, Page
from layout.table import Table
from model.productiviteit import (
    productiviteit_overzicht,
    tuple_of_productie_users,
    productiviteit_persoon,
    user_target,
    user_target_now,
    billable_trend_person,
)
from layout.chart import ScatterChart


def render_productiviteit_page():
    tables = HBlock(
        [
            Table(
                productiviteit_overzicht(),
                id='overzicht',
                headers=[
                    'persoon',
                    'omzet',
                    'uren',
                    'per uur',
                    'geboekt',
                    'productief',
                    '% productief',
                    'billable',
                    '% billable',
                ],
                aligns=['left', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right'],
                formats=['', '€', '.', '€', '.', '.', '%', '.', '%'],
                totals=[0, 1, 1, 0, 1, 1, 0, 1, 0],
            )
        ]
    )

    for user in tuple_of_productie_users():
        data = productiviteit_persoon(user)
        target = user_target(user)
        if target:
            total = sum([row[3] for row in data])
            perc = (total / user_target_now(user) - 1) * 100
            percstr = doFormat(perc, '+%')
            targetstr = f'target: € {target:,.0f}'.replace(',', '.')
        else:
            targetstr = percstr = ''
        tables.add_block(
            Table(
                data,
                id='productiviteit_' + user,
                headers=[user, targetstr, percstr, 'omzet', 'uren', 'per uur'],
                aligns=['left', 'left', 'left', 'right', 'right', 'right'],
                formats=['', '', '', '€', '.', '€'],
                totals=[0, 0, 0, 1, 1, 0],
            )
        )

    page = Page(
        [TextBlock('Productiviteit', headersize), VBlock([TextBlock('Under construction', color='red'), tables])]
    )
    page.add_onloadcode('make_users_clickable();')
    page.render('output/productiviteit.html')

    for user in tuple_of_productie_users():
        productiviteit_table = Table(
            productiviteit_persoon(user),
            headers=[user, '', '', 'omzet', 'uren', 'per uur'],
            aligns=['left', 'left', 'left', 'right', 'right', 'right'],
            formats=['', '', '', '€', '.', '€'],
            totals=[0, 0, 0, 1, 1, 0],
        )

        chartdata = [{'x': rec['datum'].strftime('%Y-%m-%d'), 'y': rec['hours']} for rec in billable_trend_person(user)]
        chart = ScatterChart(
            400, 400, values=chartdata, color='#6666cc', fill_color='#ddeeff', y_start=0, x_type='date'
        )

        page = Page([TextBlock(f'Productiviteit {user}', headersize), chart, productiviteit_table])
        page.render(f'output/productiviteit_{user}.html')


if __name__ == '__main__':
    os.chdir('..')
    render_productiviteit_page()
