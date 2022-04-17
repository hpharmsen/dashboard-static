import datetime
import os
from pathlib import Path

from layout.basic_layout import HEADER_SIZE, DEF_SIZE, MID_SIZE
from layout.block import Page, TextBlock, VBlock, HBlock
from layout.chart import ChartConfig, StackedBarChart, ScatterChart
from layout.table import Table, TableConfig
from maandrapport import HoursData, kpi_grid
from middleware.trendline import TrendLines
from model.productiviteit import corrections_percentage, largest_corrections
from model.resultaat import vulling_van_de_planning
from model.utilities import Day, Period
from settings import (
    dependent_color,
    EFFECTIVITY_RED,
    EFFECTIVITY_GREEN,
    get_output_folder,
    CORRECTIONS_RED,
    CORRECTIONS_GREEN,
    GREEN,
    RED,
    GRAY,
)


# === DDA Talk over kengetallen ==================
# KPI's
# Omzet is uren x tarief - kosten Dus als KPI's: BILLABLE UREN en GEMIDDELD TARIEF

# EFFECTIVITEIT = hoeveel heb je de mensen werkelijk op klantwerk.
# Normaal werken mensen 1832 uur
# Hoeveel daarvan op klantwerk? 50% is echt te weinig. 65% is aan de lage kant maar kan.
# Als het niet minimaal 60% a 65% is staat je winstgevendheid onder druk.
# Als je groeit: directe mensen 70%/75%/80%
# PM/lead eerder 40%/50%/60%

# efficiency = Hoe goed je bent om projecten binnen de gestelde tijd af te ronden = het gemiddelde
# daadwerkelijke uurtarief (effective rate). = BBI / UREN OP DE KLANT
# Efficiëncy maandelijks uitrekenen. Ook op type werk.
# Daadwerkelijke uurtarief t.o.v. geoffreerd uurtarief is een maatstaf van je kwaliteit

# Dus:
# uren op de klant / Beschikbare uren = effectiviteit
# BBI / billable uren = Gemiddeld tarief
# Dit alles liever alleen voor de uren-kant van de business.

# 3x5 = Magic: 5% meer uren op de klant boeken, 5% hoger gemiddeld uurtarief, 5% hogere prijs

# Labour Efficiency Ratio (dLER) = BBI / loonkosten van directe mensen. 1,9 is te laag, 2,0 is ondergrens, 2,2 is goed.

# Met al deze dingen: het probleem helder krijgen en daarmee bepalen wat de next steps zijn
# Het volgende is dan: 6 tot 12 maanden vooruit kijken

# - Effective rate = Bruto marge / alle declarabele uren (DDA: 96 bij een listprice van 103)
# - Billable uren vs geplande uren?

# === Teamleader whitepaper ==================
# - 1. Gemiddelde opbrengst per uur (%) = Factureerbare waarde per uur / kosten per uur
# - Factureerbare waarde per uur (€) = beschikbare budget te delen door het aantal gepresteerde uren op projecten.
# - Kosten per uur (€) = Loon + onkosten + (algemene kosten / #werkn).
#   en dat deel je door de netto capaciteit (billable en intern maar zonder ziek en vakantiedagen)
# - 2. Performance  (%)  = Efficiëntie x Billability
# - Efficiëntie (%) = gefactureerde waarde delen door intrinsieke waarde (budget) van diezelfde periode.
# - Billability  (%) = factureerbare uren / nettocapaciteit (= het aantal uren dat iemand effectief werkt)


def render_operations_page(output_folder: Path, year: int = None):
    if year:
        # Use given year. Create page with year name in it
        html_page = f"operations {year}.html"
        weeks = 52
        description = f"Belangrijkste KPI's over {year}"
        total_period = Period(f"{year}-01-01", f"{year + 1}-01-01")
    else:
        # Use the current year (default)
        year = int(datetime.datetime.today().strftime("%Y"))
        html_page = "operations.html"
        weeks = min(Day().week_number(), 20)
        description = f"Belangrijkste KPI's per week de afgelopen {weeks} weken"
        total_period = Period(f"{year}-01-01", Day())
    page = Page(
        [
            TextBlock("Operations KPI" "s", HEADER_SIZE),
            TextBlock(
                description,
                color="gray",
            ),
            kpi_block(weeks=weeks, total_period=total_period, total_title="YTD"),
            TextBlock('Effectiviteit is het percentage van de beschikbare uren dat we voor klanten werken.'),
            TextBlock('Billable uren zijn de uren die we daadwerkelijk factureren.'),
            TextBlock('Billable % is als percentage van de beschikbare uren.'),
            TextBlock(
                'Bij omzet op uren tellen fixed price diensten mee als omzet / gemaakte uren maar bij diensten die nog open zijn, wordt dit uurtarief gemaximeerd op €100.'
            ),
        ]
    )
    page.render(output_folder / html_page)


def kpi_block(weeks=4, verbose=True, total_period=None, total_title=""):
    week_numbers, hours_data = operations_data(weeks, total_period, total_title)
    effectivity_coloring = lambda value: dependent_color(value.effectivity(), EFFECTIVITY_RED, EFFECTIVITY_GREEN)
    corrections_coloring = lambda value: dependent_color(value.correcties_perc(), CORRECTIONS_RED, CORRECTIONS_GREEN)
    return kpi_grid(
        week_numbers,
        hours_data,
        verbose=verbose,
        effectivity_coloring=effectivity_coloring,
        corrections_coloring=corrections_coloring,
    )


def operations_data(weeks, total_period=None, total_title=""):
    monday = Day().plus_days(-2).last_monday()  # Wednesday gives the last monday, Monday and Tuesday the week before
    hours_data = []
    headers = []
    for w in range(weeks):
        monday_earlier = monday.plus_days(-7)
        period = Period(monday_earlier, monday)
        hours_data = [HoursData(period)] + hours_data
        headers = [monday_earlier.strftime("wk %W")] + headers
        monday = monday_earlier
    if total_period:
        headers += ["", total_title]
        hours_data += [None, HoursData(total_period)]
    return headers, hours_data


def operations_chart():
    width = 300
    height = 200
    week_numbers, hours_data = operations_data(10)
    billable = [round(h.billable_perc(), 1) for h in hours_data]
    effective_delta = [round(h.effectivity() - h.billable_perc(), 1) for h in hours_data]
    chartdata = [billable, effective_delta]
    chart_config = ChartConfig(
        width=width,
        height=height,
        colors=[GREEN, RED],
        min_y_axis=0,
        max_y_axis=100,
        # y_axis_max_ticks=10,
        labels=["% billlable", "% effectief maar niet billable"],
        series_labels=week_numbers,
    )
    return StackedBarChart(chartdata, chart_config)


def months_ago(number):
    return Day().plus_months(-number).str


def billable_chart():
    months_back = 3
    return VBlock(
        [
            TextBlock(
                f"Billable, hele team, laatste {months_back} maanden",
                DEF_SIZE,
                color=GRAY,
            ),
            TrendLines().chart("billable_hele_team", 250, 150, x_start=months_ago(months_back)),
        ]
    )


def planning_chart():
    # Vulling van de planning uit de planning database
    vulling = vulling_van_de_planning()
    if not vulling:
        return TextBlock("Kon de planning niet ophalen", color=RED)
    xy_values = [{"x": a["monday"], "y": a["filled"]} for a in vulling]
    return VBlock(
        [
            TextBlock("Planning", MID_SIZE),
            TextBlock(
                f"Percentage gevuld met niet interne projecten<br/>de komende {len(xy_values)} weken.",
                color=GRAY,
            ),
            ScatterChart(
                xy_values,
                ChartConfig(
                    width=250,
                    height=150,
                    colors=["#6666cc", "#ddeeff"],
                    x_type="int",
                    min_x_axis=xy_values[0]["x"],
                    max_x_axis=xy_values[-2]["x"],
                    min_y_axis=0,
                    max_y_axis=100,
                ),
            ),
        ]
    )


def corrections_block():
    weeks_back = 4
    interesting_correction = 8
    end_day = Day().plus_days(-2).last_monday()  # Wednesday gives the last monday, Monday and Tuesday the week before
    start_day = end_day.plus_weeks(-weeks_back)
    period = Period(start_day, end_day)

    def corrections_percentage_coloring(value):
        return dependent_color(value, red_treshold=5, green_treshold=3)

    corrections_list = largest_corrections(interesting_correction, period)
    if not corrections_list.empty:
        corrections_table = Table(
            corrections_list,
            TableConfig(headers=[], aligns=["left", "right"]),
        )
    else:
        corrections_table = None

    result = VBlock(
        [
            TextBlock("Correcties", MID_SIZE),
            HBlock(
                [
                    TextBlock(
                        corrections_percentage(period),
                        MID_SIZE,
                        text_format="%",
                        color=corrections_percentage_coloring,
                    ),
                    TextBlock(
                        f"correcties op productieve uren van<br/> week {period.fromday.week_number()} "
                        + f"tot en met week {period.untilday.plus_days(-1).week_number()}.",
                        color=GRAY,
                    ),
                ],
                padding=70,
            ),
            corrections_table
        ],
        link="corrections.html",
        padding=-40,
    )
    return result


if __name__ == "__main__":
    os.chdir("..")
    render_operations_page(get_output_folder())
