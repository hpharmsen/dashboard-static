from datetime import datetime, date, timedelta

from dateutil.relativedelta import relativedelta

from model.caching import cache
from settings import DATE_FORMAT


class Day:
    """In Dashboard most dates are used as yyy-mm-dd strings. This class is to facilitate that."""

    def __init__(self, *args):
        if len(args) == 3:
            dt = datetime(*args)
        elif len(args) == 0:
            dt = datetime.today()
        elif isinstance(args[0], str):
            y, m, d = args[0].split('-')
            dt = datetime(int(y), int(m), int(d))
        elif isinstance(args[0], (date, datetime)):
            dt = args[0]
        else:
            raise f'Invalid type passed to Day class: {args[0]} with type {type(args[0])}'
        self.str = dt.strftime(DATE_FORMAT)
        self.d, self.m, self.y = dt.day, dt.month, dt.year

    def __str__(self):
        return self.str

    def __lt__(self, other):
        return str(self) < str(other)

    def __gt__(self, other):
        return str(self) > str(other)

    def __le__(self, other):
        return str(self) <= str(other)

    def __ge__(self, other):
        return str(self) >= str(other)

    def __eq__(self, other):
        return str(self) == str(other)

    def __sub__(self, other):
        return (self.as_datetime() - other.as_datetime()).days

    def __hash__(self):
        return hash(str(self))

    def as_datetime(self):
        return datetime(self.y, self.m, self.d)

    def plus_days(self, increment):
        return Day(self.as_datetime() + timedelta(days=increment))

    def plus_weeks(self, increment):
        return Day(self.as_datetime() + relativedelta(weeks=increment))  # relativedelta

    def plus_months(self, increment):
        return Day(self.as_datetime() + relativedelta(months=increment))  # relativedelta

    def next(self):
        return self.plus_days(1)

    def next_weekday(self):
        day = self.plus_days(1)
        while day.day_of_week() >= 5:
            day = day.plus_days(1)
        return day

    def prev(self):
        return self.plus_days(-1)

    def day_of_week(self):
        return self.as_datetime().weekday()

    def week_number(self):
        return self.as_datetime().isocalendar()[1]

    def last_monday(self):
        return self.plus_days(-self.as_datetime().weekday())

    def strftime(self, date_format: str):
        return self.as_datetime().strftime(date_format)


class Period:
    """Utility class bundling a startdate and optionally an end date"""

    def __init__(self, fromday, untilday=None):
        if not isinstance(fromday, Day):
            fromday = Day(fromday)
        self.fromday = fromday
        if untilday and not isinstance(untilday, Day):
            untilday = Day(untilday)
        self.untilday = untilday

    def __str__(self):
        return f'{self.fromday} --> {self.untilday if self.untilday else ""}'


@cache(hours=24)
def fraction_of_the_year_past(start_day=None):
    if start_day:
        start_date_time = datetime.combine(start_day, datetime.min.time())
    else:
        y = datetime.today().year
        start_date_time = datetime(y, 1, 1)
    end_date_time = datetime.today()
    days_in_the_year = (end_date_time - start_date_time).days + 1
    return days_in_the_year / 365


def flatten_json(y):
    """ What it says: turns a json structure into a flat list of dicts """
    out = {}

    def flatten(x, name=""):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + "_")
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + str(i) + "_")
                i += 1
        else:
            out[name[:-1]] = x

    flatten(y)
    return out


if __name__ == '__main__':
    day = Day(datetime.now())
    print(f'today is {day}')
