from layout.basic_layout import DEF_SIZE, MID_SIZE
from layout.block import HBlock, VBlock, TextBlock
from layout.chart import ChartConfig, LineChart
from model.marketing import Marketing
from settings import GRAY, BLUE, GREEN, RED, ORANGE


def marketing_kpi_block(sheet: Marketing):
    new_business_link = (
        "https://docs.google.com/spreadsheets/d/1eKR3Ez1SYOt_wAlTXGcxcVyH_d4GHTq76CKJM3Dyxqc/edit#gid=1979554936"
    )
    block = HBlock(
        [
            VBlock(
                [
                    TextBlock(kpi, DEF_SIZE, padding=5, color=GRAY),
                    HBlock(
                        [
                            TextBlock(sheet.total(kpi), MID_SIZE, padding=8),
                            TextBlock(f"  (+{sheet.last(kpi)})", DEF_SIZE, padding=15),
                        ]
                    ),
                ],
                link=new_business_link,
            )
            for kpi in ["MQL", "SQL", "RFP"]
        ]
    )
    return block


def marketing_results_chart(sheet: Marketing):
    width = 250
    height = 200
    series_labels = ["Bereik", "Traffic"]
    series = [sheet.kpi_row(label) for label in series_labels]
    config = ChartConfig(
        width=width,
        height=height,
        colors=[BLUE, GREEN],
        labels=[h.split(".")[0] for h in sheet.column_headers],
        series_labels=series_labels,
        y_axis_max_ticks=5,
        y_axes_placement=["left", "right"],
        tension=0,
    )
    chart = LineChart(series, config)
    chart.canvas_height_difference = 50
    return chart


def marketing_expenses_chart(sheet):
    width = 250
    height = 200
    series_labels = ["€ Totaal", "Uren marketing intern"]
    series = [sheet.kpi_row(label) for label in series_labels]
    config = ChartConfig(
        width=width,
        height=height,
        colors=[RED, ORANGE],
        labels=[h.split(".")[0] for h in sheet.column_headers],
        series_labels=["Geld", "Uren"],
        y_axis_max_ticks=5,
        y_axes_placement=["left", "right"],
        tension=0,
    )
    chart = LineChart(series, config)
    chart.canvas_height_difference = 50
    return chart
