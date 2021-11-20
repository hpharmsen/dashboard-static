import datetime
import os
from pathlib import Path

from layout.basic_layout import headersize
from layout.block import Page, TextBlock
from maandrapportage.maandrapport import HoursData, KPIgrid
from settings import (
    dependent_color,
    EFFECTIVITY_RED,
    EFFECTIVITY_GREEN,
    get_output_folder,
    CORRECTIONS_RED,
    CORRECTIONS_GREEN,
)


def render_operations_page(output_folder: Path):
    weeks = 20
    page = Page(
        [
            TextBlock('Operations KPI' 's', headersize),
            TextBlock(
                f"Belangrijkste KPI's per week de afgelopen {weeks} weken",
                color="gray",
            ),
            kpi_grid(weeks=weeks, reverse=False),
        ]
    )
    page.render(output_folder / 'operations.html')


def kpi_grid(weeks=4, reverse=False):
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    data = []
    week_numbers = []
    for _ in range(weeks):
        monday_earlier = monday - datetime.timedelta(days=7)
        if reverse:
            data += [HoursData(monday_earlier, monday)]
            week_numbers += [monday_earlier.strftime('wk %W')]
        else:
            data = [HoursData(monday_earlier, monday)] + data
            week_numbers = [monday_earlier.strftime('wk %W')] + week_numbers
        monday = monday_earlier
    effectivity_coloring = lambda value: dependent_color(value.effectivity(), EFFECTIVITY_RED, EFFECTIVITY_GREEN)
    corrections_coloring = lambda value: dependent_color(value.correcties_perc(), CORRECTIONS_RED, CORRECTIONS_GREEN)
    return KPIgrid(
        week_numbers,
        data,
        verbose=False,
        effectivity_coloring=effectivity_coloring,
        corrections_coloring=corrections_coloring,
    )


if __name__ == '__main__':
    os.chdir('..')
    render_operations_page(get_output_folder())
