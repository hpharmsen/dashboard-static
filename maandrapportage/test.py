import os

from middleware.employee import Employee
from middleware.timesheet import Timesheet, group_by_daypersonservice
from model.productiviteit import create_querystring
from model.utilities import Period, Day
from sources.database import dataframe
from sources.simplicate import hours_dataframe


def geboekt_oud(period: Period, users=None, only_clients=0, only_billable=0):
    querystring = create_querystring(users, only_clients=only_clients, only_billable=only_billable)
    df = hours_dataframe(period).query(querystring)
    return df


def geboekt_nieuw(period: Period, users=None, only_clients=0, only_billable=0):
    ts = Timesheet()

    query = ts.query_string(period, users=users, only_clients=only_clients, only_billable=only_billable)
    query = "select * from timesheet " + query
    result = dataframe(query, ts.db)
    return result


# Nieuw checkt op tariff > 0
# tariff = timesheet_entry['tariff'] or timesheet_entry['service_tariff']
# En billable kijken we niet naar
#
# Old checkt op (tariff > 0 or service_tariff>0)


def testqueries():
    df = hours_dataframe()

    def get_diff(row):
        return row["tariff"] and not (row["tariff"] > 0)

    # diff = df.apply( get_diff, axis=1 )
    users = None  # ['Jurriaan Ruitenberg'] #['Caspar Geerlings', 'Kevin Lobine']
    day = Day("2021-01-08")
    end_day = Day("2021-02-01")

    period = Period(day, end_day)
    oud = geboekt_oud(period, users=users, only_clients=1, only_billable=1)
    oudsum = int(oud["hours"].sum() + oud["corrections"].sum())
    oudhours = int(oud["hours"].sum())
    oudcorr = int(oud["corrections"].sum())
    nieuw = geboekt_nieuw(period, users=users, only_clients=1, only_billable=1)
    nieuwsum = int(nieuw["hours"].sum() + nieuw["corrections"].sum())
    nieuwhours = int(nieuw["hours"].sum())
    nieuwcorr = int(nieuw["corrections"].sum())
    if oudsum != nieuwsum:
        a = 1

    while day < end_day:
        print(day)
        next = day.next()
        period = Period(day, next)
        oud = geboekt_oud(period, users=users, only_clients=1, only_billable=1)
        oud_per_user = oud.groupby(["employee"])[["corrections"]].sum()
        oudsum = int(oud["corrections"].sum())
        nieuw = geboekt_nieuw(period, users=users, only_clients=1, only_billable=1)
        nieuw_per_user = nieuw.groupby(["employee"])[["corrections"]].sum()
        nieuwsum = int(nieuw["corrections"].sum())
        if oudsum != nieuwsum:
            a = 1
        day = next
    pass


def grouping():
    list_of_dicts = [
        {"day": "2021-01-01", "employee": "joost", "service_id": "123", "hours": 8, "corrections": -1},
        {"day": "2021-01-01", "employee": "joost", "service_id": "123", "hours": 8, "corrections": -2},
        {"day": "2021-01-02", "employee": "joost", "service_id": "123", "hours": 8, "corrections": -3},
    ]
    df = group_by_daypersonservice(list_of_dicts)
    return df


def test_employees():
    e = Employee()
    h = e["Hans-Pete Harmsen"]
    active = e.active_employees()
    interns = e.interns()
    pass


if __name__ == "__main__":
    os.chdir("..")
    test_employees()
