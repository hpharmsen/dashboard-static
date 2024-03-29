"""Main program for the dashboard. Start as python main.py, pyhton main.py --nocache or pyhton main.py --onceaday"""

# TODO: The list below is my backlog

# Winstgevendheid: uitgaande van een productiviteit van 85%?
# Padding left/right/top/bottom mogelijk maken

# OPERATIONS
# Service Team wordt volgens mij nu niet meegerekend als 'gepland', of ik kijk verkeerd. Zou wel moeten.

# FINANCE
# - Vergelijking met begroting
# - Omzet prognose uit Simplicate??

# COMMERCE
# - Percentage Herhaalopdrachten (churn)

# CORRECTIES
# Joost: Idee: bij deze getallen in het dashboard ook de totale geboekte uren tot aan dat moment weergeven.
# Of nog beter: een percentage van de totale uren tot aan dat moment. Zet het in perspectief.

# HR
# - Begroot aantal mensen
# - Absence.html grafisch met 13 weken op de hor as en mensen op de ver as. Totaal eronder per week.

# Interactieve pagina waar je gegevens kan vinden zoals
# - Rooster uren, verlof, verzuim, beschikbare uren, effectiviteit, klant uren correcties, billable uren billable perc uurloon en omzet op uren
# - Per tijdseenheid, voor directe fte's of iedereen, per team, per persoon, per project


import datetime
import os
import shutil
import sys
from pathlib import Path

from model.caching import load_cache, clear_cache, cache_created_time_stamp
from settings import get_output_folder

# from view.billable import render_billable_page
from view.booked import render_booked_page
from view.correcties import render_correcties_page
from view.dashboard import render_dashboard
from view.debiteuren import render_debiteuren_page
from view.onderhanden_werk import render_onderhanden_werk_page
from view.operations import render_operations_page
from view.sales import render_sales_page
from view.travelbase import render_travelbase_page
from view.verzuim import render_verzuim_page
from view.winstgevendheid import render_winstgevendheid_page


def main():
    """What it says: the main function"""
    cd_to_script_path()
    output_folder = get_output_folder()
    clear_the_cache = process_command_line_params()
    if clear_the_cache:
        clear_cache()
    load_cache()
    copy_resources(output_folder)
    render_all_pages(output_folder)


def cd_to_script_path():
    path_to_go = os.path.dirname(__file__)
    if path_to_go:
        os.chdir(path_to_go)


def process_command_line_params():
    clear_the_cache = False
    for param in sys.argv[1:]:
        if param == "--nocache":
            clear_the_cache = True
        if param == "--onceaday":
            cache_created = cache_created_time_stamp()
            yesterday = datetime.datetime.today().date() + datetime.timedelta(days=-1)
            if cache_created and cache_created.day() > yesterday:
                print("Script has already run today: exiting")
                sys.exit()
            clear_the_cache = True
    return clear_the_cache


def copy_resources(output_folder):
    # Copy things like js and css files
    resource_path = Path(__file__).resolve().parent / "resources"
    for path in resource_path.iterdir():
        if path.is_file() and path.name[0] != ".":
            shutil.copyfile(path, output_folder / path.name)


def render_all_pages(output_folder):
    # render the html pages
    # print('..vrije dagen')
    # render_vrije_dagen_page(output_folder)
    print("..sales")
    render_sales_page(output_folder)
    print("..onderhanden")
    render_onderhanden_werk_page(output_folder)
    print("..debiteuren")
    render_debiteuren_page(output_folder)
    print("..operations")
    render_operations_page(output_folder)
    print("..billable")
    # render_billable_page(output_folder)
    print("..winstgevendheid")
    render_winstgevendheid_page(output_folder)
    # print('..resultaatberekening')
    # render_resultaat_berekening(output_folder)
    print("..correcties")
    render_correcties_page(output_folder)
    print("..verzuim")
    render_verzuim_page(output_folder)
    print("..travelbase")
    render_travelbase_page(output_folder)
    print("..geboekte uren")
    render_booked_page(get_output_folder())

    # Pages missing since the move to Simplicate. They might or might not return.
    # render_resultaat_vergelijking_page(output_folder)
    # render_productiviteit_page(output_folder)
    print("..dashboard")
    render_dashboard(output_folder)


if __name__ == "__main__":
    main()
