import datetime
import os
import sys

import pandas as pd

from model.utilities import fraction_of_the_year_past
from sources import database as db
from model.caching import reportz
from sources.googlesheet import sheet_tab, to_int
from model.trendline import trends
from sources.simplicate import simplicate, hours_dataframe, DATE_FORMAT

# @reportz(hours=24)
# def productiviteit_persoon(user):
#     y = datetime.today().year
#     res = []
#     result_tasks, sumbudget, sumhours, warnings = calculate(user, y)
#     b = sum([task['budget'] for task in result_tasks])
#     if b != sumbudget:
#         pass
#     for line in result_tasks:
#         res += [[line['client'], line['project'], line['task'], line['budget'], line['hours'], line['hourly']]]
#     return res


def roster_hours():
    roster = {}
    sim = simplicate()
    data = sim.contract()
    for d in data:
        roster[d['employee']['name']] = 40 * float(d['parttime_percentage']) / 100
    return roster


def roster_hours_user( user ):
    #return roster_hours().get(user,0)
    sim = simplicate()
    roster = sim.timetable_simple( user )
    res = sum([day[0]+day[1] for day in roster])/2 # 2 weeks
    return res

@reportz(hours=24)
def tuple_of_productie_users():
    productie_teams = {'Development', 'PM', 'Service Team', 'Concept & Design', 'Testing'}
    sim = simplicate()
    users = sim.employee({'employment_status': 'active'})
    users = [u['name'] for u in users if set(t['name'] for t in u.get('teams', [])).intersection(productie_teams)]
    return users


# @reportz(hours=24)
# def productiviteit_overzicht():
#     y = datetime.datetime.today().year
#     res = []
#     for user in tuple_of_productie_users():
#         tasks, budget, hours, allwarnings = calculate(user, y)
#         if geboekte_uren_users(user):
#             besch = geboekte_uren_users(user)
#             prod = geboekte_uren_users(user, only_clients=1)
#             bill = geboekte_uren_users(user, billable=1)
#             perc_productief = prod / besch * 100
#             perc_billable = bill / besch * 100
#         else:
#             besch = prod = bill = 0
#             perc_productief = perc_billable = 0
#         res += [
#             [user, budget, hours, budget / hours if hours else 0, besch, prod, perc_productief, bill, perc_billable]
#         ]
#     return sorted(res, key=lambda a: a[1], reverse=True)


# @reportz(hours=24)
# def cijfers_werknemers_value(user, key):
#     tab = sheet_tab('Cijfers werknemers 2019', '2019')
#     col = tab[0].index(key)
#     rows = [r for r in tab if r[0] == user]
#     if not rows:
#         return 0
#     target = rows[0][col]
#     if not target:
#         return 0
#     return to_int(target.replace(',', '.'))


# def user_target(user):
#     return cijfers_werknemers_value(user, 'Target jaar')
#
#
# def user_target_now(user):
#     return fraction_of_the_year_past() * user_target(user)


@reportz(hours=2)
def geboekte_uren(only_productie_users=0, only_clients=0, billable=0, fromdate=None, untildate=None):
    users = tuple_of_productie_users() if only_productie_users else None
    return geboekte_uren_users(users, only_clients, billable, fromdate, untildate)


@reportz(hours=2)
def geboekte_uren_users(users, only_clients=0, billable=0, fromdate=None, untildate=None):
    df = hours_dataframe() # Do not count leaves

    query = ['type=="normal"']
    if fromdate:
        query += [f'day >= "{fromdate.strftime(DATE_FORMAT)}"']
    if untildate:
        query += [f'day < "{untildate.strftime(DATE_FORMAT)}"']
    if only_clients:
        query += ['organization not in ("Oberon", "Qikker Online B.V.")']
    if users:
        if type(users) == str:
            users = (users,)  # make it a tuple
        query += [f'employee in {users}']
    if billable:
        query += ['(tariff > 0 or service_tariff>0)']

    query_string = ' and '.join(query)
    df = df.query(query_string)
    hours = df['hours'].sum()
    if billable:
        hours += df['corrections'].sum()
    return hours


@reportz(hours=24)
def beschikbare_uren_productie(fromdate=None, untildate=None):
    hours = geboekte_uren(only_productie_users=1, fromdate=fromdate, untildate=untildate)
    return hours


@reportz(hours=24)
def beschikbare_uren_iedereen(fromdate=None, untildate=None):
    hours = geboekte_uren(only_productie_users=0, fromdate=fromdate, untildate=untildate)
    return hours


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
    hours = geboekte_uren(only_productie_users=1, only_clients=1, billable=1, fromdate=fromdate, untildate=untildate)
    return hours


@reportz(hours=2)
def billable_uren_iedereen(fromdate=None, untildate=None):
    hours = geboekte_uren(only_productie_users=0, only_clients=1, billable=1, fromdate=fromdate, untildate=untildate)
    return hours


# Percentages
def productiviteit_perc_productie(fromdate=None, untildate=None):
    return 100 * productieve_uren_productie() / beschikbare_uren_productie()


def billable_perc_productie(fromdate=None, untildate=None):
    return 100 * billable_uren_productie(fromdate, untildate) / beschikbare_uren_productie(fromdate, untildate)


def productiviteit_perc_iedereen(fromdate=None, untildate=None):
    return 100 * productieve_uren_iedereen(fromdate, untildate) / beschikbare_uren_iedereen(fromdate, untildate)


def billable_perc_iedereen(fromdate=None, untildate=None):
    res = 100 * billable_uren_iedereen(fromdate, untildate) / beschikbare_uren_iedereen(fromdate, untildate)
    trends.update('billable_hele_team', round(res, 1))
    return res

def billable_perc_user( user ):
    if geboekte_uren_users(user):
        res = 100 * geboekte_uren_users(user, billable=1) / geboekte_uren_users(user)
    else:
        res = 0
    return res

def percentage_directe_werknemers():
    '''DDA Cijfer. Is het percentage productiemedewerkers tov het geheel'''
    untildate = datetime.date.today()
    fromdate = untildate - datetime.timedelta(days=183)
    return 100 * beschikbare_uren_productie(fromdate, untildate) / beschikbare_uren_iedereen(fromdate, untildate)


@reportz(hours=8)
def billable_trend_person_week(user, startweek=1):
    # Returns a list of labels and a list of hours
    thisweek = datetime.datetime.now().isocalendar()[1]
    labels = list(range( startweek, thisweek))
    hours = [0] * len( labels )

    #d1 = hours_dataframe()
    #d2 = d1.query(f'type=="normal" and employee=="{user}" and tariff>0')
    #d3 = d2.groupby(['week'])[['hours']].sum()

    dictdict = hours_dataframe()\
        .query(f'type=="normal" and employee=="{user}" and (tariff>0 or service_tariff>0)')\
        .groupby(['week'])[['hours']].sum()\
        .to_dict('index')
    for key, val in dictdict.items():
        pos = key-startweek
        if 0 <= pos < len(labels):
            hours[pos] = dictdict[key]['hours']
    return (labels, hours)



def weekno_to_date(rec):
    d = f"{rec['year']}-W{rec['weekno']}-1"
    rec['date'] = datetime.strptime(d, '%G-W%V-%u').strftime('%Y-%m-%d')
    return rec


if __name__ == '__main__':
    os.chdir('..')
    for key, value in roster_hours().items():
        print( value, key )
    sys.exit()
    today = datetime.datetime(2021, 1, 16)  # datetime.date.today()
    yesterday = datetime.datetime(2021, 1, 11)  # today + datetime.timedelta(days=-1)
    b = geboekte_uren(only_productie_users=1, only_clients=1, fromdate=yesterday, untildate=today)
    print(b)
    lastmonth = datetime.date.today() - datetime.timedelta(days=30)
    print(productiviteit_perc_productie(lastmonth))
    print()
    print('productiviteit_perc_productie')
    print(productieve_uren_productie(), '/', beschikbare_uren_productie(), '=', productiviteit_perc_productie())
    print()
    print('billable_perc_productie')
    print(billable_uren_productie(), '/', beschikbare_uren_productie(), '=', billable_perc_productie())
    print()
    print('productiviteit_perc_iedereen')
    print(productieve_uren_iedereen(), '/', beschikbare_uren_iedereen(), '=', productiviteit_perc_iedereen())
    print()
    print('billable_perc_iedereen')
    print(billable_uren_iedereen(), '/', beschikbare_uren_iedereen(), '=', billable_perc_iedereen())
