import os
from pathlib import Path

from layout.basic_layout import HEADER_SIZE, DEF_SIZE
from layout.block import VBlock, TextBlock, Page, HBlock
from layout.table import Table, TableConfig
from model.organisatie import (
    verzuim_normal_hours,
    verzuim_absence_hours,
    verzuimpercentage,
    verzuim_list,
)
from model.utilities import Period, Day
from settings import get_output_folder, GRAY, dependent_color


def render_verzuim_page(output_folder: Path):
    months = 3
    period = Period(Day().plus_months(-months))
    table = VBlock(
        [
            Table(
                verzuim_list(period),
                TableConfig(
                    headers=["Naam", "Dag", "soort", "Dagen"],
                    aligns=["left", "left", "left", "right"],
                    formats=[
                        "",
                        "",
                        "",
                        ".5",
                    ],
                    totals=[0, 0, 0, 1],
                ),
            ),
        ]
    )

    verzuim = verzuimpercentage(period)
    verzuim_color = dependent_color(verzuim, 3, 1.5)
    page = Page(
        [
            TextBlock("Verzuim", HEADER_SIZE),
            TextBlock(f"De afgelopen {months} maanden", color=GRAY),
            HBlock(
                [
                    VBlock(
                        [
                            TextBlock(
                                "Geboekte uren", DEF_SIZE, color="gray", padding=5
                            ),
                            TextBlock("Verzuim uren", DEF_SIZE, color="gray"),
                            TextBlock("Verzuimopercentage", DEF_SIZE, color="gray"),
                        ]
                    ),
                    VBlock(
                        [
                            TextBlock(
                                verzuim_normal_hours(period),
                                DEF_SIZE,
                                text_format=".",
                                padding=5,
                            ),
                            TextBlock(
                                verzuim_absence_hours(period), DEF_SIZE, text_format="."
                            ),
                            TextBlock(verzuim, verzuim_color, text_format="%1"),
                        ]
                    ),
                ]
            ),
            table,
        ]
    )
    page.render(output_folder / "absence.html")


if __name__ == "__main__":
    os.chdir("..")
    render_verzuim_page(get_output_folder())
