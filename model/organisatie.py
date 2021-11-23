import datetime
import os
from datetime import datetime

import pandas as pd

from model.caching import cache
from model.utilities import fraction_of_the_year_past, Period
from sources.googlesheet import sheet_tab, sheet_value
from sources.simplicate import hours_dataframe, simplicate

FTE_SHEET = 'Begroting 2020'
FTE_TAB = 'Personeelsplanning'
FTE_ROW = 30
FTE_START_COL = 4


@cache(hours=168)
def aantal_mensen(hours=168):
    tab = sheet_tab('Contracten werknemers', 'stats')
    return sheet_value(tab, 2, 6)


@cache(hours=168)
def aantal_fte():
    tab = sheet_tab('Contracten werknemers', 'stats')
    return sheet_value(tab, 3, 6)


@cache(hours=168)
def aantal_fte_begroot():
    tab = sheet_tab(FTE_SHEET, FTE_TAB)
    m = datetime.today().month
    res = sheet_value(tab, FTE_ROW, FTE_START_COL + m - 1)
    return res


def verzuimpercentage(period: Period):
    verzuim = verzuim_absence_hours(period)
    normal = verzuim_normal_hours(period)
    percentage = 100 * verzuim / (normal + verzuim)
    return percentage


def verzuim_normal_hours(period: Period):
    result = hours_dataframe(period).query(f'type=="normal"')['hours'].sum()
    return result


def verzuim_absence_hours(period: Period, employees: list = []):
    query = f'type!="normal" and project_name=="Verzuim / Sick leave"'
    if employees:
        query += ' and employee in @employees'
    result = hours_dataframe(period).query(query)['hours'].sum()
    return result


def leave_hours(period: Period, employees: list = []):
    query = f'type!="normal" and project_name=="Verlof / Leave"'
    if employees:
        query += ' and employee in @employees'
    result = hours_dataframe(period).query(query)['hours'].sum()
    return result


def verzuim_list(period):
    result = (
        hours_dataframe(period)
            .query(
            f'type=="absence" and label !="Feestdagenverlof / National holidays leave" and hours>0'
        )
            .sort_values(['employee', 'day'])[['employee', 'day', 'label', 'hours']]
    )
    return result


# @reportz(hours=24)
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


if __name__ == '__main__':
    os.chdir('..')
    # print(verzuim_list(verzuim_from_day(91)))
