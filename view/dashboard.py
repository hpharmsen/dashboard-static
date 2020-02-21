import os
import datetime
from dateutil.relativedelta import relativedelta

from model.caching import load_cache
from layout.block import TextBlock, Page, VBlock, HBlock, Grid
from layout.table import Table, TableConfig
from layout.chart import StackedBarChart, ScatterChart, ChartConfig
from layout.basic_layout import defsize, midsize, headersize
from model.organisatie import aantal_mensen, aantal_fte, aantal_fte_begroot
from model.productiviteit import (
    productiviteit_perc_productie,
    productiviteit_perc_iedereen,
    billable_perc_productie,
    billable_perc_iedereen,
)
from model.resultaat import (
    omzet_begroot,
    omzet_verschil_percentage,
    winst_begroot,
    winst_werkelijk,
    winst_verschil,
    top_x_klanten_laatste_zes_maanden,
    update_omzet_per_week,
    debiteuren_30_60_90,
    toekomstige_omzet_per_week,
    opbrengsten,
)
from model.sales import sales_waarde, werk_in_pijplijn, top_x_sales
from model.trendline import trends


def render_dashboard():

    page = Page(
        [
            HBlock(
                [
                    VBlock([sales_block(), klanten_block()]),
                    VBlock([resultaat_block(), pijplijn_block(), organisatie_block()]),
                    VBlock([productiviteit_block(), billable_chart(), omzet_chart(), omzet_prognose_chart()]),
                    VBlock([rocks_block(), debiteuren_block()]),
                ]
            )
        ]
    )

    page.render('output/dashboard.html')
    page.render('output/limited/dashboard.html', limited=True)


######### Kolom 1: Sales + Klanten ###########


def sales_block():
    sales = VBlock(
        [
            TextBlock('Sales', headersize),
            TextBlock('saleswaarde', defsize, color='gray', padding=10),
            TextBlock(
                sales_waarde(), headersize, format='K', tooltip='Som van openstaande trajecten<br/>maal hun kans.'
            ),
            trends.chart('sales_waarde', 250, 150, min_y_axis=0),
            TextBlock('Top 5 sales kansen', midsize),
            Table(top_x_sales(5), TableConfig(headers=[], aligns=['left', 'right'], formats=['', '€'])),
        ],
        'sales.html',
    )
    return sales


def klanten_block():
    # Risico
    klanten = VBlock(
        [
            TextBlock('Klanten', midsize),
            TextBlock('Top 3 klanten laatste 6 maanden', defsize, padding=10, color='gray'),
            Table(
                top_x_klanten_laatste_zes_maanden(3),
                TableConfig(headers=[], aligns=['left', 'right', 'right'], formats=['', '€', '%'], totals=[0, 0, 1]),
            ),
        ],
        'clients.html',
    )
    return klanten


######### Kolom 2: Resultaat + Organisatie ###########


def resultaat_block():
    def winst_coloring(value):
        return 'green' if value > 10 else 'red' if value < -20 else 'black'

    resultaat = VBlock(
        [
            TextBlock('Resultaat', headersize),
            TextBlock('Omzet', defsize, color='gray', padding=10, limited=False),
            HBlock(
                [
                    VBlock(
                        [
                            TextBlock('Begroot', defsize, color='gray', padding=5, limited=False),
                            TextBlock('Werkelijk', defsize, color='gray', limited=False),
                        ]
                    ),
                    VBlock(
                        [
                            TextBlock(omzet_begroot(), defsize, format='K', padding=5, limited=False),
                            TextBlock(opbrengsten(), defsize, format='K', limited=False),
                        ]
                    ),
                    TextBlock(omzet_verschil_percentage(), midsize, format='+%', limited=False),
                ]
            ),
            TextBlock('Winst', defsize, color='gray', padding=10, limited=True),
            VBlock(
                [
                    HBlock(
                        [
                            VBlock(
                                [
                                    TextBlock('Begroot', defsize, color='gray', padding=5, limited=True),
                                    TextBlock('Werkelijk', defsize, color='gray', limited=True),
                                ]
                            ),
                            VBlock(
                                [
                                    TextBlock(winst_begroot(), defsize, format='K', padding=5, limited=True),
                                    TextBlock(winst_werkelijk(), defsize, format='K', limited=True),
                                ]
                            ),
                            TextBlock(winst_verschil(), midsize, format='+K', color=winst_coloring, limited=True),
                        ]
                    )
                ]
            ),
        ],
        link="resultaat_berekening.html",
    )
    return resultaat


def pijplijn_block():
    pijplijn = VBlock(
        [
            TextBlock('In de pijplijn', defsize, padding=10, color='gray'),
            TextBlock(
                werk_in_pijplijn(),
                headersize,
                format='K',
                tooltip='Werk dat binnengehaald is maar nog niet uitgevoerd.',
            ),
            trends.chart('werk_in_pijplijn', 250, 150, min_y_axis=0),
        ]
    )
    return pijplijn


def organisatie_block():
    fte = aantal_fte()
    fte_begroot = aantal_fte_begroot()
    fte_color = 'black' if fte_begroot - fte < 1 else 'red'
    organisatie = VBlock(
        [
            TextBlock('Organisatie', headersize),
            HBlock(
                [
                    VBlock(
                        [
                            TextBlock('Aantal mensen', defsize, padding=5, color='gray'),
                            TextBlock(aantal_mensen(), midsize, format='.5'),
                        ]
                    ),
                    VBlock(
                        [
                            TextBlock('Aantal FTE', defsize, padding=5, color='gray'),
                            TextBlock(fte, midsize, color=fte_color, format='.5'),
                            TextBlock('Begroot', defsize, padding=5, color='gray'),
                            TextBlock(fte_begroot, midsize, color='gray', format='.5'),
                        ]
                    ),
                ]
            ),
        ]
    )
    return organisatie


######### Kolom 3: Productiviteit ###########


def productiviteit_block():

    # Productiviteit is: max aantal werkuren (contract minus verlof en feestdagen) * 85%
    def productivity_coloring(value):
        # Volgens Simplicate > 75% is goed (rood), >70% is redelijk, >65 is break even, <65% is verlies
        return 'green' if value > 75 else 'red' if value < 68 else 'black'

    lastmonth = datetime.date.today() - datetime.timedelta(days=30)

    productiviteit_perc_productie_block = TextBlock(
        productiviteit_perc_productie(lastmonth),
        midsize,
        format='%',
        tooltip='''Percentage van geboekte uren door productiemensen (dat is ex. office,
                       recruitment, MT) op productietaken zoals FE, Non-billable, PM of Testing.  Laatste maand.''',
        color=productivity_coloring,
    )

    billable_perc_productie_block = TextBlock(
        billable_perc_productie(lastmonth),
        midsize,
        format='%',
        tooltip='''Percentage van geboekte uren door productiemensen (ex. office,
                       recruitment, MT) op billable taken zoals FE, PM of Testing. Laatste maand.''',
    )
    productiviteit_perc_iedereen_block = TextBlock(
        productiviteit_perc_iedereen(lastmonth),
        midsize,
        format='%',
        tooltip='''Percentage van geboekte uren door het hele team op productietaken
                       zoals FE, Non-billable, PM of Testing. Laatste maand.''',
        color=productivity_coloring,
    )

    billable_perc_iedereen_block = TextBlock(
        billable_perc_iedereen(lastmonth),
        midsize,
        format='%',
        tooltip='''Percentage van geboekte uren door het hele team op billable taken
                       zoals FE, Non-billable, PM of Testing. Laatste maand.''',
    )

    return VBlock(
        [
            TextBlock('Productiviteit', headersize),
            HBlock(
                [
                    TextBlock('&nbsp', defsize, padding=90, color='gray'),
                    TextBlock('productief', defsize, color='gray'),
                    TextBlock('Billable', defsize, color='gray'),
                ]
            ),
            HBlock(
                [
                    TextBlock('Productie', defsize, padding=40, color='gray'),
                    productiviteit_perc_productie_block,
                    billable_perc_productie_block,
                ]
            ),
            HBlock(
                [
                    TextBlock('Hele team', defsize, padding=38, color='gray'),
                    productiviteit_perc_iedereen_block,
                    billable_perc_iedereen_block,
                ]
            ),
        ]
    )


def six_months_ago():
    return (datetime.date.today() - relativedelta(months=6)).strftime('%Y-%m-%d')


def billable_chart():
    return VBlock(
        [
            TextBlock('Billable, hele team, laatste 6 maanden', defsize, color='gray'),
            trends.chart('billable_hele_team', 250, 150, x_start=six_months_ago()),
        ]
    )


def omzet_chart():
    # Behaalde omzet per week
    update_omzet_per_week()
    return VBlock(
        [
            TextBlock('Omzet per week, laatste zes maanden...', defsize, color='gray', limited=False),
            trends.chart('omzet_per_week', 250, 150, x_start=six_months_ago(), min_y_axis=0, max_y_axis=60000),
        ]
    )


def omzet_prognose_chart():
    # En in de toekomst
    six_months_from_now = datetime.date.today() + relativedelta(months=6)
    xy = [
        {'x': a['monday'], 'y': a['weekturnover']}
        for a in toekomstige_omzet_per_week()
        if a['monday'] <= six_months_from_now
    ]
    return VBlock(
        [
            TextBlock('...en de komende zes', defsize, color='gray', limited=False),
            ScatterChart(
                xy,
                ChartConfig(
                    width=250, height=150, colors=['#6666cc', '#ddeeff'], x_type='date', min_y_axis=0, max_y_axis=60000
                ),
            ),
        ]
    )


######### Kolom 4: Rocks + Debiteuren ###########


def rocks_block():
    def rocks_row(owner, rock, status):
        return [TextBlock(owner, color='green'), TextBlock(rock), TextBlock('⬤', color=status)]

    rocks_grid = Grid(cols=3)
    rocks_grid.add_row(rocks_row('Gert', '1. CTO rol "technische standaardisatie" beleggen.', 'red'))
    rocks_grid.add_row(rocks_row('Gert', '2. Nieuwe pand bekend', 'orange'))
    rocks_grid.add_row(rocks_row('RdB', '3. Salesconcept (open source, Oberon, maatwerk)', 'red'))
    rocks_grid.add_row(rocks_row('HPH', '4. Qikker Ja mits / Nee beslissing', 'orange'))

    return VBlock([TextBlock('Q1 Rocks', headersize), rocks_grid], limited=True)


def debiteuren_block():
    return VBlock(
        [
            TextBlock('Debiteuren', midsize),
            StackedBarChart(
                debiteuren_30_60_90(),
                ChartConfig(
                    width=240,
                    height=470,
                    labels=['<30 dg', '30-60 dg', '60-90 dg', '> 90 dg'],
                    colors=['#7C7', '#FD0', '#FFA500', '#c00'],
                    max_y_axis=350000,
                ),
            ),
        ],
        link='debiteuren.html',
    )


# def project_type_chart():
#     # Omzet per type project pie chart
#     data = omzet_per_type_project()
#     project_types = data['project_type'].tolist()
#     project_turnovers = omzet_per_type_project()['turnover'].tolist()
#     return PieChart(
#         260, 520, 'omzet per type project', project_types, project_turnovers, ['#55C', '#C55', '#5C5', '#555', '#5CC']
#     )
#
#
# def product_type_chart():
#     # Omzet per product pie chart
#     product_types = omzet_per_type_product()['product_type'].tolist()
#     product_turnovers = omzet_per_type_product()['turnover'].tolist()
#     return PieChart(
#         240, 520, 'omzet per product', product_types, product_turnovers, ['#5c5', '#C55', '#55C', '#555', '#5CC']
#     )


if __name__ == '__main__':
    os.chdir('..')
    load_cache()
    render_dashboard()
