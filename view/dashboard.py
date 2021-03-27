import json
import os
import datetime
import urllib
from dateutil.relativedelta import relativedelta

from model.caching import load_cache
from layout.block import TextBlock, Page, VBlock, HBlock, Grid
from layout.table import Table, TableConfig
from layout.chart import StackedBarChart, ScatterChart, ChartConfig
from layout.basic_layout import defsize, midsize, headersize
from model.organisatie import aantal_mensen, aantal_fte, aantal_fte_begroot, verzuimpercentage, vrije_dagen_pool
from model.productiviteit import (
    productiviteit_perc_productie,
    productiviteit_perc_iedereen,
    billable_perc_productie,
    billable_perc_iedereen,
    percentage_directe_werknemers,
    corrections_last_month,
    corrections_percentage,
)
from model.resultaat import (
    omzet_begroot,
    omzet_werkelijk,
    omzet_verschil_percentage,
    winst_begroot,
    winst_werkelijk,
    winst_verschil,
    top_x_klanten_laatste_zes_maanden,
    update_omzet_per_week,
    vulling_van_de_planning,
)
from model.finance import debiteuren_30_60_90_yuki, gemiddelde_betaaltermijn
from model.sales import sales_waarde, werk_in_pijplijn, top_x_sales
from model.travelbase import get_bookings, BRANDS
from model.trendline import trends
from view.travelbase import scatterchart as travelbase_scatterchart

GREEN = 'green'  #'#7C7'
YELLOW = '#FD0'
ORANGE = '#FFA500'
RED = '#c00'
BLACK = '#000'
GRAY = 'gray'


def dependent_color(value, red_treshold, green_treshold):
    # Returns color GREEN, BLACK, RED depending on value
    if red_treshold < green_treshold:
        return RED if value < red_treshold else GREEN if value > green_treshold else BLACK
    else:
        return RED if value > red_treshold else GREEN if value < green_treshold else BLACK


def render_dashboard(output_folder):
    page = Page([HBlock([commerce_block(), operations_block(), finance_block(), hr_block()])])
    page.render(output_folder / 'dashboard.html')


######### Kolom 1: Commerce ###########


def commerce_block():
    sales_waarde_value = sales_waarde()
    sales_waarde_color = dependent_color(sales_waarde_value, 200000, 300000)
    commerce = VBlock(
        [
            TextBlock('Commerce', headersize),
            TextBlock('saleswaarde', midsize, padding=10),
            TextBlock(
                sales_waarde_value,
                headersize,
                format='K',
                color=sales_waarde_color,
                tooltip='Som van openstaande trajecten<br/>maal hun kans.',
            ),
            trends.chart('sales_waarde', 250, 150, min_y_axis=0, x_start=six_months_ago()),
            VBlock(
                [
                    TextBlock('Top 5 sales kansen', midsize),
                    Table(top_x_sales(5), TableConfig(headers=[], aligns=['left', 'right'], formats=['', '€'])),
                ],
                link='sales.html',
            ),
            # klanten_block()
            travelbase_block(),
        ]
    )
    return commerce


def klanten_block():
    klanten = VBlock(
        [
            TextBlock('Klanten', midsize),
            TextBlock('Top 3 klanten laatste 6 maanden', defsize, padding=10, color=GRAY),
            Table(
                top_x_klanten_laatste_zes_maanden(3),
                TableConfig(headers=[], aligns=['left', 'right', 'right'], formats=['', '€', '%'], totals=[0, 0, 1]),
            ),
        ],
        link='clients.html',
    )
    return klanten


def travelbase_block():
    bookings = get_bookings()
    legend = ', '.join([f'{brand}: {int(bookings[brand].sum())}' for brand in BRANDS])
    return VBlock(
        [
            TextBlock('Travelbase', midsize),
            TextBlock('Aantal boekingen per week', color=GRAY),
            travelbase_scatterchart(bookings, 250, 180),
            TextBlock(legend),
        ],
        link='travelbase.html',
    )


######### Kolom 2: Operations ###########


def operations_block():
    return VBlock(
        [
            TextBlock('Operations', headersize),
            productiviteit_block(),
            billable_chart(),
            planning_chart(),
            corrections_block(),
        ]
    )


def productiviteit_block():

    # Productiviteit is: max aantal werkuren (contract minus verlof en feestdagen) * 85%
    productivity_coloring = lambda value: dependent_color(value, 68, 75)
    # Volgens Simplicate > 75% is goed (groen), >70% is redelijk, >65 is break even, <65% is verlies

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
            TextBlock('Productiviteit', midsize),
            HBlock(
                [
                    TextBlock('&nbsp', defsize, padding=90, color=GRAY),
                    TextBlock('productief', defsize, color=GRAY),
                    TextBlock('Billable', defsize, color=GRAY),
                ]
            ),
            HBlock(
                [
                    TextBlock(
                        f'Productie ({int(percentage_directe_werknemers())}%)',
                        defsize,
                        padding=0,
                        color=GRAY,
                        tooltip='DDA noemt dit directe werknemers. Daar is het gemiddeld 86% van het werknemersbestand.',
                    ),
                    productiviteit_perc_productie_block,
                    billable_perc_productie_block,
                ]
            ),
            HBlock(
                [
                    TextBlock('Hele team', defsize, padding=38, color=GRAY),
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
            TextBlock('Billable, hele team, laatste 6 maanden', defsize, color=GRAY),
            trends.chart('billable_hele_team', 250, 150, x_start=six_months_ago()),
        ]
    )


def planning_chart():
    # Vulling van de planning uit de planning database
    six_months_from_now = datetime.date.today() + relativedelta(months=6)
    six_months_from_now_str = six_months_from_now.strftime('%Y-%m-%d')
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    xy = [{'x': a['monday'], 'y': a['filled']} for a in vulling_van_de_planning()]
    return VBlock(
        [
            TextBlock('Planning', midsize),
            TextBlock(f'Percentage gevuld met niet interne projecten<br/>de komende {len(xy)} weken.', color=GRAY),
            ScatterChart(
                xy,
                ChartConfig(
                    width=250,
                    height=150,
                    colors=['#6666cc', '#ddeeff'],
                    x_type='int',
                    min_x_axis=xy[0]['x'],
                    max_x_axis=xy[-2]['x'],
                    min_y_axis=0,
                    max_y_axis=100,
                ),
            ),
        ]
    )


def pijplijn_block():
    return None  # Moet nog uit Simplicate komen
    in_pijplijn_value = werk_in_pijplijn()
    in_pijplijn_color = dependent_color(in_pijplijn_value, 350000, 500000)
    pijplijn = VBlock(
        [
            TextBlock('In de pijplijn', defsize, padding=10, color=GRAY),
            TextBlock(
                in_pijplijn_value,
                headersize,
                color=in_pijplijn_color,
                format='K',
                tooltip='Werk dat binnengehaald is maar nog niet uitgevoerd.',
            ),
            trends.chart('werk_in_pijplijn', 250, 150, min_y_axis=0, x_start=six_months_ago()),
        ]
    )
    return pijplijn


def corrections_block():
    def corrections_percentage_coloring(value):
        return dependent_color(value, red_treshold=4.9, green_treshold=2)

    result = VBlock(
        [
            TextBlock('Correcties', midsize),
            HBlock(
                [
                    TextBlock(corrections_percentage(), midsize, format='%', color=corrections_percentage_coloring),
                    TextBlock('correcties op uren<br/>tussen 1 week geleden<br/>en 5 weken geleden.', color=GRAY),
                ],
                padding=70,
            ),
        ],
        link='corrections.html',
    )
    return result


######### Kolom 3: Finance ###########


def finance_block():
    return VBlock([TextBlock('Finance', headersize), resultaat_block(), omzet_chart(), debiteuren_block()])


def resultaat_block():
    winst_coloring = lambda value: dependent_color(value, -20, 10)
    winst_percentage = int(winst_werkelijk() / omzet_werkelijk() * 100)
    winst_percentage_coloring = lambda value: dependent_color(value, 10, 15)
    resultaat = VBlock(
        [
            TextBlock('Resultaat', midsize),
            TextBlock('Omzet', defsize, color='gray', padding=10),
            HBlock(
                [
                    VBlock(
                        [
                            TextBlock('Begroot', defsize, color='gray', padding=5),
                            TextBlock('Werkelijk', defsize, color='gray'),
                        ]
                    ),
                    VBlock(
                        [
                            TextBlock(omzet_begroot(), defsize, format='K', padding=5),
                            TextBlock(omzet_werkelijk(), defsize, format='K'),
                        ]
                    ),
                    TextBlock(omzet_verschil_percentage(), midsize, format='+%'),
                ]
            ),
            TextBlock('Winst', defsize, color='gray', padding=10),
            # TextBlock('Tijdelijk niet beschikbaar', defsize, color='gray', padding=10),
            VBlock(
                [
                    HBlock(
                        [
                            VBlock(
                                [
                                    TextBlock('Begroot', defsize, color='gray', padding=5),
                                    TextBlock('Werkelijk', defsize, color='gray'),
                                ]
                            ),
                            VBlock(
                                [
                                    TextBlock(winst_begroot(), defsize, format='K', padding=5),
                                    TextBlock(winst_werkelijk(), defsize, format='K'),
                                ]
                            ),
                            TextBlock(winst_verschil(), midsize, format='+K', color=winst_coloring),
                        ]
                    ),
                    HBlock(
                        [
                            TextBlock('Winstpercentage', color=GRAY, padding=5),
                            TextBlock(
                                winst_percentage,
                                format='%',
                                color=winst_percentage_coloring,
                                tooltip='Gemiddeld bij DDA in 2019: 7%, high performers: 16%',
                            ),
                        ]
                    ),
                ]
            ),
        ],
        link="resultaat_berekening.html",
    )
    return resultaat


def omzet_chart():
    # Behaalde omzet per week
    update_omzet_per_week()
    return VBlock(
        [
            TextBlock('Omzet per week, laatste 6 maanden...', defsize, color=GRAY),
            trends.chart('omzet_per_week', 250, 150, x_start=six_months_ago(), min_y_axis=0, max_y_axis=80000),
        ],
        link='billable.html',
    )


def debiteuren_block():
    betaaltermijn = gemiddelde_betaaltermijn()
    betaaltermijn_color = dependent_color(betaaltermijn, 45, 30)
    return VBlock(
        [
            # TextBlock('Debiteuren uit Oberview', midsize),
            # TextBlock('Betaaltermijn in dagen', defsize, color=GRAY, padding=12),
            # TextBlock(
            #     round(betaaltermijn, 0),
            #     midsize,
            #     color=betaaltermijn_color,
            #     tooltip='Gemiddeld bij DDA in 2019: 40 dagen',
            # ),
            # StackedBarChart(
            #     debiteuren_30_60_90_extranet(),
            #     ChartConfig(
            #         width=240,
            #         height=470,
            #         labels=['<30 dg', '30-60 dg', '60-90 dg', '> 90 dg'],
            #         colors=[GREEN, YELLOW, ORANGE, RED],
            #         max_y_axis=450000,
            #     ),
            # ),
            TextBlock('Debiteuren (Yuki)', midsize),
            StackedBarChart(
                debiteuren_30_60_90_yuki(),
                ChartConfig(
                    width=240,
                    height=400,
                    labels=['<30 dg', '30-60 dg', '60-90 dg', '> 90 dg'],
                    colors=[GREEN, YELLOW, ORANGE, RED],
                    max_y_axis=450000,
                ),
            ),
        ],
        link='debiteuren.html',
    )


######### Kolom 4: HR ###########


def hr_block():
    return VBlock(
        [TextBlock('HR', headersize), team_block(), tevredenheid_block(), verzuim_block(), vakantiedagen_block()]
    )


def team_block():
    fte = aantal_fte()
    fte_begroot = aantal_fte_begroot()

    return VBlock(
        [
            TextBlock('Team', midsize),
            HBlock(
                [
                    VBlock(
                        [
                            TextBlock('Aantal mensen', defsize, padding=5, color=GRAY),
                            TextBlock(aantal_mensen(), midsize, format='.5'),
                        ]
                    ),
                    VBlock(
                        [
                            TextBlock('Aantal FTE', defsize, padding=5, color=GRAY),
                            TextBlock(fte, midsize, color=dependent_color(fte_begroot - fte, 1, -1), format='.5'),
                            # TextBlock('Begroot', defsize, padding=5, color=GRAY),
                            # TextBlock(fte_begroot, midsize, color=GRAY, format='.5'),
                        ]
                    ),
                ]
            ),
        ]
    )


def verzuim_block():

    verzuim = verzuimpercentage()
    verzuim_color = dependent_color(verzuim, 3, 1)
    return VBlock(
        [
            TextBlock('Verzuim', midsize),
            TextBlock('Verzuimpercentage de laatste 3 maanden', defsize, color=GRAY),
            TextBlock(verzuim, midsize, format='%1', color=verzuim_color, tooltip='Gemiddeld bij DDA in 2019: 3.0%'),
        ]
    )


def vakantiedagen_block():
    pool = vrije_dagen_pool()
    pool_color = dependent_color(pool, 10, 2)
    return VBlock(
        [
            TextBlock('Vrije dagen pool', midsize, padding=5),
            TextBlock(
                'Aantal dagen dat eigenlijk al opgemaakt<br/>had moeten worden maar dat niet is.', defsize, color=GRAY
            ),
            HBlock(
                [
                    TextBlock(pool, midsize, format='.1', color=pool_color),
                    TextBlock('dagen/fte', color=GRAY, padding=0),
                ],
                link='freedays.html',
            ),
        ]
    )


def tevredenheid_block():
    return None  # VBlock([TextBlock('Happiness', midsize), TextBlock('Data nodig...', color=GRAY)])


######### Kolom 4: Rocks + Debiteuren ###########


def rocks_block():
    def rocks_row(owner, rock):
        return [TextBlock(owner, color=GREEN), TextBlock(rock)]

    rocks_grid = Grid(cols=3)
    rocks_grid.add_row(rocks_row('HPH', '1. Verhuizen'))
    rocks_grid.add_row(rocks_row('HPH', '2. Qikker def. besluit'))
    rocks_grid.add_row(rocks_row('Martijn', '3. Marketing vol op gang'))
    rocks_grid.add_row(rocks_row('Gert', '4. Zomertijd nuttig inzetten'))
    rocks_grid.add_row(rocks_row('RdB', '5. TOR live'))

    return VBlock([TextBlock('Q3 Rocks', headersize), rocks_grid])


def corona_block():
    corona_url = 'https://coronadashboard.rijksoverheid.nl/json/NL.json'
    corona_besmet = '-'
    corona_color = RED
    reproduction_index = '-'
    reproduction_color = RED
    format = None
    try:
        with urllib.request.urlopen(corona_url) as f:
            corona_json = json.load(f)
        corona_besmet = corona_json['infectious_people_count']['last_value']['infectious_avg']
        if corona_besmet == None:
            # Soms is avg None, dan rekenen we het zelf uit
            corona_besmet = (
                corona_json['infectious_people_count']['last_value']['infectious_high']
                + corona_json['infectious_people_count']['last_value']['infectious_low']
            ) / 2
        corona_color = dependent_color(corona_besmet, 3600, 1200)
        reproduction_index = corona_json['reproduction_index_last_known_average']['last_value'][
            'reproduction_index_avg'
        ]
        if reproduction_index == None:
            reproduction_index = '-'
        reproduction_color = dependent_color(reproduction_index, 1, 0.75)
        format = '.2'
    except:
        pass
    return VBlock(
        [
            TextBlock('Corona', headersize),
            TextBlock('Geschat aantal met Corona besmette mensen in Nederland', defsize, padding=5, color=GRAY),
            TextBlock(corona_besmet, midsize, color=corona_color),
            TextBlock('Reproductie index', defsize, padding=5, color=GRAY),
            TextBlock(reproduction_index, midsize, format=format, color=reproduction_color),
        ]
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
