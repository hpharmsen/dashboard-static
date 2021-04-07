# TODO

# FINANCE
# - Vergelijking met begroting
# - Werkkapitaal en cashflow in dashboard
# - Omzet prognose uit Simplicate

# COMMERCE
# - omzet_per_klant_laatste_zes_maanden()
# - Percentage Herhaalopdrachten (churn)

# OPERATIONS
# - Effective rate = Bruto marge / alle declarabele uren (DDA: 96 bij een listprice van 103)
# - Gemiddeld uurtarief op billable uren en totaal (omzet/uren)
# - Billable uren vs geplande uren?
# Uit de teamleader whitepaper
# - 1. Gemiddelde opbrengst per uur (%) = Factureerbare waarde per uur / kosten per uur
# - Factureerbare waarde per uur (€) bereken je door het beschikbare budget te delen door het aantal gepresteerde uren op projecten.
# - Kosten per uur (€) = Loon + onkosten + (algemene kosten / #werkn).
#   en dat deel je door de netto capaciteit (billable en intern maar zonder ziek en vakantiedagen)
# - 2. Performance  (%)  = Efficiëntie x Billability
# - Efficiëntie (%) = gefactureerde waarde delen door intrinsieke waarde (budget) van diezelfde periode.
# - Billability  (%) = factureerbare uren / nettocapaciteit (= het aantal uren dat iemand effectief werkt)

# HR
# - Begroot aantal mensen
# - FTE grafiek, ook begroot en vorig jaar
# - Vergelijking met de begroting per maand (Ik vind het een beetje jammer dat ik nu niet meer per maand met het opgestelde budget kan vergelijken, of kijk ik niet goed?)

# GENERAL
# - Geen sys.exit bij een fout maar fouten tonen in het dashboard


import sys
import os
import shutil
import subprocess

from model.caching import load_cache, clear_cache
from view.billable import render_billable_page
from view.correcties import render_correcties_page
from view.dashboard import render_dashboard
from view.debiteuren import render_debiteuren_page
from view.sales import render_sales_page

# from view.service import render_service_page
# from view.service_issues import render_service_issues_page
from view.verzuim import render_verzuim_page
from view.vrije_dagen import render_vrije_dagen_page
from view.winstgevendheid import render_winstgevendheid_page
from view.onderhanden_werk import render_onderhanden_werk_page
from view.resultaat_berekening import render_resultaat_berekening
from view.budget import render_budget_status_page
from view.target import render_target_page
from view.travelbase import render_travelbase_page

from configparser import ConfigParser
from pathlib import Path



def main():
    cd_to_script_path()
    initialize_cache()
    output_folder = get_output_folder()
    copy_resources(output_folder)
    render_all_pages(output_folder)

def get_output_folder():
    ini = ConfigParser()
    ini.read(Path(__file__).resolve().parent / 'sources' / 'credentials.ini')
    return Path(ini['output']['folder'])


def cd_to_script_path():
    path_to_go = os.path.dirname(__file__)
    if path_to_go:
        os.chdir(path_to_go)


def initialize_cache():
    for param in sys.argv[1:]:
        if param == '--nocache':
            clear_cache()
    load_cache()


def copy_resources(output_folder):
    # Copy things like js and css files
    resource_path = Path(__file__).resolve().parent / 'resources'
    for p in resource_path.iterdir():
        if p.is_file() and p.name[0] != '.':
            shutil.copyfile( p, output_folder / p.name )


def render_all_pages(output_folder):
    # render the html pages
    print( '..vrije dagen')
    render_vrije_dagen_page(output_folder)
    print( '..sales')
    render_sales_page(output_folder)
    print( '..onderhanden')
    render_onderhanden_werk_page(output_folder)
    print( '..debiteuren')
    render_debiteuren_page(output_folder)
    print( '..billable')
    render_billable_page(output_folder)
    print( '..winstgevendheid')
    render_winstgevendheid_page(output_folder)
    print( '..resultaatberekening')
    render_resultaat_berekening(output_folder)
    print( '..correcties')
    render_correcties_page(output_folder)
    print( '..travelbase')
    render_travelbase_page(output_folder)
    print( '..verzuim')
    render_verzuim_page(output_folder)

    # Pages missing since the move to Simplicate. They might or might not return.
    # render_resultaat_vergelijking_page(output_folder)
    # render_productiviteit_page(output_folder)
    # render_tor_page(output_folder)
    # render_service_issues_page(output_folder)
    # render_budget_status_page(output_folder)
    # render_target_page(output_folder)
    # render_service_page(output_folder)
    print( '..dashboard')
    render_dashboard(output_folder)

if __name__ == '__main__':
    main()
