import datetime
import json

import numpy as np
import pandas as pd
from pymysql import OperationalError

from middleware.employee import Employee
from middleware.middleware import get_middleware_db, singleton
from model.utilities import Period, Day
from sources.simplicate import simplicate, flatten_hours_data, calculate_turnover


@singleton
class Timesheet():
    def __init__(self):
        self.db = get_middleware_db()
        self._create_timesheet_table()
        # self.update()

    def _create_timesheet_table(self):
        ''' Creates the table to store timesheet data plus it's indexes '''

        # middleware_db.execute('DROP TABLE IF EXISTS timesheet;')
        self.db.execute("""CREATE TABLE IF NOT EXISTS timesheet (
                           day VARCHAR(10) NOT NULL,
                           week INTEGER NOT NULL,
                           year INTEGER NOT NULL,
                           employee VARCHAR(40) NOT NULL,
    
                           organization VARCHAR(255) NOT NULL,
                           project_id VARCHAR(50) NOT NULL,
                           project_name VARCHAR(255) NOT NULL,
                           project_number VARCHAR(10) NOT NULL,
    
                           service_id VARCHAR(50) NOT NULL,
                           service_name VARCHAR(50) NOT NULL,
    
                           tariff DECIMAL(6,2) NOT NULL,
    
                           type VARCHAR(10) NOT NULL,
                           label VARCHAR(100) NOT NULL,
    
                           hours DECIMAL(6,2) NOT NULL,
                           turnover DECIMAL(9,2) NOT NULL,
                           corrections DECIMAL(6,2) NOT NULL,
                           corrections_value DECIMAL(9,2) NOT NULL,
    
                           updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
                           PRIMARY KEY(day, employee, service_id) )
                   """)
        try:
            for field in 'week employee organization project_number type updated'.split():
                self.db.execute(f'CREATE INDEX timesheet_{field} ON timesheet ({field})')
            self.db.execute(f'CREATE INDEX timesheet_year_week ON timesheet (year,week)')
        except OperationalError:
            pass  # Index already existent

    def update(self):

        # Find newest day in database
        sim = simplicate()
        newest_result = self.db.execute('select max(day) as day from timesheet')[0]['day']
        if newest_result:
            day = Day(newest_result).plus_days(0)  # Hier moeten we nog iets mee. -14 bij --onceaday?
        else:
            day = Day(2021, 1, 1)

        today = Day()
        while day < today:
            print('updating', day)
            data = sim.hours({'day': day})
            if data:
                flat_data = flatten_hours_data(data)
                grouped_data = group_by_daypersonservice(flat_data)
                complemented_data = [complement_timesheet_data(te) for te in grouped_data]  # %(name)s
                query = f'delete from timesheet where day = "{day}";'
                self.db.execute(query)
                for timesheet_entry in complemented_data:
                    fields = []
                    values = []
                    for field, value in timesheet_entry.items():
                        fields += [field]
                        if isinstance(value, bool):
                            value = 1 and value or 0
                        values += [json.dumps(value)]
                    query = f'INSERT INTO timesheet ({", ".join(fields)}) values ({", ".join(values)});'
                    self.db.execute(query)
                self.db.commit()
            day = day.next()  # Move to the next day before repeating the loop

    def query_string(self, period: Period, only_clients=0, only_billable=0, users=None, type="normal"):
        query = f'where day>="{period.fromday}"'
        if period.untilday:
            query += f' and day<"{period.untilday}"'
        query += f' and type="{type}"'

        if only_clients:
            query += ' and organization not in ("Oberon", "Qikker Online B.V.") '
        if users:
            if isinstance(users, str):
                users = (users,)  # make it a tuple
            users_string = '("' + '","'.join(users) + '")'
            query += f" and employee in {users_string}"
        else:
            employees = Employee()
            interns = employees.interns()
            query += f""" and employee not in ("{'","'.join(interns)}")"""
        if only_billable:
            query += " and tariff > 0"

        return query

    def count(self):
        return self.db.execute('select count(*) as aantal from timesheet')[0]['aantal']

    def geboekte_uren_users(self, period, users=None, only_clients=0, only_billable=0) -> float:

        query = self.query_string(period, users=users, only_clients=only_clients, only_billable=only_billable)
        if only_billable:
            query = 'select sum(hours+corrections) as result from timesheet ' + query
        else:
            query = 'select sum(hours) as result from timesheet ' + query
        result = float(self.db.execute(query)[0]['result'] or 0)
        return result

    def geboekte_omzet_users(self, period, users=None, only_clients=0, only_billable=0) -> float:

        query = self.query_string(period, users=users, only_clients=only_clients, only_billable=only_billable)
        query = 'select sum(turnover) as result from timesheet ' + query
        query_result = self.db.execute(query)
        result = float(query_result[0]['result'] or 0)
        return result

    def query(self, period: Period, where='', sort=None):
        query_string = f'SELECT * from timesheet WHERE day>="{period.fromday}"'
        if period.untilday:
            query_string += f' AND day<"{period.untilday}"'
        if where:
            query_string += ' AND ' + where
        if sort:
            query_string += ' ORDER BY ' + ','.join(sort)
        query_result = self.db.execute(query_string)
        return query_result


def group_by_daypersonservice(list_of_dicts):
    df = pd.DataFrame(list_of_dicts)

    def first(x): return x.values[0]

    key = ['day', 'employee', 'service_id']
    agg = {colname: first for colname in df.columns if not colname in key}
    agg['hours'] = np.sum
    agg['corrections'] = np.sum
    df2 = df.groupby(key).agg(agg).reset_index()
    return df2.to_dict('records')


def complement_timesheet_data(timesheet_entry):
    def week_and_year(day_str):
        week = datetime.datetime.strptime(day_str, '%Y-%m-%d').isocalendar()[1]
        year = int(day_str[:4])
        if day_str[5] < '1' and week > 50:
            year -= 1
        return week, year

    timesheet_entry['tariff'] = timesheet_entry['tariff'] or timesheet_entry['service_tariff']
    del timesheet_entry['hours_id']
    del timesheet_entry['billable']
    del timesheet_entry['status']
    del timesheet_entry['service_tariff']
    timesheet_entry['turnover'] = calculate_turnover(timesheet_entry)
    timesheet_entry['service_name'] = timesheet_entry.pop('service')  # Renaming
    timesheet_entry['week'], timesheet_entry['year'] = week_and_year(timesheet_entry['day'])
    timesheet_entry['corrections_value'] = timesheet_entry['corrections'] * timesheet_entry['tariff']
    return timesheet_entry
