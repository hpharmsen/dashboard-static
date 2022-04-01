import datetime
import os
from datetime import datetime

import pandas as pd

import middleware.middleware_utils
from middleware.timesheet import Timesheet
from model.caching import cache
from model.utilities import fraction_of_the_year_past, Period, Day
from sources.googlesheet import sheet_tab, sheet_value, HeaderSheet
from sources.simplicate import simplicate

FTE_SHEET = 'Begroting 2020'
FTE_TAB = 'Personeelsplanning'
FTE_ROW = 30
FTE_START_COL = 4


# @cache(hours=168)
def aantal_mensen(hours=168):
    tab = HeaderSheet('Contracten werknemers', 'stats')
    return tab['Mensen', 'Totaal']


#@cache(hours=168)
def aantal_fte():
    tab = HeaderSheet('Contracten werknemers', 'stats')
    return tab['FTE', 'Totaal'], tab['Direct FTE', 'Totaal']


@cache(hours=168)
def aantal_fte_begroot():
    tab = sheet_tab(FTE_SHEET, FTE_TAB)
    m = datetime.today().month
    res = sheet_value(tab, FTE_ROW, FTE_START_COL + m - 1)
    return res


def verzuimpercentage(period: Period):
    timesheet = Timesheet()
    verzuim = timesheet.absence_hours(period)
    normal = timesheet.normal_hours(period)
    percentage = 100 * verzuim / (normal + verzuim)
    return percentage


def verzuim_list(period):
    timesheet = Timesheet()
    list_of_dicts = list(timesheet.parameterized_query(
        period,
        'type="absence" and hours>0',
        sort=['employee', 'day'],
    ))
    if not list_of_dicts:
        return []
    result = []
    last = list_of_dicts[0]
    last_day = Day(last['day'])
    for d in list_of_dicts[1:]:
        if d['employee'] == last['employee'] and d['label'] == last['label'] and Day(d['day']) - last_day <= 4:
            last['hours'] += d['hours']
        else:
            result += [[last['employee'], last['day'], last['label'], float(last['hours'] / 8)]]
            last = d
        last_day = Day(d['day'])
    result += [[last['employee'], last['day'], last['label'], float(last['hours'] / 8)]]
    return result


@cache(hours=24)
def vrije_dagen_overzicht():
    sim = simplicate()
    year = datetime.today().year
    frac = fraction_of_the_year_past()

    # Get the list of current employees
    employees = sim.employee({'status': 'active'})
    employees = [u['name'] for u in employees if u['name'] != 'Filipe José Mariano dos Santos']

    # 1. Get the balance of all active employees per start of the year
    balance_list = sim.to_pandas(sim.leavebalance())

    # Filter the list to only active employees and balance changing leaves
    balance_list = balance_list[balance_list.employee_name.isin(employees)].query('leavetype_affects_balance==True')

    year_start = balance_list.query(f'year<{year}').groupby(['employee_name']).sum('balance')['balance'] / 8

    # 2. Get the newly available free days this year
    this_year_all = sim.to_pandas(sim.leave({'year': year}))
    this_year = this_year_all[this_year_all.employee_name.isin(employees)].query('leavetype_affects_balance==True')
    this_year_new = this_year.groupby(['employee_name']).max('hours')['hours'] / 8  # ouch!

    # 2b. Calculate the days already past
    # now = datetime.datetime.now()
    # this_year_done = this_year.apply(lambda a: max(0,(now - a['start_date'].strptime('%Y-%m-%d %H:%M;%S')).days*8), axis=1)

    # 3. Get the balance for this year
    this_year_balance = this_year.groupby(['employee_name']).sum('hours')['hours'] / 8

    # 4. Get the days

    # 4. Put them all in one overview
    overview = pd.concat([year_start, this_year_new, this_year_balance], axis=1).fillna(0)
    overview.columns = ['year_start', 'this_year_new', 'this_year_balance']

    # 5. Plus extra calculated columns
    overview['available'] = overview.apply(lambda x: x['year_start'] + x['this_year_balance'], axis=1)

    # Pool = Last + Year * Frac - Done
    overview['pool'] = overview.apply(lambda x: x['year_start'] + x['this_year_new'] * frac, axis=1)
    overview.reset_index(level=0, inplace=True)

    return overview


def vrije_dagen_pool():
    vrije_dagen_overschot = vrije_dagen_overzicht()['pool'].sum()
    FTEs = aantal_fte()
    return vrije_dagen_overschot / FTEs


# @cache(hours=24)
def booked_days_before_noon(period: Period):
    db = middleware.middleware_utils.get_middleware_db()
    fromday = period.fromday.last_monday()
    untilday = period.untilday.last_monday() if period.untilday else Day().last_monday()
    query = f'''
        select year, week, count(*) as aantal from (
            select `day`, `week`, `year`, employee, sum(hours) as tot_hours
            from timesheet
            where day>='{fromday}' and day < '{untilday}' and
                  (DATEDIFF(DATE(created_at), DATE(`day`)) = 0 or 
                  (DATEDIFF(DATE(created_at), DATE(`day`)) = 1 and TIME(created_at) <= '12:00:00'))
            group by `day`, employee
            having tot_hours>=7
            order by employee) q1
        group by year, week
        order by year, week'''
    results = db.query(query)
    return results


if __name__ == '__main__':
    os.chdir('..')
    m = Day().last_monday()
    b = booked_days_before_noon(Period('2022-01-01'))
