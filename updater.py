import sys

from main import cd_to_script_path
from middleware.employee import Employee
from middleware.invoice import Invoice
from middleware.project import Project
from middleware.service import Service
from middleware.timesheet import Timesheet
from middleware.trendline import TrendLines
from model import finance
from model.caching import clear_cache
from model.resultaat import update_omzet_per_week
from model.travelbase import update_bookings_per_day
from model.utilities import Day
from settings import get_output_folder


def update_employee():
    print('Updating employees')
    employee = Employee()
    employee.repopulate()


def update_project():
    print('Updating projects')
    project = Project()
    project.repopulate()


def update_service():
    print('Updating services')
    service = Service()
    service.repopulate()


def update_timesheet(day=None):
    print('Updating timesheet')
    timesheet = Timesheet()
    timesheet.update(day)


def update_travelbase():
    print('Updating Travelbase')
    update_bookings_per_day('bookings')
    update_bookings_per_day('tickets')


def update_finance():
    cash = finance.cash()
    TrendLines().update('cash', int(cash))
    update_omzet_per_week()


def update_invoices(day=None):
    invoice = Invoice()
    invoice.update(day)


def check_if_has_run_today():
    output_folder = get_output_folder()
    updater_file = output_folder / 'last_updated.txt'
    if updater_file.is_file():
        with open(updater_file) as f:
            last_updated = Day(f.read())
            if last_updated == Day():
                print('Script has already run today: exiting')
                sys.exit()
    with open(updater_file, 'w') as f:
        f.write(str(Day()))


if __name__ == '__main__':
    cd_to_script_path()
    if '--onceaday' in sys.argv:
        check_if_has_run_today()
        clear_cache()
    if '--nocache' in sys.argv:
        clear_cache()

    update_employee()
    update_project()
    update_service()
    update_timesheet()
    update_travelbase()
    update_finance()
