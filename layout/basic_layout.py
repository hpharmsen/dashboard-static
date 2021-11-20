''' For formatting text in Blocks '''

from functools import partial
import pandas as pd

DEF_SIZE = 12
MID_SIZE = 28
HEADER_SIZE = 43


def do_format(item, format_string=None):
    if format_string:
        plus = ''
        if format_string[0] == '+':
            format_string = format_string[1:]
            if item > 0:
                plus = '+'
        if format_string == 'K':
            formatted = f'{item / 1000:,.0f} K'.replace(',', '.')
        elif format_string == '%':
            formatted = f"{item:.0f}%"
        elif format_string == '%1':
            formatted = f"{item:.1f}%"
        elif format_string == '.':
            formatted = f"{item:,.0f}".replace(',', '.')
        elif format_string == '.1':
            formatted = f"{item:,.1f}".replace(',', '.')
        elif format_string == '.2':
            formatted = f"{item:,.2f}".replace(',', '.')
        elif format_string == '€':
            formatted = f"€ {item:,.0f}".replace(',', '.')
        elif format_string == '.5':
            formatted = str(round(float(str(item).replace(',', '.')) * 2) / 2)
        try:
            return plus + formatted
        except:
            pass

    if isinstance(item, float):
        formatted = f'{item:,.0f}'.replace(',', '.')
    elif isinstance(item, pd.DataFrame):
        formatted = item.to_html(index=False)
    else:
        formatted = item

    return formatted


identity_formatter = lambda x: x
euro_formatter = partial(do_format, format='€')
float_formatter = partial(do_format, format='.')
k_formatter = partial(do_format, format='K')