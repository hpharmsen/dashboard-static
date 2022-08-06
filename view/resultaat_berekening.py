""" Voor het genereren van de resultaat_berekening.html pagina
    waarin stap voor stap staat hoe het resultaat is berekend."""
import os
from decimal import Decimal
from functools import partial
from pathlib import Path

from layout.basic_layout import DEF_SIZE, MID_SIZE

# from model.onderhanden_werk import simplicate_onderhanden_werk
from layout.block import TextBlock, Block, Page, VBlock, HBlock, Grid
from model.caching import clear_cache
from model.log import log
from model.resultaat import (
    omzet_begroot,
    omzet_tm_maand,
    omzet_tm_nu,
    bruto_marge_werkelijk,
    kosten_werkelijk,
    winst_begroot,
    winst_werkelijk,
    projectkosten_tm_nu,
    laatste_geboekte_maand,
    projectkosten_tm_maand,
    kosten_boekhoudkundig_tm_maand,
    kosten_begroot_na_maand,
)
from settings import get_output_folder, MAANDEN


def add_row(grid, *args, bold=False, coloring=None):
    row = []
    style = "font-weight:bold" if bold else ""
    for idx, arg in enumerate(args):
        if not isinstance(arg, Block):
            text_format = url = ""
            if isinstance(arg, tuple):
                arg, url = arg
            if isinstance(arg, (int, Decimal, float)):
                text_format = "."
            colorfunc = (
                partial(coloring, idx) if coloring else None
            )  # Convert function with idx, value as function to value as function
            arg = TextBlock(
                arg,
                DEF_SIZE,
                style=style,
                text_format=text_format,
                url=url,
                color=colorfunc,
            )
        row += [arg]
    grid.add_row(row)


def winst_berekening_block():
    grid = Grid(
        cols=5, aligns=["left", "right", "right", "right", "right"], has_header=True
    )

    laatste_maand = laatste_geboekte_maand()
    naam_laatste_maand = MAANDEN[laatste_maand - 1]
    naam_huidige_maand = MAANDEN[laatste_maand]
    yuki_omzet_url = (
        "https://oberon.yukiworks.nl/domain/aspx/Finances.aspx?app=FinReports.aspx"
    )
    begroting_url = "https://docs.google.com/spreadsheets/d/1KsVEIBcnlntGR9dHYn_gSREmpoidWUUZoGlCN7ck7Zo/edit#gid=2127576386"

    add_row(
        grid, "", "Boekhouding (Yuki)", "Correctie", "Totaal nu", "Begroot", bold=True
    )

    omzet_tm_laatste_maand = omzet_tm_maand(laatste_maand)
    add_row(
        grid,
        f"Omzet t/m {naam_laatste_maand}",
        (omzet_tm_laatste_maand, yuki_omzet_url),
    )

    projectkosten_tm_laatste_maand = projectkosten_tm_maand(laatste_maand)
    add_row(
        grid,
        f"Projectkosten t/m {naam_laatste_maand}",
        (-projectkosten_tm_maand(laatste_maand), yuki_omzet_url),
    )

    omzet_nu = omzet_tm_nu()
    add_row(
        grid,
        f"Omzet vanaf {naam_huidige_maand}",
        "",
        (omzet_nu - omzet_tm_laatste_maand, yuki_omzet_url),
        "",
        "",
    )

    add_row(
        grid,
        f"Projectkosten vanaf {naam_huidige_maand}",
        "",
        (
            -projectkosten_tm_nu() + projectkosten_tm_maand(laatste_maand),
            yuki_omzet_url,
        ),
    )

    onderhanden = simplicate_onderhanden_werk()
    add_row(
        grid,
        "Onderhanden werk nu (Simplicate)",
        "",
        (onderhanden, "onderhanden.html"),
        "",
        "",
    )

    begroot = omzet_begroot()
    werkelijk = bruto_marge_werkelijk()
    add_row(
        grid,
        "Opbrengsten",
        omzet_tm_laatste_maand - projectkosten_tm_laatste_maand,
        "",
        werkelijk,
        begroot,
        bold=True,
    )
    add_row(grid)

    kosten_tm_laatste_maand = kosten_boekhoudkundig_tm_maand(laatste_maand)
    add_row(
        grid,
        f"Kosten t/m {naam_laatste_maand}",
        (kosten_tm_laatste_maand, yuki_omzet_url),
        "",
        "",
        "",
    )

    begroot = kosten_begroot_na_maand(laatste_maand)
    add_row(
        grid,
        f"Begrote kosten vanaf {naam_huidige_maand}",
        "",
        (begroot, begroting_url),
        "",
        "",
    )

    add_row(
        grid,
        "Kosten",
        kosten_tm_laatste_maand,
        "",
        kosten_werkelijk(),
        kosten_tm_laatste_maand + begroot,
        bold=True,
    )
    add_row(grid)

    yuki_winst = (
        omzet_tm_laatste_maand
        - projectkosten_tm_laatste_maand
        - kosten_tm_laatste_maand
    )
    werkelijk = winst_werkelijk()
    begroot = winst_begroot()
    add_row(
        grid,
        "Winst",
        yuki_winst,
        "",
        werkelijk,
        begroot,
        bold=True,
    )
    return VBlock(
        [TextBlock("Winstberekening", MID_SIZE), grid], block_id="Winstberekening"
    )


def render_resultaat_berekening(output_folder: Path):

    page = Page([HBlock([winst_berekening_block()])])
    page.render(output_folder / "resultaat_berekening.html")


if __name__ == "__main__":
    os.chdir("..")
    clear_cache()
    render_resultaat_berekening(get_output_folder())
