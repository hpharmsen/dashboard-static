import pandas as pd
from functools import partial

defsize = 12
midsize = 28
headersize = 43


def doFormat(item, format=None):
    if format:
        plus = ''
        if format[0] == '+':
            format = format[1:]
            if item > 0:
                plus = '+'
        if format == 'K':
            formatted = f'{item / 1000:,.0f} K'.replace(',', '.')
        elif format == '%':
            formatted = f"{item:.0f}%"
        elif format == '%1':
            formatted = f"{item:.1f}%"
        elif format == '.':
            formatted = f"{item:,.0f}".replace(',', '.')
        elif format == '.1':
            formatted = f"{item:,.1f}".replace(',', '.')
        elif format == '.2':
            formatted = f"{item:,.2f}".replace(',', '.')
        elif format == '€':
            formatted = f"€ {item:,.0f}".replace(',', '.')
        elif format == '.5':
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


identityformatter = lambda x: x
euroformatter = partial(doFormat, format='€')
floatformatter = partial(doFormat, format='.')
