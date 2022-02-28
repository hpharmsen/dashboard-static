""" Generates the dashboard.html file """
import os

import pandas as pd
from numpy import ceil

from layout.basic_layout import DEF_SIZE, MID_SIZE, HEADER_SIZE
from layout.block import TextBlock, Page, VBlock, HBlock
from layout.chart import StackedBarChart, ScatterChart, ChartConfig
from layout.table import Table, TableConfig
from middleware.trendline import TrendLines
from model import log
from model.caching import load_cache
from model.finance import debiteuren_30_60_90_yuki
from model.organisatie import (
    aantal_mensen,
    aantal_fte,
    verzuimpercentage,
)
from model.productiviteit import corrections_percentage, largest_corrections
from model.resultaat import (
    top_x_klanten_laatste_zes_maanden,
    vulling_van_de_planning,
)
from model.sales import sales_waarde, top_x_sales
from model.travelbase import get_bookings_per_week, BRANDS
from model.utilities import Day, Period
from settings import (
    get_output_folder,
    GREEN,
    YELLOW,
    ORANGE,
    RED,
    BLACK,
    GRAY,
    dependent_color,
)
from view.operations import kpi_block, operations_data
from view.travelbase import scatterchart as travelbase_scatterchart


def render_dashboard(output_folder):
    page = Page([HBlock([commerce_block(), operations_block(), finance_block(), hr_block()])])
    page.render(output_folder / "dashboard.html")


######### Kolom 1: Commerce ###########


def commerce_block():
    minimal_interesting_amount = 20000
    sales_waarde_value = sales_waarde()
    top_sales = top_x_sales(minimal_amount=minimal_interesting_amount)
    sales_waarde_color = dependent_color(sales_waarde_value, 250000, 350000)
    commerce = VBlock(
        [
            TextBlock("Commerce", HEADER_SIZE),
            TextBlock("Saleswaarde", MID_SIZE, padding=10),
            TextBlock(
                "Verwachte omzet maal kans van alle actieve<br/>salestrajecten.",
                color=GRAY,
            ),
            TextBlock(
                sales_waarde_value,
                HEADER_SIZE,
                text_format="K",
                color=sales_waarde_color,
                tooltip="Som van openstaande trajecten<br/>maal hun kans.",
            ),
            TrendLines().chart("sales_waarde", 250, 150, min_y_axis=0, x_start=months_ago(6)),
            VBlock(
                [
                    TextBlock(f"Top {len(top_sales)} sales kansen", MID_SIZE),
                    TextBlock(
                        f"Met een verwachte waarde van minimaal € {minimal_interesting_amount}.",
                        color=GRAY,
                    ),
                    Table(
                        top_sales,
                        TableConfig(headers=[], aligns=["left", "right"], formats=["", "€"]),
                    ),
                ],
                link="sales.html",
            ),
            # klanten_block()
            travelbase_block(),
        ]
    )
    return commerce


def klanten_block():
    klanten = VBlock(
        [
            TextBlock("Klanten", MID_SIZE),
            TextBlock("Top 3 klanten laatste 6 maanden", DEF_SIZE, padding=10, color=GRAY),
            Table(
                top_x_klanten_laatste_zes_maanden(3),
                TableConfig(
                    headers=[],
                    aligns=["left", "right", "right"],
                    formats=["", "€", "%"],
                    totals=[0, 0, 1],
                ),
            ),
        ],
        link="clients.html",
    )
    return klanten


def travelbase_block():
    bookings = get_bookings_per_week(booking_type="bookings", only_complete_weeks=True)
    if not isinstance(bookings, pd.DataFrame):
        return TextBlock("Kon boekingen niet ophalen", color=RED)
    legend = ", ".join([f"{brand}: {int(bookings[brand].sum())}" for brand in BRANDS])
    return VBlock(
        [
            TextBlock("Travelbase", MID_SIZE),
            TextBlock("Aantal boekingen per week", color=GRAY),
            travelbase_scatterchart(bookings, 250, 180),
            TextBlock(legend),
        ],
        link="travelbase.html",
    )


######### Kolom 2: Operations ###########


def operations_block():
    return VBlock(
        [
            TextBlock("Operations", HEADER_SIZE),
            TextBlock("KPI's", MID_SIZE),
            HBlock([kpi_block(verbose=False)], link="operations.html", padding=40),
            TextBlock(""),  # Todo: verticale marge mogelijk maken
            operations_chart(),
            TextBlock(""),  # Todo: verticale marge mogelijk maken
            # billable_chart(),
            corrections_block(),
            planning_chart(),
        ]
    )


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
        bottom_labels=week_numbers,
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

    def project_link(_, fullline):
        return f"https://oberon.simplicate.com/projects/{fullline[0]}/hours"

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
            Table(
                largest_corrections(interesting_correction, period),
                TableConfig(
                    headers=[],
                    aligns=["left", "left", "right"],
                    hide_columns=[0],
                    row_linking=project_link,
                ),
            ),
        ],
        link="corrections.html",
    )
    return result


######### Kolom 3: Finance ###########


def finance_block():
    return VBlock(
        [
            TextBlock("Finance", HEADER_SIZE),
            omzet_chart(),
            debiteuren_block(),
            cash_block(),
        ]
    )


# def resultaat_block():
#     return None
#
#     def winst_coloring(value):
#         return dependent_color(value, -20000, 20000)
#
#     winst_percentage = int(winst_werkelijk() / bruto_marge_werkelijk() * 100)
#
#     def winst_percentage_coloring(value):
#         return dependent_color(value, 6, 15)
#
#     resultaat = VBlock(
#         [
#             TextBlock("Resultaat", MID_SIZE),
#             TextBlock("Omzet", DEF_SIZE, color="gray", padding=10),
#             HBlock(
#                 [
#                     VBlock(
#                         [
#                             TextBlock("Begroot", DEF_SIZE, color="gray", padding=5),
#                             TextBlock("Werkelijk", DEF_SIZE, color="gray"),
#                         ]
#                     ),
#                     VBlock(
#                         [
#                             TextBlock(
#                                 omzet_begroot(), DEF_SIZE, text_format="K", padding=5
#                             ),
#                             TextBlock(
#                                 bruto_marge_werkelijk(), DEF_SIZE, text_format="K"
#                             ),
#                         ]
#                     ),
#                     TextBlock(omzet_verschil_percentage(), MID_SIZE, text_format="+%"),
#                 ]
#             ),
#             TextBlock("Winst", DEF_SIZE, color="gray", padding=10),
#             # TextBlock('Tijdelijk niet beschikbaar', defsize, color='gray', padding=10),
#             VBlock(
#                 [
#                     HBlock(
#                         [
#                             VBlock(
#                                 [
#                                     TextBlock(
#                                         "Begroot", DEF_SIZE, color="gray", padding=5
#                                     ),
#                                     TextBlock("Werkelijk", DEF_SIZE, color="gray"),
#                                 ]
#                             ),
#                             VBlock(
#                                 [
#                                     TextBlock(
#                                         winst_begroot(),
#                                         DEF_SIZE,
#                                         text_format="K",
#                                         padding=5,
#                                     ),
#                                     TextBlock(
#                                         winst_werkelijk(), DEF_SIZE, text_format="K"
#                                     ),
#                                 ]
#                             ),
#                             TextBlock(
#                                 winst_verschil(),
#                                 MID_SIZE,
#                                 text_format="+K",
#                                 color=winst_coloring,
#                             ),
#                         ]
#                     ),
#                     HBlock(
#                         [
#                             TextBlock("Winstpercentage", color=GRAY, padding=5),
#                             TextBlock(
#                                 winst_percentage,
#                                 text_format="%",
#                                 color=winst_percentage_coloring,
#                                 tooltip="Gemiddeld bij DDA in 2019: 7%, high performers: 16%",
#                             ),
#                         ]
#                     ),
#                 ]
#             ),
#         ],
#         link="resultaat_berekening.html",
#     )
#     return resultaat


def omzet_chart():
    # Behaalde omzet per week
    x_end = Day().plus_days(-2).last_monday()
    x_start = x_end.plus_months(-6)
    return VBlock(
        [
            TextBlock("Omzet"),
            TextBlock("per week, laatste 6 maanden...", DEF_SIZE, color=GRAY),
            TrendLines().chart(
                "omzet_per_week",
                250,
                150,
                x_start=x_start,
                x_end=x_end,
                min_y_axis=0,
                max_y_axis=90000,
            ),
        ],
        link="billable.html",
    )


def debiteuren_block():
    # betaaltermijn = gemiddelde_betaaltermijn()
    # betaaltermijn_color = dependent_color(betaaltermijn, 45, 30)
    debiteuren = debiteuren_30_60_90_yuki()
    max_y = ceil(sum(debiteuren) / 100000) * 100000
    return VBlock(
        [
            TextBlock("Debiteuren", MID_SIZE),
            StackedBarChart(
                debiteuren,
                ChartConfig(
                    width=240,
                    height=250,
                    labels=["<30 dg", "30-60 dg", "60-90 dg", "> 90 dg"],
                    colors=[GREEN, YELLOW, ORANGE, RED],
                    max_y_axis=max(450000, max_y),
                ),
            ),
        ],
        link="debiteuren.html",
    )


def cash_block():
    return VBlock(
        [
            TextBlock("Cash", MID_SIZE),
            TrendLines().chart("cash", 250, 150, min_y_axis=0, x_start=months_ago(6)),
        ]
    )


######### Kolom 4: HR ###########


def hr_block():
    return VBlock(
        [
            TextBlock("HR", HEADER_SIZE),
            team_block(),
            tevredenheid_block(),
            verzuim_block(),
            # vakantiedagen_block(),
            error_block(),
        ]
    )


def team_block():
    fte = aantal_fte()
    # fte_begroot = aantal_fte_begroot()
    fte_color = BLACK  # dependent_color(fte_begroot - fte, 1, -1)

    return VBlock(
        [
            TextBlock("Team", MID_SIZE),
            HBlock(
                [
                    VBlock(
                        [
                            TextBlock("Aantal mensen", DEF_SIZE, padding=5, color=GRAY),
                            TextBlock(aantal_mensen(), MID_SIZE, text_format=".5"),
                        ]
                    ),
                    VBlock(
                        [
                            TextBlock("Aantal FTE", DEF_SIZE, padding=5, color=GRAY),
                            TextBlock(fte, MID_SIZE, color=fte_color, text_format=".5"),
                            # TextBlock('Begroot', defsize, padding=5, color=GRAY),
                            # TextBlock(fte_begroot, midsize, color=GRAY, format='.5'),
                        ]
                    ),
                ]
            ),
        ]
    )


def verzuim_block():
    period = Period(Day().plus_months(-3))
    verzuim = verzuimpercentage(period)
    verzuim_color = dependent_color(verzuim, 3, 1.5)
    return VBlock(
        [
            TextBlock("Verzuim", MID_SIZE),
            TextBlock("Verzuimpercentage de laatste 3 maanden", DEF_SIZE, color=GRAY),
            TextBlock(
                verzuim,
                MID_SIZE,
                text_format="%1",
                color=verzuim_color,
                tooltip="Gemiddeld bij DDA in 2019: 3.0%. Groen bij 1,5%, rood bij 3%",
            ),
        ],
        link="absence.html",
    )


# def vakantiedagen_block():
#     pool = vrije_dagen_pool()
#     pool_color = BLACK  # dependent_color(pool, 10, 2)
#     return VBlock(
#         [
#             TextBlock('Vrije dagen pool', MID_SIZE, padding=5),
#             TextBlock(
#             'Aantal dagen dat eigenlijk al opgemaakt<br/>had moeten worden maar dat niet is.', DEF_SIZE, color=GRAY
#             ),
#             HBlock(
#                 [
#                     TextBlock(pool, MID_SIZE, text_format='.1', color=pool_color),
#                     TextBlock('dagen/fte', color=GRAY, padding=0),
#                 ],
#                 link='freedays.html',
#             ),
#         ]
#     )


def tevredenheid_block():
    return None  # VBlock([TextBlock('Happiness', midsize), TextBlock('Data nodig...', color=GRAY)])


def error_block():
    errs = log.get_errors()
    if not errs:
        return None
    error_lines = [
        TextBlock(
            f'<b>{err["file"]}, {err["function"]}</b><br/>{err["message"]}',
            DEF_SIZE,
            width=260,
            color=RED,
        )
        for err in errs
    ]
    return VBlock([TextBlock("Errors", MID_SIZE)] + error_lines)


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


if __name__ == "__main__":
    os.chdir("..")
    load_cache()
    render_dashboard(get_output_folder())
