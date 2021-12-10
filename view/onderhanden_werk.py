import os
from pathlib import Path

import pandas as pd

from layout.basic_layout import HEADER_SIZE
from layout.block import TextBlock, Page, Grid
from model.caching import load_cache
from model.onderhanden_werk import ohw_list
from settings import get_output_folder, BOLD, ITALIC, RED
from sources.simplicate import simplicate


def onderhanden_werk_list():
    grid = Grid(
        cols=5,
        has_header=False,
        line_height=0,
        aligns=['left', 'right', 'left', 'right', 'right'],
    )

    def explanation(row):
        if row['ohw_type'] == 'Strippenkaart':
            explainfields = ['restant_budget']
        elif row['ohw_type'] == 'Fixed':
            explainfields = ['verwacht']
        else:
            explainfields = ['besteed', 'correcties', 'inkoop', 'verkoopmarge']
        result = row['ohw_type'] + '<br/>'
        for field in explainfields:
            if row[field]:
                if row[field] > 0:
                    result += f'+ {field}: {row[field]}<br/>'
                else:
                    result += f'- {field}: {-row[field]}<br/>'
        if row['ohw_type'] != 'Strippenkaart':
            result += f'- gefactureerd: {row["gefactureerd"]}'
        return result

    def add_service_row(row):
        start_date = row['start_date'] if type(row['start_date']) == str else ''
        end_date = row['end_date'] if type(row['end_date']) == str else ''
        grid.add_row(
            [
                TextBlock(row['service'], style=ITALIC),
                TextBlock(row['ohw'], text_format='€', tooltip=explanation(row), style=ITALIC),
                TextBlock(start_date, style=ITALIC),
                TextBlock(end_date, style=ITALIC),
            ]
        )

    def add_project_row(service_rows):
        row = service_rows[0]
        title = f"{row['project_number']} - {row['organization_name']} {row['project_name']}"
        ohw = sum([sr['ohw'] for sr in service_rows])
        grid.add_row(
            [
                TextBlock(title, style=BOLD),
                TextBlock(ohw, text_format='€', style=BOLD),
                TextBlock(row['pm'], style=BOLD),
            ]
        )

    grid.add_row(
        [
            TextBlock(''),
            TextBlock('OHW', style=BOLD),
            TextBlock('Startdatum', style=BOLD),
            TextBlock('Einddatum', style=BOLD),
        ]
    )
    sim = simplicate()
    onderhanden = ohw_list(sim, minimum_amount=1000)
    if not isinstance(onderhanden, pd.DataFrame):
        return TextBlock('Fout in ophalen onderhanden werk', color=RED)
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
    grid.add_row([TextBlock('TOTAAL', style=BOLD), TextBlock(total_ohw, text_format='€', style=BOLD)])
    return grid


def render_onderhanden_werk_page(output_folder: Path):

    page = Page([TextBlock('Onderhanden werk', HEADER_SIZE), onderhanden_werk_list()])
    page.render(output_folder / 'onderhanden.html')


if __name__ == '__main__':
    os.chdir('..')
    load_cache()
    render_onderhanden_werk_page(get_output_folder())
