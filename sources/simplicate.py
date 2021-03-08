import datetime
import json
import os
from decimal import Decimal

import pandas as pd
from pathlib import Path
from configparser import ConfigParser
from pysimplicate import Simplicate

from model.caching import reportz

_simplicate = None  # Singleton
_simplicate_hours_dataframe = pd.DataFrame()

CACHE_FOLDER = 'sources/simplicate_cache'
PANDAS_FILE = CACHE_FOLDER + '/hours.pd'
DATE_FORMAT = '%Y-%m-%d'


def simplicate():
    global _simplicate
    if not _simplicate:
        ini = ConfigParser()
        ini.read(Path(__file__).resolve().parent / 'credentials.ini')

        subdomain = ini['simplicate']['subdomain']
        api_key = ini['simplicate']['api_key']
        api_secret = ini['simplicate']['api_secret']

        _simplicate = Simplicate(subdomain, api_key, api_secret)
    return _simplicate


@reportz(hours=24)
def active_projects():
    projects = [
        {
            'project': project.get('project_number', ''),
            'spent': project['budget']['hours'].get('value_spent', 0),
            'invoiced': project['budget']['total']['value_invoiced'],
        }
        for project in simplicate().project({'active': True})
    ]
    return projects


def onderhanden_werk_list():
    df = pd.read_pickle(PANDAS_FILE)

    def corrections(project):
        return df.query(f'project_number=="{project}"')['corrections'].sum()

    oh = pd.DataFrame(
        [
            {
                'project': project['project'],
                'spent': project['spent'],
                'corr': corrections(project),
                'inv': project['invoiced'],
                'OH': project['spent'] + corrections(project) - project['invoiced'],
            }
            for project in active_projects()
        ]
    ).sort_values(by=['OH'])

    oh.drop(oh[(oh.project == 'TOR-3')].index, inplace=True)
    return oh


def hours_dataframe():
    global _simplicate_hours_dataframe
    if _simplicate_hours_dataframe.empty:
        _simplicate_hours_dataframe = update_hours()
    return _simplicate_hours_dataframe


def update_hours():

    # Load or create the dataframe
    try:
        df = pd.read_pickle(PANDAS_FILE)
    except Exception as e:
        df = pd.DataFrame()

    # Als pandas file van vandaag is, is het goed voor nu
    if not df.empty and datetime.datetime.fromtimestamp(os.path.getmtime(PANDAS_FILE)).date() == datetime.date.today():
        return df
    # Uitgecommentarieerd zolang ik niet weet of we met indienen van uren gaan werken
    # if df.empty:
    #     first_simplicate_nonconfirmed_day = datetime.date(2021, 1, 1)
    # else:
    #     non_approved = df.query( 'hours > 0 & tariff > 0 and (status=="to_forward" | status=="forwarded") ')
    #     first_simplicate_nonconfirmed_day = datetime.datetime.strptime( non_approved['day'].min(), DATE_FORMAT).date()

    # day = first_simplicate_nonconfirmed_day
    today = datetime.date.today()
    if df.empty:  # Begin bij het begin
        day = datetime.date(2021, 1, 1)
    else:
        day = today + datetime.timedelta(days=-14)  # Zolang ik niet weet of we met indienen van uren gaan werken
    while day < today:

        print(day)
        data = hours_data_from_day(day, use_cache=False)
        # Update the dataframe with he newly loaded data
        flat_data = flatten_hours_data(data)
        if df.empty:
            df = pd.DataFrame(flat_data)
            complement(df)
        else:
            day_str = day.strftime(DATE_FORMAT)
            df.drop(df[df.day == day_str].index, inplace=True)
            new_df = pd.DataFrame(flat_data)
            complement(new_df)
            df = df.append(new_df, ignore_index=True)

        day += datetime.timedelta(days=1)  # Move to the next day before repeating the loop

    df = df.reset_index(drop=True)
    df.to_pickle(PANDAS_FILE)
    return df


def complement(df):
    df['tariff'] = df.apply(lambda a: a['tariff'] / 2 if a['project_number'] == 'TOR-3' else a['tariff'], axis=1)
    df['service_tariff'] = df.apply(
        lambda a: a['service_tariff'] / 2 if a['project_number'] == 'TOR-3' else a['service_tariff'], axis=1
    )
    df['turnover'] = (df['hours'] + df['corrections']) * df['tariff']
    df['week'] = df.apply(lambda a: datetime.datetime.strptime(a['day'], '%Y-%m-%d').isocalendar()[1], axis=1)


def flatten_hours_data(data):
    result = [
        {
            'employee': d['employee']['name'],
            'organization': d['project']['organization']['name'],
            'project_name': d['project']['name'],
            'project_number': d['project'].get('project_number', ''),
            'service': d['projectservice']['name'],
            'type': d['type']['type'],
            'service_tariff': float(d['type']['tariff']),
            'label': d['type']['label'],
            'billable': d['billable'],
            'tariff': d['tariff'],
            'hours': d['hours'],
            'day': d['start_date'].split()[0],
            'status': d.get(
                'status', 'projectmanager_approved'
            ),  # Dat status niet ingevuld is, kan waarschijnlijk alleen bij mijn eigen uren
            'corrections': d['corrections']['amount'],
        }
        for d in data
    ]
    return result


# def hours(
#     start_date: str,
#     end_date: str,
#     only_billable=False,
# ):
#     '''start_date is inclusive, end_date is not'''
#     billable = non_billable = other = turnover = 0
#     data = hours_data(start_date, end_date)
#     for d in data:
#         if d['status'] != 'projectmanager_approved' or d['type']['type'] == 'absence':
#             continue
#         hrs = d['hours']
#         corr = d['corrections']['amount']
#         if corr > 0:
#             hrs += corr
#         if d['tariff'] > 0 or d['projectservice']['name'] == 'DevOps & Servers':
#             billable += hrs
#             turnover += hrs * d['tariff']
#             if corr < 0:
#                 non_billable -= corr
#         else:
#             other += hrs
#     return (billable, non_billable, other, turnover)


# def hours_data(start_date: datetime.date, end_date: datetime.date):
#     '''start_date is inclusive, end_date is not'''
#     assert start_date < end_date, 'start_date should be before end_date'
#     data = []
#     while start_date != end_date:
#         data += hours_data_from_day(start_date)
#         start_date += datetime.timedelta(days=1)
#     return data


def hours_data_from_day(day: datetime.date, use_cache=True):
    cache_file = os.path.join(CACHE_FOLDER, day.strftime(DATE_FORMAT)) + '.json'
    if use_cache and os.path.isfile(cache_file):
        with open(cache_file) as f:
            data = json.load(f)
    else:
        sim = simplicate()
        data = sim.hours({'day': day})
        with open(cache_file, 'w') as f:
            json.dump(data, f)
    return data


if __name__ == '__main__':
    os.chdir('..')
    update_hours()
