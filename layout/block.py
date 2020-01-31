import datetime
from functools import partial
from itertools import zip_longest
from pathlib import Path
import pandas as pd
from model.caching import cache_time_stamp

from layout.basic_layout import doFormat

Kformatter = partial(doFormat, format='K')


class Block:
    def __init__(
        self,
        children=[],
        width=None,
        height=None,
        bg_color='white',
        align_children='absolute',
        id='',
        limited=False,
        tooltip='',
    ):
        self.id = id
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.align_children = align_children
        self.children = [(child, '') for child in children]
        self.limited = limited  # If True, this block should not be shown when rendered with limited=1
        self.tooltip = tooltip  # If set, shows this text as an html over tooltip

    def add_absolute_block(self, left, top, block, link=''):
        ''' Will be deprecated '''
        self.children += [(left, top, block, link)]

    def add_block(self, block, link=''):
        self.children += [(block, link)]

    def content(self):
        return ''

    def render_children(self, limited=False):
        res = ''
        if self.align_children == 'absolute':
            for left, top, child, link in self.children:
                c = child.render_absolute(left, top, limited=limited)
                if link:
                    c = f'<a href="{link}" class="link">{c}</a>'
                res += '\n' + c
        else:
            for child, link in self.children:
                c = child.render(self.align_children, limited=limited)
                if link:
                    c = f'<a href="{link}" class="link">{c}</a>'
                res += '\n' + c
        return res

    def render_absolute(self, left=None, top=None, limited=False):
        if self.limited and limited:
            return ''

        return self.do_render('absolute', left=left, top=top, limited=limited)
        # return f'''<div style="position:absolute; left:{left}px; top:{top}px; {width} {height} background-color:{self.bg_color}">
        #             {self.content()}
        #             {self.render_children(limited=limited)}
        #             </div>
        #         '''

    def render(self, align='', limited=False):
        if self.limited and limited:
            return ''
        id = f'id="{self.id}"' if self.id else ''

        clear = 'clear:both;' if align == 'vertical' else ''
        float = 'float:left;' if align == 'horizontal' else ''
        if align == 'horizontal':
            padding = 'padding-right:40px;'
        elif align == 'vertical':
            padding = 'padding-bottom:40px;'
        else:
            padding = ''
        return self.do_render('relative', id=id, clear=clear, float=float, padding=padding, limited=limited)

    def do_render(self, position, id='', clear='', float='', padding='', left=None, top=None, limited=False):
        height = f'height:{self.height}px; ' if self.height else ''
        width = f'width:{self.width}px; ' if self.width else ''
        position_str = (
            f'position:absolute; left:{left}px; top:{top}px;'
            if position == 'absolute'
            else f'position:relative; {float} {clear}'
        )
        tooltip_class = 'class="tooltip"' if self.tooltip else ''
        tooltip_text = f'<span class="tooltiptext">{wrap(self.tooltip,42)}</span>' if self.tooltip else ''
        return f'''<div {id} {tooltip_class} style="{position_str} {width} {height} {padding} background-color:{self.bg_color}; ">
                    {tooltip_text}
                    {self.content()}
                    {self.render_children(limited=limited)}
                    </div>
                '''


class HBlock(Block):
    def __init__(self, children=[], width=None, height=None, bg_color='white', id='', limited=False):
        super().__init__(
            children=children,
            width=width,
            height=height,
            bg_color=bg_color,
            id=id,
            align_children='horizontal',
            limited=limited,
        )


class VBlock(Block):
    def __init__(self, children=[], width=None, height=None, bg_color='white', id='', limited=False):
        super().__init__(
            children=children,
            width=width,
            height=height,
            bg_color=bg_color,
            id=id,
            align_children='vertical',
            limited=limited,
        )


class TextBlock(Block):
    def __init__(
        self,
        text,
        font_size=12,
        width=None,
        height=None,
        bg_color='',
        color='',
        font_family='Arial',
        style='',
        format='',
        url=None,
        limited=False,
        tooltip='',
    ):
        super().__init__([], width=width, height=height, bg_color=bg_color, limited=limited, tooltip=tooltip)
        self.text = doFormat(text, format)
        self.font_size = font_size
        self.font_family = font_family
        self.style = style
        if callable(color):  # color parameter could be a function of the text passed
            self.color = color(text)
        else:
            self.color = color
        self.url = url

    def content(self):
        colorstr = f'color:{self.color};' if self.color else ''
        res = f'''<span style="font-size:{self.font_size}px; {colorstr} font-family:{self.font_family}; {self.style}">{self.text}</span>'''
        if self.url:
            res = f'<a href="{self.url}" class="link">{res}</a>'
        return res


def wrap(s, width):
    chunks = []
    while s:
        if len(s) < width:
            chunks += [s]
        else:
            chunks += [s[:width].rsplit(' ', 1)[0]]
        s = s[len(chunks[-1]) :].strip()
    return '<br/>'.join(chunks)


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


class Grid(Block):
    def __init__(self, rows=0, cols=0, width=None, height=None, id='', aligns=None, limited=False, has_header=False):
        super().__init__(width=width, height=height, id=id, limited=limited)
        self.rows = rows
        self.cols = cols
        self.cells = [[None for i in range(cols)] for j in range(rows)]
        self.aligns = aligns
        self.has_header = has_header

    def add_row(self, row=[]):
        assert len(row) <= self.cols, 'Row has more items than grid rows have'
        self.rows += 1
        if len(row) < self.cols:
            row += [None] * (self.cols - len(row))
        self.cells += [row]

    def set_cell(self, row, col, block):
        assert row < self.rows
        assert col < self.cols
        self.cells[row][col] = block

    def render_children(self, limited=False):
        width = f' width="{self.width}"' if self.width else ''
        res = f'<table{width} class="grid">'
        for row in range(self.rows):
            res += '<tr>'
            for col in range(self.cols):
                child = self.cells[row][col]
                childHtml = child.render(limited=self.limited) if child else '&nbsp'
                align = f'align="{self.aligns[col]}"' if self.aligns else ''
                tag = 'th' if row == 0 and self.has_header else 'td'
                res += f'<{tag} {align}>{childHtml}</{tag}>\n'
            res += '</tr>'
        res += '</table>'
        return res


class Page(Block):
    def __init__(self, children=[], align_children='vertical'):
        super().__init__(children=children, align_children=align_children)
        self.onloadcode = ''

    def add_onloadcode(self, code):
        ''' Add extra js code to be run in window.onload'''
        self.onloadcode += code

    def render(self, filename, limited=False):
        with open(filename, 'w') as f:

            timestamp = cache_time_stamp().strftime('%d-%m %H:%M')

            template = 'template_limited.html' if limited else 'template.html'
            with open(Path(__file__).resolve().parent / template) as t:
                template_html = t.read()
            page_html = (
                template_html.replace('[timestamp]', timestamp)
                .replace('[children]', self.render_children(limited))
                .replace('[onloadcode]', self.onloadcode)
            )
            f.write(page_html)

    def render_absolute(self, left=None, top=None, limited=False):
        raise ('Page has no render absolute')
