""" Functies voor het berekenen van uren / productiviteit / billability etc. """
import os

import pandas as pd

from middleware.employee import Employee
from middleware.timesheet import Timesheet, hours_dataframe
from model.caching import cache, load_cache
from model.utilities import Day, Period
from sources.simplicate import simplicate


# @cache(hours=24)
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
        and u["name"] != "Angela Duijs"
    ]
    return users


def percentage_directe_werknemers():
    """DDA Cijfer. Is het percentage productiemedewerkers tov het geheel
    todo: interessanter is het percentage van de salariskosten.
    Salariskosten (incl pensioen en belasting) van de directe mensen moeten 70%-75% zijn (Olivier)."""
    period = Period(Day().plus_months(-6))
    productie_users = tuple_of_productie_users()
    return (
        100
        * beschikbare_uren_volgens_rooster(period, employees=productie_users)[0]
        / beschikbare_uren_volgens_rooster(period)[0]
    )


# @cache(hours=8)
def billable_trend_person_week(user, period):
    # Returns a list of labels and a list of hours
    startweek = period.fromday.week_number()
    untilweek = (
        period.untilday.week_number()
        if period.untilday
        else Day().plus_days(7).week_number()
    )
    if untilweek > startweek:
        labels = list(range(startweek, untilweek))
    else:
        labels = list(range(startweek, 53)) + list(range(1, untilweek))
    hours = [0] * len(labels)

    hours_per_week = (
        hours_dataframe(period)
        .query(f'type=="normal" and employee=="{user}" and tariff>0')
        .groupby(["week"])[["hours"]]
        .sum()
        .to_dict("index")
    )
    for key, value in hours_per_week.items():
        try:
            pos = labels.index(key)
        except ValueError:
            pass
        hours[pos] = value["hours"]
        # pos = key - startweek
        # if 0 <= pos < len(labels):
        #    hours[pos] = value["hours"]
    return labels, hours


# ############## CORRECTIONS ####################


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


def corrections_list(period: Period):
    timesheet = Timesheet()
    query = f'''select `organization`, project_name, sum(hours) as hours, sum(corrections) as corrections
                from timesheet t join project p on t.project_number=p.project_number
                where day>="{period.fromday}"'''
    if period.untilday:
        query += f' and day<"{period.untilday}"'
    query += """ group by p.project_number
                having sum(corrections) < -2
                order by corrections"""
    corrections = timesheet.full_query(query)
    return pd.DataFrame(corrections)


@cache(hours=24)
def corrections_percentage(period: Period):
    df = hours_dataframe(period)
    data = df.query("tariff>0")
    percentage_corrected = 100 * -data["corrections"].sum() / data["hours"].sum()
    return percentage_corrected


def largest_corrections(minimum, period: Period):
    def format_project_name(line):
        name = line["organization"] + " - " + line["project_name"]
        if len(name) > 45:
            name = name[: 45 - 1] + ".."
        return name

    df = hours_dataframe(period)
    query = "corrections < 0"
    top_corrections = (
        df.query(query)
        .groupby(["project_name", "organization"])[["corrections"]]
        .sum()
        .query(f"corrections<-{minimum}")
        .sort_values(by="corrections")
        .reset_index()  # make index a column
    )
    if top_corrections.empty:
        return None
    top_corrections["corrections"] = -top_corrections["corrections"]
    top_corrections["project_name"] = top_corrections.apply(format_project_name, axis=1)
    top_corrections = top_corrections.drop("organization", axis=1)
    return top_corrections


@cache(hours=24)
def get_timetables(sim):
    res = sim.timetable()
    return res


def beschikbare_uren_volgens_rooster(period: Period, employees=None):

    if employees is None:
        employees = []
    sim = simplicate()
    # Get the list of current employees
    if not employees:
        interns = Employee().interns()
    else:
        interns = []

    # Roosteruren
    timetables = get_timetables(sim)
    tot = 0
    for timetable in timetables:
        if (
            not timetable["employee"]["name"]
            or employees
            and timetable["employee"]["name"] not in employees
            or not employees
            and timetable["employee"]["name"] in interns
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
    timesheet = Timesheet()
    leave = timesheet.leave_hours(period, employees)

    # Ziek
    absence = timesheet.absence_hours(period, employees)

    return float(tot), float(leave), float(absence)


if __name__ == "__main__":
    os.chdir("..")
    load_cache()

    period_ = Period("2021-06-01", "2021-10-01")
    l = largest_corrections(1, period_)
    print(l)
