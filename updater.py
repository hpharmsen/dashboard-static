import sys

from middleware.employee import Employee
from middleware.project import Project
from middleware.timesheet import Timesheet
from middleware.trendline import TrendLines
from model import finance
from model.caching import cache_created_time_stamp, clear_cache
from model.resultaat import update_omzet_per_week
from model.travelbase import update_bookings_per_day
from model.utilities import Day


def update_employee():
    print('Updating employees')
    employee = Employee()
    employee.update()


def update_project():
    print('Updating projects')
    project = Project()
    project.update()


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


if __name__ == '__main__':
    if '--onceaday' in sys.argv:
        cache_created = cache_created_time_stamp()  # todo: deze lijkt te resetten als dashboard heeft gedraaid
        yesterday = Day().prev()
        if cache_created and Day(cache_created) > yesterday:
            print('Script has already run today: exiting')
            sys.exit()
        clear_cache()
    if '--nocache' in sys.argv:
        clear_cache()

    update_employee()
    update_project()
    update_timesheet()
    update_travelbase()
    update_finance()
