import datetime
import os
from pathlib import Path

from layout.basic_layout import HEADER_SIZE
from layout.block import Page, TextBlock
from maandrapport import HoursData, kpi_grid
from model.utilities import Day, Period
from settings import (
    dependent_color,
    EFFECTIVITY_RED,
    EFFECTIVITY_GREEN,
    get_output_folder,
    CORRECTIONS_RED,
    CORRECTIONS_GREEN,
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
    weeks = 20
    if year:
        # Use given year. Create page with year name in it
        html_page = f'operations {year}.html'
    else:
        # Use the current year (default)
        year = int(datetime.datetime.today().strftime('%Y'))
        html_page = 'operations.html'
    total_period = Period(f'{year}-01-01', f'{year + 1}-01-01')
    page = Page(
        [
            TextBlock('Operations KPI' 's', HEADER_SIZE),
            TextBlock(
                f"Belangrijkste KPI's per week de afgelopen {weeks} weken",
                color="gray",
            ),
            kpi_block(weeks=weeks, total_period=total_period, total_title='YTD'),
        ]
    )
    page.render(output_folder / html_page)


def kpi_block(weeks=4, verbose=True, total_period=None, total_title=''):
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


def operations_data(weeks, total_period=None, total_title=''):
    monday = Day().last_monday()
    hours_data = []
    headers = []
    for w in range(weeks):
        monday_earlier = monday.plus_days(-7)
        period = Period(monday_earlier, monday)
        hours_data = [HoursData(period)] + hours_data
        headers = [monday_earlier.strftime('wk %W')] + headers
        monday = monday_earlier
    if total_period:
        headers += ['', total_title]
        hours_data += [None, HoursData(total_period)]
    return headers, hours_data


if __name__ == '__main__':
    os.chdir('..')
    render_operations_page(get_output_folder())
