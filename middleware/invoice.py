""" Handles the Invoice class and invoice table """
from functools import partial

from middleware.base_table import BaseTable, PROJECT_NUMBER, SIMPLICATE_ID, HOURS, MONEY
from middleware.middleware_utils import singleton
from model.utilities import flatten_json, Period, Day
from sources.simplicate import simplicate


# @cache(hours=1)
def sim_invoices(day: Day):
    sim = simplicate()
    invoices = sim.invoice({"from_date": day})
    return invoices


@singleton
class Invoice(BaseTable):
    def __init__(self):
        self.table_name = 'invoice'
        self.table_definition = f'''
               invoice_number VARCHAR(20) NOT NULL,
               invoice_date DATETIME NOT NULL,
               organization VARCHAR(80) NOT NULL,
               project_number {PROJECT_NUMBER} NULL,
               service_id {SIMPLICATE_ID} NULL,
               description VARCHAR(120) NULL,
               amount {HOURS} DEFAULT 1.0,
               price {MONEY} NOT NULL,
            '''
        self.primary_key = ''
        self.index_fields = 'invoice_number invoice_date organization project_number'
        super().__init__()

    def update(self, day: Day):
        get_day_data = partial(self.get_data, day)
        self.db.execute(f'delete from invoice where invoice_date >= "{day}"')
        self.db.commit()
        self.insert_dicts(get_day_data)

    def get_data(self, day=None):
        if not day:
            day = Day('2021-01-01')  # For repopulate
        invoices = sim_invoices(day=day)
        for invoice in invoices:
            invoice_number = invoice.get("invoice_number")
            if not invoice_number:
                continue  # conceptfactuur
            print('Updating', invoice_number, invoice["organization"]["name"])
            for invoice_line in invoice["invoice_lines"]:
                line = flatten_json(invoice_line)

                # Probeer project en project_number op te halen
                project = invoice.get('project')
                if not project:
                    projects = invoice.get('projects')
                    if projects:
                        project = projects[0]
                project_number = project['project_number'] if project else None

                # We gaan uit van de service_id is die er niet, neem project_number
                service_id = line.get("service_id", project_number)

                yield {
                    'invoice_number': invoice_number,
                    'invoice_date': invoice['date'],
                    'organization': invoice["organization"]["name"],
                    'project_number': project_number,
                    'service_id': service_id,
                    'description': line['description'],
                    'amount': line['amount'],
                    'price': line['price']}


    def lines(self, period: Period):
        query = f'''select * from invoice 
                    where invoice_date >= "{period.fromday}" and invoice_date < "{period.untilday}"
                    group by invoice_number order by invoice date'''
        result = self.db.execute(query)
        return result


    def invoices(self, period: Period):
        query = f'''select invoice_number, invoice_date, organization, project_number, sum(amount*price) as invoice_amount 
                    from invoice
                    where invoice_date >= "{period.fromday}" and invoice_date < "{period.untilday}"
                    group by invoice_number order by invoice_date'''
        result = self.db.execute(query)
        return result

    def invoiced_per_customer(self, period: Period):
        query = f'''select organization, sum(amount*price) as invoiced 
                    from invoice
                    where invoice_date >= "{period.fromday}" and invoice_date < "{period.untilday}"
                    group by organization order by organization'''
        result = self.db.execute(query)
        return result

    def invoiced_per_service(self, period: Period):
        query = f'''select service_id, sum(amount*price) as invoiced 
                    from invoice
                    where invoice_date >= "{period.fromday}" and invoice_date <= "{period.untilday}"
                    group by service_id'''
        result = self.db.execute(query)
        return result


if __name__ == '__main__':
    invoice = Invoice()
    # day = Day('2021-12-31')
    # invoice.update(day)
    invoice.repopulate()
    # invoice.update(Day().plus_days(-7))
    # period = Period( Day().plus_days(-7), Day())
    # invoices = invoice.invoices(period)
    # for inv in invoices:
    #     print( inv )
