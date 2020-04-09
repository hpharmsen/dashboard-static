import os
from datetime import datetime
from functools import partial

from layout.basic_layout import defsize, midsize, headersize
from layout.block import HBlock, VBlock, TextBlock, Page
from layout.table import Table, TableConfig
from model.jira_issues import alle_issues_van_project, open_issues_van_project
from model.service import service_klanten
from view.service_issues import BASE_LINK


def render_service_klanten_pages():
    for klant in service_klanten().to_dict('records'):
        if klant['JiraURL']:
            issues = alle_issues_van_project(klant['JiraURL'])
            render_service_klant_page(klant, issues)


def render_service_klant_page(klant, issues):

    page = Page([TextBlock(klant['name'], headersize), issues_block(issues), open_issues_block(klant['JiraURL'])])

    page.render(f'output/klanten/{klant["JiraURL"]}.html')
    page.render(f'output/limited/klanten/{klant["JiraURL"]}.html', limited=1)


def UTC_to_datetime(utc_string):
    return datetime.strptime(utc_string.split('T')[0], '%Y-%m-%d')


def issues_block(issues):

    stati = {}
    total_resolve_time = 0
    issues_resolved = 0
    for issue in issues:
        stati[issue['resolution']] = issue['resolution']
        if issue['resolution'] != 'Unresolved':
            created = UTC_to_datetime(issue['created'])
            resolved = UTC_to_datetime(issue['updated'])
            resolve_time = (resolved - created).days
            total_resolve_time += resolve_time
            issues_resolved += 1
    average_resolve_time = f'{total_resolve_time / issues_resolved:.0f}' if issues_resolved else ''

    aantal_totaal = len(issues)
    aantal_opgelost = len([i for i in issues if i['status'] in ('Done', 'Closed')])
    # open_issues = [i for i in issues if not i['status'] in ('Done','Closed')]
    return VBlock(
        [
            TextBlock('Issues', midsize),
            HBlock(
                [
                    VBlock(
                        [
                            TextBlock('aantal issues', defsize, color='gray', padding=10),
                            TextBlock(aantal_totaal, headersize),
                        ]
                    ),
                    VBlock(
                        [
                            TextBlock('aantal opgelost', defsize, color='gray', padding=10),
                            TextBlock(aantal_opgelost, headersize),
                        ]
                    ),
                    VBlock(
                        [
                            TextBlock('gemiddelde oplostijd', defsize, color='gray', padding=10),
                            TextBlock(average_resolve_time, headersize, padding=10),
                            TextBlock('dagen', defsize, color='gray'),
                        ]
                    ),
                ]
            ),
        ]
    )


def open_issues_block(JiraURL):

    get_issues_function = partial(open_issues_van_project, project_key=JiraURL)
    row_linking = lambda l, v: BASE_LINK + f' AND project = %22{JiraURL}%22 AND status = %22{v[0]}%22'

    return VBlock(
        [
            TextBlock('Open issues', midsize),
            Table(
                get_issues_function(),
                TableConfig(
                    headers=['status', 'aantal'], aligns=['left', 'right'], totals=[0, 1], row_linking=row_linking
                ),
            ),
        ]
    )


if __name__ == '__main__':

    os.chdir('..')
    render_service_klanten_pages()
