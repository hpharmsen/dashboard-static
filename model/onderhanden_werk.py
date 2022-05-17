import math
import os
from functools import lru_cache

import pandas as pd
from pandas import DataFrame

from middleware.invoice import Invoice
from middleware.service import Service
from model.caching import load_cache
from model.utilities import Day, Period


@lru_cache()
def ohw_sum(day: Day, minimal_intesting_value: int):
    df = ohw_list(day, minimal_intesting_value)
    if df.empty:
        return 0

    # Loop through the list and take the project_ohw of each unique project
    total_ohw = 0
    last_project__id = ""
    for _, row in df.iterrows():
        if row["project_id"] != last_project__id:
            if abs(row["project_ohw"]) >= minimal_intesting_value:
                total_ohw += row["project_ohw"]
            last_project__id = row["project_id"]

    return total_ohw


# @cache(hours=1)
def ohw_list(day: Day, minimal_intesting_value: int, group_by_project=0) -> DataFrame:
    """OHW is calculated including work and invoices of the specified day"""
    pd.options.mode.chained_assignment = None

    # 1. Alle active projecten en de diensten daarvan
    service_df = Service().projects_and_services(day)

    # 4. Facturatie
    service_invoiced = invoiced_by_date(day)

    def get_service_invoiced(row):
        return service_invoiced.get(row["service_id"], 0)

    service_df["invoiced"] = service_df.apply(get_service_invoiced, axis=1).astype(int)

    # 5. Onderhanden werk berekenen
    service_df["service_ohw"] = (
        service_df["turnover"] - service_df["invoiced"]  # + service_df["service_costs"]
    )
    service_df = service_df.query("service_ohw >=100 | service_ohw < -100").copy()

    # Group by project either to return projects or to be able to sort the services by project OHW
    project_df = (
        service_df.groupby(
            [
                "organization",
                "pm",
                "project_number",
                "project_name",
                "project_costs",
                "project_id",
            ]
        )
        .agg({"turnover": "sum", "invoiced": "sum"})  # , "service_costs": "sum"
        .reset_index()
    )

    def get_project_invoiced(row):
        res = service_invoiced.get(row["project_number"], 0)
        if math.isnan(res):
            res = 0
        return res

    project_df["project_invoiced"] = project_df.apply(
        get_project_invoiced, axis=1
    ).astype(int)

    project_df["project_ohw"] = (
        project_df["turnover"]
        # + project_df["service_costs"]
        - project_df["invoiced"]
        + project_df["project_costs"]
        - project_df["project_invoiced"]
    )

    if group_by_project:
        if minimal_intesting_value:
            project_df = project_df.query(
                f"ohw>{minimal_intesting_value} | ohw<-{minimal_intesting_value}"
            ).copy()
        project_df = project_df.sort_values(by="ohw", ascending=False)
    else:
        if service_df.empty:
            return project_df

        # Als er kosten direct op het project zijn geboekt of facturen direct op het project,
        # voeg dan een extra 'service' toe
        for index, project in project_df.iterrows():
            invoiced = project["project_invoiced"]
            if math.isnan(invoiced):
                invoiced = 0
            costs = project.get("project_costs", 0)
            if math.isnan(costs):
                costs = 0
            if project["project_number"] == "SM2022":
                project_df.at[
                    index, "project_invoiced"
                ] -= 17575  # Hack, dit zijn uren die zijn meegenomen uit 2021
                project_df.at[index, "project_ohw"] -= 17575
            if invoiced or costs:
                new_row = {
                    "project_id": project["project_id"],
                    "project_number": project["project_number"],
                    "project_name": project["project_name"],
                    "turnover": 0,
                    "service_name": "Kosten/facturen direct op het project",
                    "service_costs": costs,
                    "invoiced": invoiced,
                    "service_ohw": costs - invoiced,
                    "organization": project["organization"],
                    "pm": project["pm"],
                    "project_costs": project["project_costs"],
                }
                new_row = {
                    key: [value] for key, value in new_row.items()
                }  # Make values into lists instead of scalars
                service_df = pd.concat(
                    [service_df, pd.DataFrame(new_row)], ignore_index=True
                )

        # Sort services by the total owh of their project
        project_ohws = {
            p["project_number"]: p["project_ohw"] for _, p in project_df.iterrows()
        }
        service_df["project_ohw"] = service_df.apply(
            lambda row: project_ohws.get(row["project_number"], 0), axis=1
        )
        if minimal_intesting_value:
            service_df = service_df.query(
                f"project_ohw > {minimal_intesting_value} | project_ohw < -{minimal_intesting_value}"
            )
        project_df = service_df.sort_values(by="project_ohw", ascending=False)

    pd.options.mode.chained_assignment = "warn"
    return project_df


@lru_cache()
def invoiced_by_date(day: Day):
    period = Period("2021-01-01", day)
    invoice = Invoice()
    invoiced = invoice.invoiced_per_service(period)
    return {i["service_id"]: i["invoiced"] for i in invoiced}


# @cache(hours=4)
# def invoiced_per_customer(period: Period):
#     invoice = Invoice()
#     invoices = invoice.invoiced_per_customer(period)
#     df = DataFrame(invoices)
#     return df


if __name__ == "__main__":
    os.chdir("..")
    load_cache()
    test_day = Day()
    ohw = ohw_list(test_day, minimal_intesting_value=1000)
    print(ohw)
    # print(ohw['ohw'].sum())
