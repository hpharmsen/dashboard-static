from datetime import datetime, date, timedelta

from dateutil.relativedelta import relativedelta

from model.caching import reportz
from settings import DATE_FORMAT


class Day():
    ''' In Dashboard most dates are used as yyy-mm-dd strings. This class is to facilitate that. '''

    def __init__(self, *args):
        if len(args) == 3:
            self.str = datetime(*args).strftime(DATE_FORMAT)
        elif len(args) == 0:
            self.str = datetime.today().strftime(DATE_FORMAT)
        elif isinstance(args[0], str):
            self.str = args[0]
        elif isinstance(args[0], (date, datetime)):
            self.str = args[0].strftime(DATE_FORMAT)
        else:
            raise f'Invalid type passed to Day class: {args[0]} with type {type(args[0])}'
        y, m, d = self.str.split('-')
        self.d, self.m, self.y = int(d), int(m), int(y)

    def __str__(self):
        return self.str

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


@reportz(hours=24)
def fraction_of_the_year_past(start_day=None):
    if start_day:
        start_date_time = datetime.combine(start_day, datetime.min.time())
    else:
        y = datetime.today().year
        start_date_time = datetime(y, 1, 1)
    end_date_time = datetime.today()
    days_in_the_year = (end_date_time - start_date_time).days + 1
    return days_in_the_year / 365


if __name__ == '__main__':
    day = Day(datetime.now())
    print(f'today is {day}')
