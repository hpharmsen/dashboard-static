import datetime
import os
from datetime import datetime, timedelta

import pandas as pd

from model.utilities import fraction_of_the_year_past
from sources.googlesheet import sheet_tab, sheet_value
from sources.simplicate import hours_dataframe, simplicate, DATE_FORMAT
from model.caching import reportz

FTE_SHEET = 'Begroting 2020'
FTE_TAB = 'Personeelsplanning'
FTE_ROW = 30
FTE_START_COL = 4


@reportz(hours=168)
def aantal_mensen(hours=168):
    tab = sheet_tab('Contracten werknemers', 'stats')
    return sheet_value(tab, 2, 6)


@reportz(hours=168)
def aantal_fte():
    tab = sheet_tab('Contracten werknemers', 'stats')
    return sheet_value(tab, 3, 6)


@reportz(hours=168)
def aantal_fte_begroot():
    tab = sheet_tab(FTE_SHEET, FTE_TAB)
    m = datetime.today().month
    res = sheet_value(tab, FTE_ROW, FTE_START_COL + m - 1)
    return res


def verzuimpercentage(days=91):
    DATE_FORMAT = '%Y-%m-%d'
    from_day = max('2021-01-01', (datetime.today() + timedelta(days=-90)).strftime(DATE_FORMAT))

    full_df = hours_dataframe()
    verzuim = full_df.query(f'type=="absence" and day >="{from_day}"')['hours'].sum()
    normal = full_df.query(f'type=="normal" and day >="{from_day}"')['hours'].sum()
    percentage = 100 * verzuim / (normal + verzuim)
    return percentage


# @reportz(hours=24)
def vrije_dagen_overzicht():
    sim = simplicate()
    today = datetime.today().strftime('%Y-%m-%d')
    year = datetime.today().year
    frac = fraction_of_the_year_past()

    employees = (
        sim.to_pandas(sim.timetable()).query(f"(end_date != end_date) or (end_date>'{today}')").employee_name.unique()
    )  # (end_date != end_date) is to check for NaN
    full_balance_list = sim.to_pandas(sim.leavebalance())
    current_balance_list = full_balance_list[full_balance_list.employee_name.isin(employees)].query(
        'leavetype_affects_balance==True'
    )
    current_balance_list = current_balance_list[
        current_balance_list['employee_name'] != 'Filipe José Mariano dos Santos'
    ]
    last_year = current_balance_list.query(f'year<{year}').groupby(['employee_name']).sum('balance')['balance'] / 8

    # This year
    fulll_thisyear_list = sim.to_pandas(sim.leave({'year': year}))
    current_thisyear_list = fulll_thisyear_list[fulll_thisyear_list.employee_name.isin(employees)].query(
        'leavetype_affects_balance==True'
    )
    this_year_balance = current_thisyear_list.groupby(['employee_name']).sum('hours')['hours'] / 8
    this_year_new = current_thisyear_list.groupby(['employee_name']).max('hours')['hours'] / 8
    overview = pd.concat([last_year, this_year_new, this_year_balance], axis=1).fillna(0)
    overview.columns = ['last_year', 'this_year_new', 'this_year_balance']
    overview['available'] = overview.apply(lambda x: x['last_year'] + x['this_year_balance'], axis=1)
    overview['pool'] = overview.apply(lambda x: x['last_year'] + x['this_year_new'] * frac, axis=1)
    overview.reset_index(level=0, inplace=True)
    # today = datetime.today().strftime(DATE_FORMAT)
    # year = datetime.today().year
    # frac = fraction_of_the_year_past()
    #
    # employees = (
    #     sim.to_pandas(sim.timetable()).query(f"(end_date != end_date) or (end_date>'{today}')").employee_name.unique()
    # )  # (end_date != end_date) is to check for NaN
    # full_balance_list = sim.to_pandas(sim.leavebalance())
    # current_balance_list = full_balance_list[full_balance_list.employee_name.isin(employees)].query(
    #     'leavetype_affects_balance==True'
    # )
    # current_balance_list = current_balance_list[
    #     current_balance_list['employee_name'] != 'Filipe José Mariano dos Santos'
    # ]
    #
    # last_year = current_balance_list.query(f'year<{year}').groupby(['employee_name']).sum('balance')['balance'] / 8
    #
    # # This year
    # fulll_thisyear_list = sim.to_pandas(sim.leave({'year':year}))
    # current_thisyear_list = fulll_thisyear_list[fulll_thisyear_list.employee_name.isin(employees)].query(
    #     'leavetype_affects_balance==True'
    # )
    # this_year_balance = current_thisyear_list.groupby(['employee_name']).sum('hours')['hours'] / 8
    # this_year_new = current_thisyear_list.groupby(['employee_name']).max('hours')['hours'] / 8
    # # used = current_balance_list.query(f'(year=={year}) and (balance<0)').groupby(['employee_name']).sum('balance')[
    # #           'balance'] / -8
    # overview = pd.concat([last_year, this_year_new, this_year_balance], axis=1).fillna(0)
    # overview.columns = ['year_start', 'this_year']
    # overview['available'] = overview.apply(lambda x: x['last_year'] + x['this_year_balance'], axis=1)
    # overview['pool'] = overview.apply(lambda x: x['last_year'] + x['this_year_start'] * frac, axis=1)
    # overview.reset_index(level=0, inplace=True)
    return overview


def vrije_dagen_pool():
    vrije_dagen_overschot = vrije_dagen_overzicht()['pool'].sum()
    FTEs = aantal_fte()
    return vrije_dagen_overschot / FTEs


if __name__ == '__main__':
    os.chdir('..')
    print(vrije_dagen_pool())
