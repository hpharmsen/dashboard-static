import os
from datetime import datetime

from layout.basic_layout import defsize, midsize, headersize
from layout.block import HBlock, VBlock, TextBlock, Page
from layout.table import Table, TableConfig
from sources.jira_issues import (
    service_issues_per_laatste_update,
    belangrijkste_service_issues,
    service_issues_per_prioriteit,
)
from model.service import (
    # omzet_op_service_projecten,
    # service_omzet_door_serviceteam,
    # service_omzet_per_persoon,
    service_klanten,
    # service_omzet_persoon_maand,
    service_team,
)

# TODO:
# Targets chart voor serviceteam mensen aanpassen aan wanneer ze begonnen zijn
# Issues samenvatting: Critical/Blocker, > 30 dag, Oudste issue, doorklik naar Service issues
# Klanten doorklikken naar klantpagina
#   Aantal issues laatste 6 maanden
#     Per prioriteit
#   Wat er nu open staat
#     Per status
from model.target import users_and_targets
from view.target import targets_chart


def render_service_page():

    page = Page([TextBlock('Service', headersize), issues_block(), targets_block(), service_klanten_block()])

    page.render('output/service.html')
    page.render('output/limited/service.html', limited=1)


def issues_block():
    highest_priority = service_issues_per_prioriteit()[0]
    prio_issues_color = 'red' if highest_priority[1] > 6 else 'green'
    longest_open = service_issues_per_laatste_update()[-1]
    long_open_color = 'red' if longest_open[1] > 0 else 'green'
    most_important = belangrijkste_service_issues()[0]

    return VBlock(
        [
            TextBlock('Issues', midsize),
            HBlock(
                [
                    VBlock(
                        [
                            TextBlock(highest_priority[0] + ' issues', defsize, color='gray', padding=10),
                            TextBlock(highest_priority[1], headersize, color=prio_issues_color),
                        ]
                    ),
                    VBlock(
                        [
                            TextBlock(longest_open[0] + ' open', defsize, color='gray', padding=10),
                            TextBlock(longest_open[1], headersize, color=long_open_color),
                        ]
                    ),
                    VBlock(
                        [
                            TextBlock('Oldest open issue', defsize, color='gray', padding=10),
                            TextBlock(most_important[0], headersize),
                            TextBlock(f'{most_important[3]} days inactive', defsize, color='gray', padding=10),
                        ]
                    ),
                ]
            ),
        ]
    )


# def service_omzet_block():
#     omzet_staat = Block()
#     omzet_staat.add_absolute_block(0, 0, TextBlock('Omzet op serviceprojecten', defsize, color='gray'))
#     omzet_staat.add_absolute_block(0, 70, TextBlock('Omzet door het serviceteam zelf', defsize, color='gray'))
#     omzet_staat.add_absolute_block(190, 0, TextBlock(omzet_op_service_projecten(), midsize, format='K'))
#     omzet_staat.add_absolute_block(190, 60, TextBlock(service_omzet_door_serviceteam(), midsize, format='K'))
#     omzet_staat.height = 100  # Nodig omdat een blok met alleen maar abs elementen erin zelf geen hoogte heeft
#     omzet_staat.width = 300  # Nodig omdat een blokvan 0 breed nog steeds geen ruimte in neemt
#
#     users, data = service_omzet_persoon_maand()
#     return VBlock(
#         [
#             TextBlock('Omzet', midsize),
#             omzet_staat,
#             BarChart(
#                 data,
#                 ChartConfig(
#                     width=500,
#                     height=500,
#                     title='Omzet per persoon per maand',
#                     labels=list(range(1, 13)),
#                     colors=['#4285f4', '#db4437', '#f4b400', '#0f9d58', '#9900ff', '#46bdc6'],
#                     bottom_labels=users,
#                 ),
#             ),
#         ]
#     )

# def service_team_block():
#     return VBlock(
#         [
#             TextBlock('Team', midsize),
#             Table(
#                 service_omzet_per_persoon(),
#                 TableConfig(headers=['Persoon', 'Service omzet'], aligns=['left', 'right'], formats=['', '€']),
#             ),
#         ]
#     )


def targets_block():
    team = service_team()
    data = users_and_targets(datetime.today().year, specific_users=team)
    return VBlock([TextBlock('Targets', midsize), targets_chart(data, 800, 340)])


def service_klanten_block():
    def link_to_client_page(row_index, row):
        if row[2]:
            return f'klanten/{row[2]}.html'

    klanten = service_klanten()
    return VBlock(
        [
            TextBlock('Klanten', midsize),
            Table(
                klanten,
                TableConfig(
                    headers=['Klant', 'project', 'billable uren', 'totaal uren', 'omzet', 'per uur'],
                    aligns=['left', 'left', 'right', 'right', 'right', 'right'],
                    formats=['', '', '0', '0', '€', '€'],
                    hide_columns=[2],
                    row_linking=link_to_client_page,
                ),
            ),
        ]
    )


if __name__ == '__main__':

    os.chdir('..')
    render_service_page()
