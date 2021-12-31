import calendar

# from model.onderhanden_werk import simplicate_onderhanden_werk
from model.onderhanden_werk import ohw
from model.utilities import Day
from sources.yuki import Yuki, COSTS, ASSETS, LIABILITIES


class YukiResult:
    def __init__(self, year, month):
        self.year = year
        self.month = month
        self.date = last_date_of_month(year, month)
        self.prev_day = last_date_of_month(year, month - 1) if month > 1 else last_date_of_month(year - 1, 12)
        self.yuki = Yuki()

    def month(self, name, day: Day, account_type: int = None):
        assert day is None or isinstance(day, Day)
        assert account_type is None or isinstance(account_type, int)
        day, prev_day = self.day_couple(day)
        return self.yuki.post(name, account_type, day) - self.yuki.post(name, account_type, prev_day)

    def month_ytd(self, name, day: Day = None, account_type: int = None):
        assert day is None or isinstance(day, Day)
        assert account_type is None or isinstance(account_type, int)
        day, prev_day = self.day_couple(day)
        ytd = self.yuki.post(name, account_type, day)
        monthly = ytd - self.yuki.post(name, account_type, prev_day)
        return monthly, ytd

    def month_prev(self, name, day: Day = None, account_type: int = None):
        assert day is None or isinstance(day, Day)
        assert account_type is None or isinstance(account_type, int)
        day, prev_day = self.day_couple(day)
        current_value = self.yuki.post(name, account_type, day)
        previous_value = self.yuki.post(name, account_type, prev_day)
        return current_value, previous_value

    def day_couple(self, day: Day = None):
        """Returns a date plus last day of previous month if date is passed.
        If not, returns self.date and self.prev_day"""
        if day:
            prev_day = last_date_of_month(day.y, day.m - 1) if day.m > 1 else last_date_of_month(day.y - 1, 12)
        else:
            day = self.date
            prev_day = self.prev_day
        return day, prev_day

    def total_profit(self, day: Day = None):
        return tuple_add(self.profit(day), self.mutation_wip(day))

    def mutation_wip(self, day: Day):
        wip_now, wip_last_month = self.get_work_in_progress(day)
        if not day:
            day = Day()
        year_start = Day(day.y, 1, 1)
        wip_year_start = ohw(year_start)
        return (
            wip_now - wip_last_month,
            wip_now - wip_year_start,
        )

    def profit(self, day: Day = None):
        res = [
            b + oi - oe + d + f
            for b, oi, oe, d, f in zip(
                self.bbi(day),
                self.other_income(day),
                self.operating_expenses(day),
                self.depreciation(day),
                self.financial(day),
            )
        ]
        return res

    def financial(self, day: Day = None):
        return self.month_ytd('financial_result', day)

    def depreciation(self, day: Day = None):
        return self.month_ytd('depreciation', day)

    def operating_expenses(self, day: Day = None):
        return tuple_add(self.personnell(day), self.company_costs(day))

    # def margin(self):
    #     return tuple_add(self.product_propositie(),
    #                      self.team_propositie(),
    #                      self.service(),
    #                      self.hosting(),
    #                      self.travelbase(),
    #                      self.other_income())

    def product_propositie(self, day: Day = None):
        return tuple_add(self.omzet(day), self.projectkosten(day))

    def omzet(self, day: Day = None):
        return self.month_ytd('turnover', day)

    def projectkosten(self, day: Day = None):
        return self.month_ytd('project_expenses', day)

    def team_propositie(self, day: Day = None):
        return tuple_add(self.omzet_trajecten(day), self.uitbesteed_werk(day))

    def uitbesteed_werk(self, day: Day = None):
        return self.month_ytd('outsourcing_expenses', day)

    def omzet_trajecten(self, day: Day = None):
        return self.month_ytd('teamproposition', day)

    def service(self, day: Day = None):
        return self.month_ytd('service', day)

    def hosting(self, day: Day = None):
        return tuple_add(
            self.month_ytd('hosting', day), self.month_ytd('hosting_expenses', day)
        )

    def travelbase(self, day: Day = None):
        return 0, 0  # self.month_ytd('travelbase', day ) # todo: Hier aparte post in Yuki van maken?

    def bbi(self, day: Day = None):
        res = tuple_add(
            self.omzet(day),
            self.projectkosten(day),
            self.uitbesteed_werk(day),
            self.month_ytd('hosting_expenses', day),
        )
        return res

    def other_income(self, day: Day = None):
        return self.month_ytd('other_income', day)

    def personnell(self, day: Day = None):
        return tuple_add(self.people(day), self.wbso(day))

    def company_costs(self, day: Day = None):
        return tuple_add(
            self.housing(day), self.marketing(day), self.other_expenses(day)
        )

    def marketing(self, day: Day = None):
        return self.month_ytd('marketing', day)

    def housing(self, day: Day = None):
        return self.month_ytd('housing', day)

    def other_expenses(self, day: Day = None):
        return self.month_ytd('other_expenses', account_type=COSTS, day=day)

    def people(self, day: Day = None):
        return tuple(p - w for p, w in zip(self.month_ytd('people', day), self.wbso(day)))

    def wbso(self, day: Day = None):
        return self.month_ytd('subsidy', day)

    # BALANCE
    def short_term_debt(self, day: Day = None):
        return tuple_add(
            self.creditors(day),
            self.debt_to_employees(day),
            self.taxes(day),
            self.other_debts(day),
        )

    def creditors(self, day: Day = None):
        return self.month_prev('creditors', day)

    def debt_to_employees(self, day: Day = None):
        return self.month_prev('debts_to_employees', day)

    def taxes(self, day: Day = None):
        return self.month_prev('taxes', day)

    def other_debts(self, day: Day = None):
        result = self.month_prev('other_debts', account_type=LIABILITIES, day=day)
        kruisposten = self.month_prev('kruisposten', day)
        if kruisposten[0] > 0:
            result = (result[0] + kruisposten[0], result[1])
        if kruisposten[1] > 0:
            result = (result[0], result[1] + kruisposten[1])
        return result

    def other_receivables(self, day: Day = None):
        result = self.month_prev('other_receivables', account_type=ASSETS, day=day)
        kruisposten = self.month_prev('kruisposten', day)
        if kruisposten[0] < 0:
            result = (result[0] - kruisposten[0], result[1])
        if kruisposten[1] < 0:
            result = (result[0], result[1] - kruisposten[1])
        return result

    def get_work_in_progress(self, day: Day = None):
        day, prev_day = self.day_couple(day)
        return ohw(day), ohw(prev_day)


def last_date_of_month(year: int, month: int):
    return Day(year, month, calendar.monthrange(year, month)[1])
    # was :return f'{year}-{month:02}-{calendar.monthrange(year, month)[1]:02}'


def tuple_add(*args):  # 135965+115941+40046+5395+1880
    return [sum(value) for value in list(zip(*args))]
