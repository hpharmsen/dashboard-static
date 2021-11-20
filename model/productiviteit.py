import datetime
import os
from collections import defaultdict

from model.caching import reportz, load_cache
from model.organisatie import verzuim_absence_hours, leave_hours
from model.trendline import trends
from sources.simplicate import simplicate, hours_dataframe, DATE_FORMAT
import pandas as pd


@reportz(hours=24)
def roster_hours():
    roster = {}
    sim = simplicate()
    data = sim.contract()
    for d in data:
        roster[d['employee']['name']] = 40 * float(d['parttime_percentage']) / 100
    return roster


@reportz(hours=24)
def roster_hours_user(user):
    # return roster_hours().get(user,0)
    sim = simplicate()
    roster = sim.timetable_simple(user)
    res = sum([day[0] + day[1] for day in roster]) / 2  # 2 weeks
    return res


@reportz(hours=24)
def tuple_of_productie_users():
    productie_teams = {'Development', 'PM', 'Service Team', 'Concept & Design', 'Testing'}
    sim = simplicate()
    users = sim.employee({'status': 'active'})
    users = [u['name'] for u in users if set(t['name'] for t in u.get('teams', [])).intersection(productie_teams)]
    return users


@reportz(hours=2)
def geboekte_uren(only_productie_users=0, only_clients=0, only_billable=0, fromdate=None, untildate=None):
    users = tuple_of_productie_users() if only_productie_users else None
    return geboekte_uren_users(users, only_clients, only_billable, fromdate, untildate)


@reportz(hours=2)
def geboekte_uren_users(users, only_clients=0, only_billable=0, fromdate=None, untildate=None):
    querystring = create_querystring(
        users, only_clients=only_clients, only_billable=only_billable, fromdate=fromdate, untildate=untildate
    )
    df = hours_dataframe().query(querystring)
    hours = df['hours'].sum()
    if only_billable:
        hours += df['corrections'].sum()
    return hours


@reportz(hours=2)
def geboekte_omzet_users(users, only_clients=0, only_billable=0, fromdate=None, untildate=None):
    querystring = create_querystring(
        users, only_clients=only_clients, only_billable=only_billable, fromdate=fromdate, untildate=untildate
    )
    df = hours_dataframe().query(querystring)
    turnover = df['turnover'].sum()
    return turnover


def create_querystring(users, only_clients=0, only_billable=0, fromdate=None, untildate=None):
    query = ['type=="normal"']
    if fromdate:
        query += [f'day >= "{fromdate.strftime(DATE_FORMAT)}"']
    if untildate:
        query += [f'day < "{untildate.strftime(DATE_FORMAT)}"']
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


@reportz(hours=24)
def beschikbare_uren_productie(fromdate=None, untildate=None):
    hours = geboekte_uren(only_productie_users=1, fromdate=fromdate, untildate=untildate)
    return hours


@reportz(hours=24)
def beschikbare_uren_iedereen(fromdate=None, untildate=None):
    hours = geboekte_uren(only_productie_users=0, fromdate=fromdate, untildate=untildate)
    return hours

@reportz(hours=24)
def get_interns(sim):
    ''' Returns a set of users with function Stagiair'''
    return {e['name'] for e in sim.employee({'function': 'Stagiair'})}

@reportz(hours=2)
def beschikbare_uren_via_wat_is_geboekt(fromdate, untildate, employees:list=[]):
    ''' Oude methode, op basis van alle medewerkers (geen stagairs) en hun geboekte uren per dag afgerond naar 0, 4 of 8 uur'''
    sim = simplicate()
    interns = get_interns(sim)
    query = f'day>="{fromdate}" and day<"{untildate}"'
    if employees:
        query += ' and employee in @employees'
    else:
        query += ' and employee not in @interns'
    grouped = (
        hours_dataframe()
        .query(query)  # Filter on date range
        .groupby(['employee', 'day', 'type'])[['hours']]
        .sum()  # Group hours by employee, day and type
        .unstack()  # Dubbel niveau headers eruit
        .fillna(0)  # Nan -> 0
        .reset_index()
    )  # Convert indexes to columns
    if len(grouped.columns)  == 3:
        assert list(grouped.columns.values) == [('employee', ''), ('day', ''), ('hours', 'normal')]
        grouped.columns = ['employee', 'day', 'normal']
    elif len(grouped.columns)  == 4:
        assert list(grouped.columns.values) == [('employee', ''), ('day', ''), ('hours', 'leave'), ('hours', 'normal')]
        grouped.columns = ['employee', 'day', 'leave', 'normal']
    else:
        grouped.columns = ['employee', 'day', 'absence', 'leave', 'normal']
    grouped['available'] = grouped.apply(
        lambda a: min(8, round((a['normal']) / 4, 0) * 4), axis=1
    )  # Round to closest multiple of 4
    available = grouped['available'].sum()
    return available


###### PRODUCTIEF ############


@reportz(hours=2)
def productieve_uren_productie(fromdate=None, untildate=None):
    hours = geboekte_uren(only_productie_users=1, only_clients=1, fromdate=fromdate, untildate=untildate)
    return hours


@reportz(hours=2)
def productieve_uren_iedereen(fromdate=None, untildate=None):
    hours = geboekte_uren(only_productie_users=0, only_clients=1, fromdate=fromdate, untildate=untildate)
    return hours


########## BILLABLE ############


@reportz(hours=2)
def billable_uren_productie(fromdate=None, untildate=None):
    hours = geboekte_uren(
        only_productie_users=1, only_clients=1, only_billable=1, fromdate=fromdate, untildate=untildate
    )
    return hours


@reportz(hours=2)
def billable_uren_iedereen(fromdate=None, untildate=None):
    hours = geboekte_uren(
        only_productie_users=0, only_clients=1, only_billable=1, fromdate=fromdate, untildate=untildate
    )
    return hours


# Percentages
def productiviteit_perc_productie(fromdate=None, untildate=None):
    return 100 * productieve_uren_productie(fromdate, untildate) / beschikbare_uren_productie(fromdate, untildate)


def billable_perc_productie(fromdate=None, untildate=None):
    return 100 * billable_uren_productie(fromdate, untildate) / beschikbare_uren_productie(fromdate, untildate)


def productiviteit_perc_iedereen(fromdate=None, untildate=None):
    return 100 * productieve_uren_iedereen(fromdate, untildate) / beschikbare_uren_iedereen(fromdate, untildate)


def billable_perc_iedereen(fromdate=None, untildate=None):
    avail = beschikbare_uren_iedereen(fromdate, untildate)
    res = 100 * billable_uren_iedereen(fromdate, untildate) / avail
    trends.update('billable_hele_team', round(res, 1))
    return res


def billable_perc_user(user):
    billable = geboekte_uren_users(user, only_billable=1)
    total = geboekte_uren_users(user)
    if total:
        res = 100 * billable / total
    else:
        res = 0
    return res


def productiviteit_perc_user(user):
    productive = geboekte_uren_users(user, only_clients=1)
    total = geboekte_uren_users(user)
    if total:
        res = 100 * productive / total
    else:
        res = 0
    return res


def percentage_directe_werknemers():
    '''DDA Cijfer. Is het percentage productiemedewerkers tov het geheel'''
    untildate = datetime.date.today()
    fromdate = untildate - datetime.timedelta(days=183)
    return 100 * beschikbare_uren_productie(fromdate, untildate) / beschikbare_uren_iedereen(fromdate, untildate)


#@reportz(hours=8)
def billable_trend_person_week(user, startweek=1):
    # Returns a list of labels and a list of hours
    thisweek = datetime.datetime.now().isocalendar()[1]
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


@reportz(hours=24)
def corrections_last_month():
    # Returns a dataframe with project, hours
    df = hours_dataframe()
    lastmonth = (datetime.datetime.today() + datetime.timedelta(days=-30)).strftime(DATE_FORMAT)
    x = (
        df.query(f'day>="{lastmonth}"')
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


@reportz(hours=24)
def corrections_all():
    # returns a dataframe of organization, project_name, project_id, corrections
    df = hours_dataframe()
    result = (
        df.groupby(['organization', 'project_name', 'project_id'])
        .agg({'hours': 'sum', 'corrections': 'sum'})
        .query('corrections < 0')
        .sort_values('corrections')
        .reset_index()
    )
    result['corrections'] = result.apply(lambda a: int(a['corrections']), axis=1)
    return result


@reportz(hours=24)
def corrections_percentage(from_weeks_ago, until_weeks_ago):
    df = hours_dataframe()
    one_week_ago = (datetime.datetime.today() + datetime.timedelta(weeks=-until_weeks_ago)).strftime(DATE_FORMAT)
    five_weeks_ago = (datetime.datetime.today() + datetime.timedelta(weeks=-from_weeks_ago)).strftime(DATE_FORMAT)
    data = df.query(f'(tariff>0 or service_tariff>0) and day>="{five_weeks_ago}" and day<"{one_week_ago}"')
    percentage_corrected = 100 * -data['corrections'].sum() / data['hours'].sum()
    return percentage_corrected


def largest_corrections(minimum, weeks_back):
    df = hours_dataframe()
    today = datetime.datetime.today().strftime(DATE_FORMAT)
    two_weeks_ago = (datetime.datetime.today() + datetime.timedelta(weeks=-weeks_back)).strftime(DATE_FORMAT)
    query = f'corrections < 0 and day>="{two_weeks_ago}" and day<"{today}"'
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

@reportz(hours=24)
def get_timetable(sim):
    res = sim.timetable()
    return res


def beschikbare_uren_volgens_rooster(fromdate, untildate, employees:list=[]):
    # todo: wat doen we met stagairs? Die tellen nu mee.

    if type(fromdate) in (datetime.datetime,datetime.date):
        fromdate = fromdate.strftime(DATE_FORMAT)
    if type(untildate) in (datetime.datetime,datetime.date):
        untildate = untildate.strftime(DATE_FORMAT)

    sim = simplicate()
    # Get the list of current employees
    if not employees:
        interns = get_interns(sim)
        employees = set(hours_dataframe().query(f'day>="{fromdate}" and day<"{untildate}"').employee.unique())
        employees.difference_update(interns)

    # Roosteruren
    timetable = get_timetable(sim)
    tot = 0
    for t in timetable:
        if t['employee']['name'] not in employees \
            or t['start_date'] >= untildate \
            or t.get('end_date','9999') < fromdate:
            continue
        day = max(t['start_date'],fromdate)
        y,m,d = day.split('-')
        date = datetime.datetime(int(y),int(m),int(d))
        table = [(t['even_week'][f'day_{i}']['hours'], t['odd_week'][f'day_{i}']['hours']) for i in range(1, 8)]
        ending_day_of_roster = min(t.get('end_date','9999'), untildate)
        while date.strftime(DATE_FORMAT) < ending_day_of_roster:
            day_of_week = date.weekday()  # weekday is 0 for Monday
            week_number = date.isocalendar()[1]
            index = week_number % 2
            tot += table[day_of_week][index]
            date += datetime.timedelta(days=1)

    # Vrij
    leave = leave_hours(fromdate, untildate, employees)

    # Ziek
    absence = verzuim_absence_hours(fromdate, untildate, employees)

    return tot, leave, absence

if __name__ == '__main__':
    os.chdir('..')
    load_cache()

    # until_date = datetime.date.today() + datetime.timedelta(weeks=-1)
    # from_date = datetime.date.today() + datetime.timedelta(weeks=-2)
    sim = simplicate()
    fromdate = '2021-06-01'
    untildate = '2021-10-01'
    # Get the list of current employees
    employees = set(hours_dataframe().query(f'day>="{fromdate}" and day<"{untildate}"').employee.unique())

    for e in employees:
         r, v, z = beschikbare_uren_volgens_rooster(fromdate, untildate, [e])
         c = r - v - z # rooster - vrij - ziek
         b = beschikbare_uren_via_wat_is_geboekt(fromdate, untildate, [e])
         if c-b>30:
            print( e, b, c, b-c)
    #for i in range( 9 ):
    #    c = beschikbare_uren2(f'2021-0{i+1}-01', f'2021-{i+2}-01')
    #    b = beschikbare_uren(f'2021-0{i+1}-01', f'2021-{i+2}-01')
    #    print( i+1, b, c )
    a = b-c
    # print()
    # print('productiviteit_perc_productie')
    # print(
    #     productieve_uren_productie(from_date, until_date),
    #     '/',
    #     beschikbare_uren_productie(from_date, until_date),
    #     '=',
    #     productiviteit_perc_productie(from_date, until_date),
    # )
    # print()
    # print('billable_perc_productie')
    # print(
    #     billable_uren_productie(from_date, until_date),
    #     '/',
    #     beschikbare_uren_productie(from_date, until_date),
    #     '=',
    #     billable_perc_productie(from_date, until_date),
    # )
    # print()
    # print('productiviteit_perc_iedereen')
    # print(
    #     productieve_uren_iedereen(from_date, until_date),
    #     '/',
    #     beschikbare_uren_iedereen(from_date, until_date),
    #     '=',
    #     productiviteit_perc_iedereen(from_date, until_date),
    # )
    # print()
    # print('billable_perc_iedereen')
    # print(
    #     billable_uren_iedereen(from_date, until_date),
    #     '/',
    #     beschikbare_uren_iedereen(from_date, until_date),
    #     '=',
    #     billable_perc_iedereen(from_date, until_date),
    # )
