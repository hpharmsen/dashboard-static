import os
from pathlib import Path

import pandas as pd

from layout.basic_layout import HEADER_SIZE
from layout.block import TextBlock, Page, Grid
from model.caching import load_cache
from model.onderhanden_werk import ohw_list, ohw_sum
from model.utilities import Day
from settings import get_output_folder, BOLD, ITALIC, RED


def onderhanden_werk_list(day=None, minimal_intesting_ohw_value: int = 0):
    if not day:
        day = Day()

    grid = Grid(
        cols=8,
        has_header=False,
        line_height=0,
        aligns=['left', 'right', 'right', 'right', 'right', 'left', 'right', 'right'],
    )

    def explanation(row):
        return ''  # todo: Uitleg later weer eens fixen
        # if row['ohw_type'] == 'Strippenkaart':
        #     explainfields = ['restant_budget']
        # elif row['ohw_type'] == 'Fixed':
        #     explainfields = ['verwacht']
        # else:
        #     explainfields = ['besteed', 'correcties', 'inkoop', 'verkoopmarge']
        # result = row['ohw_type'] + '<br/>'
        # for field in explainfields:
        #     if row[field]:
        #         if row[field] > 0:
        #             result += f'+ {field}: {row[field]}<br/>'
        #         else:
        #             result += f'- {field}: {-row[field]}<br/>'
        # if row['ohw_type'] != 'Strippenkaart':
        #     result += f'- gefactureerd: {row["gefactureerd"]}'
        # return result

    def add_service_row(row):
        # start_date = row['start_date'] if type(row['start_date']) == str else ''
        # end_date = row['end_date'] if type(row['end_date']) == str else ''
        start_date = end_date = ''  # todo: Re-add start date and end date to the table.
        grid.add_row(
            [
                TextBlock(row['service_name'], style=ITALIC),
                TextBlock(row['turnover'], text_format='€', style=ITALIC),
                TextBlock(row['invoiced'], text_format='€', style=ITALIC),
                TextBlock(row['service_costs'], text_format='€', style=ITALIC),
                TextBlock(row['service_ohw'], text_format='€', style=ITALIC),
                TextBlock(start_date, style=ITALIC),
                TextBlock(end_date, style=ITALIC),
            ]
        )

    def add_project_row(service_rows):
        row = service_rows[0]
        title = f"{row['project_number']} - {row['organization']} - {row['project_name']}"
        turnover = sum([sr['turnover'] for sr in service_rows])
        invoiced = sum([sr['invoiced'] for sr in service_rows])
        costs = row['project_costs']
        ohw = row['project_ohw']
        grid.add_row(
            [
                TextBlock(title, style=BOLD, url='https://oberon.simplicate.com/projects/' + row['project_id']),
                TextBlock(turnover, text_format='€', style=BOLD),
                TextBlock(invoiced, text_format='€', style=BOLD),
                TextBlock(costs, text_format='€', style=BOLD),
                TextBlock(ohw, text_format='€', style=BOLD),
                TextBlock(row['pm'], style=BOLD),
            ]
        )
        return ohw

    grid.add_row(
        [
            TextBlock(''),
            TextBlock('Omzet', style=BOLD),
            TextBlock('Gefactureerd', style=BOLD),
            TextBlock('Kosten', style=BOLD),
            TextBlock('OHW', style=BOLD),
            TextBlock('', style=BOLD),  # Was: Startdatum
            TextBlock('', style=BOLD),  # Was: Einddatum
        ]
    )
    onderhanden = ohw_list(day, minimal_intesting_value=minimal_intesting_ohw_value)

    if not isinstance(onderhanden, pd.DataFrame):
        return TextBlock('Fout in ophalen onderhanden werk', color=RED)
    last_project_number = ''
    service_rows = []
    total_ohw = 0
    for _, row in onderhanden.iterrows():
        if row['project_number'] != last_project_number:
            # New project
            if service_rows:
                # We collected service rows, add the project and add the service rows
                total_ohw += add_project_row(service_rows)
                for service_row in service_rows:
                    add_service_row(service_row)
                grid.add_row()
                service_rows = []
            last_project_number = row['project_number']
        service_rows += [row]
    # Now add the last colllected project
    total_ohw += add_project_row(service_rows)
    for service_row in service_rows:
        add_service_row(service_row)

    # Totaal
    grid.add_row()
    grid.add_row([TextBlock('TOTAAL', style=BOLD), '', '', '', TextBlock(total_ohw, text_format='€', style=BOLD)])
    return grid


def render_onderhanden_werk_page(output_folder: Path):
    day = Day()
    page = Page([TextBlock(f'Onderhanden werk per {day.strftime("%d/%m")}', HEADER_SIZE), onderhanden_werk_list(day)])
    page.render(output_folder / 'onderhanden.html')


if __name__ == '__main__':
    os.chdir('..')
    load_cache()

    days = [Day()]
    for test_day in days:
        test_page = Page(
            [
                TextBlock(f'Onderhanden werk per {test_day.strftime("%d/%m")}', HEADER_SIZE),
                onderhanden_werk_list(test_day),
            ]
        )
        if test_day == Day():
            test_page.render(get_output_folder() / 'onderhanden.html')
        else:
            test_page.render(get_output_folder() / f'onderhanden{test_day}.html')
        print(test_day, ohw_sum(test_day, minimal_intesting_value=1000))
