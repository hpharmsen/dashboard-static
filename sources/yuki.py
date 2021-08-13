from pathlib import Path
import requests
import datetime
from configparser import ConfigParser
from bs4 import BeautifulSoup
from decimal import Decimal

from model.caching import reportz
from settings import ini

BASE_URL = 'https://api.yukiworks.nl/ws/Accounting.asmx'

_yuki = None  # Singleton


def yuki():
    global _yuki
    if not _yuki:
        _yuki = Yuki()
    return _yuki


class Yuki:
    def __init__(self):
        api_key = ini['yuki']['api_key']
        self.administration_id = ini['yuki']['administration_id']
        body = self.call('/Authenticate', {'accessKey': api_key})
        self.session_id = body.text

    def call(self, endpoint, params={}):
        url = BASE_URL + endpoint + '?'
        if hasattr(self, 'session_id'):
            url += f'sessionID={self.session_id}&'
        if hasattr(self, 'administration_id'):
            url += f'administrationID={self.administration_id}&'
        for key, value in params.items():
            url += f'{key}={value}&'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        return soup.html.body

    def administrations(self):
        body = self.call(f'/Administrations')
        admins = body.administrations.find_all('administration')
        return [(a.contents[1].text, a['id']) for a in admins]

    def debtors(self):
        # Returns list of date:datetime, days:int, customer:str, description:str, open:Decimal
        params = {'includeBankTransactions': 'false', 'sortOrder': '1'}
        body = self.call(f'/OutstandingDebtorItems', params)
        items = body.outstandingdebtoritems.find_all('item')
        result = []
        for item in items:
            balance_type = item.type
            if item.type.text == 'Beginbalans':
                continue
            date = datetime.datetime.strptime(item.date.text, '%Y-%m-%d')
            days = (datetime.datetime.today() - date).days
            contact = item.contact.text
            self.text = item.description.text
            description = self.text
            openamount = float(item.openamount.text)
            result += [
                {'date': date, 'days': days, 'customer': contact, 'description': description, 'open': openamount}
            ]
        return result

    # @reportz(hours=24)
    def account_balance(self, date_str=None, balance_type=None, account_codes=None):
        # Resultatenrekening en balans
        if not date_str:
            date_str = datetime.datetime.today().strftime('%Y-%m-%d')
        if type(account_codes) == 'str':
            account_codes = [account_codes]

        def valid_code(code):
            if not account_codes:
                return True
            for c in account_codes:
                if code.startswith(c):
                    return True
            return False

        params = {'transactionDate': date_str}
        body = self.call(f'/GLAccountBalance', params)
        items = body.glaccountbalance.find_all('glaccount')
        # <glaccount balancetype="B" code="02110">
        #   <description>Verbouwingen</description>
        #   <amount>104488.58</amount>
        # </glaccount>
        res = [
            {
                'description': item.description.text,
                'amount': Decimal(item.amount.text),
                'code': item.attrs['code'],
                'balance_type': item.attrs['balancetype'],
            }
            for item in items
            if (not balance_type or item.attrs['balancetype'] == balance_type) and valid_code(item.attrs['code'])
        ]
        return res

    def profit(self, date_str=None):
        return self.income(date_str) - self.costs(date_str)

    def income(self, date_str=None):
        res = -sum([a['amount'] for a in self.account_balance(date_str, account_codes='8')])
        return res

    def direct_costs(self, date_str=None):
        res = sum([a['amount'] for a in self.account_balance(date_str, account_codes=['6'])])
        return res

    def costs(self, date_str=None):
        res = sum([a['amount'] for a in self.account_balance(date_str, account_codes=['4'])])
        return res


if __name__ == '__main__':
    yuki = Yuki()
    print(yuki.profit('2021-01-31'))

    print(yuki.profit())
    print(yuki.income())
    print(yuki.costs())
    print(yuki.income() - yuki.costs())
    # print(yuki.administrations())
    # print(yuki.debtors())
