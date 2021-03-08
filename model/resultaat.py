import calendar
from datetime import datetime, timedelta
import warnings
from model.caching import reportz
from beautiful_date import *
import pandas as pd
from decimal import Decimal

from model.productiviteit import tuple_of_productie_users
from sources import database as db
from model.trendline import trends
from sources.simplicate import simplicate, onderhanden_werk_list, DATE_FORMAT
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
# RESULTAAT_SUBSIDIE_ROW = 29
RESULTAAT_BOEKHOUD_KOSTEN_ROW = 49
# RESULTAAT_OMZET_ROW = 52
RESULTAAT_BIJGEWERKT_ROW = 39
# RESULTAAT_FACTUREN_VORIG_JAAR_ROW = 54
# RESULTAAT_BONUSSEN_ROW = 62

##### WINST #####


def winst_verschil_percentage():
    ''' Hoeveel de winst percentueel hoger is dan begroot '''
    return 100 * winst_verschil() / winst_begroot()


def winst_verschil():
    ''' Hoeveel de winst boven de begrote winst ligt. '''
    return winst_werkelijk() - winst_begroot()


def winst_werkelijk():
    ''' De daadwerkelijk gerealiseerde kosten tot nu toe '''
    return omzet_werkelijk() - kosten_werkelijk()


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
    o = omzet_werkelijk()
    b = omzet_begroot()
    return o - b


##### BEGROTE OMZET #####


@reportz(hours=24)
def omzet_begroot():
    ''' Begrote omzet tot en met vandaag. '''
    h = begroting_maandomzet(virtuele_maand())
    v = begroting_maandomzet(virtuele_maand() - 1)
    vd = virtuele_dag()  # Dag van de maand maar doorgeteld als de vorige maand nog niet is ingevuld in de boekhouding
    return Decimal(v + vd / 30 * (h - v))


@reportz(hours=24)
def begroting_maandomzet(maand):
    ''' Begrote omzet van de meegegeven maand. Komt uit het begroting sheet. '''
    if maand == 0:
        return 0
    tab = sheet_tab(BEGROTING_SHEET, BEGROTING_TAB)
    return sheet_value(tab, BEGROTING_INKOMSTEN_ROW, maand + 2) * 1000


##### OMZET #####


@reportz
def omzet_werkelijk():
    res = omzet_tm_nu() + onderhanden_werk()
    return res


# @reportz(hours=24)
def omzet_tm_vorige_maand():
    return yuki().income(last_day_of_last_month())


# @reportz(hours=24)
def projectkosten_tm_vorige_maand():
    return yuki().direct_costs(last_day_of_last_month())


# @reportz(hours=24)
def omzet_tm_nu():
    return yuki().income()


# @reportz(hours=24)
def projectkosten_tm_nu():
    return yuki().direct_costs()


def onderhanden_werk():
    return Decimal(onderhanden_werk_list()['OH'].sum())


###### KOSTEN ######


@reportz(hours=24)
def kosten_begroot_deze_maand():
    ''' '''
    d = virtuele_dag()
    m = virtuele_maand()
    res = Decimal(d / 30) * (kosten_begroot_tm_maand(m) - kosten_begroot_tm_maand(m - 1))
    return res


def kosten_boekhoudkundig_tm_vorige_maand():
    return yuki().costs(last_day_of_last_month())


@reportz(hours=24)
def kosten_begroot_tm_maand(m):
    ''' Begrote kosten t/m maand m  '''
    if m == 0:
        return 0
    tab = sheet_tab(BEGROTING_SHEET, BEGROTING_TAB)
    res = sheet_value(tab, BEGROTING_KOSTEN_ROW, m + 2) * 1000
    return Decimal(res)


def kosten_begroot():
    ''' Het begrote aantal kosten t/m nu '''
    res = kosten_begroot_tm_maand(virtuele_maand() - 1) + kosten_begroot_deze_maand()
    return res


def kosten_verschil_percentage():
    ''' Hoeveel de kosten percentueel hoger is dan begroot '''
    return 100 * kosten_verschil() / kosten_begroot()


def kosten_verschil():
    ''' Hoeveel de omzet boven de begrote kosten ligt. '''
    return kosten_werkelijk() - kosten_begroot()


def kosten_werkelijk():
    ''' De daadwerkelijk gerealiseerde kosten tot nu toe '''
    kosten_laatste_maand = yuki().costs(last_day_of_last_month())
    return kosten_laatste_maand + Decimal(kosten_begroot_deze_maand())


##### DIVERSEN #####


def virtuele_dag():
    """Als boekhouding van de vorige maand nog niet is bijgewerkt retourneert
    dit het dagnummer doorgenummerd vanuit de vorige maand. Dus 31, 32, 33, etc.
    Anders gewoon het dagnummer."""
    vd = datetime.today().day
    if not bijgewerkt():
        vd += 30  # Gewoon in de vorige maand doortellen
    return vd


def virtuele_maand():
    """Als boekhouding van de vorige maand nog niet is bijgewerkt retourneert
    dit het nummer van vorige maand. Anders deze maand."""
    vm = datetime.today().month
    if not bijgewerkt():
        vm -= 1  # We kijken nog naar vorige maand
    return vm


@reportz(hours=24)
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


@reportz(hours=10)
def laatste_maand_resultaat(row):
    ''' Retourneert data uit de laatst ingevulde boekhouding kolom van het data sheet '''
    if virtuele_maand() == 1:
        return 0  # Voor januari is er nog geen vorige maand
    col = virtuele_maand() + 1
    tab = sheet_tab(BEGROTING_SHEET, RESULTAAT_TAB)
    res = sheet_value(tab, row, col)
    if not res:
        return 0
    return res * 1000


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
    turnover = simplicate().turnover(
        {'start_date': fromday.strftime('%Y-%m-%d'), 'end_date': untilday.strftime('%Y-%m-%d')}
    )
    return int(turnover)


def toekomstige_omzet_per_week():
    last_day = trends.last_registered_day('omzet_per_week')
    query = f'''select min(day) as monday, ifnull(round(sum(dayhours)),0) as plannedhours from
        (select day, sum(hours) as dayhours from
            (select date(startDate) as day,
                    sum(least((enddate - startDate)/10000,8)) as hours
             from planning_reservation pr
             join planning_location pl on pl.id=pr.planning_locationId
             left join project p on p.id=pr.projectId
             where startDate > "{last_day}" AND planning_typeId = '17' and p.customerId<>4
             group by day) q1
        group by day) q2
    group by year(day), week(day)
    having weekday(monday)=0
    order by day'''
    table = db.dataframe(query)[1:]  # vanaf 1 omdat de eerste waarde ook al in de omzet_per_week zit
    return [{'monday': last_day, 'weekturnover': 0}]  # TODO: DEZE MOET EEN LIJST VAN VERWACHTE OMZETTEN GAAN TERUGGEVEN


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
    order by day'''
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


#################### DEBITEUREN ################################################
def debiteuren_leeftijd_analyse():
    df = debiteuren_leeftijd_analyse_extranet()
    yuki_result = debiteuren_leeftijd_analyse_yuki()
    df = df.append(yuki_result, ignore_index=True)
    df = (
        df.groupby(["factuuradres"])
        .agg({'open': 'sum', 'a30': 'sum', "a60": 'sum', 'a90': 'sum', "90plus": 'sum'})
        .reset_index()
    )
    df = df.sort_values("open", ascending=False)
    return df


@reportz(hours=24)
def debiteuren_leeftijd_analyse_extranet():
    query = 'select * from age_analysis_view order by 90plus desc, a90 desc, a60 desc'
    warnings.filterwarnings("ignore")
    result = db.dataframe(query)
    return result


@reportz(hours=24)
def debiteuren_leeftijd_analyse_yuki():
    debiteuren = yuki().debtors()
    df = pd.DataFrame(debiteuren)
    df = df.drop(df[df.open <= 0].index)
    # df = df.drop( 'open <= 0', axis=1)
    df['a30'] = df.apply(lambda row: row.open if row.days < 30 else 0, axis=1)
    df['a60'] = df.apply(lambda row: row.open if 30 <= row.days < 60 else 0, axis=1)
    df['a90'] = df.apply(lambda row: row.open if 60 <= row.days < 90 else 0, axis=1)
    df['90plus'] = df.apply(lambda row: row.open if row.days >= 90 else 0, axis=1)
    df.rename(columns={'customer': 'factuuradres'}, inplace=True)
    df = (
        df.groupby(["factuuradres"])
        .agg({'open': 'sum', 'a30': 'sum', "a60": 'sum', 'a90': 'sum', "90plus": 'sum'})
        .reset_index()
    )
    df = df.sort_values("open", ascending=False)
    return df


@reportz(hours=24)
def debiteuren_openstaand():
    dla = debiteuren_leeftijd_analyse()
    return dla['open'].sum()


@reportz(hours=24)
def debiteuren_30_60_90():
    dla = debiteuren_leeftijd_analyse()
    a30 = dla['a30'].sum()
    a60 = dla['a60'].sum()
    a90 = dla['a90'].sum()
    plus90 = dla['90plus'].sum()
    return (a30, a60, a90, plus90)


def debiteuren_30_60_90_extranet():
    dla = debiteuren_leeftijd_analyse_extranet()
    a30 = dla['a30'].sum()
    a60 = dla['a60'].sum()
    a90 = dla['a90'].sum()
    plus90 = dla['90plus'].sum()
    return (a30, a60, a90, plus90)


def debiteuren_30_60_90_yuki():
    dla = debiteuren_leeftijd_analyse_yuki()
    a30 = int(dla['a30'].sum())
    a60 = int(dla['a60'].sum())
    a90 = int(dla['a90'].sum())
    plus90 = int(dla['90plus'].sum())
    return (a30, a60, a90, plus90)


def gemiddelde_betaaltermijn(days=90):
    query = f'''select avg(datediff(payment_date,invoice_date)) as days
                from invoice where payment_date >= DATE(NOW()) - INTERVAL {days} DAY'''
    return db.value(query)


################# KLANTEN #####################################


@reportz(hours=24)
def top_x_klanten_laatste_zes_maanden(number=3):
    # df = omzet_per_klant().copy(deep=True)
    return omzet_per_klant_laatste_zes_maanden().head(number)


@reportz(hours=24)
def omzet_per_klant_laatste_zes_maanden():
    ''' DataFrame van klant, omzet, percentage '''

    # TODO: Invullen vanuit Simplicate (of Yuki)
    df = pd.DataFrame([{'klant': 'alle klanten', 'omzet': 1, 'percentage': 100.0}])
    totaal = df['omzet'].sum()
    df['percentage'] = df['omzet'] * 100.0 / totaal
    return df


if __name__ == '__main__':
    # update_omzet_per_week()
    # print(debiteuren_leeftijd_analyse())
    # print(debiteuren_30_60_90_yuki())
    # print(toekomstige_omzet_per_week())
    print(vulling_van_de_planning())
