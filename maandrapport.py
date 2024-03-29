import datetime
import os
import sys
from pathlib import Path

import pdfkit

from layout.basic_layout import HEADER_SIZE, MID_SIZE
from layout.block import TextBlock, Page, VBlock, HBlock, Grid
from layout.chart import BarChart, ChartConfig
from maandrapportage.financials import profit_and_loss_block, balance_block
from maandrapportage.yuki_results import YukiResult, last_date_of_month
from model.caching import load_cache
from model.hoursdata import HoursData
from model.utilities import Day, Period
from settings import (
    get_output_folder,
    MAANDEN,
    GRAY,
    get_monthly_folder,
    CORRECTIONS_RED,
    CORRECTIONS_GREEN,
    RED,
)

# TODO:
# - Omzet Travelbase is nog nul
# - Investeringen is nog nul
# - Mutaties eigen vermogen is nog nul
from sources.googlesheet import panic
from view.onderhanden_werk import onderhanden_werk_list


def render_maandrapportage(output_folder, year, month):
    minimal_interesting_owh_value = 1000
    yuki_result = YukiResult(
        year, month, minimal_interesting_owh_value=minimal_interesting_owh_value
    )

    afschrijvingen = yuki_result.post("-WAfs")
    warning = (
        None
        if afschrijvingen
        else TextBlock(
            "Dit is een voorlopig overzicht. De boekhouding van deze maand is nog niet compleet.\n",
            color=RED,
        )
    )

    page = Page(
        [
            VBlock(
                [
                    TextBlock(
                        f"Maandrapportage {MAANDEN[month - 1].lower()}, {year}",
                        HEADER_SIZE,
                    ),
                    warning,
                    hours_block(year, month),
                    profit_and_loss_block(yuki_result),
                    balance_block(yuki_result),
                    # ...HBlock([cash_block(), debiteuren_block()]),
                    # cashflow_analysis_block(yuki_result),
                    ohw_block(year, month, minimal_interesting_owh_value),
                ]
            )
        ]
    )
    htmlpath = output_folder / f"{year}_{month:02}.html"
    page.render(htmlpath, template="maandrapportage.html")

    # Generate PDF
    pdfpath = htmlpath.with_suffix(".pdf")
    options = {"enable-local-file-access": None}
    pdfkit.from_file(str(htmlpath), str(pdfpath), options=options)


def no_func(_):
    return  # Create empty function


def kpi_grid(
    columns_headers,
    data,
    effectivity_coloring=no_func,
    corrections_coloring=no_func,
    verbose=True,
):
    assert len(columns_headers) == len(data)
    num_of_cols = len(data) + 1
    aligns = ["left"] + ["right"] * len(
        data
    )  # First column left, the rest right aligned
    grid = Grid(
        cols=num_of_cols, has_header=False, line_height=0, aligns=aligns
    )  # +1 is for the header column

    def add_row(title, row_data, text_format, coloring=no_func):
        row = [TextBlock(title)]
        for d in row_data:
            # color=coloring(d)# if coloring else None
            row += [TextBlock(d, text_format=text_format)]
        grid.add_row(row)

    grid.add_row([None] + columns_headers)

    def attr_list(attr, minus=1):
        for d in data:
            if not d:
                yield ""
            else:
                a = getattr(d, attr)
                if callable(a):
                    yield minus * a()
                else:
                    yield minus * a

    if verbose:
        # grid.add_row([TextBlock('Rooster uren')] + [TextBlock(d.rooster, text_format='.') for d in data])
        add_row("Rooster uren", attr_list("rooster"), text_format=".")
        add_row("Verlof", attr_list("verlof", -1), text_format=".")
        add_row("Verzuim", attr_list("verzuim", -1), text_format=".")
        add_row("Beschikbare uren", attr_list("beschikbaar"), text_format=".")

    # tooltip = f'Groen bij {EFFECTIVITY_GREEN}, Rood onder de {EFFECTIVITY_RED}'
    # add_row('Verzuim', attr_list('verzuim', -1), text_format='.')
    add_row("Effectiviteit", attr_list("effectivity"), text_format="%")

    if verbose:
        add_row("Klant uren", attr_list("op_klant_geboekt"), text_format=".")

    tooltip = f"Groen onder de {CORRECTIONS_GREEN * 100:.0f}%, Rood boven de {CORRECTIONS_RED * 100:.0f}%"
    add_row(
        "Correcties",
        attr_list("correcties", -1),
        coloring=corrections_coloring,
        text_format=".",
    )
    # grid.add_row(
    #     [TextBlock('Correcties', tooltip=tooltip)]
    #     + [TextBlock(-d.correcties(), color=corrections_coloring(d), text_format='.') for d in data]
    # )

    if verbose:
        add_row("Billable uren", attr_list("billable"), text_format=".")
        # grid.add_row([TextBlock('Billable uren')] + [TextBlock(d.billable, text_format='.') for d in data])
        # grid.add_row([TextBlock('Billable %')] + [TextBlock(d.billable_perc(), text_format='%') for d in data])
        # grid.add_row([TextBlock('Gemiddeld uurloon')] + [TextBlock(d.uurloon(), text_format='€') for d in data])
        add_row("Billable %", attr_list("billable_perc"), text_format="%")
        add_row("Gemiddeld uurloon", attr_list("uurloon"), text_format="€")

    add_row("Omzet op uren", attr_list("omzet"), text_format="K")
    # grid.add_row([TextBlock('Omzet op uren')] + [TextBlock(d.omzet, text_format='K') for d in data])
    return grid


def hours_block(year, month):
    month_names = []
    data = []
    for m in range(month):
        month_names += [TextBlock(MAANDEN[m])]
        fromday = Day(year, m + 1, 1)
        untilday = fromday.plus_months(1)
        period = Period(fromday, untilday)
        data += [HoursData(period)]
    headers = month_names
    curyear = int(datetime.datetime.today().strftime("%Y"))
    if month > 1:  # Januari heeft geen YTD kolom
        headers += ["", str(year) if month == 12 else "YTD"]
        if year == curyear:
            total_period = Period(
                str(curyear) + "-01-01", Day(year, month, 1).plus_months(1)
            )
        else:
            total_period = Period(Day(year, 1, 1), Day(year, month, 1).plus_months(1))
        data += [None, HoursData(total_period)]
    grid = kpi_grid(headers, data)

    chart = None
    if month >= 3:  # Voor maart heeft een grafiekje niet veel zin
        chart_data = data[:-2] if month > 1 else data  # -2 is haalt de total col eraf
        chart = VBlock(
            [
                TextBlock("Omzet op uren per maand"),
                BarChart(
                    [d.omzet for d in chart_data],
                    ChartConfig(
                        width=60 * month,
                        height=150,
                        colors=["#ddeeff"],
                        series_labels=[MAANDEN[m] for m in range(month)],
                        y_axis_max_ticks=5,
                    ),
                ),
            ],
            css_class="no-print",
        )

    return VBlock(
        [
            TextBlock("Billable uren", MID_SIZE),
            TextBlock(
                """Beschikbare uren zijn alle uren die we hebben na afrek van vrije dagen en verzuim.<br/>
                   Klant uren zijn alle uren besteed aan werk voor klanten. <br/>
                   Billable uren is wat er over is na correcties. <br/>
                   Omzet is de omzet gemaakt in die uren.""",
                color=GRAY,
            ),
            grid,
            chart,
        ]
    )


# Deloitte: In de maandrapportage zou ik dan geschreven toelichtingen verwachten omtrent afwijkingen van de begroting en
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


def render_maandrapportage_page(monthly_folder, output_folder: Path):
    lines = []
    files = sorted(
        [f for f in monthly_folder.iterdir() if f.suffix == ".html"], reverse=True
    )
    for file in files:
        year, month = file.stem.split("_")
        htmlpath = monthly_folder / file
        pdfpath = os.path.relpath(htmlpath.with_suffix(".pdf"), start=output_folder)
        htmlpath = os.path.relpath(htmlpath, start=output_folder)
        lines += [
            HBlock(
                [
                    TextBlock(MAANDEN[int(month) - 1] + " " + year, url=htmlpath),
                    TextBlock("pdf", url=pdfpath),
                ]
            )
        ]
    page = Page([TextBlock("Maandrapportages", HEADER_SIZE)] + lines)
    page.render(output_folder / "maandrapportages.html")


def report(render_year, render_month):
    print(f"\nGenerating report for {MAANDEN[render_month - 1]} {render_year}")
    render_maandrapportage(get_monthly_folder(), render_year, render_month)
    render_maandrapportage_page(get_monthly_folder(), get_output_folder())


def ohw_block(year, month, minimal_intesting_ohw_value: int):
    day = last_date_of_month(year, month)
    # day = Day(year, month + 1, 1) if month < 12 else Day(year + 1, 1, 1)
    return VBlock(
        [
            TextBlock(f"Onderhanden werk", MID_SIZE),
            onderhanden_werk_list(
                day, minimal_intesting_ohw_value=minimal_intesting_ohw_value
            ),
        ],
        css_class="page-break-before",
        style="page-break-before: always;",
    )


def process_params():
    today = datetime.datetime.today()
    if len(sys.argv) == 1:
        year = today.year
        month = today.month - 1
        if month == 0:
            month = 12
            year -= 1
        return [(year, month)]  # Last month

    if len(sys.argv) == 2:
        # Generate report for the month or year specified in the parameter
        if sys.argv[1] == "all":
            # Generate all reports for all months starting Januari 2021
            result = []
            for year in range(2021, today.year + 1):
                months = today.month - 1 if year == today.year else 12
                for month in range(1, months + 1):
                    result += [(year, month)]
            return result  # Alle voorbije maanden vanaf 2021

        param = int(sys.argv[1])
        if param <= 12:
            return [(today.year, param)]  # This year, specified month

        year = param
        months = today.month - 1 if year == today.year else 12
        return [
            (year, month) for month in range(1, months + 1)
        ]  # This year, all finished months so far

    # Twee parameters
    month = int(sys.argv[1])
    year = int(sys.argv[2])
    if month > 12:
        panic(
            f"Invalid parameter {month} for month. Usage: python maandrapport.py 5 2022"
        )
    return [(year, month)]


if __name__ == "__main__":
    load_cache()
    to_render = process_params()
    for r in to_render:
        report(*r)
