import os
from datetime import datetime

from layout.basic_layout import defsize, midsize, headersize
from layout.block import Block, HBlock, VBlock, TextBlock, Page
from layout.table import Table, TableConfig
from model.service import (
    # omzet_op_service_projecten,
    # service_omzet_door_serviceteam,
    # service_omzet_per_persoon,
    service_klanten,
    # service_omzet_persoon_maand,
    service_team,
)
from layout.chart import BarChart, ChartConfig

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

    page = Page([TextBlock('Service', headersize), targets_block(), HBlock([service_klanten_block()])])

    page.render('output/service.html')
    page.render('output/limited/service.html', limited=1)


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


def service_klanten_block():
    klanten = VBlock(
        [
            TextBlock('Klanten', midsize),
            Table(
                service_klanten(),
                TableConfig(
                    headers=['Klant', 'project', 'billable uren', 'totaal uren', 'omzet', 'per uur'],
                    aligns=['left', 'left', 'right', 'right', 'right', 'right'],
                    formats=['', '', '0', '0', '€', '€'],
                ),
            ),
        ]
    )
    return klanten


def targets_block():
    team = service_team()
    data = users_and_targets(datetime.today().year, specific_users=team)
    return VBlock([TextBlock('Targets', midsize), targets_chart(data, 800, 340)])


if __name__ == '__main__':
    os.chdir('..')
    render_service_page()
