""" Functies voor het berekenen van uren / productiviteit / billability etc. """
import os

import pandas as pd

from model.caching import cache, load_cache
from model.organisatie import verzuim_absence_hours, leave_hours
from model.utilities import Day, Period
from sources.simplicate import simplicate, hours_dataframe


@cache(hours=24)
def tuple_of_productie_users():
    productie_teams = {
        "Development",
        "PM",
        "Service Team",
        "Concept & Design",
        "Testing",
    }
    sim = simplicate()
    users = sim.employee({"status": "active"})
    users = [
        u["name"]
        for u in users
        if set(t["name"] for t in u.get("teams", [])).intersection(productie_teams)
    ]
    return users


@cache(hours=2)
def geboekte_uren_users(period: Period, users, only_clients=0, only_billable=0):
    querystring = create_querystring(
        users, only_clients=only_clients, only_billable=only_billable
    )
    df = hours_dataframe(period).query(querystring)
    hours = df["hours"].sum()
    if only_billable:
        hours += df["corrections"].sum()
    return hours


@cache(hours=2)
def geboekte_omzet_users(period: Period, users, only_clients=0, only_billable=0):
    querystring = create_querystring(
        users, only_clients=only_clients, only_billable=only_billable
    )
    df = hours_dataframe(period).query(querystring)
    turnover = df["turnover"].sum()
    return turnover


def create_querystring(users, only_clients=0, only_billable=0):
    query = ['type=="normal"']
    if only_clients:
        query += ['organization not in ("Oberon", "Qikker Online B.V.") ']
    if users:
        if isinstance(users, str):
            users = (users,)  # make it a tuple
        query += [f"employee in {users}"]
    else:
        interns = get_interns(simplicate())
        query += [f"""employee not in ("{'","'.join(interns)}")"""]
    if only_billable:
        query += ["(tariff > 0 or service_tariff>0)"]

    return " and ".join(query)


@cache(hours=24)
def get_interns(sim):
    """ Returns a set of users with function Stagiair"""
    return {e["name"] for e in sim.employee({"function": "Stagiair"})}


def percentage_directe_werknemers():
    """DDA Cijfer. Is het percentage productiemedewerkers tov het geheel"""
    period = Period(Day().plus_months(-6))
    productie_users = tuple_of_productie_users()
    return (
            100
            * beschikbare_uren_volgens_rooster(period, employees=productie_users)[0]
            / beschikbare_uren_volgens_rooster(period)[0]
    )


@cache(hours=8)
def billable_trend_person_week(user, startweek=1):
    # Returns a list of labels and a list of hours
    thisweek = Day().week_number()
    labels = list(range(startweek, thisweek))
    hours = [0] * len(labels)

    hours_per_week = (
        hours_dataframe()
            .query(
            f'type=="normal" and employee=="{user}" and (tariff>0 or service_tariff>0)'
        )
            .groupby(["week"])[["hours"]]
            .sum()
            .to_dict("index")
    )
    for key, value in hours_per_week.items():
        pos = key - startweek
        if 0 <= pos < len(labels):
            hours[pos] = value["hours"]
    return (labels, hours)


############### CORRECTIONS ####################


def format_project_name(row):
    maxlen = 40
    name = str(row["organization"]).split()[0] + " - " + str(row["project_name"])
    if len(name) > maxlen:
        name = name[: maxlen - 1] + ".."
    return name


@cache(hours=24)
def corrections_count(period: Period):
    # Returns a dataframe with project, hours
    df = hours_dataframe(period)
    hours_per_project = (
        df.groupby(["organization", "project_name"])
            .agg({"hours": "sum", "corrections": "sum"})
            .sort_values("corrections")
            .query("corrections < -10")
            .reset_index()
            .copy()
    )
    result = pd.DataFrame()
    if hours_per_project.empty:
        result["project"] = ""
        result["hours"] = ""
    else:
        result["project"] = hours_per_project.apply(format_project_name, axis=1)
        result["hours"] = hours_per_project.apply(
            lambda a: f"{-int(a['corrections'])}/{int(a['hours'])}", axis=1
        )
    return result


@cache(hours=24)
def corrections_list(period: Period):
    # returns a dataframe of organization, project_name, project_id, corrections
    df = hours_dataframe(period)
    result = (
        df.groupby(["organization", "project_name", "project_id"])
            .agg({"hours": "sum", "corrections": "sum"})
            .query("corrections < 0")
            .sort_values("corrections")
            .reset_index()
    )
    result["corrections"] = result.apply(lambda a: int(a["corrections"]), axis=1)
    return result


@cache(hours=24)
def corrections_percentage(period: Period):
    df = hours_dataframe(period)
    data = df.query("(tariff>0 or service_tariff>0)")
    percentage_corrected = 100 * -data["corrections"].sum() / data["hours"].sum()
    return percentage_corrected


def largest_corrections(minimum, period: Period):
    df = hours_dataframe(period)
    query = "corrections < 0"
    top_corrections = (
        df.query(query)
            .groupby(["project_id", "project_number", "project_name"])[["corrections"]]
            .sum()
            .query(f"corrections<-{minimum}")
            .sort_values(by="corrections")
            .reset_index()  # make index a column
    )
    top_corrections["corrections"] = -top_corrections["corrections"]
    return top_corrections


@cache(hours=24)
def get_timetables(sim):
    res = sim.timetable()
    return res


def beschikbare_uren_volgens_rooster(period: Period, employees=None):
    # todo: wat doen we met stagairs? Die tellen nu mee.

    if employees is None:
        employees = []
    sim = simplicate()
    # Get the list of current employees
    if not employees:
        interns = get_interns(sim)
        employees = set(hours_dataframe(period).employee.unique())
        employees.difference_update(interns)

    # Roosteruren
    timetables = get_timetables(sim)
    tot = 0
    for timetable in timetables:
        if (
                not timetable["employee"]["name"]
                or timetable["employee"]["name"] not in employees
                or period.untilday
                and timetable["start_date"] >= period.untilday.str
                or timetable.get("end_date", "9999") < period.fromday.str
        ):
            continue
        day = Day(max(timetable["start_date"], period.fromday.str))
        table = [
            (
                timetable["even_week"][f"day_{i}"]["hours"],
                timetable["odd_week"][f"day_{i}"]["hours"],
            )
            for i in range(1, 8)
        ]
        untilday = period.untilday if period.untilday else Day()
        ending_day_of_roster = min(timetable.get("end_date", "9999"), untilday.str)
        while day.str < ending_day_of_roster:
            index = day.week_number() % 2
            tot += table[day.day_of_week()][index]
            day = day.next()

    # Vrij
    leave = leave_hours(period, employees)

    # Ziek
    absence = verzuim_absence_hours(period, employees)

    return tot, leave, absence


if __name__ == "__main__":
    os.chdir("..")
    load_cache()

    period_ = Period("2021-06-01", "2021-10-01")
    # Get the list of current employees
    employees_ = set(hours_dataframe(period_).employee.unique())

    for e in employees_:
        r, v, z = beschikbare_uren_volgens_rooster(period_, [e])
