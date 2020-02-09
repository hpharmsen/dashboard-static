from itertools import zip_longest

import pandas as pd

from layout.basic_layout import doFormat
from layout.block import Block, wrap


class Table(Block):
    def __init__(
        self,
        data=[],
        id='',
        headers=None,
        aligns=[],
        formats=[],
        totals=[],
        row_coloring=None,
        cell_coloring=None,
        cell_hovering=None,
        row_linking=None,
        limited=False,
        hide_columns=[],
    ):
        super().__init__(id=id, limited=limited)
        if isinstance(data, pd.DataFrame):
            if headers == None:
                headers = list(data.columns)
                if hide_columns:
                    headers = [header for index, header in enumerate(headers) if not index in hide_columns]
            data = data.values.tolist()
        elif len(data) > 0 and isinstance(data[0], dict):
            if headers == None:
                headers = data[0].keys()
                if hide_columns:
                    headers = [header for index, header in enumerate(headers) if not index in hide_columns]
            data = [list(d.values()) for d in data]
        self.data = data
        self.headers = headers
        self.aligns = aligns  # e.g. ['left','left','right']
        self.formats = formats
        self.totals = totals  # which columns should have totals e.g. [0,0,1,1]
        self.row_coloring = row_coloring  # Function that determines how table rows should be colored
        self.cell_coloring = cell_coloring  # Function that determines how table cells should be colored
        self.cell_hovering = cell_hovering  # Function that determines the tooltip for a cell
        self.row_linking = row_linking  # Function that determines the linked url of a row
        self.hide_colums = hide_columns

    def content(self):
        res = '<table class="plain">'
        if self.headers:
            res += (
                '\n<tr>'
                + ''.join(
                    [f'<th style="text-align:{align}">{h}</th>' for h, align in zip_longest(self.headers, self.aligns)]
                )
                + '</tr>'
            )
        totals = [0 if t else '' for t in self.totals]  # Values in the totals row
        for row_index, fullline in enumerate(self.data):

            if self.hide_colums:
                line = [l for i, l in enumerate(fullline) if not i in self.hide_colums]
            else:
                line = fullline

            res += '\n'

            # Row link
            linking = ''
            if self.row_linking:
                link = self.row_linking(row_index, fullline)
                if link:
                    linking = f''' class=linkable_row onclick="document.location = '{link}';"'''

            # Row color
            coloring = ''
            if self.row_coloring:
                coloring = self.row_coloring(row_index, line)
                coloring = f' style="color:{coloring}"' if coloring else ''
            res += f'<tr{linking}{coloring}>'

            # try: # WHAAT?
            col_index = 0
            for field, align, format, add_total in zip_longest(
                line, self.aligns, self.formats, self.totals, fillvalue=''
            ):
                formatted_field = doFormat(field, format)
                coloring = ''
                if self.cell_coloring:
                    coloring = self.cell_coloring(row_index, col_index, field)
                    coloring = f' background-color:{coloring}' if coloring else ''
                tooltip_class = tooltip_text = ''
                if self.cell_hovering:
                    tooltip = self.cell_hovering(row_index, col_index, fullline)
                    tooltip_class = 'class="tooltip" style="position:relative;"' if tooltip else ''
                    tooltip_text = f'<span class="tooltiptext">{wrap(tooltip,42)}</span>' if tooltip else ''
                res += f'<td style="text-align:{align};{coloring}"><div {tooltip_class} style="text-align:{align}">{tooltip_text}<span>{formatted_field}</span></div></td>'
                if self.totals and add_total:
                    totals[col_index] += field
                col_index += 1
            # except:
            #    pass
            res += '</tr>'

        if self.totals:
            res += '<tr>'
            for add_total, t, align, format in zip_longest(self.totals, totals, self.aligns, self.formats):
                if add_total and format:
                    t = doFormat(t, format)
                res += f'<td style="text-align:{align}"><b>{t}</b></td>'
            res += '</tr>'
        res += '</table>'
        return res

    def render_children(self, limited=False):
        return ''  # overwrite Block's render_children