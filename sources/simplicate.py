import datetime
import json
import os
import sys

import pandas as pd
from pathlib import Path
from configparser import ConfigParser
from pysimplicate import Simplicate

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


def hours_dataframe():
    global _simplicate_hours_dataframe
    if _simplicate_hours_dataframe.empty:
        _simplicate_hours_dataframe = update_hours()
    return _simplicate_hours_dataframe


def update_hours():
    """This function does the following:
    1. Update all yyy-mm-dd.json files in CACHE_FOLDER that are older than last_simplicate_confirmed_day
    2. Load data from PANDAS_FILE and update it with all yyy-mm-dd.json that have a newer dat than the PANDAS_FILE

    TODO: Loop over datums ipv over json files want er kan er wel eens een missen
    """

    last_simplicate_confirmed_day = datetime.date.today() + datetime.timedelta(
        days=-7
    )  # For now set it to the last week

    # Load or creat the dataframe

    try:
        df = pd.read_pickle(PANDAS_FILE)
        pandas_modified_date = datetime.date.fromtimestamp(os.path.getmtime(PANDAS_FILE)).strftime(DATE_FORMAT)
    except:
        df = None
        pandas_modified_date = '2020-01-01'

    for json_file in os.listdir(CACHE_FOLDER):
        if not json_file.endswith('.json'):
            continue
        json_path = os.path.join(CACHE_FOLDER, json_file)
        day_str = json_file.split('.')[0]
        # Update all yyy-mm-dd.json files in CACHE_FOLDER that are older than last_simplicate_confirmed_day
        json_file_modified_date = datetime.date.fromtimestamp(os.path.getmtime(json_path))
        if json_file_modified_date > last_simplicate_confirmed_day:
            data = hours_data_from_day(datetime.datetime.strptime(day_str, DATE_FORMAT).date())
        elif json_file_modified_date > pandas_modified_date:
            data = json.load(json_path)
        else:
            continue
        # Update the dataframe with he newly loaded data
        flat_data = flatten_hours_data(data)
        if type(df) == pd.DataFrame:
            df.drop(df[df.day == day_str].index, inplace=True)
            c = len(df)
            print(len(df))
            df = df.append(pd.DataFrame(flat_data))
            c = len(df)
            print(len(df))
        else:
            df = pd.DataFrame(flat_data)
    df = df.reset_index(drop=True)
    df.to_pickle(PANDAS_FILE)
    return df


def flatten_hours_data(data):
    result = [
        {
            'employee': d['employee']['name'],
            'organization': d['project']['organization']['name'],
            'project_name': d['project']['name'],
            'project_number': d['project'].get('project_number', ''),
            'service': d['projectservice']['name'],
            'type': d['type']['type'],
            'label': d['type']['label'],
            'billable': d['billable'],
            'tariff': d['tariff'],
            'hours': d['hours'],
            'day': d['start_date'].split()[0],
            'status': d['status'],
            'corrections': d['corrections']['amount'],
        }
        for d in data
    ]
    return result


def hours(
    start_date: str,
    end_date: str,
    only_billable=False,
):
    '''start_date is inclusive, end_date is not'''
    billable = non_billable = other = turnover = 0
    data = hours_data(start_date, end_date)
    for d in data:
        if d['status'] != 'projectmanager_approved' or d['type']['type'] == 'absence':
            continue
        hrs = d['hours']
        corr = d['corrections']['amount']
        if corr > 0:
            hrs += corr
        if d['tariff'] > 0 or d['projectservice']['name'] == 'DevOps & Servers':
            billable += hrs
            turnover += hrs * d['tariff']
            if corr < 0:
                non_billable -= corr
        else:
            other += hrs
    return (billable, non_billable, other, turnover)


def hours_data(start_date: datetime.date, end_date: datetime.date):
    '''start_date is inclusive, end_date is not'''
    assert start_date < end_date, 'start_date should be before end_date'
    data = []
    while start_date != end_date:
        data += hours_data_from_day(start_date)
        start_date += datetime.timedelta(days=1)
    return data


def hours_data_from_day(day: datetime.date):
    cache_file = os.path.join(CACHE_FOLDER, day.strftime(DATE_FORMAT)) + '.json'
    if os.path.isfile(cache_file):
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

    sys.exit()
    billable, non_billable, other, turnover = hours('2021-01-04', '2021-01-23')
    print(billable, non_billable, other)
    print('€', turnover)
    tot = billable + non_billable + other
    prod_perc = int((billable + non_billable) / tot * 100)
    bill_perc = int((billable) / tot * 100)
    print(prod_perc, bill_perc)
