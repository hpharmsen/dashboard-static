from pandas import DataFrame

from middleware.base_table import BaseTable, SIMPLICATE_ID, MONEY
from middleware.middleware_utils import singleton
from model.utilities import Day
from sources.simplicate import simplicate


@singleton
class Service(BaseTable):
    def __init__(self):
        self.table_name = 'service'
        self.table_definition = f"""
               service_id {SIMPLICATE_ID} NOT NULL,
               service_name VARCHAR(80) NOT NULL,
               project_id {SIMPLICATE_ID} NOT NULL,
               status varchar(20) NOT NULL,
               invoice_method varchar(20) NOT NULL,
               service_costs {MONEY} NULL,
               price {MONEY} NULL,
               start_date DATETIME,
               end_date DATETIME,
            """
        self.primary_key = 'service_id'
        self.index_fields = 'project_id start_date end_date status'
        super().__init__()

    def update(self):
        self._create_project_table(force_recreate=1)
        sim = simplicate()
        services = []

        # Get the list of services
        services_json = sim.service({"track_hours": True})

        # status != "flushed"' is een beetje tricky want er is geen mogeljkheid om te achterhalen
        # wat de status was op de opgegeven datum. Eens flushed, altijd flushed dus.
        # Een beetje geschiedvervalsing wellicht?
        status_query = 'invoice_method != "Subscription" & status != "flushed"'
        # start_date en end_date worden slecht bijgehouden dus daar hebben we ook niks aan
        # behalve dan dat we dingen eruit kunnen filteren die echt te oud zijn, of nog niet begonnen
        # end_date != end_date is a construct to check for NaN
        status_query += f' & (end_date != end_date | end_date > "2021-01-01")'
        status_query += f' & (start_date != start_date | start_date <= "{Day()}")'

        # Add up expenses per service and save them in service_costs field in the json
        for service in services_json:
            service_costs = 0
            for cost_type in service.get("cost_types", []):
                service_costs += cost_type["purchase_tariff"]
            service["service_costs"] = service_costs

        p = sim.to_pandas(services_json)
        df: DataFrame = (
            sim.to_pandas(services_json)
                .query(status_query)[
                ["id", "name", "project_id", "status", "invoice_method", "service_costs", "price", "start_date",
                 "end_date"]
            ]
                .rename(columns={"id": "service_id", "name": "service_name"})
        )  # end_date > "{date}" &

        self.insert_dicts(df.to_dict('records'))


if __name__ == '__main__':
    service_table = Service()
    service_table.update()
