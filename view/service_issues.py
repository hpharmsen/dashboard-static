import os
import urllib
from layout.basic_layout import midsize, headersize
from layout.block import HBlock, VBlock, TextBlock, Page
from layout.table import Table, TableConfig
from model.jira_issues import (
    service_jql,
    service_issues_per_status,
    service_issues_per_prioriteit,
    service_issues_per_persoon,
    service_issues_per_project,
    service_issues_per_laatste_update,
    belangrijkste_service_issues,
)


def issue_table(title, retrieve_issues_function, row_coloring=None, row_linking=None):
    issues = retrieve_issues_function()
    assert len(issues[0]) == 2  # Type en count
    return VBlock(
        [
            TextBlock('per ' + title, midsize),
            Table(
                issues,
                TableConfig(
                    headers=[title, 'aantal'],
                    aligns=['left', 'right'],
                    totals=[0, 1],
                    row_coloring=row_coloring,
                    row_linking=row_linking,
                ),
            ),
        ]
    )


def issue_table_split(title, retrieve_issues_function, cell_text_coloring=None, cell_linking=None, row_linking=None):
    issues = retrieve_issues_function()
    assert len(issues[0]) == 3  # Type, count aan Oberon geassigned, count aan klant geassigned
    return VBlock(
        [
            TextBlock('per ' + title, midsize),
            Table(
                issues,
                TableConfig(
                    headers=[title, 'Oberon', 'Klant'],
                    aligns=['left', 'right', 'right'],
                    totals=[0, 1, 1],
                    cell_text_coloring=cell_text_coloring,
                    row_linking=row_linking,
                    cell_linking=cell_linking,
                ),
            ),
        ]
    )


def priority_coloring(row_index, col_index, field):
    if field == 'Critical':
        return 'red'
    if col_index == 2:
        return
    if field == 'Major':
        return 'orange'
    return None


def time_open_coloring(row_index, col_index, field):
    if field in ('< 1 dag', '< 2 dagen'):
        return 'green'
    if field == '30 dagen of meer':
        return 'red'
    if col_index == 1 and field == '< 30 dagen':
        return 'orange'
    return None


def time_open_linking(l, v):
    if v[0] == '< 1 dag':
        from_date = '-1d'
        to_date = '0d'
    elif v[0] == '< 4 dagen':
        from_date = '-4d'
        to_date = '-1d'
    elif v[0] == '<7 dagen':
        from_date = '-7d'
        to_date = '-4d'
    elif v[0] == '< 30 dagen':
        from_date = '-30d'
        to_date = '-7d'
    else:
        from_date = '-999d'
        to_date = '-30d'
    return BASE_LINK + f' AND updated > {from_date} AND updated < {to_date}'


JIRA_LINK = 'https://teamoberon.atlassian.net/issues/?filter=-4&jql='
BASE_LINK = JIRA_LINK + urllib.parse.quote(service_jql())


def priomap(priority):
    return {
        'Kritiek': 'Critical',
        'Groot': 'Major',
        'Normaal': 'Normal',
        'Gering': 'Minor',
        'Wish list': '&quot;Wish list&quot;',
    }.get(priority, priority)


def render_service_issues_page():

    prioriteit = issue_table_split(
        'per prioriteit',
        service_issues_per_prioriteit,
        cell_text_coloring=priority_coloring,
        row_linking=lambda l, v: BASE_LINK + f" AND priority = {priomap(v[0])}",  # TODO cell linking van maken
    )
    persoon = issue_table(
        'per persoon', service_issues_per_persoon, row_linking=lambda l, v: BASE_LINK + f' AND assignee = %22{v[0]}%22 '
    )
    status = issue_table_split(
        'per status', service_issues_per_status, row_linking=lambda l, v: BASE_LINK + f' AND status = %22{v[0]}%22 '
    )
    project = issue_table_split(
        'per project', service_issues_per_project, row_linking=lambda l, v: BASE_LINK + f' AND project = %22{v[0]}%22 '
    )
    update = issue_table_split(
        'per laatste update',
        service_issues_per_laatste_update,
        cell_text_coloring=time_open_coloring,
        row_linking=time_open_linking,
    )

    important_issues = VBlock(
        [
            TextBlock('belangrijkst om op te pakken', midsize),
            Table(
                belangrijkste_service_issues(),
                TableConfig(
                    headers=['issue', 'status', 'prioriteit', 'dagen inactief', 'assignee', 'punten'],
                    aligns=['left', 'left', 'left', 'center', 'left', 'center'],
                    row_linking=lambda l, v: 'https://teamoberon.atlassian.net/browse/' + v[0],
                ),
            ),
        ]
    )

    row1 = HBlock([prioriteit, update, important_issues])
    row2 = HBlock([persoon, status, project])
    page = Page([TextBlock('Openstaande service issues', headersize), VBlock([row1, row2])])

    page.render('output/service_issues.html')
    page.render('output/limited/service_issues.html', limited=1)


if __name__ == '__main__':
    os.chdir('..')
    render_service_issues_page()
