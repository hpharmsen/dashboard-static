import calendar

from model.onderhanden_werk import ohw_sum
from model.utilities import Day
from sources.yuki_accountmodel import YukiAccountModel


class YukiResult:
    def __init__(self, year, month, minimal_interesting_owh_value):
        self.year = year
        self.month = month
        self.day = last_date_of_month(year, month)
        self.prev_day = last_date_of_month(year, month - 1) if month > 1 else last_date_of_month(year - 1, 12)
        self.yuki_now = YukiAccountModel(self.day)
        self.yuki_now.add_ohw(ohw_sum(self.day, minimal_interesting_owh_value))
        self.yuki_last = YukiAccountModel(self.prev_day)
        self.yuki_last.add_ohw(ohw_sum(self.prev_day, minimal_interesting_owh_value))

    def month(self, name):
        return self.yuki_now.post(name)[0] - self.yuki_last.post(name)[0]

    def month_ytd(self, name):
        ytd = self.yuki_now.post(name)[0]
        month = ytd - self.yuki_last.post(name)[0]
        return month, ytd

    def month_prev(self, name):
        return self.yuki_now.post(name)[0], self.yuki_last.post(name)[0]

    def post(self, name):
        return self.yuki_now.post(name)[0]


def last_date_of_month(year: int, month: int):
    return Day(year, month, calendar.monthrange(year, month)[1])


def tuple_add(*args):  # 135965+115941+40046+5395+1880
    return [sum(value) for value in list(zip(*args))]
