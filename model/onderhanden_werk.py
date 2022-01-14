import os
from collections import defaultdict

import pandas as pd
from pandas import DataFrame
from pysimplicate import Simplicate

from middleware.timesheet import Timesheet
from model.caching import cache, load_cache
from model.utilities import Day, Period
from sources.simplicate import simplicate


@cache(hours=1)
def ohw_sum(day: Day, minimal_intesting_value=0):
    df = ohw_list(day)
    if df.empty:
        return 0

    # Loop through the list and take the project_ohw of each unique project
    total_ohw = 0
    last_project__id = ""
    for _, row in df.iterrows():
        if row["project_id"] != last_project__id:
            if abs(row["project_ohw"]) >= minimal_intesting_value:
                total_ohw += row["project_ohw"]
                print(">", row["project_ohw"])
            last_project__id = row["project_id"]

    return total_ohw


@cache(hours=1)
def ohw_list(day: Day, minimal_intesting_value=0, group_by_project=0) -> DataFrame:
    sim = simplicate()

    # Nieuwe methode:
    # 1. Alle active projecten en de diensten daarvan
    service_df = simplicate_projects_and_services(sim, day)
    # service_df = service_df.query('project_number=="THIE-27"')

    # todo: OWH berekenen voor FixedFee services
    # Gaat mis bij projecten zoals CAP-13. Andere zoals strippenkaarten, ODC-1 gaan wel goed.
    # Het beste zou zijn: min(fixedfee, hours*tariff - invoiced)
    # Waarbij fixedfee het afgesproken bedrag is en tariff meestal niet bekend zal zijn dus dan maar 100.
    # Voor nu houden we fixedfee ook niet bij in de service. Sterker nog, we hebben helemaal geen service-object
    # want de service-gegevens staan in timesheet erbij. Dat moet eigenlijk eerst gefixt met een eigen tabel.
    # Tot die tijd is OHW van alle fixedfee projecten gewoon altijd 0.

    # 2. Omzet -/- correcties berekenen
    service_ids = service_df["service_id"].tolist()
    service_turnovers = Timesheet().services_with_their_turnover(service_ids, day)

    def calculate_turover(row):
        turnover = service_turnovers.get(row["service_id"], 0)
        if row["invoice_method"] == "FixedFee":  # Gerealiseerde omzet kan nooit meer zijn dan de afgesproken prijs
            turnover = min(int(float(row.get("price"))), turnover)
        return turnover

    service_df["turnover"] = service_df.apply(calculate_turover, axis=1).astype(int)

    # 3. Projectkosten
    # Kosten kunnen per project of per service in Simplicate staan.
    # In TUI-3 per project:
    # https://oberon.simplicate.com/api/v2/projects/project/project:99d4d0998d588c6bfeaad60b7a7437df
    # https://oberon.simplicate.com/api/v2/projects/service?q[project_id]=project:99d4d0998d588c6bfeaad60b7a7437df
    # En in MANA-6 per service:
    # https://oberon.simplicate.com/api/v2/projects/project/project:17863c4398681034feaad60b7a7437df
    # https://oberon.simplicate.com/api/v2/projects/service?q[project_id]=project:17863c4398681034feaad60b7a7437df
    # Beide komen al uit simplicate_projects_and_services()
    service_df["service_costs"] = service_df["service_costs"].astype(int)
    service_df["project_costs"] = service_df["project_costs"].astype(int)

    # 4. Facturatie
    service_invoiced = invoiced_by_date(sim, day)

    def get_invoiced(row):
        invoiced = service_invoiced.get(row["service_id"])
        if not invoiced:
            invoiced = service_invoiced.get(row["project_number"], 0)
        return invoiced

    service_df["invoiced"] = service_df.apply(get_invoiced, axis=1).astype(int)

    # 5. Onderhanden werk berekenen
    service_df["service_ohw"] = service_df["turnover"] + service_df["service_costs"] - service_df["invoiced"]
    service_df = service_df.query("service_ohw != 0").copy()

    # Group by project either to return projects or to be able to sort the services by project OHW
    project_df = (
        service_df.groupby(["organization", "pm", "project_number", "project_name", "project_costs"])
            .agg({"turnover": "sum", "invoiced": "sum", "service_costs": "sum"})
            .reset_index()
    )
    project_df["project_ohw"] = (
            project_df["turnover"] + project_df["service_costs"] + project_df["project_costs"] - project_df["invoiced"]
    )

    if group_by_project:
        if minimal_intesting_value:
            project_df = project_df.query(f"ohw>{minimal_intesting_value} | ohw<-{minimal_intesting_value}").copy()
        project_df = project_df.sort_values(by="ohw", ascending=False)
    else:
        # Sort services by the total owh of their project
        project_ohws = {p["project_number"]: p["project_ohw"] for _, p in project_df.iterrows()}
        service_df["project_ohw"] = service_df.apply(lambda row: project_ohws.get(row["project_number"], 0), axis=1)
        if minimal_intesting_value:
            service_df = service_df.query(
                f"project_ohw > {minimal_intesting_value} | project_ohw < -{minimal_intesting_value}"
            )
        project_df = service_df.sort_values(by="project_ohw", ascending=False)

    return project_df


@cache(hours=8)
def simplicate_projects_and_services(sim: Simplicate, day: Day) -> DataFrame:
    """Returns a dataframe with all active projects and services at a given date"""

    # Get the list of services
    services_json = sim.service({"track_hours": True})

    # status != "flushed"' is een beetje tricky want er is geen mogeljkheid om te achterhalen
    # wat de status was op de opgegeven datum. Eens flushed, altijd flushed dus.
    # Een beetje geschiedvervalsing wellicht?
    status_query = 'invoice_method != "Subscription" & status != "flushed"'
    # start_date en end_date worden slecht bijgehouden dus daar hebben we ook niks aan
    # behalve dan dat we dingen eruit kunnen filteren die echt te oud zijn, of nog niet begonnen
    # end_date != end_date is a construct to check for NaN
    status_query += f' & (end_date != end_date | end_date > "{day.plus_months(-12)}")'
    status_query += f' & (start_date != start_date | start_date <= "{day}")'

    # Add up expenses per service and save them in service_costs field in the json
    for service in services_json:
        service_costs = 0
        for cost_type in service.get("cost_types", []):
            service_costs += cost_type["purchase_tariff"]
        service["service_costs"] = service_costs

    services = (
        sim.to_pandas(services_json)
            .query(status_query)[
            ["project_id", "status", "id", "name", "start_date", "end_date", "invoice_method", "service_costs", "price"]
        ]
            .rename(columns={"id": "service_id", "name": "service_name"})
    )  # end_date > "{date}" &

    # services = services.query('project_id=="project:99bec48587324a42feaad60b7a7437df"')

    # Same with the list of projects
    projects_json = sim.project({"status": "tab_pactive"})
    project_renames = {
        "id": "project_id",
        "name": "project_name",
        "budget_costs_value_spent": "project_costs",
        "project_manager_name": "pm",
        "organization_name": "organization",
    }
    project_query = (
        'organization_name not in ["Oberon","Travelbase"] & my_organization_profile_organization_name=="Oberon"'
    )
    projects = (
        sim.to_pandas(projects_json)
            .query(project_query)[
            ["id", "project_number", "name", "organization_name", "project_manager_name", "budget_costs_value_spent"]
        ]
            .rename(columns=project_renames)
    )

    # Join them
    project_service = pd.merge(services, projects, on=["project_id"])
    return project_service


@cache(hours=4)
def invoiced_by_date(sim: Simplicate, day: Day):
    invoices = sim.invoice({"from_date": "2021-01-01", "until_date": day})
    result = defaultdict(float)
    for inv in invoices:
        if not inv.get("invoice_number"):
            continue  # conceptfactuur
        for line in inv["invoice_lines"]:
            line_json = flatten_json(line)
            service_id = line_json.get("service_id")  # We gaan uit van de service_id
            if not service_id:
                projects = inv.get("projects")  # Als die er niet is, kijk in projects
                if projects:  # en gebruik het nummer van het eerste project
                    service_id = projects[0].get("project_number")
                else:
                    continue  # Ook niet? Ok, ik geef het op

            result[service_id] += float(line_json["price"]) * float(line_json["amount"])
    return result


def invoiced_per_customer(sim: Simplicate, period: Period):
    invoices = sim.invoice({"from_date": period.fromday, "until_date": period.untilday})
    result = []
    for inv in invoices:
        if not inv.get("invoice_number"):
            continue  # conceptfactuur
        for line in inv["invoice_lines"]:
            line_json = flatten_json(line)
            line_json["turnover"] = float(line_json["price"]) * float(line_json["amount"])
            line_json["organization"] = inv["organization"]["name"]
            result += [line_json]
    df = DataFrame(result).groupby("organization")[["turnover"]].sum()
    return df


def flatten_json(y):
    out = {}

    def flatten(x, name=""):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + "_")
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + str(i) + "_")
                i += 1
        else:
            out[name[:-1]] = x

    flatten(y)
    return out


if __name__ == "__main__":
    os.chdir("..")
    load_cache()
    day = Day("2022-01-01")
    sim = simplicate()
    invoiced = invoiced_per_customer(sim, Period("2021-01-01", "2022-01-01"))
    pass
    # ohw = ohw_list(date)
    # print(ohw)
    # print(ohw['ohw'].sum())
