import datetime
import sys

import numpy as np
import pandas as pd
from pymysql import OperationalError

from middleware.base_table import BaseTable
from middleware.employee import Employee
from middleware.middleware_utils import singleton
from model.caching import cache
from model.utilities import Period, Day
from sources.simplicate import simplicate, flatten_hours_data, calculate_turnover


@singleton
class Timesheet(BaseTable):
    def __init__(self):
        self.table_name = 'timesheet'
        self.table_definition = """
            CREATE TABLE IF NOT EXISTS timesheet (
               day VARCHAR(10) NOT NULL,
               week INTEGER NOT NULL,
               year INTEGER NOT NULL,
               employee VARCHAR(40) NOT NULL,

               project_id VARCHAR(50) NOT NULL,
               project_number VARCHAR(10) NOT NULL,

               service_id VARCHAR(50) NOT NULL,
               service_name VARCHAR(80) NOT NULL,

               tariff DECIMAL(6,2) NOT NULL,

               type VARCHAR(10) NOT NULL,
               label VARCHAR(100) NOT NULL,

               hours DECIMAL(6,2) NOT NULL,
               turnover DECIMAL(9,2) NOT NULL,
               corrections DECIMAL(6,2) NOT NULL,
               corrections_value DECIMAL(9,2) NOT NULL,

               updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

               PRIMARY KEY(day, employee, service_id) )
               CHARACTER SET utf8
            """
        self.index_fields = 'day employee project_number type updated'
        super().__init__()

        if "--onceaday" in sys.argv:
            self.update()
            try:
                self.db.execute(f'CREATE INDEX timesheet_year_week ON timesheet (year,week)')
            except OperationalError:
                pass  # index already existent

    def update(self):

        sim = simplicate()

        # Find newest day in database
        newest_result = self.db.execute('select max(day) as day from timesheet')[0]['day']
        if newest_result:
            day = Day(newest_result).plus_days(-14)
        else:
            day = Day(2021, 1, 1)
        today = Day()
        if day >= today:
            return

        while day < today:
            print('updating', day)
            data = sim.hours({'day': day})
            if data:
                flat_data = flatten_hours_data(data)
                flat_df = pd.DataFrame(flat_data)
                grouped_data = group_by_daypersonservice(flat_data)
                grouped_df = pd.DataFrame(grouped_data)
                complemented_data = [complement_timesheet_data(te) for te in grouped_data]  # %(name)s
                comp_df = pd.DataFrame(complemented_data)
                self.db.execute(f'delete from timesheet where day = "{day}"')
                self.insert_dicts(complemented_data)
            day = day.next()  # Move to the next day before repeating the loop

    @staticmethod
    def where_clause(period: Period, only_clients=0, only_billable=0, users=None, hours_type=None):
        query = f'where day>="{period.fromday}"'
        if period.untilday:
            query += f' and day<"{period.untilday}"'
        if hours_type:
            query += f' and type="{hours_type}"'

        if only_clients:
            query = (
                    ' join project on project.project_id=timesheet.project_id '
                    + query
                    + ' and organization not in ("Oberon", "Qikker Online B.V.") '
            )
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

        query = self.where_clause(
            period, users=users, only_clients=only_clients, only_billable=only_billable, hours_type='normal'
        )
        if only_billable:
            query = 'select sum(hours+corrections) as result from timesheet ' + query
        else:
            query = 'select sum(hours) as result from timesheet ' + query
        result = float(self.db.execute(query)[0]['result'] or 0)
        return result

    def geboekte_omzet_users(self, period, users=None, only_clients=0, only_billable=0) -> float:
        query = self.where_clause(
            period, users=users, only_clients=only_clients, only_billable=only_billable, hours_type='normal'
        )
        query = 'select sum(turnover) as result from timesheet ' + query
        query_result = self.db.execute(query)
        result = float(query_result[0]['result'] or 0)
        return result

    def normal_hours(self, period: Period, employees: list = []):
        """Number of hours with the type normal in Period. Filtering on employees is optional."""
        return self.hours_with_type(period, 'normal', employees)

    def leave_hours(self, period: Period, employees: list = []):
        """Number of hours with the type leave in Period. Filtering on employees is optional."""
        return self.hours_with_type(period, 'leave', employees)

    def absence_hours(self, period: Period, employees: list = []):
        """Number of hours with the type absence in Period. Filtering on employees is optional."""
        return self.hours_with_type(period, 'absence', employees)

    def hours_with_type(self, period: Period, type: str, employees: list = []):
        """Number of hours with the given type (normal, absence, leave) in Period. Filtering on employees is optional."""
        query = 'select sum(hours) as result from timesheet ' + self.where_clause(
            period, users=employees, hours_type=type
        )
        query_result = self.db.execute(query)
        result = float(query_result[0]['result'] or 0)
        return result

    def query(self, period: Period, where: str = '', sort=None, with_project_data=False):
        if with_project_data:
            query_string = f'''SELECT t.*, p.organization, p.project_name, p.pm, p.status as project_status 
                               FROM timesheet t JOIN project p ON p.project_id=t.project_id'''
        else:
            query_string = 'SELECT * from timesheet'
        query_string += f' WHERE day>="{period.fromday}"'
        if period.untilday:
            query_string += f' AND day<"{period.untilday}"'
        if where:
            query_string += ' AND ' + where
        if sort:
            if not isinstance(sort, list):
                sort = [sort]
            query_string += ' ORDER BY ' + ','.join(sort)
        query_result = self.db.execute(query_string)
        return query_result

    def full_query(self, query_string):
        return self.db.execute(query_string)


def group_by_daypersonservice(list_of_dicts):
    df = pd.DataFrame(list_of_dicts)

    def first(x):
        return x.values[0]

    key = ['day', 'employee', 'service_id']
    agg = {colname: first for colname in df.columns if colname not in key}
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
    # Feestdagenverlof / National holidays leave -> leave
    if timesheet_entry['label'] == 'Feestdagenverlof / National holidays leave':
        timesheet_entry['type'] = 'leave'
    return timesheet_entry


@cache(hours=4)
def hours_dataframe(period: Period):
    timesheet = Timesheet()
    list_of_dicts = timesheet.query(period, with_project_data=True)
    df = pd.DataFrame(list_of_dicts)
    df.tariff = df.tariff.astype(float)
    df.hours = df.hours.astype(float)
    df.turnover = df.turnover.astype(float)
    df.corrections = df.corrections.astype(float)
    df.corrections_value = df.corrections_value.astype(float)
    return df


if __name__ == '__main__':
    timesheet_table = Timesheet()
    timesheet_table._create_project_table(force_recreate=0)
    timesheet_table.update()
