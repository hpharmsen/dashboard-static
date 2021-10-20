import datetime
import os
from pathlib import Path

import pdfkit

from financials import profit_and_loss_block, balance_block, cashflow_analysis_block
from model.productiviteit import geboekte_uren_users, geboekte_omzet_users, beschikbare_uren
from view.dashboard import cash_block, debiteuren_block
from yuki_results import YukiResult
from model.caching import load_cache
from layout.block import TextBlock, Page, VBlock, HBlock, Grid
from layout.basic_layout import headersize, midsize
from settings import get_output_folder, MAANDEN, GRAY
from main import get_output_folder


# TODO:
# - Omzet Travelbase is nog nul
# - Investeringen is nog nul
# - Mutaties eigen vermogen is nog nul


def render_maandrapportage(output_folder, year, month):
    yuki_result = YukiResult(year, month)
    page = Page(
        [
            VBlock(
                [
                    TextBlock(f'Maandrapportage {MAANDEN[month - 1].lower()}, {year}', headersize),
                    hours_block(year, month),
                    profit_and_loss_block(yuki_result, year, month),
                    balance_block(yuki_result, year, month),
                    # HBlock([cash_block(), debiteuren_block()]),
                    cashflow_analysis_block(yuki_result, year, month),
                ]
            )
        ]
    )
    htmlpath = output_folder / f'monthly{year}_{month:02}.html'
    page.render(htmlpath, template='maandrapportage.html')

    # Generate PDF
    pdfpath = htmlpath.with_suffix('.pdf')
    options = {"enable-local-file-access": None}
    pdfkit.from_file(str(htmlpath), str(pdfpath), options=options)


def hours_block(year, month):
    month_names = []
    available_hours = []
    client_hours = []
    effectivity = []
    billable_hours = []
    writeoffs = []
    turnovers = []
    for m in range(month):
        month_names += [TextBlock(MAANDEN[m])]
        fromdate = datetime.datetime(year, m + 1, 1)
        untildate = datetime.datetime(year, m + 2, 1) if m < 11 else datetime.datetime(year + 1, m + 1, 1)
        beschikbaar = beschikbare_uren(fromdate=fromdate, untildate=untildate)
        op_klant_geboekt = geboekte_uren_users(
            users=None, only_clients=1, only_billable=0, fromdate=fromdate, untildate=untildate
        )
        available_hours += [beschikbaar]
        client_hours += [op_klant_geboekt]
        effectivity += [100 * op_klant_geboekt / beschikbaar]
        billable_hours += [
            geboekte_uren_users(users=None, only_clients=1, only_billable=1, fromdate=fromdate, untildate=untildate)
        ]
        writeoffs += [billable_hours[-1] - client_hours[-1]]
        turnovers += [
            geboekte_omzet_users(users=None, only_clients=1, only_billable=0, fromdate=fromdate, untildate=untildate)
        ]

    actual_hourly_rates = [t / h for t, h in zip(turnovers, billable_hours)]

    grid = Grid(cols=month + 1, has_header=False, line_height=0)  # +1 is for the header column
    grid.add_row([None] + month_names)
    grid.add_row([TextBlock('Beschikbare uren')] + [TextBlock(b, format='.') for b in available_hours])
    grid.add_row([TextBlock('Effectiviteit')] + [TextBlock(b, format='%') for b in effectivity])
    grid.add_row([TextBlock('Klant uren')] + [TextBlock(b, format='.') for b in client_hours])
    grid.add_row([TextBlock('Correcties')] + [TextBlock(b, format='.') for b in writeoffs])
    grid.add_row([TextBlock('Billable uren')] + [TextBlock(b, format='.') for b in billable_hours])
    grid.add_row([TextBlock('Gemiddeld uurloon')] + [TextBlock(r, format='€') for r in actual_hourly_rates])
    grid.add_row([TextBlock('Omzet op uren')] + [TextBlock(t, format='K') for t in turnovers])

    return VBlock(
        [
            TextBlock('Billable uren', midsize),
            TextBlock(
                '''Beschikbare uren zijn alle uren die we hebben na afrek van vrije dagen en verzuim.<br/>
                          Klant uren zijn alle uren besteed aan werk voor klanten. <br/>
                          Billable uren is wat er over is na correcties. <br/>
                          Omzet is de omzet gemaakt in die uren.''',
                color=GRAY,
            ),
            grid,
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


def render_maandrapportage_page(output_folder: Path):
    lines = []
    for month in range(1, 10):
        month_name = MAANDEN[month - 1]
        htmlpath = output_folder / f'monthly{year}_{month:02}.html'
        pdfpath = htmlpath.with_suffix('.pdf')
        lines += [HBlock([TextBlock(month_name, url=htmlpath), TextBlock('pdf', url=pdfpath)])]
    page = Page([TextBlock('Maandrapportages', headersize)] + lines)
    page.render(output_folder / 'maandrapportages.html')


if __name__ == '__main__':
    os.chdir('..')
    load_cache()
    year = 2021
    render_month = 9
    for month in range(render_month, render_month + 1):
        render_maandrapportage(get_output_folder(), year, month)

    render_maandrapportage_page(get_output_folder())
