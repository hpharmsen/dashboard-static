import calendar

from sources.simplicate import onderhanden_werk
from sources.yuki import Yuki, COSTS, ASSETS, LIABILITIES


class YukiResult:
    def __init__(self, year, month):
        self.year = year
        self.month = month
        self.date = last_date_of_month(year, month)
        self.prev_date = last_date_of_month(year, month - 1) if month > 1 else last_date_of_month(year - 1, 12)
        self.yuki = Yuki()

    def month(self, name, account_type: int = None, date_str: str = None):
        date_str, prev_date = self.date_couple(date_str)
        return self.yuki.post(name, account_type, date_str) - self.yuki.post(name, account_type, prev_date)

    def month_ytd(self, name, account_type: int = None, date_str: str = None):
        date_str, prev_date = self.date_couple(date_str)
        ytd = self.yuki.post(name, account_type, date_str)
        monthly = ytd - self.yuki.post(name, account_type, prev_date)
        return (monthly, ytd)

    def month_prev(self, name, account_type: int = None, date_str: str = None):
        date_str, prev_date = self.date_couple(date_str)
        current_value = self.yuki.post(name, account_type, date_str)
        previous_value = self.yuki.post(name, account_type, prev_date)
        return (current_value, previous_value)

    def date_couple(self, date_str: str):
        """Returns a date plus last day of previous month if date is passed.
        If not, returns self.date and self.prev_date"""
        if date_str:
            y, m, d = date_str.split('-')
            y = int(y)
            m = int(m)
            prev_date = last_date_of_month(y, m - 1) if m > 1 else last_date_of_month(y - 1, 12)
        else:
            date_str = self.date
            prev_date = self.prev_date
        return date_str, prev_date

    def total_profit(self, date_str: str = None):
        return tuple_add(self.profit(date_str=date_str), self.mutation_wip(date_str=date_str))

    def mutation_wip(self, date_str: str):
        wip_now, wip_last_month = self.get_work_in_progress(date_str=date_str)
        return (
            wip_now - wip_last_month,
            wip_now - 0,
        )  # !! Die 0 is in 2021 het geval. Moet per 2022 wellicht anders.

    def profit(self, date_str: str = None):
        # 306594 - 203625 - 5233
        b = self.bbi(date_str=date_str)
        oi = self.other_income(date_str=date_str)
        oe = self.operating_expenses(date_str=date_str)
        d = self.depreciation(date_str=date_str)
        f = self.financial(date_str=date_str)
        res = [
            b + oi - oe + d + f
            for b, oi, oe, d, f in zip(
                self.bbi(date_str=date_str),
                self.other_income(date_str=date_str),
                self.operating_expenses(date_str=date_str),
                self.depreciation(date_str=date_str),
                self.financial(date_str=date_str),
            )
        ]
        return res

    def financial(self, date_str: str = None):
        return self.month_ytd('financial_result', date_str=date_str)

    def depreciation(self, date_str: str = None):
        return self.month_ytd('depreciation', date_str=date_str)

    def operating_expenses(self, date_str: str = None):
        return tuple_add(self.personnell(date_str=date_str), self.company_costs(date_str=date_str))

    # def margin(self):
    #     return tuple_add(self.product_propositie(),
    #                      self.team_propositie(),
    #                      self.service(),
    #                      self.hosting(),
    #                      self.travelbase(),
    #                      self.other_income())

    def product_propositie(self, date_str: str = None):
        return tuple_add(self.omzet(date_str=date_str), self.projectkosten(date_str=date_str))

    def omzet(self, date_str: str = None):
        return self.month_ytd('turnover', date_str=date_str)

    def projectkosten(self, date_str: str = None):
        return self.month_ytd('project_expenses', date_str=date_str)

    def team_propositie(self, date_str: str = None):
        return tuple_add(self.omzet_trajecten(date_str=date_str), self.uitbesteed_werk(date_str=date_str))

    def uitbesteed_werk(self, date_str: str = None):
        return self.month_ytd('outsourcing_expenses', date_str=date_str)

    def omzet_trajecten(self, date_str: str = None):
        return self.month_ytd('teamproposition', date_str=date_str)

    def service(self, date_str: str = None):
        return self.month_ytd('service', date_str=date_str)

    def hosting(self, date_str: str = None):
        return tuple_add(
            self.month_ytd('hosting', date_str=date_str), self.month_ytd('hosting_expenses', date_str=date_str)
        )

    def travelbase(self, date_str: str = None):
        return (0, 0)  # self.month_ytd('travelbase', date_str ) # !! Moet nog op aparte post in Yuki

    def bbi(self, date_str=None):
        o = self.omzet(date_str=date_str)
        p = self.projectkosten(date_str=date_str)
        u = self.uitbesteed_werk(date_str=date_str)
        h = self.month_ytd('hosting_expenses', date_str=date_str)
        res = tuple_add(
            self.omzet(date_str=date_str),
            self.projectkosten(date_str=date_str),
            self.uitbesteed_werk(date_str=date_str),
            self.month_ytd('hosting_expenses', date_str=date_str),
        )
        omzet_zonder_onderhuur = o[1] - self.other_income(date_str=date_str)[1]
        return res

    def other_income(self, date_str: str = None):
        return self.month_ytd('other_income', date_str=date_str)

    def personnell(self, date_str: str = None):
        return tuple_add(self.people(date_str=date_str), self.wbso(date_str=date_str))

    def company_costs(self, date_str: str = None):
        return tuple_add(
            self.housing(date_str=date_str), self.marketing(date_str=date_str), self.other_expenses(date_str=date_str)
        )

    def marketing(self, date_str: str = None):
        return self.month_ytd('marketing', date_str=date_str)

    def housing(self, date_str: str = None):
        return self.month_ytd('housing', date_str=date_str)

    def other_expenses(self, date_str: str = None):
        return self.month_ytd('other_expenses', account_type=COSTS, date_str=date_str)

    def people(self, date_str: str = None):
        return tuple(p - w for p, w in zip(self.month_ytd('people', date_str=date_str), self.wbso(date_str=date_str)))

    def wbso(self, date_str: str = None):
        return self.month_ytd('subsidy', date_str=date_str)

    # BALANCE
    def short_term_debt(self, date_str: str = None):
        return tuple_add(
            self.creditors(date_str=date_str),
            self.debt_to_employees(date_str=date_str),
            self.taxes(date_str=date_str),
            self.other_debts(date_str=date_str),
        )

    def creditors(self, date_str: str = None):
        return self.month_prev('creditors', date_str=date_str)

    def debt_to_employees(self, date_str: str = None):
        return self.month_prev('debts_to_employees', date_str=date_str)

    def taxes(self, date_str: str = None):
        return self.month_prev('taxes', date_str=date_str)

    def other_debts(self, date_str: str = None):
        result = self.month_prev('other_debts', account_type=LIABILITIES, date_str=date_str)
        kruisposten = self.month_prev('kruisposten', date_str=date_str)
        if kruisposten[0] > 0:
            result = (result[0] + kruisposten[0], result[1])
        if kruisposten[1] < 0:
            result = (result[0], result[1] + kruisposten[1])
        return result

    def other_receivables(self, date_str: str = None):
        result = self.month_prev('other_receivables', account_type=ASSETS, date_str=date_str)
        kruisposten = self.month_prev('kruisposten', date_str=date_str)
        if kruisposten[0] < 0:
            result = (result[0] - kruisposten[0], result[1])
        if kruisposten[1] < 0:
            result = (result[0], result[1] - kruisposten[1])
        return result

    def get_work_in_progress(self, date_str: str = None):
        date_str, prev_date = self.date_couple(date_str)
        return (
            onderhanden_werk(date_str=date_str),
            onderhanden_werk(date_str=prev_date),
        )


def last_date_of_month(year: int, month: int):
    return f'{year}-{month:02}-{calendar.monthrange(year, month)[1]:02}'


def tuple_add(*args):  # 135965+115941+40046+5395+1880
    return [sum(l) for l in list(zip(*args))]
