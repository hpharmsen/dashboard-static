from layout.basic_layout import MID_SIZE, DEF_SIZE
from layout.block import VBlock, TextBlock, HBlock
from layout.chart import ChartConfig, LineChart
from model.organisatie import booked_days_before_noon, aantal_fte, aantal_mensen, verzuimpercentage
from model.utilities import Period, Day
from settings import BLACK, GRAY, dependent_color


def team_block():
    fte, direct_fte = aantal_fte()
    # fte_begroot = aantal_fte_begroot()
    fte_color = BLACK  # dependent_color(fte_begroot - fte, 1, -1)

    return VBlock(
        [
            TextBlock("Team", MID_SIZE),
            HBlock(
                [
                    VBlock(
                        [
                            TextBlock("Mensen", DEF_SIZE, padding=5, color=GRAY),
                            TextBlock(aantal_mensen(), MID_SIZE, text_format=".5"),
                        ]
                    ),
                    VBlock(
                        [
                            TextBlock("FTE's", DEF_SIZE, padding=5, color=GRAY),
                            TextBlock(fte, MID_SIZE, color=fte_color, text_format=".5"),
                        ]
                    ),
                    VBlock(
                        [
                            TextBlock("Direct FTE's", DEF_SIZE, padding=5, color=GRAY),
                            TextBlock(direct_fte, MID_SIZE, color=fte_color, text_format=".5"),
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
            HBlock(
                [
                    TextBlock(
                        verzuim,
                        MID_SIZE,
                        text_format="%",
                        color=verzuim_color,
                        tooltip="Gemiddeld bij DDA in 2019: 3.0%. Groen bij 1,5%, rood bij 3%",
                    ),
                    TextBlock("over de laatste 3 maanden", color=GRAY),
                ],
                padding=60,
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


def uren_boek_block():
    return VBlock([
        TextBlock("Uren boeken", MID_SIZE),
        TextBlock("Percentage dagen dat volledig is geboekt voor 12:00", DEF_SIZE, color=GRAY),
        booked_before_noon_chart(250, 200)
    ], link="booked.html")


def booked_before_noon_chart(width: int, height: int):
    period = Period('2022-01-03')
    data = [d for d in booked_days_before_noon(period)]
    series = [[d['percentage'] for d in data]]
    config = ChartConfig(
        width=width,
        height=height,
        colors=["#6666cc", "#ddeeff"],
        labels=[d['week'] for d in data],
        series_labels=[""],
        min_y_axis=0,
        max_y_axis=100,
        y_axis_max_ticks=5,
        y_axis_step_size=20,
        show_legend=False,
        tension=0.2,
    )
    chart = LineChart(series, config)
    chart.canvas_height_difference = 50
    return chart


if __name__ == '__main__':
    booked_before_noon_chart(300, 200)
