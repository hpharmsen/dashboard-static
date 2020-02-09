import os
from layout.basic_layout import defsize, midsize, headersize
from layout.block import Block, HBlock, VBlock, TextBlock, Page
from layout.table import Table
from model.service import (
    omzet_op_service_projecten,
    service_omzet_door_serviceteam,
    service_omzet_per_persoon,
    service_klanten,
    service_omzet_persoon_maand,
)
from layout.chart import BarChart


def render_service_page():

    omzet_staat = Block()
    omzet_staat.add_absolute_block(0, 0, TextBlock('Omzet op serviceprojecten', defsize, color='gray'))
    omzet_staat.add_absolute_block(0, 70, TextBlock('Omzet door het serviceteam zelf', defsize, color='gray'))
    omzet_staat.add_absolute_block(190, 0, TextBlock(omzet_op_service_projecten(), midsize, format='K'))
    omzet_staat.add_absolute_block(190, 60, TextBlock(service_omzet_door_serviceteam(), midsize, format='K'))
    omzet_staat.height = 100  # Nodig omdat een blok met alleen maar abs elementen erin zelf geen hoogte heeft
    omzet_staat.width = 300  # Nodig omdat een blokvan 0 breed nog steeds geen ruimte in neemt

    users, data = service_omzet_persoon_maand()
    omzet = VBlock(
        [
            TextBlock('Omzet', midsize),
            omzet_staat,
            BarChart(
                500,
                500,
                'Omzet per persoon per maand',
                list(range(1, 13)),
                data,
                ['#4285f4', '#db4437', '#f4b400', '#0f9d58', '#9900ff', '#46bdc6'],
                bottom_labels=users,
            ),
        ]
    )

    team = VBlock(
        [
            TextBlock('Team', midsize),
            Table(
                service_omzet_per_persoon(),
                headers=['Persoon', 'Service omzet'],
                aligns=['left', 'right'],
                formats=['', '€'],
            ),
        ]
    )

    klanten = VBlock(
        [
            TextBlock('Klanten', midsize),
            Table(
                service_klanten(),
                headers=['Klant', 'project', 'billable uren', 'totaal uren', 'omzet', 'per uur'],
                aligns=['left', 'left', 'right', 'right', 'right', 'right'],
                formats=['', '', '€', '€', '€', '€'],
            ),
        ]
    )

    page = Page([TextBlock('Service', headersize), HBlock([omzet, team, klanten])])

    page.render('output/service.html')
    page.render('output/limited/service.html', limited=1)


if __name__ == '__main__':
    os.chdir('..')
    render_service_page()
