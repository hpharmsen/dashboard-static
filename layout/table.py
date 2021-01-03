from itertools import zip_longest
from typing import NamedTuple, Callable, List

import pandas as pd

from layout.basic_layout import doFormat
from layout.block import Block, wrap


class TableConfig(NamedTuple):
    id: str = ''
    headers: List = []
    aligns: List = []  # e.g. ['left','left','right']
    formats: List = []  # see basic_layout.doFormat for options
    totals: List = []  # which columns should have totals e.g. [0,0,1,1]
    row_coloring: Callable = None  # Callback that determines how table rows should be colored
    row_linking: Callable = None  # Callback that determines the linked url of a row
    cell_coloring: Callable = None  # Callback that determines how table cell backgrounds should be colored
    cell_text_coloring: Callable = None  # Callback that determines how table cell texts should be colored
    cell_hovering: Callable = None  # Callback that determines the tooltip for a cell
    cell_linking: Callable = None  # Callback that determines the linked url of a cell
    hide_columns: List = []  # List the numbers of the columns that should not be visible (0-based)


class Table(Block):
    def __init__(self, data: list = [], config: TableConfig = None, id=''):
        super().__init__(id=id)

        self.data = data
        self.config = config
        self.headers = config.headers
        if isinstance(data, pd.DataFrame):
            self._convert_data_from_dataframe_to_list_of_lists()
        elif len(data) > 0 and isinstance(data[0], dict):
            self._convert_data_from_dict_list_to_list_of_lists()

        #if self.config.hide_columns:
        #    self._hide_columns()

    def _convert_data_from_dataframe_to_list_of_lists(self):
        if self.headers == None:
            self.headers = list(self.data.columns)
        self.data = self.data.values.tolist()

    def _convert_data_from_dict_list_to_list_of_lists(self):
        if self.headers == None:
            self.headers = self.data[0].keys()
        self.data = [list(d.values()) for d in self.data]

    #def _hide_columns(self):
    #    #self.headers = [header for index, header in enumerate(self.headers) if not index in self.config.hide_columns]
    #    pass

    def render_content(self):
        res = '<table class="plain">'
        if self.headers:
            res += (
                '\n<tr>'
                + ''.join(
                    [
                        f'<th style="text-align:{align}">{h}</th>'
                        for h, align in zip_longest(self.headers, self.config.aligns)
                    ]
                )
                + '</tr>'
            )
        totals = [0 if t else '' for t in self.config.totals]  # Values in the totals row
        for row_index, fullline in enumerate(self.data):

            if self.config.hide_columns:
                line = [l for i, l in enumerate(fullline) if not i in self.config.hide_columns]
            else:
                line = fullline

            res += '\n'

            # Row link
            linking = ''
            if self.config.row_linking:
                link = self.config.row_linking(row_index, fullline)
                if link:
                    linking = f''' class=linkable_row onclick="document.location = '{link}';"'''

            # Row color
            coloring = ''
            if self.config.row_coloring:
                coloring = self.config.row_coloring(row_index, line)
                coloring = f' style="color:{coloring}"' if coloring else ''
            res += f'<tr{linking}{coloring}>'

            col_index = 0
            for field, align, format, add_total in zip_longest(
                line, self.config.aligns, self.config.formats, self.config.totals, fillvalue=''
            ):
                formatted_field = doFormat(field, format)
                coloring = ''
                if self.config.cell_coloring:
                    color = self.config.cell_coloring(row_index, col_index, field)
                    coloring += f' background-color:{color};' if color else ''
                if self.config.cell_text_coloring:
                    color = self.config.cell_text_coloring(row_index, col_index, field)
                    coloring += f' color:{color};' if color else ''
                tooltip_class = tooltip_text = ''
                if self.config.cell_hovering:
                    tooltip = self.config.cell_hovering(row_index, col_index, fullline)
                    tooltip_class = 'class="tooltip" style="position:relative;"' if tooltip else ''
                    tooltip_text = f'<span class="tooltiptext">{wrap(tooltip,42)}</span>' if tooltip else ''
                res += f'<td style="text-align:{align};{coloring}"><div {tooltip_class} style="text-align:{align}">{tooltip_text}<span>{formatted_field}</span></div></td>'
                if self.config.totals and add_total:
                    totals[col_index] += field
                col_index += 1
            res += '</tr>'

        if self.config.totals:
            res += '<tr>'
            for add_total, t, align, format in zip_longest(
                self.config.totals, totals, self.config.aligns, self.config.formats
            ):
                if add_total and format:
                    t = doFormat(t, format)
                res += f'<td style="text-align:{align}"><b>{t}</b></td>'
            res += '</tr>'
        res += '</table>'
        return res

    def render_children(self):
        return ''  # overwrite Block's render_children


if __name__ == '__main__':
    c = TableConfig(
        headers=['klant', 'project', 'grootte', 'kans', 'fase', 'waarde', 'bron'],
        aligns=['left', 'left', 'right', 'right', 'left', 'right', 'left'],
        formats=['', '', '€', '%', '', '€', ''],
        totals=[0, 0, 1, 0, 0, 1, 0],
    )
