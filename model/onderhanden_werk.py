import json
import os
from decimal import Decimal
import requests
import pandas as pd
from model.caching import reportz, load_cache
import model.log as log
from sources.simplicate import simplicate
from settings import ini


@reportz(hours=24)
def project_status_data(date_str=None):
    ''' Get Simplicate project status page in json form '''
    session = requests.Session()
    login_url = 'https://oberon.simplicate.com/site/login'
    login_data = {
        'LoginForm[username]': ini['simplicate']['username'],
        'LoginForm[password]': ini['simplicate']['password'],
    }
    report_url = 'https://oberon.simplicate.com/v1/reporting/process/reloadData?q={"page":"process","project_status":["active"],"myorganizations":["2"]}'  # myorganizations 1: Qikker, 2: Oberon, 3: Travelbase
    if date_str:
        report_url = report_url[:-1] + f',"date":"{date_str}"' + '}'

    session.post(login_url, login_data)
    try:
        try:
            json_data = session.get(report_url).json()
        except:
            json_data = session.get(report_url).json()  # Try again
    except ConnectionResetError:
        log.log_error('simplicate.py', 'onderhanden_werk', 'Connection reset by Simplicate')
        return
    except json.decoder.JSONDecodeError:
        log.log_error('simplicate.py', 'onderhanden_werk', 'JSON DecodeError')
        return
    except:
        log.log_error('simplicate.py', 'onderhanden_werk', 'Unknown error')
        return
    return json_data


@reportz(hours=72)
def simplicate_onderhanden_werk(date_str: str = ''):
    list = ohw_list(simplicate(), date_str)
    if type(list) != pd.DataFrame:
        return 0
    return Decimal(list['ohw'].sum().item())  # Itemw converts numpy.uint64 to Python scalar

def get_project_status_dataframe(date_str:str):
    ''' Convert Simplicates project status page into an enhanced dataframe with own OHW calculation.'''

    def ohw_type(s):
        if s['payment_type'] == 'Vaste prijs':
            return 'Strippenkaart' if s['Budget'] else 'Fixed'
        return 'Normal'

    def calculate_ohw(s):
        # Calculate OHW based on ohw_type
        if s['ohw_type'] == 'Strippenkaart':
            result = -s['Restant budget']
        elif s['ohw_type'] == 'Fixed':
            result = s['Verwacht'] - s['Gefactureerd']
        else:
            result = s['Besteed'] + s['Correcties'] + s[' Besteed'] - s['Gefactureerd'] + s['Marge gerealiseerd']
        return int(result)

    def parse_project_status_json(project_status_json):
        headers = [col['title'] for col in project_status_json['table']['columns']]
        res = []
        for row in project_status_json['table']['rows'][1:]:  # De eerste rij is leeg
            row_values = [rc[0]['value'] for rc in row['columns']]
            subrows = row['subrows']
            for subrow in subrows:
                subrow_values = [src[0]['value'] for src in subrow['columns']]
                rec = {'project': row['headers'][0]['value'], 'service': subrow['headers'][0]['value']}
                for key, val in zip(headers, subrow_values):
                    rec[key] = val
                res += [rec]
        project_status_dataframe = pd.DataFrame(res).replace('-', 0)
        return project_status_dataframe

    def enhance_project_status_dataframe(prs: pd.DataFrame):
        prs['project_number'] = prs.apply(
            lambda s: s['project'].rsplit('(')[-1].split(')')[0], axis=1
        )  # Between () in project
        prs['payment_type'] = prs.apply(
            lambda s: s['service'].rsplit('[')[-1].split(']')[0].strip(), axis=1
        )  # Between [] in service
        prs['service'] = prs.apply(lambda s: s['service'].split(' [')[0].strip(), axis=1)  # Chop off [Vaste prijs]
        prs['ohw_type'] = prs.apply(ohw_type, axis=1)  # Strippenkaart, Fixed or Normal
        prs['OHW2'] = prs.apply(calculate_ohw, axis=1)  # Calculate based on ohw_type
        return prs

    json = project_status_data(date_str)
    if not json:
        return
    df = parse_project_status_json(json)
    enhance_project_status_dataframe(df)
    return df


def simplicate_projects_and_services(sim):
    '''Get the list of services joined with project data like organization and pm '''
    services = (
        sim.to_pandas(sim.service())
        .query(f'invoice_method != "Subscription" & track_hours == True & status != "flushed"')[
            ['project_id', 'status', 'id', 'name', 'track_hours', 'start_date', 'end_date']
        ]
        .rename(columns={'id': 'service_id', 'name': 'service', 'status': 'service_status'})
    )

    # Same with the list of projects
    projects = sim.to_pandas(sim.project())[ # {'status': 'tab_pactive'}
        ['id', 'project_number', 'name', 'organization_name', 'project_manager_name']
    ].rename(columns={'id': 'project_id', 'name': 'project_name'})

    # Join them
    project_service = pd.merge(services, projects, on=['project_id'])
    return project_service


def ohw_list(sim, date_str='', minimum_amount=0):
    rename_columns = {
        'project_number_y': 'project_number',
        'OHW2': 'ohw',
        'project_manager_name': 'pm',
        'Besteed': 'besteed',
        'Correcties': 'correcties',
        'Marge gerealiseerd': 'verkoopmarge',
        'Verwacht':'verwacht',
        'Gefactureerd': 'gefactureerd',
        ' Besteed': 'inkoop',
    }
    return_columns = list(rename_columns.values()) + [
        'service',
        'ohw_type',
        'organization_name',
        'project_name',
        'project_id',
        'service_id',
        'start_date',
        'end_date',
    ]

    project_status_dataframe = get_project_status_dataframe(date_str)
    if type(project_status_dataframe) != pd.DataFrame:
        return  # Error occurred, no use to go on
    projects_and_services = simplicate_projects_and_services(sim)
    merged = pd.merge(project_status_dataframe, projects_and_services, on=['project_number', 'service']) \
        .rename(columns=rename_columns) \
        [return_columns]

    if minimum_amount:
        # Get project numbers of all projects with > +/- minimum_amount OWH
        ohw_projects = set(
            merged.groupby(['project_number'])
                .sum('ohw')
            .query(f'abs(ohw) >= {minimum_amount}')
            .reset_index()['project_number']
        )
        # Filter merged with this list
        merged = merged.query('abs(ohw) > 0 & project_number in @ohw_projects').sort_values(by='project_number')

    merged.sort_values(by='project_number')
    return merged


if __name__ == '__main__':
    os.chdir('..')
    load_cache()
    sim = simplicate()
    print(ohw_list(sim)['ohw'].sum())
