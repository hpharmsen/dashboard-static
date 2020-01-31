import os
from datetime import datetime

from sources.googlesheet import sheet_tab, sheet_value, to_int
from model.caching import reportz
from sources import database as db

SERVICETEAM = ('chin', 'gijs', 'vincent', 'caspar')
UURLOON = 90
BASE_QUERY = '''select SUM(CASE WHEN taskId=-2  and project_type='service' THEN hours END) AS bill, 
                       SUM(CASE WHEN taskId not in (-2,21,22) THEN hours END) AS nonb, 
                       SUM(CASE WHEN taskId in (21,22) or (taskId=-2 and project_type != 'service') THEN hours END) AS prj 
                from timesheet t, project p 
                where t.projectId = p.id'''


@reportz(hours=24)
def omzet_op_service_projecten():
    y = datetime.today().year
    query = f'''select sum(turnover) from (
                    select sum(hours)*pu.hourlyRate as turnover
                    from project p, project_user pu, timesheet ts
                    where p.id=pu.projectId and ts.projectId=p.id and ts.user=pu.user 
                    and project_type='service' and year(day) = {y} and taskId=-2
                    group by p.id, pu.user
                ) q1'''
    return db.value(query)


@reportz(hours=24)
def service_omzet_door_serviceteam():
    y = datetime.today().year
    query = f'''select sum(turnover) from (
                    select sum(hours)*pu.hourlyRate*(1+management_costs/100) as turnover
                    from project p, project_user pu, timesheet ts
                    where p.id=pu.projectId and ts.projectId=p.id and ts.user=pu.user 
                    and project_type='service' and year(day) = {y} and taskId=-2 
                    and pu.user in ('aafke','gijs','tim','vincent','gijs','caspar')
                    group by p.id, pu.user
                ) q1'''
    return db.value(query)


@reportz(hours=24)
def service_omzet_per_persoon():
    y = datetime.today().year
    query = f'''select user, sum(turnover) as turnover from (
                    select pu.user, sum(hours)*pu.hourlyRate*(1+management_costs/100) as turnover
                    from project p, project_user pu, timesheet ts
                    where p.id=pu.projectId and ts.projectId=p.id and ts.user=pu.user 
                    and project_type='service' and year(day) = {y} and taskId=-2 
                    group by p.id, pu.user
                ) q1
                group by user 
                order by turnover desc
                limit 0,10'''
    return db.dataframe(query)


def zero_if_empty(s):
    if not s:
        return 0
    return to_int(s)


@reportz(hours=24)
def service_omzet_persoon_maand():
    tab = sheet_tab("Serviceteam KPI's", 'Cijfers')
    users = []
    data = []
    for idx, col in enumerate((11, 17, 23, 30, 36, 43)):  # Columns with the turnover per user
        data += [[]]
        user = sheet_value(tab, 5, col)
        users += [user]  # Name of the user
        for month in range(12):  # Values per month
            try:
                v = sheet_value(tab, month + 6, col)
                data[idx] += [zero_if_empty(v)]
            except:
                data[idx] = 'ERR'  #!!
    return users, data


@reportz(hours=24)
def service_billable_perc_laatste_30_dagen():
    query = BASE_QUERY + f'''  and day > CURDATE() - INTERVAL 30 DAY and user in {SERVICETEAM}'''
    res = db.table(query)[0]
    return 100 * (1.1 * res['bill'] + res['prj']) / (res['bill'] + res['nonb'] + res['prj'])


@reportz(hours=24)
def service_billable_perc_jaar():
    y = datetime.today().year
    query = (
        BASE_QUERY
        + f''' and year(day) = {y} and (user in {SERVICETEAM} or user in ('tim','aafke')) and user !='chin' '''
    )
    res = db.table(query)[0]
    return 100 * (1.1 * res['bill'] + res['prj']) / (res['bill'] + res['nonb'] + res['prj'])


@reportz(hours=24)
def service_omzet():
    y = datetime.today().year
    query = (
        BASE_QUERY
        + f''' and year(day) = {y} and (user in {SERVICETEAM} or user in ('tim','aafke')) and user !='chin' '''
    )
    res = db.table(query)[0]
    print('billable', res['bill'])
    print('projecten', res['prj'])
    return UURLOON * (1.1 * res['bill'] + res['prj'])


@reportz(hours=60)
def service_klanten():
    y = datetime.today().year
    query = f'''select name, title, round(b) as billable, round(tt) as total, round(tu) as turnover, round(tu/tt) as hourly 
                from (
                    select name, title, SUM(CASE WHEN taskId=-2 THEN hours END) AS b, SUM(hours) AS tt, 
                           SUM(CASE WHEN taskId=-2 THEN hours END)*pu.hourlyRate*(1 + management_costs/100) as tu 
                    from timesheet ts 
                    join project p on ts.projectId=p.Id 
                    join customer c on p.customerId=c.Id 
                    join project_user pu on pu.projectId=p.Id and ts.user=pu.user 
                    where year(day)={y} and project_type='service' 
                    group by p.id) as q1 
                where tt>10 order by hourly desc'''
    return db.dataframe(query)


if __name__ == '__main__':
    os.chdir('..')
    print(service_omzet_persoon_maand())
