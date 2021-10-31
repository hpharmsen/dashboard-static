from functools import partial
from pathlib import Path
from model.caching import cache_modified_time_stamp

from layout.basic_layout import doFormat

Kformatter = partial(doFormat, format='K')

# Block: children=[],  align_children='absolute',; id='',
# HVBlock: children=[], id=''
# Text: text, font_size=12,; color='',; font_family='Arial',; style='',; format=''

# width=None,; height=None,; bg_color='white', link/url, tooltip, padding


class Block:
    def __init__(
        self,
        children=[],
        width=None,
        height=None,
        bg_color='white',
        align_children='absolute',
        id='',
        tooltip='',
        padding=40,
        link=None,
        css_class='',
        style='',
    ):
        self.id = id
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.align_children = align_children
        for child in children:
            assert child == None or isinstance(child, Block), f'Block {child} should be an instance of Block'
        self.children = [(child, '') for child in children]
        self.tooltip = tooltip  # If set, shows this text as an html over tooltip
        self.padding = padding  # Distance to next object
        self.link = link  # Anchor for this block
        self.css_class = css_class
        self.style = style

    def add_absolute_block(self, left, top, block, link=''):
        ''' Will be deprecated '''
        self.children += [(left, top, block, link)]

    def add_block(self, block, link=''):
        self.children += [(block, link)]

    def render_content(self):
        return ''

    def render_children(self):
        res = ''
        if self.align_children == 'absolute':
            for left, top, child, link in self.children:
                c = child.render_absolute(left, top)
                if link:
                    c = f'<a href="{link}" class="link">{c}</a>'
                res += '\n' + c
        else:
            for child, link in self.children:
                if child:
                    c = child.render(self.align_children)
                    if link:
                        c = f'<a href="{link}" class="link">{c}</a>'
                    res += '\n' + c
        return res

    def render_absolute(self, left=None, top=None):
        return self.do_render('absolute', left=left, top=top)
        # return f'''<div style="position:absolute; left:{left}px; top:{top}px; {width} {height} background-color:{self.bg_color}">
        #             {self.content()}
        #             {self.render_children()}
        #             </div>
        #         '''

    def render(self, align=''):
        id = f'id="{self.id}"' if self.id else ''

        clear = 'clear:both;' if align == 'vertical' else ''
        float = 'float:left;' if align == 'horizontal' else ''
        if align == 'horizontal':
            padding = f'padding-right:{self.padding}px;'
        elif align == 'vertical':
            padding = f'padding-bottom:{self.padding}px;'
        else:
            padding = ''
        return self.do_render('relative', id=id, clear=clear, float=float, padding=padding)

    def do_render(self, position, id='', clear='', float='', padding='', left=None, top=None):
        height = f'height:{self.height}px; ' if self.height else ''
        width = f'width:{self.width}px; ' if self.width else ''
        position_str = (
            f'position:absolute; left:{left}px; top:{top}px;'
            if position == 'absolute'
            else f'position:relative; {float} {clear}'
        )
        classes = self.css_class if self.css_class else ''
        if self.tooltip:
            classes += ' tooltip'
        # tooltip_class = 'class="tooltip"' if self.tooltip else ''
        if classes:
            classes = f'class="{classes}"'

        tooltip_text = f'<span class="tooltiptext">{wrap(self.tooltip,42)}</span>' if self.tooltip else ''
        res = f'''<div {id} {classes} style="{self.style} {position_str} {width} {height} {padding} background-color:{self.bg_color}; ">
                    {tooltip_text}
                    {self.render_content()}
                    {self.render_children()}
                    </div>
                '''
        if self.link:
            res = f'<a href="{self.link}">{res}</a>'
        return res


class HBlock(Block):
    def __init__(
        self, children=[], width=None, height=None, padding=40, bg_color='white', id='', link=None, tooltip=None
    ):
        super().__init__(
            children=children,
            width=width,
            height=height,
            padding=padding,
            bg_color=bg_color,
            id=id,
            align_children='horizontal',
            link=link,
            tooltip=tooltip,
        )


class VBlock(Block):
    def __init__(
        self,
        children=[],
        width=None,
        height=None,
        padding=40,
        bg_color='white',
        id='',
        link=None,
        tooltip=None,
        css_class='',
        style='',
    ):
        super().__init__(
            children=children,
            width=width,
            height=height,
            padding=40,
            bg_color=bg_color,
            id=id,
            align_children='vertical',
            link=link,
            tooltip=tooltip,
            css_class=css_class,
            style=style,
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
        tooltip='',
        padding=30.0,
        pagebreak=False,
    ):
        super().__init__([], width=width, height=height, bg_color=bg_color, tooltip=tooltip, padding=padding)
        self.text = doFormat(text, format)
        self.font_size = font_size
        self.font_family = font_family
        self.style = style
        if callable(color):  # color parameter could be a function of the text passed
            self.color = color(text)
        else:
            self.color = color
        self.url = url
        self.page_break_before = pagebreak

    def render_content(self):
        colorstr = f'color:{self.color};' if self.color else ''
        pagebreak = ' class="new-page" ' if self.page_break_before else ''
        res = f'''<span {pagebreak} style="font-size:{self.font_size}px; {colorstr} font-family:{self.font_family}; {self.style}">{self.text}</span>'''
        if self.url:
            res = f'<a href="{self.url}" class="link">{res}</a>'
        return res


def wrap(s, width):
    if s.count('<br'):
        return s # Newlines already included. No wrapping needed
    chunks = []
    while s:
        if len(s) < width:
            chunks += [s]
        else:
            chunks += [s[:width].rsplit(' ', 1)[0]]
        s = s[len(chunks[-1]) :].strip()
    return '<br/>'.join(chunks)


class Grid(Block):
    def __init__(self, rows=0, cols=0, width=None, line_height=None, id='', aligns=None, has_header=False):
        super().__init__(width=width, id=id)
        self.rows = rows
        self.cols = cols
        self.cells = [[None for i in range(cols)] for j in range(rows)]
        self.styles = []  # Cell styles
        self.aligns = aligns
        self.line_height = line_height
        self.has_header = has_header

    def add_row(self, row=[], styles=[]):
        assert len(row) <= self.cols, 'Row has more items than grid rows have'
        self.rows += 1
        if len(row) < self.cols:
            row += [None] * (self.cols - len(row))
        self.cells += [row]
        self.styles += [styles]  # Cell styles

    def set_cell(self, row, col, block):
        assert row < self.rows
        assert col < self.cols
        self.cells[row][col] = block

    def render_children(self):
        width = f' width="{self.width}"' if self.width else ''
        res = f'<table{width} class="grid">'
        for row in range(self.rows):
            styles = self.styles[row] if self.styles else []
            line_height = f' style="line-height:{self.line_height}px;"' if self.line_height else ''
            res += f'<tr{line_height}>'
            for col in range(self.cols):
                child = self.cells[row][col]
                childHtml = child.render() if child else '&nbsp'
                align = f' align="{self.aligns[col]}"' if self.aligns else ''
                tag = 'th' if row == 0 and self.has_header else 'td'
                style = f' style="{styles[col]}"' if len(styles) > col else ''
                res += f'<{tag}{align}{style}>{childHtml}</{tag}>\n'
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

    def render(self, filename: Path, template='template.html'):
        with open(filename, 'w') as f:

            timestamp = cache_modified_time_stamp().strftime('%d-%m %H:%M')
            base = (
                '..' if str(filename).count('klanten/') else '.'
            )  # Als file in subdir: base=..  Kan netter voor subsubs etc.

            with open(Path(__file__).resolve().parent / template) as t:
                template_html = t.read()
            page_html = (
                template_html.replace('[timestamp]', timestamp)
                .replace('[children]', self.render_children())
                .replace('[onloadcode]', self.onloadcode)
                .replace('[base]', base)
            )
            f.write(page_html)

    def render_absolute(self, left=None, top=None):
        raise ('Page has no render absolute')
