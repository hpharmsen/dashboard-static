import os
import datetime
from dateutil.relativedelta import relativedelta

from model.caching import load_cache
from layout.block import TextBlock, Block, Table, Page
from layout.chart import StackedBarChart, ScatterChart
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
    omzet_werkelijk,
    omzet_verschil_percentage,
    winst_begroot,
    winst_werkelijk,
    winst_verschil,
    top_x_klanten_laatste_zes_maanden,
    update_omzet_per_week,
    debiteuren_30_60_90,
    toekomstige_omzet_per_week)
from model.sales import sales_waarde, werk_in_pijplijn, top_x_sales
from model.trendline import trends


def sales_block():
    sales = Block()
    sales.add_absolute_block(5, 5, TextBlock('Sales', headersize))
    sales.add_absolute_block(5, 75, TextBlock('saleswaarde', defsize, color='gray'))
    sales.add_absolute_block(
        100,
        65,
        TextBlock(sales_waarde(), headersize, format='K', tooltip='Som van openstaande trajecten<br/>maal hun kans.'),
    )
    sales.add_absolute_block(5, 135, trends.chart('sales_waarde', 250, 150, y_start=0))

    # Belangrijkste sales opportunities
    sales.add_absolute_block(5, 290, TextBlock('Top 5 sales kansen', midsize))
    sales.add_absolute_block(
        5, 330, Table(top_x_sales(5), headers=[], aligns=['left', 'right'], formats=['', '€']), 'sales.html',
    )
    return sales


def productiviteit_block():

    productiviteit = Block()
    productiviteit.add_absolute_block(5, 5, TextBlock('Productiviteit', headersize))
    productiviteit.add_absolute_block(5, 115, TextBlock('productief', defsize, color='gray'))
    productiviteit.add_absolute_block(5, 165, TextBlock('Billable', defsize, color='gray'))
    productiviteit.add_absolute_block(90, 80, TextBlock('Productie', defsize, color='gray'))
    productiviteit.add_absolute_block(170, 80, TextBlock('Hele team', defsize, color='gray'))

    # Productiviteit is: max aantal werkuren (contract minus verlof en feestdagen) * 85%
    def productivity_coloring(value):
        # Volgens Simplicate > 75% is goed (rood), >70% is redelijk, >65 is break even, <65% is verlies
        return 'green' if value > 75 else 'red' if value < 68 else 'black'

    lastmonth = datetime.date.today() - datetime.timedelta(days=30)
    productiviteit.add_absolute_block(
        90,
        110,
        TextBlock(
            productiviteit_perc_productie(lastmonth),
            midsize,
            format='%',
            tooltip='''Percentage van geboekte uren door productiemensen (dat is ex. office,
                       recruitment, MT) op productietaken zoals FE, Non-billable, PM of Testing.  Laatste maand.''',
            color=productivity_coloring,
        ),
    )
    productiviteit.add_absolute_block(
        90,
        160,
        TextBlock(
            billable_perc_productie(lastmonth),
            midsize,
            format='%',
            tooltip='''Percentage van geboekte uren door productiemensen (ex. office,
                       recruitment, MT) op billable taken zoals FE, PM of Testing. Laatste maand.''',
        ),
    )
    productiviteit.add_absolute_block(
        170,
        110,
        TextBlock(
            productiviteit_perc_iedereen(lastmonth),
            midsize,
            format='%',
            tooltip='''Percentage van geboekte uren door het hele team op productietaken
                       zoals FE, Non-billable, PM of Testing. Laatste maand.''',
            color=productivity_coloring,
        ),
    )
    productiviteit.add_absolute_block(
        170,
        160,
        TextBlock(
            billable_perc_iedereen(lastmonth),
            midsize,
            format='%',
            tooltip='''Percentage van geboekte uren door het hele team op billable taken
                       zoals FE, Non-billable, PM of Testing. Laatste maand.''',
        ),
    )

    six_months_ago = (datetime.date.today() - relativedelta(months=6)).strftime('%Y-%m-%d')
    six_months_from_now = (datetime.date.today() + relativedelta(months=6))

    productiviteit.add_absolute_block(
        5, 230, TextBlock('Billable, hele team, laatste 6 maanden', defsize, color='gray')
    )
    productiviteit.add_absolute_block(
        5, 250, trends.chart('billable_hele_team', 250, 150, x_start=six_months_ago)
    )

    # Behaalde omzet per week
    update_omzet_per_week()
    productiviteit.add_absolute_block(
        5,
        430,
        TextBlock('Omzet per week, laatste zes maanden...', defsize, color='gray', limited=False)
    )
    productiviteit.add_absolute_block(
        5, 450, trends.chart('omzet_per_week', 250, 150, x_start=six_months_ago, y_start=0)
    )

    # En in de toekomst
    productiviteit.add_absolute_block(
        5,
        600,
        TextBlock('...en de komende zes', defsize, color='gray', limited=False)
    )
    xy = [{'x': a['monday'], 'y': a['weekturnover']} for a in toekomstige_omzet_per_week() if a['monday']<=six_months_from_now]
    future_turnover_chart = ScatterChart(
        250, 150, value=xy, color='#6666cc', fill_color='#ddeeff', x_type='date', y_start=0
    )
    productiviteit.add_absolute_block(
        5, 620, future_turnover_chart
    )


    return productiviteit


def resultaat_block():
    resultaat = Block(bg_color='light gray')
    resultaat.add_absolute_block(5, 5, TextBlock('Resultaat', headersize))

    resultaat.add_absolute_block(5, 65, TextBlock('Omzet', defsize, color='gray', limited=False))
    resultaat.add_absolute_block(5, 90, TextBlock('Begroot', defsize, color='gray', limited=False))
    resultaat.add_absolute_block(90, 90, TextBlock(omzet_begroot(), defsize, format='K', limited=False))
    resultaat.add_absolute_block(5, 110, TextBlock('Werkelijk', defsize, color='gray', limited=False))
    resultaat.add_absolute_block(90, 110, TextBlock(omzet_werkelijk(), defsize, format='K', limited=False))
    resultaat.add_absolute_block(140, 90, TextBlock(omzet_verschil_percentage(), midsize, format='+%', limited=False))

    def winst_coloring(value):
        return 'green' if value > 10 else 'red' if value < -20 else 'black'

    resultaat.add_absolute_block(5, 65 + 80, TextBlock('Winst', defsize, color='gray', limited=True))
    resultaat.add_absolute_block(5, 90 + 80, TextBlock('Begroot', defsize, color='gray', limited=True))
    resultaat.add_absolute_block(90, 90 + 80, TextBlock(winst_begroot(), defsize, format='K', limited=True))
    resultaat.add_absolute_block(5, 110 + 80, TextBlock('Werkelijk', defsize, color='gray', limited=True))
    resultaat.add_absolute_block(90, 110 + 80, TextBlock(winst_werkelijk(), defsize, format='K', limited=True))
    resultaat.add_absolute_block(
        140, 90 + 80, TextBlock(winst_verschil(), midsize, format='+K', color=winst_coloring, limited=True)
    )

    return resultaat


def pijplijn_block():
    pijplijn = Block()
    pijplijn.add_absolute_block(5, 10, TextBlock('in de pijplijn', defsize, color='gray'))
    pijplijn.add_absolute_block(
        100,
        0,
        TextBlock(
            werk_in_pijplijn(), headersize, format='K', tooltip='Werk dat binnengehaald is maar nog niet uitgevoerd.',
        ),
    )
    pijplijn.add_absolute_block(5, 75, trends.chart('werk_in_pijplijn', 250, 150, y_start=0))
    return pijplijn


# a = aantal_fte()
# b = aantal_fte_begroot()


def organisatie_block():
    # Organisatie
    fte = aantal_fte()
    fte_begroot = aantal_fte_begroot()
    organisatie = Block(bg_color='light gray')
    organisatie.add_absolute_block(5, 5, TextBlock('Organisatie', headersize))
    organisatie.add_absolute_block(5, 65, TextBlock('Aantal mensen', defsize, color='gray'))
    organisatie.add_absolute_block(5, 90, TextBlock(aantal_mensen(), midsize, format='.5'))
    fte_color = 'black' if fte_begroot - fte < 1 else 'red'
    organisatie.add_absolute_block(150, 65, TextBlock('Aantal FTE', defsize, color='gray'))
    organisatie.add_absolute_block(150, 90, TextBlock(fte, midsize, color=fte_color, format='.5'))
    organisatie.add_absolute_block(150, 120, TextBlock('Begroot', defsize, color='gray'))
    organisatie.add_absolute_block(150, 145, TextBlock(fte_begroot, midsize, color='gray', format='.5'))
    return organisatie


def risico_block():
    # Risico
    risico = Block()
    risico.add_absolute_block(0, 5, TextBlock('Klanten', headersize))
    risico.add_absolute_block(0, 65, TextBlock('Top 3 klanten laatste 6 maanden', defsize, color='gray'))
    risico.add_absolute_block(
        0,
        90,
        Table(
            top_x_klanten_laatste_zes_maanden(3),
            headers=[],
            aligns=['left', 'right', 'right'],
            formats=['', '€', '%'],
            totals=[0, 0, 1],
        ),
        'clients.html',
    )
    return risico


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


def age_analysis_chart():
    # Debiteuren leeftijdsanalyse
    return StackedBarChart(
        240,
        470,
        '',
        ['<30 dg', '30-60 dg', '60-90 dg', '> 90 dg'],
        debiteuren_30_60_90(),
        ['#7C7', '#FD0', '#FFA500', '#c00'],
        max_axis_value=350000,
    )


def render_dashboard():

    page = Page(align_children='absolute')
    row1 = 120
    col = 10
    page.add_absolute_block(col, row1, sales_block(), 'sales.html')

    col += 320
    page.add_absolute_block(col, row1, resultaat_block(), 'resultaat_berekening.html')
    page.add_absolute_block(col, 370, pijplijn_block())
    page.add_absolute_block(col, 600, organisatie_block())

    col += 300
    page.add_absolute_block(col, row1, productiviteit_block(), 'target.html')

    col += 340
    page.add_absolute_block(col, row1, risico_block())
    page.add_absolute_block(col, 400, TextBlock('Debiteuren', midsize))

    page.add_absolute_block(col - 10, 450, age_analysis_chart(), 'debiteuren.html')

    page.render('output/dashboard.html')
    page.render('output/limited/dashboard.html', limited=True)


if __name__ == '__main__':
    os.chdir('..')
    load_cache()
    render_dashboard()
