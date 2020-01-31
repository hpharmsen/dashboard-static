from sources import database as db


def users_and_targets(year):
    sql = f'''select t.user, target, sum(hours) as result
              from target t
              join timesheet ts on ts.user=t.user 
              join project p on p.id=ts.projectId
              where year(ts.day)='{year}' and t.year='{year}' and taskId in (-2,-6) and customerId<>4
              group by t.user
           '''
    return db.dataframe(sql)
