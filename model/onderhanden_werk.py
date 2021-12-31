import os

import pandas as pd

from middleware.timesheet import Timesheet
from model.caching import cache, load_cache
from model.utilities import Day
from sources.simplicate import simplicate


@cache(hours=24)
def ohw(date: Day):
    df = ohw_list(date)
    if df.empty:
        return 0
    result = df['ohw'].sum()
    return result


@cache(hours=24)
def ohw_list(date: Day, minimal_intesting_value=0, group_by_project=0):
    sim = simplicate()

    # Nieuwe methode:
    # 1. Alle active projecten
    # 2. De diensten daarvan
    projects_and_services = simplicate_projects_and_services(sim, date)
    active_services = projects_and_services['service_id'].tolist()

    # 3. Omzet -/- correcties berekenen
    service_df = services_with_their_turnover(date, active_services)
    if service_df.empty:
        return service_df

    # 4. Ophalen wat er is gefactureerd
    invoiced = invoiced_by_date(sim, date)

    service_df['invoiced'] = service_df.apply(lambda row: invoiced[row['service_id']], axis=1)
    service_df.turnover = service_df.turnover.astype(int)
    service_df.invoiced = service_df.invoiced.astype(int)
    service_df['ohw'] = service_df['turnover'] - service_df['invoiced']
    service_df = service_df.query('ohw != 0').copy()

    # Group by project either to return projects or to be able to sort the services by project OHW
    project_df = (
        service_df.groupby(['organization', 'pm', 'project_number', 'project_name'])
            .agg({'turnover': 'sum', 'invoiced': 'sum'})
            .reset_index()
    )
    project_df['ohw'] = project_df['turnover'] - project_df['invoiced']

    if group_by_project:
        if minimal_intesting_value:
            project_df = project_df.query(f'ohw>{minimal_intesting_value} | ohw<-{minimal_intesting_value}').copy()
        project_df = project_df.sort_values(by='ohw', ascending=False)
    else:
        # Sort services by the total owh of their project
        project_ohws = {p['project_number']: p['ohw'] for _, p in project_df.iterrows()}

        def get_ohw(row):
            pn = row['project_number']
            ohw = project_ohws.get(pn, 0)
            return ohw

        service_df['project_ohw'] = service_df.apply(get_ohw, axis=1)
        if minimal_intesting_value:
            service_df = service_df.query(
                f'project_ohw>{minimal_intesting_value} | project_ohw<-{minimal_intesting_value}'
            )

        project_df = service_df.sort_values(by='project_ohw', ascending=False)

    return project_df


@cache(hours=8)
def simplicate_projects_and_services(sim, date: Day):
    """Returns a dataframe with all active projects and services at a given date"""

    # Get the list of services
    services_json = sim.service({'track_hours': True})

    # status kunnen we niet naar kijken want er is geen mogeljkheid
    # om te achterhalen wat de status was op de opgegeven datum
    status_query = 'invoice_method != "Subscription"'
    # start_date en end_date worden slecht bijgehouden dus daar hebben we ook niks aan
    # behalve dan dat we dingen eruit kunnen filteren die echt te oud zijn, of nog niet begonnen
    status_query += f' & (end_date != end_date | end_date > "{date.plus_months(-12)}")'  # end_date != end_date is a construct to check for NaN
    status_query += f' & (start_date != start_date | start_date <= "{date}")'  # end_date != end_date is a construct to check for NaN

    services = (
        sim.to_pandas(services_json)
            .query(status_query)[['project_id', 'status', 'id', 'name', 'start_date', 'end_date']]
            .rename(columns={'id': 'service_id', 'name': 'service', 'status': 'service_status'})
    )  # end_date > "{date}" &

    # Same with the list of projects
    projects_json = sim.project({'status': 'tab_pactive'})
    projects = sim.to_pandas(projects_json)[
        ['id', 'project_number', 'name', 'organization_name', 'project_manager_name']
    ].rename(columns={'id': 'project_id', 'name': 'project_name'})

    # Join them
    project_service = pd.merge(services, projects, on=['project_id'])
    return project_service


@cache(hours=4)
def services_with_their_turnover(date: Day, active_services: list):
    # 3. Omzet berekenen
    timesheet = Timesheet()
    active_services_string = '("' + '","'.join(active_services) + '")'
    query = f'''select organization, project_name, p.project_number, p.project_id, pm, service_name, service_id, 
                start_date, end_date, sum(turnover) as turnover 
                from timesheet ts join project p on p.project_id=ts.project_id
                where my_organization_profile='Oberon' 
                  and organization not in ('Oberon','Travelbase') 
                  and service_id in {active_services_string}
                  and day<"{date}"
               group by service_id
               order by organization, service_id'''
    result = pd.DataFrame(timesheet.full_query(query))
    return result


# @cache(hours=4)
def invoiced_by_date(sim, date: Day):
    return sim.invoiced_per_service({"from_date": "2021-01-01", "until_date": date})


if __name__ == '__main__':
    os.chdir('..')
    load_cache()
    sim = simplicate()
    date = Day('2021-12-01')
    ohw = ohw_list(date)
    print(ohw)
    print(ohw['ohw'].sum())
