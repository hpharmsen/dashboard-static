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
from model.travelbase import update_bookings_per_month
from model.utilities import Day
from settings import get_output_folder
from sources.yuki import YukiEmptyBodyException, YukiInternalServerErrorException


def update_employee():
    print("Updating employees")
    employee = Employee()
    employee.repopulate()


def update_project():
    print("Updating projects")
    project = Project()
    project.repopulate()


def update_service():
    print("Updating services")
    service = Service()
    service.repopulate()


def update_timesheet(day=None):
    print("Updating timesheet")
    timesheet = Timesheet()
    timesheet.update(day)


def update_travelbase():
    print("Updating Travelbase")
    update_bookings_per_month()


def update_finance():
    try:
        cash = finance.cash()
    except YukiEmptyBodyException:
        print("!! Yuki returned an empty body")
        return
    except YukiInternalServerErrorException:
        print("!! Yuki returned an internal server error")
        return
    TrendLines().update("cash", int(cash))
    update_omzet_per_week()


def update_invoices(day=None):
    if not day:
        day = Day("2021-01-01")
    invoice = Invoice()
    invoice.update(day)


def check_if_has_run_today():
    updater_file = get_output_folder() / "last_updated.txt"
    if updater_file.is_file():
        with open(updater_file) as f:
            last_updated = Day(f.read())
            if last_updated == Day():
                print("Script has already run today: exiting")
                sys.exit()


def mark_as_has_run_today():
    updater_file = get_output_folder() / "last_updated.txt"
    with open(updater_file, "w") as f:
        f.write(str(Day()))


if __name__ == "__main__":
    cd_to_script_path()
    if "--onceaday" in sys.argv:
        check_if_has_run_today()
        clear_cache()
    if "--nocache" in sys.argv:
        clear_cache()

    update_finance()
    update_travelbase()
    update_employee()
    update_project()
    update_service()
    update_timesheet()
    update_invoices(Day().plus_months(-1))

    mark_as_has_run_today()
