import datetime
from functools import partial

import numpy as np
import pandas as pd

from middleware.base_table import BaseTable, EMPLOYEE_NAME, PROJECT_NUMBER, SIMPLICATE_ID, MONEY, HOURS
from middleware.employee import Employee
from middleware.middleware_utils import singleton
from model.caching import cache
from model.utilities import Period, Day
from sources.simplicate import simplicate, flatten_hours_data, calculate_turnover


@singleton
class Timesheet(BaseTable):
    def __init__(self):
        self.table_name = 'timesheet'
        self.table_definition = f"""
               day VARCHAR(10) NOT NULL,
               week INTEGER NOT NULL,
               year INTEGER NOT NULL,
               employee {EMPLOYEE_NAME} NOT NULL,

               project_number {PROJECT_NUMBER} NOT NULL,

               service_id {SIMPLICATE_ID} NOT NULL,

               tariff {MONEY} NOT NULL,

               type VARCHAR(10) NOT NULL,
               label VARCHAR(100) NOT NULL,

               hours {HOURS} NOT NULL,
               turnover {MONEY} NOT NULL,
               corrections {HOURS} NOT NULL,
               corrections_value {MONEY} NOT NULL,
            """
        self.primary_key = 'day, employee, service_id'
        self.index_fields = "day employee project_number type updated year__week"
        super().__init__()
        # try:
        #     self.db.execute(f"CREATE INDEX timesheet_year_week ON timesheet (year,week)")
        # except OperationalError:
        #     pass  # index already existent

    def update(self, day=None):
        """Updates all timesheet entries starting with day if provided,
        14 days before the latest entry if day is not provided
        or 1-1-2021 if there was no last entry."""

        # Find newest day in database
        newest_result = self.db.execute("select max(day) as day from timesheet")[0]["day"]
        if not day:
            if newest_result:
                day = Day(newest_result).plus_days(-14)
            else:
                day = Day(2021, 1, 1)
        today = Day()
        while day < today:
            self.db.execute(f'delete from timesheet where day = "{day}"')
            data_func = partial(self.get_day_data, day)
            self.insert_dicts(data_func)
            day = day.next()

    def get_data(self):
        day = Day(2021, 1, 1)
        today = Day()
        while day < today:
            for data in self.get_day_data(day):
                yield data
            day = day.next()  # Move to the next day before repeating the loop

    def get_day_data(self, day: Day):
        sim = simplicate()

        print("retrieving", day)
        data = sim.hours({"day": day})
        if data:
            flat_data = flatten_hours_data(data)
            grouped_data = group_by_daypersonservice(flat_data)
            for te in grouped_data:
                yield complement_timesheet_data(te)  # %(name)s

    @staticmethod
    def where_clause(period: Period, only_clients=0, only_billable=0, users=None, hours_type=None):
        query = f'where day>="{period.fromday}"'
        if period.untilday:
            query += f' and day<"{period.untilday}"'
        if hours_type:
            query += f' and type="{hours_type}"'

        if only_clients:
            query = (
                    " join project on project.project_number=timesheet.project_number "
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
        return self.db.execute("select count(*) as aantal from timesheet")[0]["aantal"]

    def geboekte_uren(self, period, users=None, only_clients=0, only_billable=0) -> float:

        query = self.where_clause(
            period, users=users, only_clients=only_clients, only_billable=only_billable, hours_type="normal"
        )
        if only_billable:
            query = "select sum(hours+corrections) as result from timesheet " + query
        else:
            query = "select sum(hours) as result from timesheet " + query
        result = float(self.db.execute(query)[0]["result"] or 0)
        return result

    def geboekte_omzet(self, period, users=None, only_clients=0, only_billable=0) -> float:
        query = self.where_clause(
            period, users=users, only_clients=only_clients, only_billable=only_billable, hours_type="normal"
        )
        query = "select sum(turnover) as result from timesheet " + query
        query_result = self.db.execute(query)
        result = float(query_result[0]["result"] or 0)
        return result

    def normal_hours(self, period: Period, employees: list = []):
        """Number of hours with the type normal in Period. Filtering on employees is optional."""
        return self.hours_with_type(period, "normal", employees)

    def leave_hours(self, period: Period, employees: list = []):
        """Number of hours with the type leave in Period. Filtering on employees is optional."""
        return self.hours_with_type(period, "leave", employees)

    def absence_hours(self, period: Period, employees: list = []):
        """Number of hours with the type absence in Period. Filtering on employees is optional."""
        return self.hours_with_type(period, "absence", employees)

    def hours_with_type(self, period: Period, type: str, employees: list = []):
        """Number of hours with the given type (normal, absence, leave) in Period. Filtering on employees is optional."""
        query = "select sum(hours) as result from timesheet " + self.where_clause(
            period, users=employees, hours_type=type
        )
        query_result = self.db.execute(query)
        result = float(query_result[0]["result"] or 0)
        return result

    def query(self, period: Period, where: str = "", sort=None, with_project_data=False):
        if with_project_data:
            query_string = f"""SELECT t.*, p.organization, p.project_name, p.pm, p.status as project_status 
                               FROM timesheet t JOIN project p ON p.project_number=t.project_number"""
        else:
            query_string = "SELECT * from timesheet"
        query_string += f' WHERE day>="{period.fromday}"'
        if period.untilday:
            query_string += f' AND day<"{period.untilday}"'
        if where:
            query_string += " AND " + where
        if sort:
            if not isinstance(sort, list):
                sort = [sort]
            query_string += " ORDER BY " + ",".join(sort)
        query_result = self.db.execute(query_string)
        return query_result

    def full_query(self, query_string):
        return self.db.execute(query_string)

    def services_with_their_hours_and_turnover(
            self,
            service_ids: list,
            day: Day,
    ) -> dict[str, tuple[float, int]]:
        """Dict with the given service_ids as keys and their their turnovers up to the given day as values"""
        services_string = '("' + '","'.join(service_ids) + '")'
        query = f"""select service_id, sum(hours) as hours, sum(turnover) as turnover from timesheet 
                    where service_id in {services_string} and day<="{day}"
                    group by service_id"""
        result = {r["service_id"]: (float(r["hours"]), int(r["turnover"])) for r in self.full_query(query)}
        return result


def group_by_daypersonservice(list_of_dicts):
    df = pd.DataFrame(list_of_dicts)

    def first(x):
        return x.values[0]

    key = ["day", "employee", "service_id"]
    agg = {colname: first for colname in df.columns if colname not in key}
    agg["hours"] = np.sum
    agg["corrections"] = np.sum
    df2 = df.groupby(key).agg(agg).reset_index()
    return df2.to_dict("records")


def complement_timesheet_data(timesheet_entry):
    def week_and_year(day_str):
        week = datetime.datetime.strptime(day_str, "%Y-%m-%d").isocalendar()[1]
        year = int(day_str[:4])
        if day_str[5] < "1" and week > 50:
            year -= 1
        return week, year

    timesheet_entry["tariff"] = timesheet_entry["tariff"] or timesheet_entry["service_tariff"]
    del timesheet_entry["project_id"]
    del timesheet_entry["hours_id"]
    del timesheet_entry["billable"]
    del timesheet_entry["status"]
    del timesheet_entry["service_tariff"]
    timesheet_entry["turnover"] = calculate_turnover(timesheet_entry)
    del timesheet_entry["service"]  # Wordt nog gebruikt in calculate_turnover maar mag nu weg
    timesheet_entry["week"], timesheet_entry["year"] = week_and_year(timesheet_entry["day"])
    timesheet_entry["corrections_value"] = timesheet_entry["corrections"] * timesheet_entry["tariff"]

    # De volgende is omdat in 2021 de indeling nog niet goed was
    if timesheet_entry["type"] == "absence" and timesheet_entry[
        "label"] == "Feestdagenverlof / National holidays leave":
        timesheet_entry["type"] = "leave"
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


if __name__ == "__main__":
    timesheet_table = Timesheet()
    # timesheet_table.create_table(force_recreate=0)
    # timesheet_table.update(Day('2021-12-01'))
    timesheet_table.repopulate()
