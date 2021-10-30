import math
import os

from model.caching import load_cache
from model.onderhanden_werk import ohw_list
from sources.simplicate import simplicate
from layout.basic_layout import headersize, midsize
from layout.block import VBlock, TextBlock, Page, Grid
from layout.table import Table, TableConfig
from pathlib import Path
from settings import get_output_folder, BOLD, ITALIC


def onderhanden_werk_list():
    grid = Grid(
        cols=9,
        has_header=False,
        line_height=0,
        aligns=['left', 'right', 'right', 'right', 'right', 'right', 'left', 'right', 'right'],
    )

    def add_service_row(row):
        start_date = row['start_date'] if type(row['start_date']) == str else ''
        end_date = row['end_date'] if type(row['end_date']) == str else ''
        grid.add_row(
            [
                TextBlock(row['service'], style=ITALIC),
                TextBlock(row['ohw'], format='€', style=ITALIC),
                TextBlock(row['besteed'], format='€', style=ITALIC),
                TextBlock(row['correcties'], format='€', style=ITALIC),
                TextBlock(row['verkoopmarge'], format='€', style=ITALIC),
                TextBlock(row['gefactureerd'], format='€', style=ITALIC),
                TextBlock(row['ohw_type'], style=ITALIC),
                TextBlock(start_date, style=ITALIC),
                TextBlock(end_date, style=ITALIC),
            ]
        )

    def add_project_row(service_rows):
        row = service_rows[0]
        title = f"{row['project_number']} - {row['organization_name']} {row['project_name']}"
        ohw = sum([sr['ohw'] for sr in service_rows])
        besteed = sum([sr['besteed'] for sr in service_rows])
        correcties = sum([sr['correcties'] for sr in service_rows])
        verkoopmarge = sum([sr['verkoopmarge'] for sr in service_rows])
        gefactureerd = sum([sr['gefactureerd'] for sr in service_rows])
        grid.add_row(
            [
                TextBlock(title, style=BOLD),
                TextBlock(ohw, format='€', style=BOLD),
                TextBlock(besteed, format='€'),
                TextBlock(correcties, format='€'),
                TextBlock(verkoopmarge, format='€'),
                TextBlock(gefactureerd, format='€'),
                TextBlock(row['pm'], style=BOLD),
            ]
        )

    grid.add_row(
        [
            TextBlock(''),
            TextBlock('OHW', style=BOLD),
            TextBlock('Besteed', style=BOLD),
            TextBlock('Correcties', style=BOLD),
            TextBlock('Verkoopmarge', style=BOLD),
            TextBlock('Gefactureerd', style=BOLD),
            TextBlock('Type', style=BOLD),
            TextBlock('Startdatum', style=BOLD),
            TextBlock('Einddatum', style=BOLD),
        ]
    )
    sim = simplicate()
    onderhanden = ohw_list(sim, minimum_amount=1000)
    last_project_number = ''
    service_rows = []
    for _, row in onderhanden.iterrows():
        if row['project_number'] != last_project_number:
            # New project
            if service_rows:
                # We collected service rows, add the project and add the service rows
                add_project_row(service_rows)
                for service_row in service_rows:
                    add_service_row(service_row)
                grid.add_row()
                service_rows = []
            last_project_number = row['project_number']
        service_rows += [row]
    # Now add the last colllected project
    add_project_row(service_rows)
    for service_row in service_rows:
        add_service_row(service_row)

    # Totaal
    total_ohw = onderhanden['ohw'].sum()
    grid.add_row()
    grid.add_row([TextBlock('TOTAAL', style=BOLD), TextBlock(total_ohw, format='€', style=BOLD)])
    return grid


def render_onderhanden_werk_page(output_folder: Path):

    page = Page([TextBlock('Onderhanden werk', headersize), onderhanden_werk_list()])
    page.render(output_folder / 'onderhanden.html')


if __name__ == '__main__':
    os.chdir('..')
    load_cache()
    render_onderhanden_werk_page(get_output_folder())
