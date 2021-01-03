import collections
from datetime import datetime
from dateutil import parser as dateparser
from jira import JIRA, JIRAError  # pip install jira
from sources import database as db
import configparser
from pathlib import Path
from model.caching import reportz

DEFAULT_FIELDS = ['created', 'assignee', 'project', 'priority', 'updated', 'summary', 'status', 'labels', 'resolution']
SORT_ON_COUNT = 1

ini = configparser.ConfigParser()
ini.read(Path(__file__).resolve().parent / 'credentials.ini')
jira_user = ini['jira']['user']
jira_key = ini['jira']['key']
jira_server = ini['jira']['server']

# Get token at: https://id.atlassian.com/manage/api-tokens
jira = JIRA(basic_auth=(jira_user, jira_key), options={'server': jira_server})


@reportz(hours=24)
def alle_issues_van_project(project_key):
    return jira_issues_and_where_the_ball_is('', project_keys=[project_key])


def open_issues_van_project(project_key):
    issues = jira_issues_and_where_the_ball_is(service_jql(), project_keys=[project_key])
    grouped = group_issues_by_field(issues, 'status', sort_field='status_id')
    return grouped


@reportz(hours=1)
def service_issues_per_status():
    return group_issues_by_field(service_issues(), 'status', sort_field='status_id', split_by_where_the_ball_is=True)


@reportz(hours=1)
def service_issues_per_prioriteit():
    return group_issues_by_field(
        service_issues(), 'priority', sort_field='priority_id', split_by_where_the_ball_is=True
    )


@reportz(hours=1)
def service_issues_per_persoon():
    issues = service_issues()
    res = group_issues_by_field(issues, 'assignee')
    return res


@reportz(hours=1)
def service_issues_per_project():
    return group_issues_by_field(
        service_issues(), 'project', sort_field=SORT_ON_COUNT, reverse=True, split_by_where_the_ball_is=True
    )


@reportz(hours=1)
def service_issues_per_maand():
    return group_issues_by_field(service_issues(), 'updated_month', reverse=True)


@reportz(hours=1)
def service_issues_per_laatste_update():
    return group_issues_by_field(
        service_issues(), 'time_since_update', sort_field='updated', reverse=True, split_by_where_the_ball_is=True
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

    issues = service_assigned_to_oberon('reporter not in membersOf(Oberon)')

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


@reportz(hours=2)
def service_issues():
    return jira_issues_and_where_the_ball_is(service_jql())


@reportz(hours=1)
def service_assigned_to_oberon(extra_constraint=''):
    jql = jql_add(service_jql(), '(assignee in membersOf(Oberon) OR assignee=EMPTY)')
    if extra_constraint:
        jql = jql_add(jql, extra_constraint)
    return jira_issues(jql)


def service_jql():
    keys = '"' + '", "'.join(service_jira_keys()) + '"'
    jql = f'resolution = Unresolved AND project in ({keys}) AND status not in (suspended) AND (labels != support OR labels is empty)'
    return jql


@reportz(hours=1)
def service_jira_keys():
    # From Oberview
    query = 'SELECT JiraURL FROM project p JOIN customer c on c.id=p.customerId WHERE project_type = "service" and JiraURL != ""'
    all_jira_keys = [p.key for p in jira.projects()]
    return [rec['JiraURL'] for rec in db.table(query) if rec['JiraURL'] in all_jira_keys]


def jira_issues_and_where_the_ball_is(jql, fields=DEFAULT_FIELDS, project_keys=None):
    assigned_to_oberon = jira_issues(jql_add(jql, 'assignee in membersOf(Oberon)'), fields, project_keys)
    for issue in assigned_to_oberon:
        issue['where_the_ball_is'] = 'oberon'
    assigned_to_client = jira_issues(jql_add(jql, 'assignee not in membersOf(Oberon)'), fields, project_keys)
    for issue in assigned_to_client:
        issue['where_the_ball_is'] = 'client'
    return assigned_to_oberon + assigned_to_client


def jira_issues(
    jql,
    fields=DEFAULT_FIELDS,
    project_keys=None,
):
    if project_keys:  #!! Is dit nog nodig?
        issues = []
        for key in project_keys:
            project_jql = jql_add(jql, f"project='{key}'")
            issues += find_issues(project_jql, fields)
    else:
        issues = find_issues(jql, fields)
    return [flatten(issue) for issue in issues]


def find_issues(jql, fields):
    block_size = 100
    block_num = 0
    issues = []
    while True:
        start_idx = block_num * block_size

        try:
            iss = jira.search_issues(jql, startAt=start_idx, maxResults=block_size, json_result=True, fields=fields)[
                'issues'
            ]
        except JIRAError as e:
            raise e
            # break
        if len(iss) == 0:
            # Retrieve issues until there are no more to come
            break
        issues += iss
        block_num += 1
        if block_num > 100:
            break
    return issues


def jql_add(jql, extra_constraint):
    if jql and not jql.strip().endswith(' and'):
        jql += ' and '
    return jql + extra_constraint


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
    issue['resolution'] = issue['resolution']['name'] if issue['resolution'] else 'Unresolved'
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


def group_issues_by_field(issues, group_field, sort_field=None, reverse=False, split_by_where_the_ball_is=False):
    if split_by_where_the_ball_is:
        oberon_issues, client_issues = split_on_condition(issues, lambda a: a['where_the_ball_is'] == 'oberon')
        keys = collections.Counter([i[group_field] for i in issues]).keys()
        oberon_result = counts_list(oberon_issues, group_field)
        client_result = counts_list(client_issues, group_field)
        result = [(key, oberon_result.get(key, 0), client_result.get(key, 0)) for key in keys]
    else:
        counts = counts_list(issues, group_field)
        result = list(counts.items())

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


def split_on_condition(seq, condition):
    a, b = [], []
    for item in seq:
        (a if condition(item) else b).append(item)
    return a, b


def counts_list(issues, group_field):
    counted = collections.Counter([i[group_field] for i in issues])
    return counted  # result = list(counted.items())
    return result


#############

if __name__ == '__main__':
    print(service_issues_per_status())
    # issues = service_issues()
    # print(service_issues_per_status())
    # print(service_issues_per_prioriteit())
    # print(service_issues_per_persoon())
    # print(service_issues_per_project())
    # print(service_issues_per_maand())
