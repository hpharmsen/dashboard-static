import sys
import requests
import datetime
from bs4 import BeautifulSoup
from decimal import Decimal

from model.caching import reportz
from settings import ini

BASE_URL = 'https://api.yukiworks.nl/ws/Accounting.asmx'

_yuki = None  # Singleton

ASSETS = 1
LIABILITIES = 2
INCOME = 3
COSTS = 4

ACCOUNT_CODES = {
    'tangible_fixed_assets': '02',
    'investments': ['02110', '02200', '02300', '02400'],
    # Verbouwingen, Machines, Inventaris, Hardware (tangible minus afschrijvingen)
    'financial_fixed_assets': '03',
    'share_capital': '0800',
    'reserves': ['0840', '0805', '0890'],  # Algemene reserve, Agio reserve, Overige reserve
    'undistributed_result': ['0900'],
    'liquid_assets': [11, 12],
    'debtors': 1300,
    'other_receivables': [1321, 1330, 1335, 1350, 13999, 233],
    'kruisposten': 23101,  # Special case, kan debet en credit zijn
    'creditors': [16000],
    'other_debts': [15, 16100, 16999, 23000, 23010, 23020],
    'debts_to_employees': [170, 175, 20000],
    'taxes': [171, 176, 179, 18, 24],
    'costs': 4,
    'people': 40,
    'housing': 41,
    'marketing': 44,
    'other_expenses': 45,
    'depreciation': 49,
    'teamproposition': 80002,
    'productproposition': [80001, 80050],
    'service': 80004,
    'hosting': 80003,
    'turnover': [8000, 8005, 8006, 80999],  # Alles behalve onderhuur
    'other_income': [80070],  # Onderhuur
    'subsidy': 40105,
    'income': 8,
    'hosting_expenses': 60352,
    'outsourcing_expenses': 60350,
    'project_expenses': 60351,
    'financial_result': [85, 86, 87, 88, 89],
}


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
        if response.status_code == 500:
            print('Yuki:', response.text)
            sys.exit()
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

    @reportz(hours=24)
    def account_balance(self, date_str=None, balance_type=None, account_codes=None):
        # Resultatenrekening en balans
        if not date_str:
            date_str = datetime.datetime.today().strftime('%Y-%m-%d')
        if account_codes and type(account_codes) != list:
            account_codes = [account_codes]

        def valid_code(code):
            if not account_codes:
                return True
            for c in account_codes:
                if code.startswith(str(c)):
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
        return self.post('costs', date_str)

    @reportz(hours=24)
    def post(self, account, account_type=None, date_str=None):
        ab = self.account_balance(date_str, account_codes=ACCOUNT_CODES[account])
        res = 0
        for a in ab:
            if account_type in (ASSETS, COSTS):
                multiplier = 1
            elif account_type in (LIABILITIES, INCOME):
                multiplier = -1
            else:
                multiplier = (
                    -1
                    if a['code'][:2]
                    in (
                        '08',
                        '09',
                        '15',
                        '16',
                        '17',
                        '18',
                        '20',
                        '23',
                        '24',
                        '49',
                        '60',
                        '80',
                        '85',
                        '86',
                        '87',
                        '88',
                        '89',
                    )
                    else 1
                )
            res += a['amount'] * multiplier
        import pandas as pd

        p = pd.DataFrame(ab)
        return res

    def test_codes(self):

        account_codes = []
        for codes in ACCOUNT_CODES.values():
            if type(codes) != list:
                codes = [codes]
            account_codes += [str(code) for code in codes]

        ab = yuki.account_balance()
        for post in ab:
            for ac in account_codes:
                if post['code'].startswith(ac):
                    break
            else:
                print(f"code {post['code']} ({post['description']} ) niet gevonden.")
                continue
        else:
            print('Grote else')


if __name__ == '__main__':
    yuki = Yuki()
    yuki.test_codes()
    j = yuki.account_balance('2021-01-31')
    s = yuki.account_balance('2021-09-30')
    import pandas as pd

    dj = pd.DataFrame(j)
    ds = pd.DataFrame(s)
    print(yuki.profit('2021-01-31'))

    print(yuki.profit())
    print(yuki.income())
    print(yuki.costs())
    print(yuki.income() - yuki.costs())
    # print(yuki.administrations())
    # print(yuki.debtors())
