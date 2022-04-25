""" Caches yuki account balance data per day. Default is to store each last day of the month """
from functools import partial, lru_cache

from middleware.base_table import BaseTable, MONEY
from middleware.middleware_utils import singleton
from model.utilities import Day
from sources.yuki import Yuki, ACCOUNT_CODES, ASSETS, LIABILITIES


@singleton
class Account(BaseTable):
    def __init__(self):
        super().__init__()
        self.yuki = Yuki()
        self.table_name = 'account'
        self.table_definition = f"""
               day VARCHAR(10) NOT NULL,
               account VARCHAR(40) NOT NULL,
               amount {MONEY} NOT NULL,
            """
        self.primary_key = 'day__account'
        self.index_fields = ''

    def get_data(self):
        today = Day()
        y = today.y
        m = today.m
        while y >= 2021:
            day = Day(y, m, 1).prev()  # Last day of the previous month
            print('Getting yuki data for', day)
            for data in self.get_day_data(day):
                yield data
            m -= 1
            if m == 0:
                y -= 1
                m = 12

    def get_day_data(self, day):
        for account, codes in ACCOUNT_CODES.items():
            if account == 'other_receivables':
                amount = self.yuki.post(account, account_type=ASSETS, day=day)
                crossposts = self.yuki.post('crossposts', day)
                if crossposts < 0:
                    amount -= crossposts
            elif account == 'other_debts':
                amount = self.yuki.post(account, account_type=LIABILITIES, day=day)
                crossposts = self.yuki.post('crossposts', day)
                if crossposts > 0:
                    amount += crossposts
            else:
                amount = self.yuki.post(account, None, day)
            yield {'day': day, 'account': account, 'amount': amount}

    def update(self, day):
        self.db.execute(f'delete from account where day="{day}"')
        self.db.commit()
        data_func = partial(self.get_day_data, day)
        self.insert_dicts(data_func)

    @lru_cache
    def day_balance(self, day: Day):
        accounts = self.db.select(self.table_name, {'day': day})
        if not accounts:
            self.db.update(day)
            accounts = self.db.select(self.table_name, {'day': day})
        return {acc['account']: acc['amount'] for acc in accounts}

    def post(self, name: str, account_type: str, day: Day):
        day_balance = self.day_balance(day)
        value = day_balance[name]
        return value


if __name__ == '__main__':
    account_table = Account()
    # d = Day('2021-11-30')
    ##for a in account_table.get_day_data(d):
    #    pass
    account_table.repopulate()
    # account_table.update( Day('2021-12-31'))
    print(account_table.post('turnover', None, Day('2021-12-31')))
