import os
from datetime import datetime, timedelta

from model.utilities import fraction_of_the_year_past
from sources.googlesheet import sheet_tab, sheet_value
from sources import database as db
from sources.simplicate import hours_dataframe
from model.caching import reportz

FTE_SHEET = 'Begroting 2020'
FTE_TAB = 'Personeelsplanning'
FTE_ROW = 30
FTE_START_COL = 4


@reportz(hours=168)
def aantal_mensen(hours=168):
    tab = sheet_tab('Contracten werknemers', 'stats')
    return sheet_value(tab, 2, 6)


@reportz(hours=168)
def aantal_fte():
    tab = sheet_tab('Contracten werknemers', 'stats')
    return sheet_value(tab, 3, 6)


@reportz(hours=168)
def aantal_fte_begroot():
    tab = sheet_tab(FTE_SHEET, FTE_TAB)
    m = datetime.today().month
    res = sheet_value(tab, FTE_ROW, FTE_START_COL + m - 1)
    return res


def verzuimpercentage(days=91):
    DATE_FORMAT = '%Y-%m-%d'
    from_day = max('2021-01-01', (datetime.today() + timedelta(days=-90)).strftime(DATE_FORMAT))

    full_df = hours_dataframe()
    verzuim = full_df.query(f'type=="absence" and day >="{from_day}"')['hours'].sum()
    normal = full_df.query(f'type=="normal" and day >="{from_day}"')['hours'].sum()
    percentage = 100 * verzuim / (normal + verzuim)
    return percentage


@reportz(hours=24)
def vrije_dagen_pool():
    y = datetime.today().year
    left_over_from_last_year = db.value(f'select sum(amount) from freedays where type="end" and year={y-1}')
    free_days_for_this_year = db.value(f'select sum(amount) from freedays where type="start" and year={y}')
    beschikbaar_hele_jaar = int(free_days_for_this_year + left_over_from_last_year)
    daadwerkelijk_opgemaakt = db.value(
        f'''SELECT sum(if( name like "%(Dag vrij)", 1, if(name like "%(Halve dag vrij)", .5, 0))) as opgemaakt
                             FROM planning_reservation
                             WHERE planning_typeId = '18' and year(startDate)={y}  and startdate<NOW() and planning_locationId is not null'''
    )
    normaal_gesproken_opgemaakt = int(beschikbaar_hele_jaar * fraction_of_the_year_past())
    pool = (normaal_gesproken_opgemaakt - daadwerkelijk_opgemaakt) / aantal_fte()
    # print( 'beschikbaar',beschikbaar )
    # print( 'normaal', normaal)
    # print( 'pool', pool)
    return pool


#
# @reportz
# def geboekte_uren_productie():
#     y = datetime.today().year
#     query = f'''select sum(hours) as hours
#                 from timesheet ts, planning_location pl
#                 where year(day) = {y} and pl.name = ts.user and planning_locationGroupId in (2, 3, 4, 6, 8, 9, 13)'''
#     return db.value(query)
#
#
# @reportz
# def geboekte_uren_totaal():
#     y = datetime.today().year
#     query = f'''select sum(hours) as hours from timesheet where year(day)={y}'''
#     return db.value(query)
#
#
# @reportz
# def billable_uren_productie():
#     y = datetime.today().year
#     query = f'''select sum(hours) from timesheet ts, project p, planning_location pl
#                 where ts.projectId=p.id and pl.name=ts.user and internal=0 and year(day)={y}
#                   and ts.taskId in (-6,-4,-2,2,3,4,5,7,8,21,22) and planning_locationGroupId in (2,3,4,6,8,9,13)'''
#     return db.value(query)
#
#
# @reportz
# def billable_uren_totaal():
#     y = datetime.today().year
#     query = f'''select sum(hours) from timesheet ts, project p
#                 where ts.projectId=p.id and internal=0 and year(day)={y} and ts.taskId in (-6,-4,-2,3,4,5,6,7,8,21,22)'''
#     return db.value(query)
#
#
# @reportz
# def bezettingsgraad_productie():
#     return 100.0 * billable_uren_productie() / geboekte_uren_productie()
#
#
# @reportz
# def bezettingsgraad_totaal():
#     return 100.0 * billable_uren_totaal() / geboekte_uren_totaal()
#
#
# @reportz
# def mensen_in_productie():
#     query = 'select count(*) from planning_location pl join planning_locationgroup plg on plg.id=pl.planning_locationGroupId'
#     return db.value(query)
#
#
# @reportz
# def productiedagen_per_maand():
#     dagen_per_maand = 45 * 5 / 12
#     productie_percentage = aantal_fte() / aantal_mensen() * 0.85  # ObSessions
#     return mensen_in_productie() * dagen_per_maand * productie_percentage

if __name__ == '__main__':
    os.chdir('..')
    print(vrije_dagen_pool())
