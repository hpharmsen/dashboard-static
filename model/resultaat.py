import calendar
import decimal
import os
from datetime import datetime, timedelta

from model.caching import reportz
from beautiful_date import *
import pandas as pd
from decimal import Decimal

from model.productiviteit import tuple_of_productie_users
from model.winstgevendheid import winst_per_klant
from sources import database as db
from model.trendline import trends
from sources.simplicate import simplicate, onderhanden_werk, DATE_FORMAT, hours_dataframe
from sources.yuki import yuki
from sources.googlesheet import sheet_tab, sheet_value

BEGROTING_SHEET = 'Begroting 2021'
BEGROTING_TAB = 'Begroting'
BEGROTING_KOSTEN_ROW = 23
BEGROTING_INKOMSTEN_ROW = 32
BEGROTING_INKOMSTEN_VORIG_JAAR_ROW = BEGROTING_INKOMSTEN_ROW + 1
BEGROTING_WINST_ROW = 35
BEGROTING_WINST_VORIG_JAAR_ROW = BEGROTING_WINST_ROW + 1

RESULTAAT_TAB = 'Resultaat'
RESULTAAT_KOSTEN_ROW = BEGROTING_KOSTEN_ROW
RESULTAAT_BIJGEWERKT_ROW = 51

##### WINST #####


def winst_verschil_percentage():
    ''' Hoeveel de winst percentueel hoger is dan begroot '''
    return 100 * winst_verschil() / winst_begroot()


def winst_verschil():
    ''' Hoeveel de winst boven de begrote winst ligt. '''
    return winst_werkelijk() - winst_begroot()


def winst_werkelijk():
    ''' De daadwerkelijk gerealiseerde kosten tot nu toe '''
    return bruto_marge_werkelijk() - kosten_werkelijk()


def winst_begroot():
    ''' De begrote winst tot nu toe '''
    return omzet_begroot() - kosten_begroot()


#################### OMZET #############################


@reportz
def omzet_verschil_percentage():
    ''' Hoeveel de omzet percentueel hoger is dan begroot '''
    return 100 * omzet_verschil() / omzet_begroot()


@reportz
def omzet_verschil():
    ''' Hoeveel de omzet boven de begrote omzet ligt. '''
    o = bruto_marge_werkelijk()
    b = omzet_begroot()
    return o - b


##### BEGROTE OMZET #####


@reportz(hours=24)
def omzet_begroot():
    res = omzet_begroot_na_maand(0)
    return res


@reportz(hours=24)
def omzet_begroot_na_maand(m):
    ''' Begrote kosten na maand m gerekend tot vandaag '''

    h = huidige_maand()
    begroot_tm_m = omzet_begroot_tm_maand(m)
    begroot_tm_h = omzet_begroot_tm_maand(h)
    aantal_maanden_na_laatste_maand = Decimal(h - m - 1 + datetime.today().day / 30)
    res = (begroot_tm_h - begroot_tm_m) / (h - m) * aantal_maanden_na_laatste_maand
    return Decimal(res)


@reportz(hours=24)
def omzet_begroot_tm_maand(m):
    ''' Begrote kosten t/m maand m  '''
    if m == 0:
        return 0
    tab = sheet_tab(BEGROTING_SHEET, BEGROTING_TAB)
    res = sheet_value(tab, BEGROTING_INKOMSTEN_ROW, m + 2) * 1000
    return Decimal(res)


##### OMZET #####


@reportz
def bruto_marge_werkelijk():
    res = omzet_tm_nu() - projectkosten_tm_nu() + onderhanden_werk()
    return res


@reportz(hours=24)
def omzet_tm_maand(m):
    return yuki().income(last_day_of_month(m))


@reportz(hours=24)
def projectkosten_tm_maand(m):
    return yuki().direct_costs(last_day_of_month(m))


@reportz(hours=24)
def omzet_tm_nu():
    return yuki().income()


@reportz(hours=24)
def projectkosten_tm_nu():
    return yuki().direct_costs()


###### KOSTEN ######


def kosten_boekhoudkundig_tm_maand(m):
    return yuki().costs(last_day_of_month(m))


@reportz(hours=24)
def kosten_begroot_tm_maand(m):
    ''' Begrote kosten t/m maand m  '''
    if m == 0:
        return 0
    tab = sheet_tab(BEGROTING_SHEET, BEGROTING_TAB)
    res = sheet_value(tab, BEGROTING_KOSTEN_ROW, m + 2) * 1000
    return Decimal(res)


@reportz(hours=24)
def kosten_begroot_na_maand(m):
    ''' Begrote kosten na maand m gerekend tot vandaag '''
    h = huidige_maand()
    begroot_tm_m = kosten_begroot_tm_maand(m)
    begroot_tm_h = kosten_begroot_tm_maand(h)
    aantal_maanden_na_laatste_maand = Decimal(h - m - 1 + datetime.today().day / 30)
    res = (begroot_tm_h - begroot_tm_m) / (h - m) * aantal_maanden_na_laatste_maand
    return Decimal(res)


def kosten_begroot():
    ''' Het begrote aantal kosten t/m nu '''
    res = kosten_begroot_na_maand(0)
    return res


def kosten_verschil_percentage():
    ''' Hoeveel de kosten percentueel hoger is dan begroot '''
    return 100 * kosten_verschil() / kosten_begroot()


def kosten_verschil():
    ''' Hoeveel de omzet boven de begrote kosten ligt. '''
    return kosten_werkelijk() - kosten_begroot()


def kosten_werkelijk():
    ''' De daadwerkelijk gerealiseerde kosten tot nu toe '''
    laatste_maand = laatste_geboekte_maand()
    return kosten_boekhoudkundig_tm_maand(laatste_maand) + kosten_begroot_na_maand(laatste_maand)


##### DIVERSEN #####


def virtuele_dag():
    """Als boekhouding van de nog niet is bijgewerkt retourneert
    dit het dagnummer doorgenummerd vanuit de laatste complete maand. Dus 31, 32, 33, etc.
    Anders gewoon het dagnummer."""
    d = datetime.today().day
    m = datetime.today.month
    d += 30 * (laatste_geboekte_maand() - m)  # Gewoon in de nieuwe maanden doortellen
    return d


def laatste_geboekte_maand():
    # Nummer van de laatste maand die in de boekhouding is bijgewerkt
    tab = sheet_tab(BEGROTING_SHEET, RESULTAAT_TAB)
    for m in range(12):
        data = sheet_value(tab, RESULTAAT_BIJGEWERKT_ROW, m + 3)
        if not data:
            return m
    return 12


# @reportz(hours=24)
def bijgewerkt():
    """Checkt in de Resultaat tab van het Keycijfers sheet of de boekhouding van afgelopen
    maand al is ingevuld."""
    tab = sheet_tab(BEGROTING_SHEET, RESULTAAT_TAB)
    vm = vorige_maand()
    data = sheet_value(tab, RESULTAAT_BIJGEWERKT_ROW, vm + 2)
    return data


def vorige_maand():
    ''' Nummer van de vorige maand. '''
    return datetime.today().month - 1


def huidige_maand():
    ''' Nummer van de huidige maand. '''
    return datetime.today().month


def volgende_maand():
    ''' Nummer van de volgende maand. '''
    return datetime.today().month + 1


def last_day_of_last_month():
    y = datetime.now().year
    m = vorige_maand()
    d = calendar.monthrange(y, m)[1]
    return datetime(y, m, d)


def last_day_of_month(m):
    y = datetime.now().year  # !! Gaat mis na einde jaar
    d = calendar.monthrange(y, m)[1]
    return datetime(y, m, d)


def update_omzet_per_week():
    ''' Tabel van dag, omzet waarbij dag steeds de maandag is van de week waar het om gaat '''
    trend_name = 'omzet_per_week'
    last_day = trends.second_last_registered_day(trend_name)  # Always recalculate the last since hours may have changed
    y, m, d = last_day.split('-')
    last_day = BeautifulDate(int(y), int(m), int(d)) - MO  # Last Monday on or before the last calculated day
    last_sunday = D.today() - SU
    for monday in drange(last_day, last_sunday, 7 * days):
        sunday = monday + 6 * days
        week_turnover = get_turnover_from_simplicate(monday, sunday)
        # if monday < BeautifulDate(2021, 1, 1):
        #    week_turnover += get_turnover_from_extranet(monday, sunday)
        trends.update(trend_name, week_turnover, monday)


@reportz(hours=24)
def get_turnover_from_simplicate(fromday, untilday):
    # Including untilday
    # turnover = simplicate().turnover(
    #     {'start_date': fromday.strftime('%Y-%m-%d'), 'end_date': untilday.strftime('%Y-%m-%d')}
    # )
    df = hours_dataframe().query(f'day >= "{fromday}" and day<="{untilday}" and project_number !="TOR-3"')
    turnover = df['turnover'].sum()
    return int(turnover)


@reportz(hours=24)
def vulling_van_de_planning():
    # Planned hours
    last_week = (datetime.today() + timedelta(weeks=-1)).strftime(DATE_FORMAT)
    # last_day = trends.last_registered_day('omzet_per_week')
    query = f'''select week(day,5) as weekno, ifnull(round(sum(dayhours)),0) as plannedhours from
        (select day, sum(hours) as dayhours from
            (select date(startDate) as day,
                    sum(least((enddate - startDate)/10000,8)) as hours
             from planning_reservation pr
             join planning_location pl on pl.id=pr.planning_locationId
             left join project p on p.id=pr.projectId
             where startDate > "{last_week}" AND planning_typeId = '17' and (p.customerId is null or p.customerId <> 4)
             group by day) q1
        group by day) q2
    group by year(day), weekno
    order by day
    limit 16'''
    table = db.dataframe(query)

    # Roster
    timetable = [
        t
        for t in simplicate().timetable()
        if not t.get('end_date') and t['employee']['name'] in tuple_of_productie_users()
    ]
    odd = {
        table['employee']['name']: [table['odd_week'][f'day_{i}']['hours'] for i in range(1, 6)] for table in timetable
    }
    even = {
        table['employee']['name']: [table['even_week'][f'day_{i}']['hours'] for i in range(1, 6)] for table in timetable
    }
    odd_tot = sum([sum(week) for week in odd.values()])
    even_tot = sum([sum(week) for week in even.values()])
    table['roster'] = table.apply(lambda a: even_tot if a['weekno'] % 2 == 0 else odd_tot, axis=1)

    # Leaves
    leaves = pd.DataFrame(
        [
            {
                'day': l['start_date'].split()[0],
                'week': int(datetime.strptime(l['start_date'].split()[0], DATE_FORMAT).strftime('%W')),
                'hours': -l['hours'],
                'employee': l['employee']['name'],
            }
            for l in simplicate().leave({'start_date': '2021-01-01'})
        ]
    )
    leave_hours_per_week = leaves.groupby(['week']).sum(['hours'])
    table['leaves'] = table.apply(
        lambda row: leave_hours_per_week.at[row['weekno'], 'hours']
        if row['weekno'] in leave_hours_per_week.index
        else 0,
        axis=1,
    )

    # Filled
    table['filled'] = table.apply(lambda row: int(100 * row['plannedhours'] / (row['roster'] - row['leaves'])), axis=1)
    table['monday'] = table.apply(
        lambda row: datetime.strptime(f'2021-W{int(row["weekno"])}-1', "%Y-W%W-%w").strftime(DATE_FORMAT), axis=1
    )
    res = table[['monday', 'filled']].to_dict('records')
    return res


################# KLANTEN #####################################


@reportz(hours=24)
def top_x_klanten_laatste_zes_maanden(number=3):
    # df = omzet_per_klant().copy(deep=True)
    return omzet_per_klant_laatste_zes_maanden().head(number)


@reportz(hours=24)
def omzet_per_klant_laatste_zes_maanden():
    ''' DataFrame van klant, omzet, percentage '''

    result = winst_per_klant(datetime.now() + timedelta(days=-183))

    # Nieuw dataframe met alleen de juiste kolommen
    data = [result['customer'], result['turnover hours'] + result['turnover fixed']]
    headers = ['klant', 'omzet']
    df = pd.concat(data, axis=1, keys=headers)

    # Percentages per klant
    totaal = df['omzet'].sum()
    df['percentage'] = df['omzet'] * 100.0 / totaal
    return df.sort_values(by="omzet", ascending=False)


def simplicate_gefactureerd(tm_maand=12):
    sim = simplicate()
    from_date = '2021-01-01'
    until_date = datetime.today().strftime(DATE_FORMAT)
    inv = sim.invoice({'from_date': from_date, 'until_date': until_date})
    inv_df = sim.to_pandas(inv)
    invs = inv_df[['invoice_number', 'total_excluding_vat', 'status_name', 'organization_name', 'project_name', 'date']]
    return decimal.Decimal(invs['total_excluding_vat'].sum())


if __name__ == '__main__':
    os.chdir('..')
    print(simplicate_gefactureerd())
    print(yuki().income())
    print(simplicate_gefactureerd() - yuki().income())

    # update_omzet_per_week()
    # print(debiteuren_leeftijd_analyse())
    # print(debiteuren_30_60_90_yuki())
    # print(toekomstige_omzet_per_week())
    # print(vulling_van_de_planning())
