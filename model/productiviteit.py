from datetime import datetime
from sources import database as db
from model.caching import reportz
from sources.googlesheet import sheet_tab, to_int
from model.trendline import trends

special_oberon_project_ids = (1536, 1429, 1711)  # Oberview, Serverbeheer, Oberon website

# Hours and budgets realised per year, project, task for a specific user.
taskProjectSql = '''SELECT ts.user, ts.projectId, c.name AS client, p.title AS project, t.id AS taskId, t.name AS task,  IF( tp.budget >0, tp.budget, IFNULL(pu.hourlyRate,p.hourlyrate) * SUM( hours ) ) AS budget, 
GREATEST(0,SUM( hours )-ifnull(tp.research,0)) AS hours, tp.research, YEAR( ts.day ) AS bookyear, p.completedPerc, p.hourlybasis, IFNULL(pu.hourlyRate,p.hourlyrate) as hourlyrate 
FROM timesheet ts
LEFT JOIN task t ON t.id = ts.taskid 
JOIN project p ON p.id = ts.projectid AND (p.internal = 0 OR p.id in %(special_project_ids)s)
LEFT JOIN customer c ON c.id = p.customerId
left join task_project tp on tp.taskid=ts.taskid AND ts.user = tp.user and tp.projectid=p.id
left join project_user pu on pu.projectId=p.id and pu.user=ts.user
WHERE ts.user = '%(user)s'
AND (YEAR(ts.day)=%(year)s or YEAR(ts.day)=%(year)s-1)
GROUP BY ts.projectId, ts.taskId, bookyear
ORDER BY client, project, ts.taskId, bookyear'''


def calculate(user, year):
    # Return variables
    result_tasks = []
    sumhours = 0.0
    sumbudget = 0.0
    warnings = []
    lastProjectId = -1  #!!
    lastTaskId = -1  #!!

    special_oberon_tasks = []
    sql = taskProjectSql % {'year': year, 'user': user, 'special_project_ids': special_oberon_project_ids}
    clientdata = db.table(sql)

    hoursLastYear = 0
    for task in clientdata:
        if task['bookyear'] == year - 1:
            # Special case, this project is partly in the last year.
            hoursLastYear = task['hours']
            lastProjectId = task['projectId']
            lastTaskId = task['taskId']
            continue

        if task['projectId'] in special_oberon_project_ids and task['hourlybasis'] == 1:
            # Oberview of serverbeheer. Deze doen we apart want we rekenen hier het gemiddelde uurloon van de huidige user voor.
            special_oberon_tasks += [task]
            continue

        if (
            hoursLastYear
            and lastProjectId == task['projectId']
            and lastTaskId == task['taskId']
            and task['taskId'] != -2
            and task['hourlybasis'] != 1
        ):
            # Ok, part of the hours was booked last year so reduce the budget for this year, o and task is not "Billable"
            ratioHoursThisYear = task['hours'] / (hoursLastYear + task['hours'])
            task['budget'] = task['budget'] * ratioHoursThisYear
            hoursLastYear = 0  # reset

        # With hourly basis tasks, every hour counts so budget is hours * hourly rate
        if task['hourlybasis'] == 1:
            task['budget'] = task['hours'] * task['hourlyrate']

        # If the project is not yet finished this year. Reduce the budget
        elif task['completedPerc']:
            task['budget'] = task['budget'] * task['completedPerc'] * 0.01

        # Calculate hourly turnover for this task
        task['hourly'] = task['hours'] > 0 and task['budget'] / task['hours'] or 0

        # Add to the total hours
        sumhours += task['hours']

        # if not task['taskId'] in [-3, -5]:  # Non billable en reistijd
        #    sumbudget += task['budget']

        if (
            task['hours'] >= 8 and not task['budget'] and task['taskId'] not in [-1, -3, -5, 1]
        ):  # -1 = Bugfixing/onvoorzien -3 = Non billabla, 1 = Sales
            warnings += [
                '{client} - {project} ({projectId}) - {task} has no budget. {hours} hours for '.format(**task) + user
            ]

        if task['hours'] >= 4 or task['budget'] > 400:  # Ignore tasks that are too small

            if task['budget'] <= 1 or task['taskId'] in [-3, -5]:  # Non billable en reistijd
                task['budget'] = 0
                task['hourly'] = 0
            result_tasks += [task]
            sumbudget += task['budget']

    # OK, and now the same trick for Serverbeheer and Oberview
    average = sumbudget / sumhours if sumhours > 0 else 0
    for task in special_oberon_tasks:
        task['hourly'] = average
        task['budget'] = task['hours'] * average * 0.8  # We count internal projects for 80%
        sumhours += task['hours']
        result_tasks += [task]
        sumbudget += task['budget']

        b = sum([task['budget'] for task in result_tasks])
        if b != sumbudget:
            pass
    return (result_tasks, sumbudget, sumhours, warnings)


@reportz(hours=24)
def productiviteit_persoon(user):
    y = datetime.today().year
    res = []
    result_tasks, sumbudget, sumhours, warnings = calculate(user, y)
    b = sum([task['budget'] for task in result_tasks])
    if b != sumbudget:
        pass
    for line in result_tasks:
        res += [[line['client'], line['project'], line['task'], line['budget'], line['hours'], line['hourly']]]
    return res


@reportz(hours=24)
def tuple_of_productie_users():
    return [
        rec['name']
        for rec in db.table(
            'select name from planning_location where searchOrder>0 order by planning_locationGroupId, searchOrder'
        )
    ]


@reportz(hours=24)
def productiviteit_overzicht():
    y = datetime.today().year
    res = []
    for user in tuple_of_productie_users():
        tasks, budget, hours, allwarnings = calculate(user, y)
        if geboekte_uren_user(user):
            besch = geboekte_uren_user(user) * 0.85
            prod = geboekte_uren_user(user)  # TODO: Deze kloppen nog niet !!
            bill = geboekte_uren_user(user, billable=1)
            perc_productief = prod / besch * 100
            perc_billable = bill / besch * 100
        else:
            besch = prod = bill = 0
            perc_productief = perc_billable = 0
        res += [
            [user, budget, hours, budget / hours if hours else 0, besch, prod, perc_productief, bill, perc_billable]
        ]
    return sorted(res, key=lambda a: a[1], reverse=True)


@reportz(hours=24)
def cijfers_werknemers_value(user, key):
    tab = sheet_tab('Cijfers werknemers 2019', '2019')
    col = tab[0].index(key)
    rows = [r for r in tab if r[0] == user]
    if not rows:
        return 0
    target = rows[0][col]
    if not target:
        return 0
    return to_int(target.replace(',', '.'))


def user_target(user):
    return cijfers_werknemers_value(user, 'Target jaar')


# @reportz(hours=24)
def fraction_of_the_year_past(start_day=None):
    if start_day:
        start_date_time = datetime.combine(start_day, datetime.min.time())
    else:
        y = datetime.today().year
        start_date_time = datetime(y, 1, 1)
    days_in_the_year = (datetime.today() - start_date_time).days + 1
    return days_in_the_year / 365


def user_target_now(user):
    return fraction_of_the_year_past() * user_target(user)


########## UREN ############
BILLABLE_TASKS = (-6, -4, -3, -2, -1, 2, 3, 4, 5, 6, 7, 21, 22)


@reportz(hours=2)
def geboekte_uren(only_productie_users=0, only_clients=0, billable=0, fromdate=None, untildate=None):
    sql = f'select user, sum(hours) as hours from timesheet ts, project p where ts.projectId=p.id'
    if only_productie_users:
        sql += f' and user in {tuple(tuple_of_productie_users())}'
    if only_clients:
        sql += ' and internal=0'
    if billable:
        sql += f' and taskId in {BILLABLE_TASKS}'
    if fromdate:
        sql += f''' and day>="{fromdate.strftime('%Y/%m/%d')}"'''
        if untildate:
            sql += f''' and day<="{untildate.strftime('%Y/%m/%d')}"'''
    else:
        sql += f' and year(day)={datetime.today().year}'
    sql += ' group by user'
    return db.dataframe(sql)


@reportz(hours=2)
def geboekte_uren_user(user, only_clients=0, billable=0, fromdate=None, untildate=None):
    y = datetime.today().year
    sql = f'select COALESCE(SUM(hours),0) as hours from timesheet where user="{user}"'
    if only_clients:
        sql += ' and internal=0'
    if billable:
        sql += f' and taskId in {BILLABLE_TASKS}'
    if fromdate:
        sql += f''' and day>="{fromdate.strftime('%Y/%m/%d')}"'''
        if untildate:
            sql += f''' and day<="{untildate.strftime('%Y/%m/%d')}"'''
    else:
        sql += f' and year(day)={datetime.today().year}'
    return db.value(sql)


######### BESCHIKBAAR ##########


# def beschikbare_uren(productie_users=0):
#     y = datetime.today().year
#     sql = f'select user, 0.85 * sum(hours) as hours from timesheet where year(day)={y}'
#     if productie_users:
#         sql += ' and user in {tuple(productie_users())}'
#     sql += ' group by user'
#     return db.dataframe(sql)


# def beschikbare_uren_persoon(user):
#    df = geboekte_uren()
#    return int(df.loc[df['user'] == user]['hours'])


@reportz(hours=24)
def beschikbare_uren_productie(fromdate=None, untildate=None):
    df = geboekte_uren(only_productie_users=1, fromdate=fromdate, untildate=untildate)
    return df['hours'].sum() * 0.85


@reportz(hours=24)
def beschikbare_uren_iedereen(fromdate=None, untildate=None):
    df = geboekte_uren(only_productie_users=0, fromdate=fromdate, untildate=untildate)
    return df['hours'].sum() * 0.85


###### PRODUCTIEF ############
# def productieve_uren_persoon(user):
#    df = geboekte_uren(productie_users=0, billable=0)
#    return df.loc[df['user'] == user]['hours']


@reportz(hours=2)
def productieve_uren_productie(fromdate=None, untildate=None):
    df = geboekte_uren(only_productie_users=1, only_clients=1, fromdate=fromdate, untildate=untildate)
    return df['hours'].sum()


@reportz(hours=2)
def productieve_uren_iedereen(fromdate=None, untildate=None):
    df = geboekte_uren(only_productie_users=0, only_clients=1, fromdate=fromdate, untildate=untildate)
    return df['hours'].sum()


########## BILLABLE ############

# def billable_uren_persoon(user):
#    df = geboekte_uren(productie_users=1, billable=1)
#    return df.loc[df['user'] == user]['hours']


@reportz(hours=2)
def billable_uren_productie(fromdate=None, untildate=None):
    df = geboekte_uren(only_productie_users=1, only_clients=1, billable=1, fromdate=fromdate, untildate=untildate)
    return df['hours'].sum()


@reportz(hours=2)
def billable_uren_iedereen(fromdate=None, untildate=None):
    df = geboekte_uren(only_productie_users=0, only_clients=1, billable=1, fromdate=fromdate, untildate=untildate)
    return df['hours'].sum()


# Percentages


def productiviteit_perc_productie(fromdate=None, untildate=None):
    return 100 * productieve_uren_productie(fromdate, untildate) / beschikbare_uren_productie(fromdate, untildate)


def billable_perc_productie(fromdate=None, untildate=None):
    return 100 * billable_uren_productie(fromdate, untildate) / beschikbare_uren_productie(fromdate, untildate)


def productiviteit_perc_iedereen(fromdate=None, untildate=None):
    return 100 * productieve_uren_iedereen(fromdate, untildate) / beschikbare_uren_iedereen(fromdate, untildate)


def billable_perc_iedereen(fromdate=None, untildate=None):
    res = 100 * billable_uren_iedereen(fromdate, untildate) / beschikbare_uren_iedereen(fromdate, untildate)
    trends.update('billable_hele_team', round(res, 1))
    return res


@reportz(hours=48)
def billable_trend_person(user):
    # Aantal billable uren per week gemeten in timeslots van twee weken van 26 weken geleden tot aan nu
    sql = f'''select date_add( curdate(), interval -slot*14-7 DAY) as datum, ifnull(amount/2,0) as hours from 
                (select 12 as slot union all select 11 union all select 10 union all select 9 union all 
                 select 8 union all select 7 union all select 6 union all select 5 union all select 4 union all 
                 select 3 union all select 2 union all select 1 union all select 0) as slots
              left join (
                select datediff(now(), day) DIV 14 as timegroup, sum(hours) as amount
                from timesheet ts
                join project p on p.id=ts.projectId
                where day<=now() 
                  and datediff(now(), day) < 26*7 
                  and user='{user}'
                  and (taskId=-2 
                    or taskId=-6 
                    or (p.project_type='fixed' and p.customerId!=4)
                      )
                group by timegroup) timegroups 
              on timegroups.timegroup = slots.slot'''
    return db.table(sql)


# @reportz(hours=48)
def billable_trend_person_week(user):
    # Aantal billable uren per weeknummer
    sql = f'''
            select year(day) as year, week(day) as weekno, sum(hours) as hours
            from timesheet ts
            where taskId in (-2,-4,-6) and day > DATE_SUB(curdate(), INTERVAL 6 MONTH) and ts.user='{user}'
            group by week(day) '''
    res = db.table(sql)
    res_rec = {r['weekno']: r['hours'] for r in res}
    curweek = int(datetime.now().strftime('%V'))
    if curweek >= 26:
        weeks = range(curweek - 26, curweek)
    else:
        weeks = list(range(curweek + 26, 53)) + list(range(1, curweek))
    res = [{'weekno': week, 'hours': res_rec.get(week, 0)} for week in weeks]
    return res


def weekno_to_date(rec):
    d = f"{rec['year']}-W{rec['weekno']}-1"
    rec['date'] = datetime.strptime(d, '%G-W%V-%u').strftime('%Y-%m-%d')
    return rec


if __name__ == '__main__':
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
