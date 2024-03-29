import pandas as pd
from pandas import DataFrame

from middleware.base_table import BaseTable, SIMPLICATE_ID, MONEY
from middleware.middleware_utils import singleton
from model.utilities import Day
from sources.simplicate import simplicate


@singleton
class Service(BaseTable):
    def __init__(self):
        super().__init__()
        self.table_name = "service"
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
        self.primary_key = "service_id"
        self.index_fields = "project_id start_date end_date status"

    def get_data(self):
        sim = simplicate()

        # Get the list of services
        services_json = sim.service({"track_hours": True})

        for service in services_json:

            # status != "flushed"' is een beetje tricky want er is geen mogeljkheid om te achterhalen
            # wat de status was op de opgegeven datum. Eens flushed, altijd flushed dus.
            # Een beetje geschiedvervalsing wellicht?
            if (
                service["invoice_method"] == "Subscription"
                or service["status"] == "flushed"
            ):
                continue

            # start_date en end_date worden slecht bijgehouden dus daar hebben we ook niks aan
            # behalve dan dat we dingen eruit kunnen filteren die echt te oud zijn, of nog niet begonnen
            if service.get("end_date") and service["end_date"] <= "2021-01-01":
                continue
            if service.get("start_date") and service["start_date"] > Day():
                continue

            # Selecteer de velden die we nodig hebben
            fields = [
                "project_id",
                "status",
                "invoice_method",
                "price",
                "start_date",
                "end_date",
            ]
            res = {key: service.get(key) for key in fields}
            res["service_id"] = service["id"]
            res["service_name"] = service["name"]

            # Add up expenses per service and save them in service_costs field in the json
            service_costs = 0
            for cost_type in service.get("cost_types", []):
                service_costs += cost_type["purchase_tariff"]
            res["service_costs"] = service_costs

            yield res

        # df: DataFrame = (
        #     sim.to_pandas(services_json)
        #         .query(status_query)[
        #
        #     ]
        #         .rename(columns={"id": "service_id", "name": "service_name"})
        # )  # end_date > "{date}" &
        #
        # self.insert_dicts(df.to_dict('records'))

    def projects_and_services(self, day: Day) -> DataFrame:

        # status != "flushed"' is een beetje tricky want er is geen mogeljkheid om te achterhalen
        # wat de status was op de opgegeven datum. Eens flushed, altijd flushed dus.
        # Een beetje geschiedvervalsing wellicht?
        # start_date en end_date worden slecht bijgehouden dus daar hebben we ook niks aan
        # behalve dan dat we dingen eruit kunnen filteren die echt te oud zijn, of nog niet begonnen
        query = f"""select s.*, p.project_number, project_name, `organization`, pm, project_costs,
                        sum(hours) as hours, sum(turnover) as turnover  
                    from service s
                    join project p on p.project_id=s.project_id
                    left join timesheet ts on ts.service_id=s.service_id and ts.day <= "{day}"
                    where invoice_method != "Subscription" 
                      and s.status != "flushed"
                      and p.status != "closed"
                      and (p.end_date is null or p.end_date > "{day.plus_months(-12)}")
                      and (p.start_date is null or p.start_date <= "{day}") 
                      and `organization` not in ("Oberon","Travelbase") 
                    group by service_id
                    order by project_id, s.start_date
                   """
        dataframe = pd.read_sql_query(query.replace("%", "%%"), self.db.engine).fillna(
            0
        )
        # Kosten komen ook al mee in het project dus hier weghalen anders dubbel
        dataframe["service_costs"] = 0
        return dataframe


if __name__ == "__main__":
    service_table = Service()
    service_table.repopulate()
