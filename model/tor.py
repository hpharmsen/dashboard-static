from sources import database as db
from model.caching import reportz


@reportz(hours=24)
def tor_projecten():
    query = '''select id, title, budget, hours, sum(spent_per_user) as spent, sum(spent_per_user)/budget*100 as perc_spent from (
                    select p.id, title, budget, sum(hours) as hours, pu.hourlyRate * sum(hours) as spent_per_user
                    from project p 
                    join project_user pu on pu.projectId=p.id
                    join timesheet t on t.projectId=p.Id and t.user=pu.user
                    where p.title like 'TOR3%'
                    group by p.id, pu.user) q1
                group by id order by id'''

    return db.dataframe(query)


@reportz(hours=24)
def tor_per_maand():
    query = '''select concat(m,'/',y) as maand, sum(hours) as uren, sum(spent_per_user)as besteed, 
                      sum(spent_per_user)/4 tefactureren 
               from (
                    select year(day) as y, month(day) as m, sum(hours) as hours, pu.hourlyRate * sum(hours) as spent_per_user
                    from project p 
                    join project_user pu on pu.projectId=p.id
                    join timesheet t on t.projectId=p.Id and t.user=pu.user
                    where p.title like 'TOR3%'
                    group by p.id, pu.user, year(day), month(day)) q1
               group by y,m order by y,m'''
    return db.dataframe(query)


@reportz(hours=24)
def tor_facturen():
    query = 'select invoice_id as id, DATE_FORMAT(invoice_date, "%d-%m-%y") as date, invoice_amount as amount, status from invoice where project_id=1712'
    return db.dataframe(query)


@reportz(hours=24)
def tor_total_budget():
    return tor_projecten()['budget'].sum()


@reportz(hours=24)
def tor_total_spent():
    return tor_projecten()['spent'].sum()


@reportz
def tor_perc_spent():
    return tor_total_spent() / tor_total_budget() * 100
