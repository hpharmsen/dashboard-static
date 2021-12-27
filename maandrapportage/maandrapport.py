import datetime
import os
import sys
from pathlib import Path

import pdfkit

from layout.basic_layout import HEADER_SIZE, MID_SIZE
from layout.block import TextBlock, Page, VBlock, HBlock, Grid
from layout.chart import BarChart, ChartConfig
from maandrapportage.financials import profit_and_loss_block, balance_block, cashflow_analysis_block
from maandrapportage.yuki_results import YukiResult
from middleware.timesheet import Timesheet
from model.caching import load_cache
from model.productiviteit import geboekte_uren_users, beschikbare_uren_volgens_rooster
from model.utilities import Day, Period
from settings import (
    get_output_folder,
    MAANDEN,
    GRAY,
    get_monthly_folder,
    CORRECTIONS_RED,
    CORRECTIONS_GREEN,
)


# TODO:
# - Omzet Travelbase is nog nul
# - Investeringen is nog nul
# - Mutaties eigen vermogen is nog nul


class HoursData:
    ''' Class to store and calculate the main production KPI's '''

    # rooster : float
    # verlof : float
    # verzuim : float
    # beschikbaar: float
    # op_klant_geboekt: float
    # billable: float
    # omzet: float

    def __init__(self, period: Period, employees: list = []):
        self.rooster, self.verlof, self.verzuim = beschikbare_uren_volgens_rooster(period, employees)
        self.op_klant_geboekt_old = geboekte_uren_users(period, users=employees, only_clients=1, only_billable=0)
        ts = Timesheet()
        self.op_klant_geboekt = ts.geboekte_uren_users(period, users=employees, only_clients=1, only_billable=0)
        self.billable_old = geboekte_uren_users(
            period,
            users=employees,
            only_clients=1,
            only_billable=1,
        )
        self.billable = ts.geboekte_uren_users(
            period,
            users=employees,
            only_clients=1,
            only_billable=1,
        )
        # self.omzet_old = geboekte_omzet_users(period, users=employees, only_clients=1, only_billable=0)
        self.omzet = ts.geboekte_omzet_users(period, users=employees, only_clients=1, only_billable=0)

    def beschikbaar(self) -> float:
        return self.rooster - self.verlof - self.verzuim

    def effectivity(self):
        return 100 * self.op_klant_geboekt / self.beschikbaar() if self.beschikbaar() else 0

    def billable_perc(self):
        return 100 * self.billable / self.beschikbaar() if self.beschikbaar() else 0

    def correcties(self):
        return self.op_klant_geboekt - self.billable

    def correcties_perc(self):
        return (self.op_klant_geboekt - self.billable) / self.op_klant_geboekt if self.op_klant_geboekt else 0

    def uurloon(self):
        return self.omzet / self.billable if self.billable else 0


def render_maandrapportage(output_folder, year, month):
    yuki_result = YukiResult(year, month)
    page = Page(
        [
            VBlock(
                [
                    TextBlock(f'Maandrapportage {MAANDEN[month - 1].lower()}, {year}', HEADER_SIZE),
                    hours_block(year, month),
                    profit_and_loss_block(yuki_result, year, month),
                    balance_block(yuki_result, year, month),
                    # HBlock([cash_block(), debiteuren_block()]),
                    cashflow_analysis_block(yuki_result, year, month),
                ]
            )
        ]
    )
    htmlpath = output_folder / f'{year}_{month:02}.html'
    page.render(htmlpath, template='maandrapportage.html')

    # Generate PDF
    pdfpath = htmlpath.with_suffix('.pdf')
    options = {"enable-local-file-access": None}
    pdfkit.from_file(str(htmlpath), str(pdfpath), options=options)


NO_FUNC = lambda a: None  # Create empty function


def KPIgrid(columns_headers, data, effectivity_coloring=NO_FUNC, corrections_coloring=NO_FUNC, verbose=True):
    assert len(columns_headers) == len(data)
    num_of_cols = len(data) + 1
    aligns = ['left'] + ['right'] * len(data)  # First column left, the rest right aligned
    grid = Grid(cols=num_of_cols, has_header=False, line_height=0, aligns=aligns)  # +1 is for the header column

    def add_row(title, row_data, text_format, coloring=NO_FUNC):
        row = [TextBlock(title)]
        for d in row_data:
            # color=coloring(d)# if coloring else None
            row += [TextBlock(d, text_format=text_format)]
        grid.add_row(row)

    grid.add_row([None] + columns_headers)

    def attr_list(attr, minus=1):
        # a =  getattr(data,attr)
        # if callable(a):
        #     a = a()
        # return [minus * a if d else '' for d in data]
        for d in data:
            if not d:
                yield ''
            else:
                a = getattr(d, attr)
                if callable(a):
                    yield minus * a()
                else:
                    yield minus * a

    if verbose:
        # grid.add_row([TextBlock('Rooster uren')] + [TextBlock(d.rooster, text_format='.') for d in data])
        add_row('Rooster uren', attr_list('rooster'), text_format='.')
        add_row('Verlof', attr_list('verlof', -1), text_format='.')
        add_row('Verzuim', attr_list('verzuim', -1), text_format='.')
        add_row('Beschikbare uren', attr_list('beschikbaar'), text_format='.')

    # tooltip = f'Groen bij {EFFECTIVITY_GREEN}, Rood onder de {EFFECTIVITY_RED}'
    # add_row('Verzuim', attr_list('verzuim', -1), text_format='.')
    add_row('Effectiviteit', attr_list('effectivity'), text_format='%')

    if verbose:
        add_row('Klant uren', attr_list('op_klant_geboekt'), text_format='.')

    tooltip = f'Groen onder de {CORRECTIONS_GREEN * 100:.0f}%, Rood boven de {CORRECTIONS_RED * 100:.0f}%'
    add_row('Correcties', attr_list('correcties', -1), coloring=corrections_coloring, text_format='.')
    # grid.add_row(
    #     [TextBlock('Correcties', tooltip=tooltip)]
    #     + [TextBlock(-d.correcties(), color=corrections_coloring(d), text_format='.') for d in data]
    # )

    if verbose:
        add_row('Billable uren', attr_list('billable'), text_format='.')
        # grid.add_row([TextBlock('Billable uren')] + [TextBlock(d.billable, text_format='.') for d in data])
        # grid.add_row([TextBlock('Billable %')] + [TextBlock(d.billable_perc(), text_format='%') for d in data])
        # grid.add_row([TextBlock('Gemiddeld uurloon')] + [TextBlock(d.uurloon(), text_format='€') for d in data])
        add_row('Billable %', attr_list('billable_perc'), text_format='%')
        add_row('Gemiddeld uurloon', attr_list('uurloon'), text_format='€')

    add_row('Omzet op uren', attr_list('omzet'), text_format='K')
    # grid.add_row([TextBlock('Omzet op uren')] + [TextBlock(d.omzet, text_format='K') for d in data])
    return grid


def hours_block(year, month):
    month_names = []
    data = []
    for m in range(month):
        month_names += [TextBlock(MAANDEN[m])]
        fromday = Day(year, m + 1, 1)
        untilday = Day(year, m + 2, 1) if m < 11 else Day(year + 1, m + 1, 1)
        period = Period(fromday, untilday)
        data += [HoursData(period)]
    headers = month_names + ['', 'YTD']
    curyear = datetime.datetime.today().strftime('%Y')
    total_period = Period(curyear + '-01-01')
    data += [None, HoursData(total_period)]
    grid = KPIgrid(headers, data)

    chart = None
    if month >= 3:  # Voor maart heeft een grafiekje niet veel zin
        chart = BarChart(
            [d.omzet for d in data[:-2]],  # -2 is lelijk maar haalt de total col eraf
            ChartConfig(
                width=60 * month,
                height=150,
                colors=['#ddeeff'],
                bottom_labels=[MAANDEN[m] for m in range(month)],
                y_axis_max_ticks=5
            ),
        )

    return VBlock(
        [
            TextBlock('Billable uren', MID_SIZE),
            TextBlock(
                '''Beschikbare uren zijn alle uren die we hebben na afrek van vrije dagen en verzuim.<br/>
                   Klant uren zijn alle uren besteed aan werk voor klanten. <br/>
                   Billable uren is wat er over is na correcties. <br/>
                   Omzet is de omzet gemaakt in die uren.''',
                color=GRAY,
            ),
            grid,
            VBlock([
                TextBlock('Omzet op uren per maand'),
                chart],
                css_class="no-print")
        ]
    )


# In de maandrapportage zou ik dan geschreven toelichtingen verwachten omtrent afwijkingen van de begroting en
# belangrijke ontwikkelingen.
#
# Vervolgens aangevuld met voor jullie belangrijke KPI’s.
# Welke dat exact zijn, is sterk afhankelijk van jullie business plan.
#
# Als jullie in het business plan hebben opgenomen dat een bepaalde groei gerealiseerd moet worden, door bijvoorbeeld
# meer omzet, door meer uren te verkopen of de productiviteit te verhogen. Dan zou ik verwachten dat deze KPI’s
# terugkomen in de maandrapportage (weer in vergelijking met jullie normen/begroting), omdat je er dan ook daadwerkelijk
# tijdig kan bijsturen.
#
# Ik ken jullie business plan nog niet, maar ik zou zeker verwachten:
#
# Productiviteit (directe uren vs normuren, analyse indirecte uren)
# Brutomarge analyse op projectniveau, gerealiseerd gemiddeld uurtarief
# Overzicht afboekingen en afboekingspercentages.
# Ontwikkeling OHW met ouderdom, DOB (Days of billing: hoe snel wordt het OHW gefactureerd) DSO (Days of sales
# outstanding: ouderdom debiteuren).
# Voor wat betreft de overige bedrijfskosten: enkel nader aandacht indien deze afwijken van de begroting, meestal is dat
# redelijk stabiel en zeer voorspelbaar.
#
# Salesfunnel zou ik niet direct opnemen in de maandrapportage. Vaak zitten bij het salesoverleg weer andere mensen bij
# die wellicht niet alle financiële data hoeven te zien.
# Uiteraard kan als onderdeel van je maandelijks directieoverleg “sales” een belangrijk onderdeel zijn, maar is niet
# direct nodig voor een maandrapportage. Uiteraard is alles vormvrij.
#
# Een dergelijke maandrapportage moet ook gaan groeien, maar houd in beeld wat voor jullie belangrijk is om de
# ondernemingsdoelstellingen te kunnen monitoren en hierop te kunnen bijsturen indien nodig.
#
# In de maandcijfers van een betreffende maand is altijd zichtbaar de YTD (year to date) cijfers, alsook de betreffende
# maand. Vervolgens worden bij de maandcijfers de begroting opgeteld om te kunnen voorspellen of de doelstellingen voor
# dat jaar worden behaald, voor- of achter lopen.
#
# Grafieken kunnen handig zijn, fleuren vaak de presentatie wat op. Ik zou dit alleen doen als het zinvol is.


def render_maandrapportage_page(monthly_folder, output_folder: Path, year, month):
    lines = []
    files = sorted([f for f in monthly_folder.iterdir() if f.suffix == '.html'])
    for file in files:
        month_num = int(file.stem.split('_')[1])
        htmlpath = monthly_folder / file
        pdfpath = os.path.relpath(htmlpath.with_suffix('.pdf'), start=output_folder)
        htmlpath = os.path.relpath(htmlpath, start=output_folder)
        lines += [HBlock([TextBlock(MAANDEN[month_num - 1], url=htmlpath), TextBlock('pdf', url=pdfpath)])]
    page = Page([TextBlock('Maandrapportages', HEADER_SIZE)] + lines)
    page.render(output_folder / 'maandrapportages.html')


def report(render_year, render_month):
    print(f'Generating report for {MAANDEN[render_month-1]} {render_year}')
    render_maandrapportage(get_monthly_folder(), render_year, render_month)
    render_maandrapportage_page(get_monthly_folder(), get_output_folder(), render_year, render_month)


if __name__ == '__main__':
    os.chdir('..')
    load_cache()
    if len(sys.argv) > 1 and sys.argv[1] == 'all':
        for m in range(1, datetime.datetime.today().month):
            report(datetime.datetime.today().year, m)
    else:
        try:
            render_month = int(sys.argv[1])
        except:
            render_month = datetime.datetime.today().month - 1
            if render_month == 0:
                render_month = 12
        render_year = datetime.datetime.today().year if render_month < 12 else datetime.datetime.today().year - 1
        report(render_year, render_month)
