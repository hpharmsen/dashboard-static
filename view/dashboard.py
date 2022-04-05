""" Generates the dashboard.html file """
import os

import pandas as pd

from layout.basic_layout import DEF_SIZE, MID_SIZE, HEADER_SIZE
from layout.block import TextBlock, Page, VBlock, HBlock
from middleware.trendline import TrendLines
from model import log
from model.caching import load_cache
from model.marketing import Marketing
from model.sales import sales_waarde
from model.travelbase import get_bookings_per_week, BRANDS
from settings import get_output_folder, RED, GRAY, dependent_color
from view.finance import omzet_chart, debiteuren_block, cash_block
from view.marketing import marketing_kpi_block, marketing_results_chart, marketing_expenses_chart
from view.operations import kpi_block, operations_chart, months_ago, planning_chart, corrections_block
from view.organisatie import booked_before_noon_chart, team_block, verzuim_block, tevredenheid_block
from view.sales import sales_waarde_block
from view.travelbase import scatterchart as travelbase_scatterchart


######### Kolom 1: Marketing ###########


def marketing_block():
    sheet = Marketing("Oberon - Budget + KPI's", "KPIs voor MT", 1, 1)
    marketing_link = (
        "https://docs.google.com/spreadsheets/d/1eKR3Ez1SYOt_wAlTXGcxcVyH_d4GHTq76CKJM3Dyxqc/edit#gid=1965783742"
    )
    return VBlock(
        [
            TextBlock("Marketing", HEADER_SIZE),
            TextBlock("KPI's", MID_SIZE, padding=20),
            TextBlock(f"Bijgewerkt t/m {sheet.column_headers[-1]}", color=GRAY),
            marketing_kpi_block(sheet),
            TextBlock(""),  # Todo: verticale marge mogelijk maken
            TextBlock("Resultaten", MID_SIZE, padding=10),
            marketing_results_chart(sheet),
            TextBlock("Uitgaven", MID_SIZE, padding=10),
            marketing_expenses_chart(sheet),
        ],
        link=marketing_link,
    )


######### Column 2: Sales

def sales_block():
    sales_waarde_value = sales_waarde()
    sales_waarde_color = dependent_color(sales_waarde_value, 250000, 350000)
    return VBlock(
        [
            TextBlock("Sales", HEADER_SIZE),
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
            sales_waarde_block(),
        ]
    )


######### Kolom 3: Operations ###########

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


######### Kolom 4: Finance ###########


def finance_block():
    return VBlock(
        [
            TextBlock("Finance", HEADER_SIZE),
            omzet_chart(),
            debiteuren_block(),
            cash_block(),
        ]
    )


######### Kolom 5: HR ###########

def hr_block():
    return VBlock(
        [
            TextBlock("HR", HEADER_SIZE),
            team_block(),
            tevredenheid_block(),
            verzuim_block(),
            TextBlock("Uren boeken", MID_SIZE),
            TextBlock("Percentage dagen dat volledig is geboekt voor 12:00", DEF_SIZE, color=GRAY),
            booked_before_noon_chart(250, 200),
            # vakantiedagen_block(),
            travelbase_block(),
            error_block(),
        ]
    )


def travelbase_block():
    bookings = get_bookings_per_week(booking_type="bookings", only_complete_weeks=True)
    if not isinstance(bookings, pd.DataFrame):
        return TextBlock("Kon boekingen niet ophalen", color=RED)
    legend = ", ".join([f"{brand}: {int(bookings[brand].sum())}" for brand in BRANDS])
    return VBlock(
        [
            TextBlock("Travelbase", HEADER_SIZE),
            TextBlock("Aantal boekingen per week", color=GRAY),
            travelbase_scatterchart(bookings, 250, 180),
            TextBlock(legend),
        ],
        link="travelbase.html",
    )


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


def render_dashboard(output_folder):
    page = Page([HBlock([marketing_block(), sales_block(), operations_block(), finance_block(), hr_block()])])
    page.render(output_folder / "dashboard.html")


if __name__ == "__main__":
    os.chdir("..")
    load_cache()
    render_dashboard(get_output_folder())
