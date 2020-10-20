from datetime import datetime

from model.caching import reportz


@reportz(hours=24)
def fraction_of_the_year_past(start_day=None):
    if start_day:
        start_date_time = datetime.combine(start_day, datetime.min.time())
    else:
        y = datetime.today().year
        start_date_time = datetime(y, 1, 1)
    days_in_the_year = (datetime.today() - start_date_time).days + 1
    return days_in_the_year / 365