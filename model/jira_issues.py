import collections
from datetime import datetime
from dateutil import parser as dateparser
from jira import JIRA  # pip install jira
from sources import database as db

from model.caching import reportz

# Get token at: https://id.atlassian.com/manage/api-tokens
jira = JIRA(
    basic_auth=('hph@oberon.nl', 'KmClaydlK4Hgee4Xelho6E5B'), options={'server': 'https://teamoberon.atlassian.net'}
)

SORT_ON_COUNT = 1


@reportz(hours=0.1)
def service_jira_keys():
    # From Oberview
    query = 'SELECT JiraURL FROM project p JOIN customer c on c.id=p.customerId WHERE project_type = "service" and JiraURL != ""'
    all_jira_keys = [p.key for p in jira.projects()]
    return [rec['JiraURL'] for rec in db.table(query) if rec['JiraURL'] in all_jira_keys]


def service_jql():
    keys = '%22' + '%22, %22'.join(service_jira_keys()) + '%22'
    return f'resolution = Unresolved AND project in ({keys}) AND status not in (suspended)'


def jira_issues(
    jql,
    fields=['created', 'assignee', 'project', 'priority', 'updated', 'summary', 'status', 'labels'],
    project_keys=None,
):
    if project_keys:
        issues = []
        for key in project_keys:
            project_jql = jql + ' and project=' + key
            try:
                issues += jira.search_issues(project_jql, maxResults=999, json_result=True, fields=fields)['issues']
                a = 1
            except:
                continue
    else:
        issues = jira.search_issues(jql, maxResults=999, json_result=True, fields=fields)['issues']
    return [flatten(issue) for issue in issues]


@reportz(hours=0.1)
def service_issues():
    return jira_issues('resolution = Unresolved AND status not in (suspended) ', project_keys=service_jira_keys())


@reportz(hours=0.1)
def service_assigned_to_oberon():
    return jira_issues(
        'resolution = Unresolved AND status not in (suspended) and assignee in membersOf(Oberon)',
        project_keys=service_jira_keys(),
    )


@reportz(hours=0.1)
def belangrijkste_service_issues():
    # Ranking van klanten
    query = f'''select JiraURL, round(tt) as total, round(tu) as turnover, round(tu/tt) as hourly 
                from (
                    select JiraURL, SUM(CASE WHEN taskId=-2 THEN hours END) AS b, SUM(hours) AS tt, 
                           SUM(CASE WHEN taskId=-2 THEN hours END)*pu.hourlyRate*(1 + management_costs/100) as tu 
                    from timesheet ts 
                    join project p on ts.projectId=p.Id 
                    join customer c on p.customerId=c.Id 
                    join project_user pu on pu.projectId=p.Id and ts.user=pu.user 
                    where  day > DATE(NOW()) - INTERVAL 1 YEAR and project_type='service' 
                    group by p.id) as q1 
                order by hourly desc'''
    clients = db.table(query)
    client_points = {rec['JiraURL']: rec['hourly'] for rec in clients}

    issues = jira_issues(
        'resolution = Unresolved AND status not in (suspended) and assignee in membersOf(Oberon) and reporter not in membersOf(Oberon)',
        project_keys=service_jira_keys(),
    )
    issues = [issue for issue in issues if not 'support' in issue['labels']]

    for issue in issues:
        # Basis punten zijn gebaseerd op de prioriteit
        priority_points = {'Blocker': 200, 'Critical': 30, 'Major': 20, 'Normal': 5}.get(issue['priority'], 0)

        # Elke dag open: 1pt extra
        last_updated_date = dateparser.parse(issue['updated'])
        issue['days_open'] = int(round((datetime.now() - last_updated_date).days))

        # Ranking in serviceteam klanten omzet per uur lijst: 1 pt per rank
        client_key = issue['key'].split('-')[0]
        issue['client_points'] = client_points.get(client_key, 80)
        issue['points'] = priority_points + issue['days_open'] + issue['client_points']

    issues = sorted(issues, key=lambda a: -a['points'])
    return [[r['key'], r['status'], r['priority'], r['days_open'], r['assignee'], r['points']] for r in issues[:10]]


def time_since_update(updated):
    last_updated_date = dateparser.parse(updated)
    days = (datetime.now() - last_updated_date).days
    if days < 1:
        return '< 1 dag'
    for d in (2, 4, 7, 30):
        if days < d:
            return f'< {d} dagen'
    return '30 dagen of meer'


def flatten(issue):
    key = issue['key']
    issue = issue['fields']
    issue['key'] = key
    issue['project'] = issue['project']['name']
    issue['assignee'] = issue['assignee']['displayName'] if issue['assignee'] else 'Unassigned'
    issue['priority_id'] = int(issue['priority']['id'])
    issue['priority'] = issue['priority']['name']
    issue['updated'] = issue['updated'].split('T')[0]
    issue['updated_month'] = issue['updated'][:7]
    issue['time_since_update'] = time_since_update(issue['updated'])
    issue['status_id'] = int(issue['status']['id'])
    issue['status'] = issue['status']['name']
    return issue


status_sort = {
    'Backlog': 0,
    'New': 1,
    'Estimation needed': 2,
    'Budget approval needed': 3,
    'To Do': 4.1,
    'Open': 4.2,
    'Reopened': 4.3,
    'In Progress': 5,
    'Testing': 6,
    'Deploy to acceptance': 7,
    'Waiting for acceptance': 8,
    'Deploy to live': 9,
    'Closed': 10,
    'Done': 11,
}


def group(issues, group_field, sort_field=None, reverse=False):
    counted = collections.Counter([i[group_field] for i in issues])
    result = list(counted.items())

    if sort_field == SORT_ON_COUNT:
        sort_func = lambda a: a[1]
    else:  # sort on the key
        if not sort_field:
            sort_field = group_field
        if sort_field == 'status_id':
            sort_dict = status_sort
        else:
            sort_dict = {issue[group_field]: issue[sort_field] for issue in issues}
        sort_func = lambda a: sort_dict.get(a[0], 99)
    return sorted(result, key=sort_func, reverse=reverse)


@reportz(hours=0.1)
def service_issues_per_status():
    return group(service_issues(), 'status', sort_field='status_id')


@reportz(hours=0.1)
def service_issues_per_prioriteit():
    return group(service_issues(), 'priority', sort_field='priority_id')


@reportz(hours=0.1)
def service_issues_per_persoon():
    return group(service_issues(), 'assignee')


@reportz(hours=0.1)
def service_issues_per_project():
    return group(service_issues(), 'project', sort_field=SORT_ON_COUNT, reverse=True)


@reportz(hours=0.1)
def service_issues_per_maand():
    return group(service_issues(), 'updated_month', reverse=True)


@reportz(hours=0.1)
def service_issues_per_laatste_update():
    return group(service_issues(), 'time_since_update', sort_field='updated', reverse=True)


if __name__ == '__main__':
    print(belangrijkste_service_issues())
    # issues = service_issues()
    # print(service_issues_per_status())
    # print(service_issues_per_prioriteit())
    # print(service_issues_per_persoon())
    # print(service_issues_per_project())
    # print(service_issues_per_maand())
