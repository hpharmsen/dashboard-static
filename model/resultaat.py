from datetime import datetime
import warnings
from model.caching import reportz

from sources.googlesheet import sheet_tab, sheet_value
from sources import database as db
from model.trendline import trends

tor_onderhanden_2019 = 80741.0

BEGROTING_SHEET = 'Begroting 2020'
BEGROTING_TAB = 'Begroting'
BEGROTING_KOSTEN_ROW = 23
BEGROTING_INKOMSTEN_ROW = 32
BEGROTING_INKOMSTEN_VORIG_JAAR_ROW = 33
BEGROTING_WINST_ROW = 35
BEGROTING_WINST_VORIG_JAAR_ROW = 36

RESULTAAT_TAB = 'Resultaat'
RESULTAAT_KOSTEN_ROW = 23
RESULTAAT_SUBSIDIE_ROW = 29
RESULTAAT_INKOMSTEN_ROW = 32
RESULTAAT_WINST_ROW = 35
RESULTAAT_BOEKHOUD_KOSTEN_ROW = 49
RESULTAAT_OMZET_ROW = 52
RESULTAAT_FACTUREN_VORIG_JAAR_ROW = 53
RESULTAAT_ONDERHANDEN_ROW = 54
RESULTAAT_BONUSSEN_ROW = 61


##### OMZET #####


@reportz
def omzet_verschil_percentage():
    ''' Hoeveel de omzet percentueel hoger is dan begroot '''
    return 100 * omzet_verschil() / omzet_begroot()


@reportz
def omzet_verschil():
    ''' Hoeveel de omzet boven de begrote omzet ligt. '''
    o = opbrengsten()
    b = omzet_begroot()
    return o - b


@reportz
def opbrengsten():
    res = (
        omzet_tm_vorige_maand()
        + subsidie_tm_vorige_maand()
        - onderhanden_vorig_jaar()
        + omzet_deze_maand()
        + onderhanden_werk()
    )
    return res


def onderhanden_vorig_jaar():
    return -laatste_maand_resultaat(53)


@reportz(hours=200)
def laatste_maand_resultaat(row):
    ''' Retourneert data uit de laatst ingevulde boekhouding kolom van het data sheet '''
    if virtuele_maand() == 1:
        return 0
    col = virtuele_maand() + 1
    tab = sheet_tab(BEGROTING_SHEET, RESULTAAT_TAB)
    res = sheet_value(tab, row, col)
    if not res:
        return 0
    return res * 1000


@reportz
def omzet_tm_vorige_maand():
    ''' Gefactureerde omzet t/m vorige maand zoals gerapporteerd in de boekhouding '''
    res = laatste_maand_resultaat(RESULTAAT_OMZET_ROW)
    return res


# @reportz
# def uitbesteed_tm_vorige_maand():
#     ''' Uitbesteed werk t/m vorige maand zoals gerapporteerd in de boekhouding '''
#     return laatste_maand_resultaat(DATA_UITBESTEED_ROW)


@reportz
def onderhanden_tm_vorige_maand():
    ''' Onderhanden werk t/m vorige maand zoals gerapporteerd in de boekhouding '''
    return laatste_maand_resultaat(RESULTAAT_ONDERHANDEN_ROW)


@reportz
def subsidie_tm_vorige_maand():
    ''' Ontvangen subsidie t/m vorige maand zoals gerapporteerd in de boekhouding '''
    return laatste_maand_resultaat(RESULTAAT_SUBSIDIE_ROW)


@reportz(hours=24)
def opbrengsten_tm_vorige_maand():
    ''' De bruto marge tot en met de vorige maand (zoals gerapporteerd in de boekhouding), inclusief subsidie maar zonder onderhanden werk '''
    return laatste_maand_resultaat(RESULTAAT_INKOMSTEN_ROW) + laatste_maand_resultaat(RESULTAAT_ONDERHANDEN_ROW)

    # col = virtuele_maand() + 1
    # tab = sheet_tab(BEGROTING_SHEET, RESULTAAT_TAB)
    # totaal = sheet_value(tab, RESULTAAT_INKOMSTEN_ROW, col)
    # onderhanden = sheet_value(tab, RESULTAAT_ONDERHANDEN_ROW, col)
    # res = totaal - onderhanden # - onderhanden_2019  #!! Correctie begin jaar
    # return res * 1000


@reportz(hours=1)
def omzet_deze_maand():
    ''' De omzet die volgens Oberview vanaf deze virtuele maand is gefactureerd.
        Als de afgelopen maand nog niet is verwerkt in de boekhouding is dat dus de omzet
        van de afgelopen maand plus die van de huidige maand.'''
    m = virtuele_maand()
    y = datetime.today().year
    query = f'''select ifnull(round(sum( invoice_amount)),0) as turnover 
                from invoice 
                where year(invoice_date)={y} and month(invoice_date)>={m}'''
    res = db.value(query)
    return res


# @reportz(hours=24)
# def omzet_per_type_project():
#     ''' Dataframe met omzet per type project (fixed, hosting, hourly_basis, other, service). '''
#     y = datetime.today().year
#     query = f'''select project_type, round(sum(invoice_amount)) as turnover
#                 from invoice, project
#                 where invoice.project_id=project.Id and year(invoice_date)={y}
#                 group by project_type'''
#     return db.dataframe(query)
#
#
# @reportz(hours=24)
# def omzet_per_type_product():
#     ''' Dataframe met omzet per type product (platform, web, mobile, other). '''
#     y = datetime.today().year
#     query = f'''select product_type, round(sum(invoice_amount)) as turnover
#                 from invoice, project
#                 where status in ('open','paid','proforma') and invoice.project_id=project.Id
#                   and year(invoice_date)={y} and product_type is not null
#                   group by product_type
#                   order by turnover desc
#             '''
#     return db.dataframe(query)


##### Onderhanden werk #####
def onderhanden_werk():
    ''' Werk dat is gedaan maar nog niet gefactueerd '''
    res = onderhanden_werk_uurbasis() + onderhanden_werk_fixed() + onderhanden_werk_tor()
    return res


@reportz(hours=1)
def onderhanden_werk_uurbasis_table():
    ''' Uurbasis werk dat is gedaan maar nog niet gefactueerd, per project
        Als tabel met velden name, title, done, invoiced, onderhanden '''
    query = f'''select p.id, c.name, p.title, sum(hours*pu.hourlyRate) as done, ifnull(q2.invoiced,0) as invoiced,  
                sum(hours*pu.hourlyRate)-ifnull(q2.invoiced,0) as onderhanden 
                from project p 
                left join customer c on p.customerId=c.id 
                join project_user pu on pu.projectId=p.id  
                join timesheet ts on ts.projectid=p.id and ts.user=pu.user 
                left join (select project_id as id, sum(invoice_amount) as invoiced from invoice group by project_id) q2 on q2.id=p.id 
                where p.hourlybasis=1 and p.internal=0 and phase<90 and customerId not in (4,125)  
                  and (taskId in (-2,-4,-6)) 
                group by p.id having abs(onderhanden)>=500
                order by onderhanden desc
            '''
    return db.dataframe(query)


def onderhanden_werk_uurbasis():
    ''' Uurbasis erk dat is gedaan maar nog niet gefactueerd '''
    df = onderhanden_werk_uurbasis_table()
    return df['onderhanden'].sum()


@reportz(hours=1)
def onderhanden_werk_fixed_table():
    ''' Fixed price werk dat is gedaan maar nog niet gefactueerd, per project.
        Als tabel met velden name, title, done, invoiced, onderhanden '''
    query = f'''select p.id, c.name, p.title, p.budget*p.completedPerc/100 as done, ifnull(q2.invoiced,0) as invoiced, 
                p.budget*p.completedPerc/100-ifnull(q2.invoiced,0) as onderhanden 
                from project p 
                join project_user pu on pu.projectId=p.id  
                join timesheet ts on ts.projectid=p.id and ts.user=pu.user 
                left join (select project_id as id, sum(invoice_amount) as invoiced from invoice group by project_id) q2 on q2.id=p.id 
                left join customer c on p.customerId=c.id 
                where p.hourlybasis=0 and p.internal=0 and phase<90 and customerId not in (4,125) 
                group by p.id 
                having abs(onderhanden)>=500
                order by onderhanden desc
            '''
    return db.dataframe(query)


# @reportz(hours=1)
def onderhanden_werk_fixed():
    ''' Fixed price werk dat is gedaan maar nog niet gefactueerd '''
    df = onderhanden_werk_fixed_table()
    return df['onderhanden'].sum()


# @reportz(hours=1)
def gedaan_werk_tor_table():
    sql = '''select p.id, p.title, sum(hours*pu.hourlyRate) as done 
             from project p 
             join project_user pu on pu.projectId=p.id 
             join timesheet ts on ts.projectid=p.id and ts.user=pu.user 
             where customerId=125 and taskId in (-2,-4,-6) 
             group by p.id order by p.id'''
    return db.dataframe(sql)


# @reportz(hours=1)
def gedaan_werk_tor():
    df = gedaan_werk_tor_table()
    return df['done'].sum()


# @reportz(hours=1)
def gedaan_werk_tor_dit_jaar():
    y = datetime.today().year
    sql = f'''select sum(done) from (
                select p.title, sum(hours*pu.hourlyRate) as done 
                from project p  
                join project_user pu on pu.projectId=p.id 
                join timesheet ts on ts.projectid=p.id and ts.user=pu.user 
                where customerId=125 and taskId in (-2,-4,-6) and ts.day>='{y}/1/1' 
                group by p.id
              ) q3'''

    return db.value(sql)


# @reportz(hours=1)
def invoiced_tor():
    sql = 'select sum(invoice_amount) from invoice i join project p on p.id=i.project_id where customerId=125'
    return db.value(sql)


# @reportz(hours=1)
def onderhanden_werk_tor():
    # Werk tellen we voor de helft mee. Werk van dit jaar zelfs vor 3/4 want het deel wat we activeren
    # telt ook mee, alleen niet van vorig jaar want dat telden we toen al met de winst mee.
    res = gedaan_werk_tor() / 2 + gedaan_werk_tor_dit_jaar() / 4 - invoiced_tor()
    return res


##### BEGROTE OMZET #####


@reportz(hours=24)
def omzet_begroot():
    ''' Begrote omzet tot en met vandaag. '''
    h = begroting_maandomzet(virtuele_maand())
    v = begroting_maandomzet(virtuele_maand() - 1)
    vd = virtuele_dag()  # Dag van de maand maar doorgeteld als de vorige maand nog niet is ingevuld in de boekhouding
    return v + vd / 30 * (h - v)


@reportz(hours=24)
def begroting_maandomzet(maand):
    ''' Begrote omzet van de meegegeven maand. Komt uit het begroting sheet. '''
    if maand == 0:
        return 0
    tab = sheet_tab(BEGROTING_SHEET, BEGROTING_TAB)
    return sheet_value(tab, BEGROTING_INKOMSTEN_ROW, maand + 2) * 1000


##### KOSTEN #####


def kosten_verschil_percentage():
    ''' Hoeveel de kosten percentueel hoger is dan begroot '''
    return 100 * kosten_verschil() / kosten_begroot()


def kosten_verschil():
    ''' Hoeveel de omzet boven de begrote kosten ligt. '''
    return kosten_werkelijk() - kosten_begroot()


def kosten_werkelijk():
    ''' De daadwerkelijk gerealiseerde kosten tot nu toe '''
    # a = kosten_boekhoudkundig_tm_vorige_maand()
    # b = kosten_begroot_deze_maand()
    # c = bonussen_tm_vorige_maand()
    return kosten_boekhoudkundig_tm_vorige_maand() + bonussen_tm_vorige_maand() + kosten_begroot_deze_maand()


def kosten_boekhoudkundig_tm_vorige_maand():
    ''' kosten t/m vorige maand zoals gerapporteerd in de boekhouding '''
    return laatste_maand_resultaat(RESULTAAT_BOEKHOUD_KOSTEN_ROW)


def bonussen_tm_vorige_maand():
    ''' Nog niet in de boekhouding verwerkte verwachte bonussen t/m vorige maand '''
    return (
        laatste_maand_resultaat(RESULTAAT_BONUSSEN_ROW)
        # + laatste_maand_resultaat(RESULTAAT_BONUSSEN_ROW + 1)
        # + laatste_maand_resultaat(RESULTAAT_BONUSSEN_ROW + 2)
    )


# @reportz(hours=24)
def kosten_begroot_deze_maand():
    ''' '''
    d = virtuele_dag()
    m = virtuele_maand()
    res = d / 30 * (kosten_begroot_tm_maand(m) - kosten_begroot_tm_maand(m - 1))
    return res


@reportz(hours=24)
def kosten_begroot_tm_maand(m):
    ''' Begrote kosten t/m maand m  '''
    if m == 0:
        return 0
    tab = sheet_tab(BEGROTING_SHEET, BEGROTING_TAB)
    res = sheet_value(tab, BEGROTING_KOSTEN_ROW, m + 2) * 1000
    return res


@reportz(hours=24)
def kosten_begroot():
    ''' Het begrote aantal kosten t/m nu '''
    res = kosten_begroot_tm_maand(virtuele_maand() - 1) + kosten_begroot_deze_maand()
    return res


##### WINST #####
def winst_verschil_percentage():
    ''' Hoeveel de winst percentueel hoger is dan begroot '''
    return 100 * winst_verschil() / winst_begroot()


def winst_verschil():
    ''' Hoeveel de winst boven de begrote winst ligt. '''
    return winst_werkelijk() - winst_begroot()


def winst_werkelijk():
    ''' De daadwerkelijk gerealiseerde kosten tot nu toe '''
    return opbrengsten() - kosten_werkelijk()


def winst_begroot():
    ''' De begrote winst tot nu toe '''
    return omzet_begroot() - kosten_begroot()


##### DIVERSEN #####


def vorige_maand():
    ''' Nummer van de vorige maand. '''
    return datetime.today().month - 1


def huidige_maand():
    ''' Nummer van de huidige maand. '''
    return datetime.today().month


def volgende_maand():
    ''' Nummer van de volgende maand. '''
    return datetime.today().month + 1


def virtuele_dag():
    ''' Als boekhouding van de vorige maand nog niet is bijgewerkt retourneert
        dit het dagnummer doorgenummerd vanuit de vorige maand. Dus 31, 32, 33, etc.
        Anders gewoon het dagnummer. '''
    vd = datetime.today().day
    if not bijgewerkt():
        vd += 30  # Gewoon in de vorige maand doortellen
    return vd


def virtuele_maand():
    ''' Als boekhouding van de vorige maand nog niet is bijgewerkt retourneert
        dit het nummer van vorige maand. Anders deze maand. '''
    vm = datetime.today().month
    if not bijgewerkt():
        vm -= 1  # We kijken nog naar vorige maand
    return vm


@reportz(hours=24)
def bijgewerkt():
    ''' Checkt in de Resultaat tab van het Keycijders sheet of de boekhouding van afgelopen
        maand al is ingevuld. '''
    tab = sheet_tab(BEGROTING_SHEET, RESULTAAT_TAB)
    vm = vorige_maand()
    data = sheet_value(tab, RESULTAAT_OMZET_ROW, vm + 2)
    return data


@reportz(hours=24)
def omzet_per_klant_laatste_zes_maanden():
    ''' Tabel van klantnaam, omzet '''
    query = '''select name as klant, ifnull(sum( invoice_amount),0) as omzet from invoice i, project p, customer c 
               where p.customerId=c.id and i.project_id=p.Id and invoice_date > date_add( curdate(), interval -6 MONTH) 
               group by c.id order by omzet desc'''
    df = db.dataframe(query)
    totaal = df['omzet'].sum()
    df['percentage'] = df['omzet'] * 100.0 / totaal
    return df


@reportz(hours=24)
def update_omzet_per_dag():
    ''' Tabel van dag, omzet '''
    trend_name = 'omzet_per_dag'
    last_day = trends.last_registered_day(trend_name)
    query = f'''select day, ifnull(round(sum(turnover)),0) as turnover from (select day, pu.user, hours*hourlyRate as turnover from timesheet ts
    join project_user pu on pu.projectId = ts.projectId and pu.user=ts.user
    where taskId=-2 and day > "{last_day}" and weekday(day)<5 and day < date_add( curdate(), interval -1 DAY)
    group by day, user) q1
    group by day
    order by day'''
    table = db.table(query)

    for rec in table:
        trends.update(trend_name, rec['turnover'], rec['day'])


# @reportz(hours=24)
def update_omzet_per_week():
    ''' Tabel van dag, omzet '''
    trend_name = 'omzet_per_week'
    last_day = trends.second_last_registered_day(trend_name)  # Always recalculate the last since hours may have changed
    query = f'''
    select min(day) as monday, round(sum(dayturnover)) as weekturnover from 
        (select day, sum(turnover) as dayturnover from
           (select day, pu.user, hours*hourlyRate as turnover 
            from timesheet ts
            join project_user pu on pu.projectId = ts.projectId and pu.user=ts.user
            where taskId=-2 and day>"{last_day}" and hours>0
            and day < DATE_SUB(curdate(), INTERVAL DAYOFWEEK(NOW())-1 DAY)
            group by day, user) q1
        group by day) q2
    group by year(day), week(day) 
    having weekday(monday)=0
    order by day'''
    table = db.table(query)

    for rec in table:
        trends.update(trend_name, rec['weekturnover'], rec['monday'])


def toekomstige_omzet_per_week():
    last_day = trends.last_registered_day('omzet_per_week')
    query = f'''
    select min(day) as monday, ifnull(round(sum(dayturnover)),0) as weekturnover from 
        (select day, sum(turnover) as dayturnover from
            (select date(startDate) as day, pl.name as user, 
                    least((enddate - startDate)/10000,8) * pu.hourlyRate as turnover
             from planning_reservation pr 
             join planning_location pl on pl.id=pr.planning_locationId
             join project p on p.id=pr.projectId
             join project_user pu on pu.projectId = p.id and pu.user=pl.name
             where startDate > "{last_day}" AND planning_typeId = '17' and p.customerId<>4) q1
        group by day) q2
    group by year(day), week(day) 
    having weekday(monday)=0 and monday>'2020/01/20'
    order by day'''
    table = db.table(query)
    return table


@reportz(hours=24)
def top_x_klanten_laatste_zes_maanden(number=3):
    # df = omzet_per_klant().copy(deep=True)
    return omzet_per_klant_laatste_zes_maanden().head(number)


@reportz(hours=24)
def debiteuren_leeftijd_analyse():
    query = 'select * from age_analysis_view order by 90plus desc, a90 desc, a60 desc'
    warnings.filterwarnings("ignore")
    return db.dataframe(query)


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


if __name__ == '__main__':
    update_omzet_per_week()
    print(debiteuren_leeftijd_analyse())
    print(debiteuren_30_60_90())
