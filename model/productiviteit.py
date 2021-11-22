''' Functies voor het berekenen van uren / productiviteit / billability etc. '''
import datetime
import os

import pandas as pd

from model.caching import cache, load_cache
from model.organisatie import verzuim_absence_hours, leave_hours
from model.utilities import Day
from sources.simplicate import simplicate, hours_dataframe


# @cache(hours=24)
# def roster_hours_user(user):
#     # return roster_hours().get(user,0)
#     sim = simplicate()
#     roster = sim.timetable_simple(user)
#     res = sum([day[0] + day[1] for day in roster]) / 2  # 2 weeks
#     return res


@cache(hours=24)
def tuple_of_productie_users():
    productie_teams = {'Development', 'PM', 'Service Team', 'Concept & Design', 'Testing'}
    sim = simplicate()
    users = sim.employee({'status': 'active'})
    users = [u['name'] for u in users if set(t['name'] for t in u.get('teams', [])).intersection(productie_teams)]
    return users


# @cache(hours=2)
# def geboekte_uren(fromday, untilday, only_productie_users=0, only_clients=0, only_billable=0):
#     users = tuple_of_productie_users() if only_productie_users else None
#     return geboekte_uren_users(fromday, untilday, users, only_clients, only_billable, fromday, untilday)


@cache(hours=2)
def geboekte_uren_users(fromday: Day, untilday: Day, users, only_clients=0, only_billable=0):
    querystring = create_querystring(fromday, untilday, users, only_clients=only_clients, only_billable=only_billable)
    df = hours_dataframe().query(querystring)
    hours = df['hours'].sum()
    if only_billable:
        hours += df['corrections'].sum()
    return hours


@cache(hours=2)
def geboekte_omzet_users(fromday: Day, untilday: Day, users, only_clients=0, only_billable=0):
    querystring = create_querystring(fromday, untilday, users, only_clients=only_clients, only_billable=only_billable)
    df = hours_dataframe().query(querystring)
    turnover = df['turnover'].sum()
    return turnover


def create_querystring(fromday: Day, untilday: Day, users, only_clients=0, only_billable=0):
    query = ['type=="normal"', f'day >= "{fromday}"', f'day < "{untilday}"']
    if only_clients:
        query += ['organization not in ("Oberon", "Qikker Online B.V.") ']
    if users:
        if type(users) == str:
            users = (users,)  # make it a tuple
        query += [f'employee in {users}']
    else:
        interns = get_interns(simplicate())
        query += [f'''employee not in ("{'","'.join(interns)}")''']
    if only_billable:
        query += ['(tariff > 0 or service_tariff>0)']

    return ' and '.join(query)


# @cache(hours=24)
# def beschikbare_uren_productie(fromday: Day = None, untilday: Day = None):
#     hours = geboekte_uren(fromday, untilday, only_productie_users=1)
#     return hours
#
#
# @cache(hours=24)
# def beschikbare_uren_iedereen(fromday: Day = None, untilday: Day = None):
#     hours = geboekte_uren(fromday, untilday, only_productie_users=0)
#     return hours


@cache(hours=24)
def get_interns(sim):
    ''' Returns a set of users with function Stagiair'''
    return {e['name'] for e in sim.employee({'function': 'Stagiair'})}


# @cache(hours=2)
# def beschikbare_uren_via_wat_is_geboekt(fromday: Day, untilday: Day, employees: list = []):
#     ''' Oude methode, op basis van alle medewerkers (geen stagairs) en hun geboekte uren per dag
#         afgerond naar 0, 4 of 8 uur'''
#     sim = simplicate()
#     interns = get_interns(sim)
#     query = f'day>="{fromday}" and day<"{untilday}"'
#     if employees:
#         query += ' and employee in @employees'
#     else:
#         query += ' and employee not in @interns'
#     grouped = (
#         hours_dataframe()
#         .query(query)  # Filter on date range
#         .groupby(['employee', 'day', 'type'])[['hours']]
#         .sum()  # Group hours by employee, day and type
#         .unstack()  # Dubbel niveau headers eruit
#         .fillna(0)  # Nan -> 0
#         .reset_index()
#     )  # Convert indexes to columns
#     if len(grouped.columns) == 3:
#         assert list(grouped.columns.values) == [('employee', ''), ('day', ''), ('hours', 'normal')]
#         grouped.columns = ['employee', 'day', 'normal']
#     elif len(grouped.columns) == 4:
#         assert list(grouped.columns.values) == [('employee', ''), ('day', ''), ('hours', 'leave'), ('hours', 'normal')]
#         grouped.columns = ['employee', 'day', 'leave', 'normal']
#     else:
#         grouped.columns = ['employee', 'day', 'absence', 'leave', 'normal']
#     grouped['available'] = grouped.apply(
#         lambda a: min(8, round((a['normal']) / 4, 0) * 4), axis=1
#     )  # Round to closest multiple of 4
#     available = grouped['available'].sum()
#     return available
#

###### PRODUCTIEF ############


# @cache(hours=2)
# def productieve_uren_productie(fromday: Day = None, untilday: Day = None):
#     hours = geboekte_uren(fromday, untilday, only_productie_users=1, only_clients=1)
#     return hours
#
#
# @cache(hours=2)
# def productieve_uren_iedereen(fromday: Day = None, untilday: Day = None):
#     hours = geboekte_uren(fromday, untilday, only_productie_users=0, only_clients=1)
#     return hours
#

########## BILLABLE ############

# @cache(hours=2)
# def billable_uren_productie(fromday: Day = None, untilday: Day = None):
#     hours = geboekte_uren(fromday, untilday,
#         only_productie_users=1, only_clients=1, only_billable=1
#     )
#     return hours
#
#
# @cache(hours=2)
# def billable_uren_iedereen(fromday: Day = None, untilday: Day = None):
#     hours = geboekte_uren(fromday, untilday,
#         only_productie_users=0, only_clients=1, only_billable=1
#     )
#     return hours
#

# Percentages
# def productiviteit_perc_productie(fromday: Day = None, untilday: Day = None):
#     return 100 * productieve_uren_productie(fromday, untilday) / beschikbare_uren_productie(fromday, untilday)
#
#
# def billable_perc_productie(fromday: Day = None, untilday: Day = None):
#     return 100 * billable_uren_productie(fromday, untilday) / beschikbare_uren_productie(fromday, untilday)
#
#
# def productiviteit_perc_iedereen(fromday: Day = None, untilday: Day = None):
#     return 100 * productieve_uren_iedereen(fromday, untilday) / beschikbare_uren_iedereen(fromday, untilday)
#
#
# def billable_perc_iedereen(fromday: Day, untilday: Day):
#     avail = beschikbare_uren_iedereen(fromday, untilday)
#     res = 100 * billable_uren_iedereen(fromday, untilday) / avail
#     trends.update('billable_hele_team', round(res, 1))
#     return res


# def billable_perc_user(fromday: Day, untilday: Day, user):
#     billable = geboekte_uren_users(fromday, untilday, user, only_billable=1)
#     total = geboekte_uren_users(fromday, untilday, user)
#     if total:
#         res = 100 * billable / total
#     else:
#         res = 0
#     return res
#
#
# def productiviteit_perc_user(user):
#     productive = geboekte_uren_users(user, only_clients=1)
#     total = geboekte_uren_users(user)
#     if total:
#         res = 100 * productive / total
#     else:
#         res = 0
#     return res


def percentage_directe_werknemers():
    '''DDA Cijfer. Is het percentage productiemedewerkers tov het geheel'''
    untilday = Day()
    fromday = untilday.plus_days(days=-183)
    return 100 * beschikbare_uren_productie(fromday, untilday) / beschikbare_uren_iedereen(fromday, untilday)


@cache(hours=8)
def billable_trend_person_week(user, startweek=1):
    # Returns a list of labels and a list of hours
    thisweek = Day().week_number()
    labels = list(range(startweek, thisweek))
    hours = [0] * len(labels)

    dictdict = (
        hours_dataframe()
        .query(f'type=="normal" and employee=="{user}" and (tariff>0 or service_tariff>0)')
        .groupby(['week'])[['hours']]
        .sum()
        .to_dict('index')
    )
    for key, val in dictdict.items():
        pos = key - startweek
        if 0 <= pos < len(labels):
            hours[pos] = dictdict[key]['hours']
    return (labels, hours)


def weekno_to_date(rec):
    d = f"{rec['year']}-W{rec['weekno']}-1"
    rec['date'] = datetime.strptime(d, '%G-W%V-%u').strftime('%Y-%m-%d')
    return rec


############### CORRECTIONS ####################


def format_project_name(row):
    maxlen = 40
    name = str(row['organization']).split()[0] + ' - ' + str(row['project_name'])
    if len(name) > maxlen:
        name = name[: maxlen - 1] + '..'
    return name


@cache(hours=24)
def corrections_count(fromday: Day, untilday: Day):
    # Returns a dataframe with project, hours
    df = hours_dataframe()
    x = (
        df.query(f'day>="{fromday}" and day<"{untilday}"')
            .groupby(['organization', 'project_name'])
            .agg({'hours': 'sum', 'corrections': 'sum'})
            .sort_values('corrections')
            .query('corrections < -10')
            .reset_index()
            .copy()
    )
    result = pd.DataFrame()
    if x.empty:
        result['project'] = ""
        result['hours'] = ""
    else:
        result['project'] = x.apply(format_project_name, axis=1)
        result['hours'] = x.apply(lambda a: f"{-int(a['corrections'])}/{int(a['hours'])}", axis=1)
    return result


@cache(hours=24)
def corrections_list(fromday: Day, untilday: Day):
    # returns a dataframe of organization, project_name, project_id, corrections
    df = hours_dataframe().query(f'day>="{fromday}" and day<"{untilday}"')
    result = (
        df.groupby(['organization', 'project_name', 'project_id'])
            .agg({'hours': 'sum', 'corrections': 'sum'})
            .query('corrections < 0')
            .sort_values('corrections')
            .reset_index()
    )
    result['corrections'] = result.apply(lambda a: int(a['corrections']), axis=1)
    return result


@cache(hours=24)
def corrections_percentage(fromday: Day, untilday: Day):
    df = hours_dataframe()
    data = df.query(f'(tariff>0 or service_tariff>0) and day>="{fromday}" and day<"{untilday}"')
    percentage_corrected = 100 * -data['corrections'].sum() / data['hours'].sum()
    return percentage_corrected


def largest_corrections(minimum, fromday: Day, untilday: Day):
    df = hours_dataframe()
    query = f'corrections < 0 and day>="{fromday}" and day<"{untilday}"'
    top_corrections = (
        df.query(query)
            .groupby(['project_id', 'project_number', 'project_name'])[['corrections']]
            .sum()
            .query(f'corrections<-{minimum}')
            .sort_values(by='corrections')
            .reset_index()  # make index a column
    )
    top_corrections['corrections'] = -top_corrections['corrections']
    return top_corrections


@cache(hours=24)
def get_timetable(sim):
    res = sim.timetable()
    return res


def beschikbare_uren_volgens_rooster(fromday: Day, untilday: Day, employees: list = []):
    # todo: wat doen we met stagairs? Die tellen nu mee.

    sim = simplicate()
    # Get the list of current employees
    if not employees:
        interns = get_interns(sim)
        employees = set(hours_dataframe().query(f'day>="{fromday}" and day<"{untilday}"').employee.unique())
        employees.difference_update(interns)

    # Roosteruren
    timetable = get_timetable(sim)
    tot = 0
    for t in timetable:
        if (
                t['employee']['name'] not in employees
                or t['start_date'] >= untilday.str
                or t.get('end_date', '9999') < fromday.str
        ):
            continue
        day = Day(max(t['start_date'], fromday.str))
        table = [(t['even_week'][f'day_{i}']['hours'], t['odd_week'][f'day_{i}']['hours']) for i in range(1, 8)]
        ending_day_of_roster = min(t.get('end_date', '9999'), untilday.str)
        while day.str < ending_day_of_roster:
            index = day.week_number() % 2
            tot += table[day.day_of_week()][index]
            day = day.next()

    # Vrij
    leave = leave_hours(fromday, untilday, employees)

    # Ziek
    absence = verzuim_absence_hours(fromday, untilday, employees)

    return tot, leave, absence


if __name__ == '__main__':
    os.chdir('..')
    load_cache()

    sim = simplicate()
    fromday = Day('2021-06-01')
    untilday = Day('2021-10-01')
    # Get the list of current employees
    employees = set(hours_dataframe().query(f'day>="{fromday}" and day<"{untilday}"').employee.unique())

    for e in employees:
        r, v, z = beschikbare_uren_volgens_rooster(fromday, untilday, [e])
        c = r - v - z  # rooster - vrij - ziek
        b = beschikbare_uren_via_wat_is_geboekt(fromday, untilday, [e])
        if c - b > 30:
            print(e, b, c, b - c)
    a = b - c
