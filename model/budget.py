import os
from datetime import datetime
from sources import database as db
from model.caching import reportz

# @reportz(hours=24)
def project_budget_status():
    y = datetime.today().year
    y = 2020  ## Laatste jaar van Oberview
    sql = f'''select p.id as id, name, title, pm, project_type, sum(hours) as hours, budget, budget_correction_amount, 
                    budget_correction_description, COALESCE(invoiced,0) as invoiced, ifnull(DATE_FORMAT(p.last_invoice_date, '%Y/%m/%d'),'') as last_invoice
            from project p 
            join customer c on c.id=p.customerId
            left join timesheet ts on ts.projectId=p.id
            left join (select project_id, sum(invoice_amount) as invoiced
                       from invoice 
                       group by project_id) q2 on q2.project_id=p.id
            where p.project_type != 'hosting' and (p.project_type!='uurbasis' or p.phase=90) and year={y}
              and not c.id in (4,125,225) and (p.last_invoice_date is null or ts.day is null or ts.day<p.last_invoice_date)
            group by p.id
            order by name, title'''
    projects = db.table(sql)
    for project in projects:
        if project['project_type'] != 'fixed':
            only_before_last_invoice = (
                f' and (p.phase=90 or day<="{project["last_invoice"]}")' if project['last_invoice'] else ''
            )

            sql = f'''select ifnull(sum(normalBudget),0)+ifnull(sum(criticalBudget),0) from (
                        select pu.hourlyRate *  sum(if(taskId!=-6,hours,0)) as normalBudget, 
                               pu.hourlyRateCritical * sum(if(taskId=-6,hours,0)) as criticalBudget
                        from project_user pu 
                        left join timesheet ts on ts.projectId=pu.projectId and ts.user=pu.user
                        left join project p on p.id=pu.projectId
                        where pu.projectId={project['id']} and taskId in (-2,-4,-6) {only_before_last_invoice}
                        group by pu.user ) q2
            '''
            project['budget'] += db.value(sql)
        project['budget_status'] = project['invoiced'] - project['budget'] - project['budget_correction_amount']
        try:
            project['budget_status_perc'] = (
                100 * project['budget_status'] / (project['budget'] + project['budget_correction_amount'])
            )
        except:
            project['budget_status_perc'] = 0
        if not project['budget_correction_description']:
            project['budget_correction_description'] = ''
        try:
            project['last_inv'] = (
                project['last_invoice'][8:10] + '-' + project['last_invoice'][5:7] + '-' + project['last_invoice'][0:4]
            )  # .strftime( '%d-%m-%Y')
        except:
            project['last_inv'] = '-'
        # del project['last_invoice']
    return projects


if __name__ == '__main__':
    os.chdir('..')
    for p in project_budget_status():
        print(
            p['name'],
            p['title'],
            'budget:',
            p['budget'],
            'invoiced:',
            p['invoiced'],
            'budget_status:',
            round(p['budget_status']),
            f"{round(p['budget_status_perc'])}%",
        )
