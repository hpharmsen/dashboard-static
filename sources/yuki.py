from pathlib import Path
import requests
import datetime
from configparser import ConfigParser
from bs4 import BeautifulSoup

BASE_URL = 'https://api.yukiworks.nl/ws/Accounting.asmx'

_yuki = None  # Singleton


def yuki():
    global _yuki
    if not _yuki:
        _yuki = Yuki()
    return _yuki


class Yuki:
    def __init__(self):
        ini = ConfigParser()
        ini.read(Path(__file__).resolve().parent / 'credentials.ini')
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
            date = datetime.datetime.strptime(item.date.text, '%Y-%m-%d')
            days = (datetime.datetime.today() - date).days
            contact = item.contact.text
            description = item.description.text
            openamount = float(item.openamount.text)
            result += [
                {'date': date, 'days': days, 'customer': contact, 'description': description, 'open': openamount}
            ]
        return result


if __name__ == '__main__':
    yuki = Yuki()
    print(yuki.administrations())
    print(yuki.debtors())
