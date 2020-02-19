from sources import database as db


def users_and_targets(year, specific_users=None):
    if specific_users:
        users_list = '"' + '","'.join(specific_users) + '"'
        user_constraint = f'and t.user in ({users_list}) '
    else:
        user_constraint = ''
    sql = f'''select t.user, target, sum(hours) as result,  min(day) as start_day
              from target t
              join timesheet ts on ts.user=t.user 
              join project p on p.id=ts.projectId
              where year(ts.day)='{year}' and t.year='{year}' and taskId in (-2,-6) and customerId<>4 {user_constraint}
              group by t.user
           '''
    return db.dataframe(sql)
