from numpy import ceil

from layout.basic_layout import MID_SIZE, DEF_SIZE
from layout.block import VBlock, TextBlock
from layout.chart import StackedBarChart, ChartConfig
from middleware.trendline import TrendLines
from model.finance import debiteuren_30_60_90_yuki
from model.utilities import Day
from settings import GRAY, GREEN, YELLOW, ORANGE, RED
from view.operations import months_ago


def omzet_chart():
    # Behaalde omzet per week
    x_end = Day().plus_days(-2).last_monday()
    x_start = x_end.plus_months(-6)
    return VBlock(
        [
            TextBlock("Omzet", MID_SIZE),
            TextBlock("per week, laatste 6 maanden...", DEF_SIZE, color=GRAY),
            TrendLines().chart(
                "omzet_per_week",
                250,
                150,
                x_start=x_start,
                x_end=x_end,
                min_y_axis=0,
                max_y_axis=100_000,
            ),
        ],
        link="billable.html",
    )


def debiteuren_block():
    # betaaltermijn = gemiddelde_betaaltermijn()
    # betaaltermijn_color = dependent_color(betaaltermijn, 45, 30)
    debiteuren = debiteuren_30_60_90_yuki()
    max_y = ceil(sum(debiteuren) / 100_000) * 100_000
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
                    max_y_axis=max(450_000, max_y),
                ),
            ),
        ],
        link="debiteuren.html",
    )


def cash_block():
    return VBlock(
        [
            TextBlock("Cash", MID_SIZE),
            TrendLines().chart("cash", 250, 150, min_y_axis=0, max_y_axis=1_000_000, x_start=months_ago(6)),
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
