import os

import pandas as pd

from middleware.middleware import get_middleware_db
from model.caching import cache, load_cache
from model.utilities import Day
from sources.simplicate import simplicate


# @cache(hours=24)
# def project_status_data(date_str=None):
#     ''' Get Simplicate project status page in json form '''
#     session = requests.Session()
#     login_url = 'https://oberon.simplicate.com/site/login'
#     login_data = {
#         'LoginForm[username]': ini['simplicate']['username'],
#         'LoginForm[password]': ini['simplicate']['password'],
#     }
#     report_url = 'https://oberon.simplicate.com/v1/reporting/process/reloadData?q={"page":"process","project_status":["active"],"myorganizations":["2"]}'  # myorganizations 1: Qikker, 2: Oberon, 3: Travelbase
#     if date_str:
#         report_url = report_url[:-1] + f',"date":"{date_str}"' + '}'
#
#     session.post(login_url, login_data)
#     try:
#         try:
#             json_data = session.get(report_url).json()
#         except:
#             json_data = session.get(report_url).json()  # Try again
#     except ConnectionResetError:
#         log.log_error('simplicate.py', 'onderhanden_werk', 'Connection reset by Simplicate')
#         return
#     except json.decoder.JSONDecodeError:
#         log.log_error('simplicate.py', 'onderhanden_werk', 'JSON DecodeError')
#         return
#     except:
#         log.log_error('simplicate.py', 'onderhanden_werk', 'Unknown error')
#         return
#     return json_data
#
#
# @cache(hours=72)
# def simplicate_onderhanden_werk(date_str: str = ''):
#     list = ohw_list(simplicate(), date_str)
#     if not isinstance(list, pd.DataFrame):
#         return 0
#     return Decimal(list['ohw'].sum().item())  # Itemw converts numpy.uint64 to Python scalar
#
#
# def get_project_status_dataframe(date_str: str):
#     ''' Convert Simplicates project status page into an enhanced dataframe with own OHW calculation.'''
#
#     def ohw_type(s):
#         if s['payment_type'] == 'Vaste prijs':
#             if s['Budget'] and s['Budget'] == s['Gefactureerd']:
#                 return 'Strippenkaart'
#             return 'Fixed'
#         return 'Normal'
#
#     def calculate_ohw(s):
#         # Calculate OHW based on ohw_type
#         if s['service_status'] != 'open' and s['Gefactureerd']:
#             return 0  # Service is closed and invoiced
#         if s['ohw_type'] == 'Strippenkaart':
#             result = -s['Restant budget']
#         # elif s['ohw_type'] == 'Fixed':
#         #    result = s['Verwacht'] - s['Gefactureerd']
#         else:
#             result = s['Besteed'] + s['Correcties'] + s[' Besteed'] - s['Gefactureerd'] + s['Marge gerealiseerd']
#         return int(result)
#
#     def parse_project_status_json(project_status_json):
#         headers = [col['title'] for col in project_status_json['table']['columns']]
#         res = []
#         for row in project_status_json['table']['rows'][1:]:  # De eerste rij is leeg
#             row_values = [rc[0]['value'] for rc in row['columns']]
#             subrows = row['subrows']
#             for subrow in subrows:
#                 subrow_values = [src[0]['value'] for src in subrow['columns']]
#                 rec = {'project': row['headers'][0]['value'], 'service': subrow['headers'][0]['value']}
#                 for key, val in zip(headers, subrow_values):
#                     rec[key] = val
#                 res += [rec]
#         project_status_dataframe = pd.DataFrame(res).replace('-', 0)
#         return project_status_dataframe
#
#     def enhance_project_status_dataframe(prs: pd.DataFrame):
#         projects = active_projects()
#         services = active_services()
#         ''' Add extra fields tot the project status datframe like project_number service and real OHW '''
#         get_project_number_between_brackets = lambda s: s['project'].rsplit('(')[-1].split(')')[0]
#         prs['project_number'] = prs.apply(get_project_number_between_brackets, axis=1)  # Between () in project
#
#         get_payment_type_between_brackets = lambda s: s['service'].rsplit('[')[-1].split(']')[0].strip()
#         prs['payment_type'] = prs.apply(get_payment_type_between_brackets, axis=1)
#
#         get_service_part_before_brackets = lambda s: s['service'].split(' [')[0].strip()
#         prs['service'] = prs.apply(get_service_part_before_brackets, axis=1)  # Chop off [Vaste prijs]
#
#         def get_service_status(row):
#             project_number = row['project_number']
#             project_id = projects.get(project_number)
#             if not project_id:
#                 return
#             service_name = row['service']
#             status = 'open' if (project_id, service_name) in services else 'closed'
#             return status
#
#         prs['service_status'] = prs.apply(get_service_status, axis=1)
#
#         prs['ohw_type'] = prs.apply(ohw_type, axis=1)  # Strippenkaart, Fixed or Normal
#         prs['OHW2'] = prs.apply(calculate_ohw, axis=1)  # Calculate based on ohw_type
#         return prs
#
#     json = project_status_data(date_str)
#     if not json:
#         return
#     df = parse_project_status_json(json)
#     enhance_project_status_dataframe(df)
#     return df
#
#
# def simplicate_projects_and_services(sim):
#     '''Get the list of services joined with project data like organization and pm '''
#     services = (
#         sim.to_pandas(sim.service())
#         .query(f'invoice_method != "Subscription" & track_hours == True & status != "flushed"')[
#             ['project_id', 'status', 'id', 'name', 'track_hours', 'start_date', 'end_date']
#         ]
#         .rename(columns={'id': 'service_id', 'name': 'service', 'status': 'service_status'})
#     )
#
#     # Same with the list of projects
#     projects = sim.to_pandas(sim.project())[  # {'status': 'tab_pactive'}
#         ['id', 'project_number', 'name', 'organization_name', 'project_manager_name']
#     ].rename(columns={'id': 'project_id', 'name': 'project_name'})
#
#     # Join them
#     project_service = pd.merge(services, projects, on=['project_id'])
#     return project_service
#
#
# def ohw_list(sim, date_str='', minimum_amount=0):
#     rename_columns = {
#         'project_number_y': 'project_number',
#         'OHW2': 'ohw',
#         'project_manager_name': 'pm',
#         'Besteed': 'besteed',
#         'Correcties': 'correcties',
#         'Marge gerealiseerd': 'verkoopmarge',
#         'Verwacht': 'verwacht',
#         'Gefactureerd': 'gefactureerd',
#         ' Besteed': 'inkoop',
#         'Restant budget': 'restant_budget',
#     }
#     return_columns = list(rename_columns.values()) + [
#         'service',
#         'ohw_type',
#         'organization_name',
#         'project_name',
#         'project_id',
#         'service_id',
#         'start_date',
#         'end_date',
#     ]
#
#     project_status_dataframe = get_project_status_dataframe(date_str)
#     if not isinstance(project_status_dataframe, pd.DataFrame):
#         return  # Error occurred, no use to go on
#     projects_and_services = simplicate_projects_and_services(sim)
#     merged = pd.merge(project_status_dataframe, projects_and_services, on=['project_number', 'service']).rename(
#         columns=rename_columns
#     )[return_columns]
#
#     if minimum_amount:
#         # Get project numbers of all projects with > +/- minimum_amount OWH
#         ohw_projects = set(
#             merged.groupby(['project_number'])
#             .sum('ohw')
#             .query(f'abs(ohw) >= {minimum_amount}')
#             .reset_index()['project_number']
#         )
#         # Filter merged with this list
#         merged = merged.query('abs(ohw) > 0 & project_number in @ohw_projects').sort_values(by='project_number')
#
#     merged.sort_values(by='project_number')
#     return merged

def ohw_list(date: Day):
    minimal_intesting_value = 500
    # Nieuwe methode.
    # 1. Alle active projecten
    # 2. De diensten daarvan
    projects_and_services = simplicate_projects_and_services(date)
    active_services = projects_and_services['service_id'].tolist()

    # 3. Omzet -/- correcties berekenen
    service_df = services_with_their_turnover(date, active_services)

    # 4. Ophalen wat er is gefactureerd
    invoiced = invoiced_by_date(date)

    service_df['invoiced'] = service_df.apply(lambda row: invoiced[row['service_id']], axis=1)

    # Group by project
    project_df = (service_df
                  .groupby(['project_number', 'project_name'])[['turnover', 'invoiced']]
                  .sum()
                  .reset_index())
    project_df['ohw'] = project_df['turnover'] - project_df['invoiced']

    # project_df = project_df.query(f'ohw>{minimal_intesting_value} | ohw<-{minimal_intesting_value}')

    return project_df.sort_values(by='ohw', ascending=False)

    # !!! Het gaat nu mis bij bv BAM waar de december sprint per 30-11 nul omzet heeft (klopt) maar de november sprint kennelijk al op gefactureerd staat.


# @cache(hours=8)
def simplicate_projects_and_services(date: Day):
    # 1. Alle active projecten
    # 2. De diensten daarvan

    # Get the list of services
    services_json = sim.service({'track_hours': True})

    sj = services_json
    for sj1 in sj:
        sj1['hour_types'] = None
        sj1['cost_types'] = None
        sj1['installments'] = None
    s = (sim.to_pandas(services_json)
        .query('project_id=="project:b702bba66765ebadfeaad60b7a7437df"')
        .query(
        f'invoice_method != "Subscription" & status != "flushed" & (invoice_method != "FixedFee" | status!="invoiced")')

    )  # end_date > "{date}" &

    services = (sim.to_pandas(services_json)
                .query(
        f'invoice_method != "Subscription" & status != "flushed" & (invoice_method != "FixedFee" | status!="invoiced")') \
                    [['project_id', 'status', 'id', 'name', 'start_date', 'end_date']]
                .rename(columns={'id': 'service_id', 'name': 'service', 'status': 'service_status'})
                )  # end_date > "{date}" &

    # Same with the list of projects
    projects_json = sim.project({'status': 'tab_pactive'})
    projects = sim.to_pandas(projects_json)[
        ['id', 'project_number', 'name', 'organization_name', 'project_manager_name']] \
        .rename(columns={'id': 'project_id', 'name': 'project_name'})

    # Join them
    project_service = pd.merge(services, projects, on=['project_id'])
    return project_service


@cache(hours=4)
def services_with_their_turnover(date: Day, active_services: list):
    # 3. Omzet berekenen
    # Database bij AWS
    db = get_middleware_db()
    active_services_string = '("' + '","'.join(active_services) + '")'
    query = f'''select organization, project_name, project_number, project_id, service_name, service_id, 
               sum(turnover) as turnover from timesheet
               where organization not in ('Oberon','Travelbase') and service_id in {active_services_string}
                 and day<"{date}"
               group by service_id
               order by organization, service_id'''
    result = pd.read_sql_query(query, db.db)
    return result


@cache(hours=4)
def invoiced_by_date(date: Day):
    return sim.invoiced_per_service({"from_date": "2021-01-01", "until_date": date})

if __name__ == '__main__':
    os.chdir('..')
    load_cache()
    sim = simplicate()
    date = Day('2021-12-01')
    ohw = ohw_list(date)
    print(ohw)
    print(ohw['ohw'].sum())
