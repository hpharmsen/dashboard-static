"""Main program for the dashboard. Start as python main.py, pyhton main.py --nocache or pyhton main.py --onceaday"""

# TODO: The list below is my backlog

# Afspraken met Gert;
# √ Uitrekenen van beschikbare uren toch op basis vabn rooster. Evt rooster/verzuim/verlof apart.
# √ Billable percentage erbij in maandrapportage
# √ Op de homepage de maandrapportagecijfers per week
# √ Met staafgrafiek per week met % effectief en % billable

# Winstgevendheid: uitgaande van een productiviteit van 85%?
# Padding left/right/top/bottom mogelijk maken

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
# ================================================


# FINANCE
# - Vergelijking met begroting
# - Omzet prognose uit Simplicate??

# COMMERCE
# - Percentage Herhaalopdrachten (churn)

# OPERATIONS
# - Effective rate = Bruto marge / alle declarabele uren (DDA: 96 bij een listprice van 103)
# - Gemiddeld uurtarief op billable uren en totaal (omzet/uren)
# - Billable uren vs geplande uren?
# Uit de teamleader whitepaper
# - 1. Gemiddelde opbrengst per uur (%) = Factureerbare waarde per uur / kosten per uur
# - Factureerbare waarde per uur (€) = beschikbare budget te delen door het aantal gepresteerde uren op projecten.
# - Kosten per uur (€) = Loon + onkosten + (algemene kosten / #werkn).
#   en dat deel je door de netto capaciteit (billable en intern maar zonder ziek en vakantiedagen)
# - 2. Performance  (%)  = Efficiëntie x Billability
# - Efficiëntie (%) = gefactureerde waarde delen door intrinsieke waarde (budget) van diezelfde periode.
# - Billability  (%) = factureerbare uren / nettocapaciteit (= het aantal uren dat iemand effectief werkt)
# - Wensen van Gert: https://www.notion.so/teamoberon/Dashboard-wensen-5305f0b45827460ba6b0d1c5a408dffd

# HR
# - Begroot aantal mensen


import datetime
import os
import shutil
import sys
from pathlib import Path

from model.caching import load_cache, clear_cache, cache_created_time_stamp
from model.finance import cash
from model.log import init_log
from settings import get_output_folder
from view.billable import render_billable_page
from view.correcties import render_correcties_page
from view.dashboard import render_dashboard
from view.debiteuren import render_debiteuren_page
from view.onderhanden_werk import render_onderhanden_werk_page
from view.resultaat_berekening import render_resultaat_berekening
from view.sales import render_sales_page
from view.travelbase import render_travelbase_page
from view.winstgevendheid import render_winstgevendheid_page


def main():
    ''' What it says: the main function '''
    cd_to_script_path()
    output_folder = get_output_folder()
    clear_the_cache = process_command_line_params()
    if clear_the_cache:
        clear_cache()
    load_cache()
    module_initialisations()
    copy_resources(output_folder)
    render_all_pages(output_folder)


def module_initialisations():
    cash() # Update cash trend on loading of this module'''
    init_log() # Start log entry with the current date


def cd_to_script_path():
    path_to_go = os.path.dirname(__file__)
    if path_to_go:
        os.chdir(path_to_go)


def process_command_line_params():
    clear_the_cache = False
    for param in sys.argv[1:]:
        if param == '--nocache':
            clear_the_cache = True
        if param == '--onceaday':
            cache_created = cache_created_time_stamp()
            yesterday = datetime.datetime.today().date() + datetime.timedelta(days=-1)
            if cache_created and cache_created.date() > yesterday:
                print('Script has already run today: exiting')
                sys.exit()
            clear_the_cache = True
    return clear_the_cache


def copy_resources(output_folder):
    # Copy things like js and css files
    resource_path = Path(__file__).resolve().parent / 'resources'
    for path in resource_path.iterdir():
        if path.is_file() and path.name[0] != '.':
            shutil.copyfile(path, output_folder / path.name)


def render_all_pages(output_folder):
    # render the html pages
    # print('..vrije dagen')
    # render_vrije_dagen_page(output_folder)
    print('..sales')
    render_sales_page(output_folder)
    print('..onderhanden')
    render_onderhanden_werk_page(output_folder)
    print('..debiteuren')
    render_debiteuren_page(output_folder)
    print('..billable')
    render_billable_page(output_folder)
    print('..winstgevendheid')
    render_winstgevendheid_page(output_folder)
    print('..resultaatberekening')
    render_resultaat_berekening(output_folder)
    print('..correcties')
    render_correcties_page(output_folder)
    # print('..verzuim')
    # render_verzuim_page(output_folder)
    print('..travelbase')
    render_travelbase_page(output_folder)

    # Pages missing since the move to Simplicate. They might or might not return.
    # render_resultaat_vergelijking_page(output_folder)
    # render_productiviteit_page(output_folder)
    print('..dashboard')
    render_dashboard(output_folder)


if __name__ == '__main__':
    main()
