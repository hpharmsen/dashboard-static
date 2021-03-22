# TODO
# omzet_per_klant_laatste_zes_maanden()
# Gemiddeld uurtarief op billable uren en totaal (omzet/uren)

# - Omzet prognose uit Simplicate
# - Begroot aantal mensen
# - Verzuim en vrije dagen uit Simplicate

# - Billable uren vs geplande uren?

# Elke medewerker heeft een rooster, zodat hij weet hoeveel uren je werkt p/w.
# Daar zouden vaste vrije dagen uit kunnen komen (bv elke oneven woensdag).
# Dat zit wrs. op een heel andere plek in de API inderdaad (employee>roster?)
# Die feestdagen zijn een speciale categorie van verlof waarbij het niet van de verlofuren af gaat.
# Die zitten, lijk mij, API-technisch wel op dezelfde plek.
# Alleen zag gisteren toevallig dat 2de paasdag niet op planning stond, dus wellicht toch niet helemaal.

# Productiviteit
#  - Effective rate= Bruto marge / alle declarabele uren (DDA: 96 bij een listprice van 103)
# Organisatie
# - FTE grafiek, ook begroot en vorig jaar
# - Vergelijking met de begroting per maand (Ik vind het een beetje jammer dat ik nu niet meer per maand met het opgestelde budget kan vergelijken, of kijk ik niet goed?)
# Serviceklant pagina
# - Wat een klant heeft uitgegeven
# - Chart per prio
# jira credentials in config.ini
#
# - Vergelijking met begroting
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
from view.vrije_dagen import render_vrije_dagen_page
from view.winstgevendheid import render_winstgevendheid_page
from view.onderhanden_werk import render_onderhanden_werk_page
from view.resultaat_berekening import render_resultaat_berekening
from view.budget import render_budget_status_page
from view.target import render_target_page

from configparser import ConfigParser
from pathlib import Path

ini = ConfigParser()
ini.read(Path(__file__).resolve().parent / 'sources' / 'credentials.ini')
output_folder = Path(ini['output']['folder'])


def main():
    cd_to_script_path()
    initialize_cache()
    copy_resources()
    render_all_pages()


def cd_to_script_path():
    path_to_go = os.path.dirname(__file__)
    if path_to_go:
        os.chdir(path_to_go)


def initialize_cache():
    for param in sys.argv[1:]:
        if param == '--nocache':
            clear_cache()
    load_cache()


def copy_resources():
    resource_path = Path(__file__).resolve().parent / 'resources'
    for p in resource_path.iterdir():
        if p.is_file() and p.name[0] != '.':
            shutil.copyfile( p, output_folder / p.name )


def render_all_pages():
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
