import os

from pandas import DataFrame

from middleware.middleware_utils import get_middleware_db
from model.utilities import Period
from sources.database import dataframe


# def parse_date(date_str):
#     try:  # Normally, dates in the contracten sheet are formatted like 2 feb. 1969
#         d, m, y = date_str.split()
#         m = [
#             "jan.",
#             "feb.",
#             "mrt.",
#             "apr.",
#             "mei",
#             "jun.",
#             "jul.",
#             "aug.",
#             "sep.",
#             "okt.",
#             "nov.",
#             "dec.",
#         ].index(m) + 1
#     except:  # But not always...
#         d, m, y = date_str.split("-")
#         m = int(m)
#     d = int(d)
#     y = int(y)
#     return d, m, y
#
#
# @cache(hours=60)
# def loonkosten_per_persoon():
#     """Dict met gegevens uit het contracten sheet met user als key
#     en velden:
#     - bruto: Bruto maandsalaris
#     - maand_kosten_ft: Maandelijkse kosten voor Oberon op basis van fulltime
#     - uren: Aantal uur per week
#     - kosten_jaar: Werkelijke kosten dit jaar rekening houdend met startdatum en part time"""
#     contracten = sheet_tab("Contracten werknemers", "Fixed")
#     if not contracten:
#         return []  # Error in the spreadsheet
#     ex_werknemers = sheet_tab("Contracten werknemers", "ex werknemers")
#     if not ex_werknemers:
#         return []  # Error in the spreadsheet
#
#     # Mensen die een managementfee factureren
#     rdb = {"bruto": MT_SALARIS / 12, "maand_kosten_ft": MT_SALARIS / 12, "uren": 40}
#     gert = {
#         "bruto": MT_SALARIS / 12 * 32 / 40,
#         "maand_kosten_ft": MT_SALARIS / 12,
#         "uren": 32,
#     }
#     joost = {
#         "bruto": MT_SALARIS * 104 / 110 / 12 * 36 / 40,
#         "maand_kosten_ft": MT_SALARIS * 104 / 110 / 12,
#         "uren": 36,
#     }
#     hph = rdb
#     users = {"rdb": rdb, "gert": gert, "hph": hph, "joost": joost}
#     for k in users.keys():
#         users[k]["kosten_jaar"] = (MT_SALARIS * users[k]["uren"] / 40,)
#         users[k]["jaar_kosten_pt"] = 12 * users[k]["maand_kosten_ft"] * users[k]["uren"] / 40
#         users[k]["fraction_of_the_year_worked"] = fraction_of_the_year_past()
#
#     # Werknemers en ex werknemers
#     id_col = contracten[0].index("Id")
#     bruto_col = contracten[0].index("Bruto")
#     kosten_col = contracten[0].index("Kosten voor Oberon obv full")
#     uren_col = contracten[0].index("UrenPerWeek")
#     start_date_col = contracten[0].index("InDienstGetreden")
#     end_date_col = ex_werknemers[0].index("Einddatum")
#     for line in contracten[1:] + ex_werknemers[1:]:
#         if line[id_col]:
#             d, m, y = parse_date(line[start_date_col])
#             if y == datetime.today().year:
#                 start_year_fraction = (m - 1) / 12 + d / 365
#             else:
#                 start_year_fraction = 0
#             end_year_fraction = fraction_of_the_year_past()
#             if line in ex_werknemers:
#                 try:
#                     d, m, y = parse_date(line[end_date_col])
#                 except:
#                     log_error(
#                         "winstgevendheid.py",
#                         "loonkosten_per_persoon()",
#                         "End date is not filled in for " + line[2],
#                     )
#                 if y < datetime.today().year:
#                     continue
#                 if y == datetime.today().year:
#                     end_year_fraction = (m - 1) / 12 + d / 365
#
#             maand_kosten_ft = (
#                 to_float(line[kosten_col]) if line[kosten_col] else 0
#             )  # Kosten_col zit LH, vakantiegeld etc. al bij in
#             users[line[id_col]] = {
#                 "bruto": to_float(line[bruto_col]),
#                 "maand_kosten_ft": maand_kosten_ft,
#                 "uren": to_int(line[uren_col]),
#                 "jaar_kosten_pt": 12 * maand_kosten_ft * to_int(line[uren_col]) / 40,
#                 "fraction_of_the_year_worked": end_year_fraction - start_year_fraction,
#             }
#     return users
#
#
# @cache(hours=60)
# def uurkosten_per_persoon():
#     # Vaste werknemers
#     loonkosten_pp = loonkosten_per_persoon()
#     loonkosten_pp = {user2name()[key]: val for key, val in loonkosten_pp.items() if user2name().get(key)}
#     res = {}
#     for user, kosten in loonkosten_pp.items():
#         res[user] = round(
#             (kosten["maand_kosten_ft"] + OVERIGE_KOSTEN_PER_FTE_PER_MAAND) * 12 / 45 / 40 / PRODUCTIVITEIT,
#             2,
#         )
#
#     # Freelancers
#     freelancers = sheet_tab("Contracten werknemers", "Freelance")
#     if not freelancers:
#         log_error(
#             "winstgevendheid.py",
#             "uurkosten_per_persoon",
#             "kan niet bij Freelance tab in contracten sheet",
#         )  # Error in the spreadsheet
#         return res
#     id_col = freelancers[0].index("Id")
#     bruto_per_uur_col = freelancers[0].index("BrutoPerUur")
#     for line in freelancers[1:]:
#         if line[id_col]:
#             name = user2name().get(line[id_col])
#             if name:
#                 res[name] = round(
#                     float(line[bruto_per_uur_col].replace(",", ".")) + OVERIGE_KOSTEN_PER_FREELANCE_FTR_PER_UUR,
#                     2,
#                 )
#
#     # Flex
#     flex = sheet_tab("Contracten werknemers", "Flex")
#     if not flex:
#         log_error(
#             "winstgevendheid.py",
#             "uurkosten_per_persoon",
#             "kan niet bij Flex tab in contracten sheet",
#         )  # Error in the spreadsheet
#         return res
#     id_col = flex[0].index("Id")
#     bruto_per_uur_col = flex[0].index("BrutoPerUur")
#     for line in flex[1:]:
#         if line[id_col]:
#             name = user2name().get(line[id_col])
#             if name:
#                 res[name] = round(
#                     float(line[bruto_per_uur_col].replace(",", ".")) + OVERIGE_KOSTEN_PER_FREELANCE_FTR_PER_UUR,
#                     2,
#                 )
#
#     return res
#
#
# def calculate_turnover_fixed(projects, row):
#     # todo: Needs fixing since we retrieve data from AWS database. Used in Winstgevendheid.
#     # if (
#     #         row["hours"] and row["turnover hours"] <= 0
#     # ):  # Fixed price. Hours booked but not on hoursturnover
#     #     return projects[row.name]["budget"]
#     return 0
#
#
# @cache(hours=60)
# def winst_per_project(period: Period):
#     result = (
#         project_results(period)
#         .drop("customer", axis=1)
#         .query("hours >= 10")
#         .sort_values(by="margin", ascending=False)[
#             [
#                 "number",
#                 "name",
#                 "hours",
#                 "turnover hours",
#                 "turnover fixed",
#                 "costs of hours",
#                 "margin",
#             ]
#         ]
#     )
#     result["turnover per hour"] = result.apply(
#         lambda p: round((p["turnover hours"] + p["turnover fixed"]) / p["hours"], 2),
#         axis=1,
#     )
#     result["margin per hour"] = result.apply(lambda p: round(p["margin"] / p["hours"], 2), axis=1)
#     return result
#
#
# # @cache(hours=60)
# def winst_per_klant(period: Period):
#     result = (
#         project_results(period)
#         .replace(["QS Ventures", "KV New B.V."], "Capital A")
#         .replace(["T-Mobile Netherlands B.V."], "Ben")
#         .groupby(["customer"])[["hours", "turnover hours", "turnover fixed", "costs of hours", "margin"]]
#         .sum()
#         .query("hours >= 10")
#         .sort_values(by="margin", ascending=False)
#         .reset_index()[
#             [
#                 "customer",
#                 "hours",
#                 "turnover hours",
#                 "turnover fixed",
#                 "costs of hours",
#                 "margin",
#             ]
#         ]
#     )
#     result["turnover per hour"] = (result["turnover hours"] + result["turnover fixed"]) / result["hours"]
#     result["margin per hour"] = result["margin"] / result["hours"]
#     return result
#
# # @cache(hours=24)
# def project_results(period: Period = None):
#     simplicate_projects = simplicate().project()
#     projects = {
#         p["id"]: {
#             "name": p["name"],
#             "customer": p["organization"]["name"],
#             "number": p["project_number"],
#             "budget": max(
#                 p["budget"]["total"]["value_budget"],
#                 p["budget"]["total"]["value_spent"],
#             ),
#         }
#         for p in simplicate_projects
#     }
#
#     df = worked_oberon_hours(period)
#     uurkosten = uurkosten_per_persoon()
#     pd.options.mode.chained_assignment = (
#         None  # Ignore 'A value is trying to be set on a copy of a slice from a DataFrame' error
#     )
#     df["costs of hours"] = df.apply(lambda a: uurkosten.get(a["employee"], 0) * float(a["hours"]), axis=1)
#
#     result = (
#         df.groupby(["project_number"])
#         .agg({"hours": np.sum, "turnover": np.sum, "costs of hours": np.sum})
#         .rename(columns={"turnover": "turnover hours"})
#     )
#
#     def get_customer(row):
#         project = projects.get(row.name)
#         if not project:
#             return "UNKNOWN"
#         return project["customer"]
#
#     def get_project_field(field, row):
#         project = projects.get(row.name)
#         if not project:
#             return "UNKNOWN"
#         return project[field]
#
#     result["customer"] = result.apply(partial(get_project_field, "customer"), axis=1)
#     result["name"] = result.apply(partial(get_project_field, "name"), axis=1)
#     result["number"] = result.apply(partial(get_project_field, "number"), axis=1)
#     result = result[~result.number.isin(["TRAV-1", "QIKK-1", "SLIM-28", "TOR-3"])]  # !!
#     result["turnover fixed"] = result.apply(partial(calculate_turnover_fixed, projects), axis=1)
#     result.loc[result.number == "CAP-8", ["hours", "costs of hours", "turnover fixed"]] = (
#         20,
#         20 * 75,
#         6000,
#     )  # todo: remove in 2022. Fix for CAP-8 since it cannot be edited in Simplicate. Used in Winstgevendheid.
#     result["margin"] = result["turnover hours"] + result["turnover fixed"] - result["costs of hours"]
#     return result
#
#
# @cache(hours=24)
# def winst_per_persoon(period):  # Get hours and hours turnover per person
#
#     # Get hours and hours turnover per person
#     result = (
#         worked_oberon_hours(period)
#         .groupby(["employee"])[["hours", "turnover"]]
#         .sum()
#         .rename(columns={"turnover": "turnover hours"})
#         .reset_index()
#     )
#
#     # Voeg mensen toe die geen uren boeken
#     # todo: Dit moet anders, geen specifieke mensen in de code
#     employee_names = ["Angela Duijs", "Lunah Smits", "Mel Schuurman", "Martijn van Klaveren"]
#     employees = [{"employee": employee, "hours": 0, "turnover hours": 0} for employee in employee_names]
#     result = pd.concat([result, pd.DataFrame(employees)])
#
#     # Add results from fixed price projects
#     result["turnover fixed"] = 0
#     for index, project in fixed_projects(period).iterrows():
#         person_hours = hours_per_person(period, index)
#         for _, ph in person_hours.iterrows():
#             turnover = project["turnover fixed"] / project["hours"] * ph["hours"]
#             result.loc[result.employee == ph["employee"], "turnover fixed"] += turnover
#
#     result.loc[
#         result.employee == "Paulo Nuno da Cruz Moreno", "employee"
#     ] = "Paulo Nuno Da Cruz Moreno"  # todo: !! temporary
#
#     # Add the salary and office costs per person
#     result["costs"] = result.apply(calculate_employee_costs, axis=1)
#
#     # Calculate the margin per person
#     result["turnover"] = result["turnover hours"] + result["turnover fixed"]
#     result["margin"] = result["turnover"] - result["costs"]
#     result = result.sort_values(by="margin", ascending=False)
#     return result[["employee", "hours", "turnover", "margin"]]
#
#
# @cache(hours=24)
# def calculate_employee_costs(row):
#     user = name2user()[row["employee"]]
#     loonkosten_user = loonkosten_per_persoon().get(user)
#     if loonkosten_user:
#         costs = (loonkosten_user["jaar_kosten_pt"] + OVERIGE_KOSTEN_PER_FTE_PER_MAAND * 12) * loonkosten_user[
#             "fraction_of_the_year_worked"
#         ]
#     else:
#         # Freelance
#         uurkosten = uurkosten_per_persoon().get(row["employee"])
#         if not uurkosten:
#             return 0
#         costs = row["hours"] * (uurkosten + OVERIGE_KOSTEN_PER_FREELANCE_FTR_PER_UUR)
#     return costs
#
#
# def fixed_projects(period):
#     return project_results(period).query("`turnover fixed` > 0")[["number", "name", "hours", "turnover fixed"]]
#
#
# def hours_per_person(period, project_id):
#     df = (
#         hours_dataframe(period)
#         .query(f'project_id=="{project_id}"')
#         .groupby(["employee"])[["hours"]]
#         .sum()
#         .reset_index()
#     )
#     return df
#
#
# @cache(hours=24)
# def worked_oberon_hours(period: Period = None):
#     where_clause = 'type=="normal" and employee != "Freelancer" and organization != "Oberon"'
#     df = hours_dataframe(period).query(where_clause)
#     return df

## ============================================================================================================


def winst_per_klant(period: Period) -> DataFrame:
    db = get_middleware_db()
    fixed_price_query = f'''
        select `organization` as customer, sum(price-service_costs) as `turnover fixed`
        from project p 
        join service s on s.project_id=p.project_id
        where `organization` is not null and (s.end_date is null or s.end_date >'{period.fromday}')
        group by `organization`
        having `turnover fixed` != 0'''
    fixed_price_dict = {rec['customer']: rec['turnover fixed'] for rec in db.query(fixed_price_query)}

    untilclause = f' and day<"{period.untilday}"' if period.untilday else ''
    per_customer_query = f'''
        select `organization` as customer, sum(hours) as hours, sum(turnover) as `turnover hours`, 
               sum(hours*hourly_costs) as `costs of hours`
        from timesheet t
        left join employee e on t.employee=e.name
        left join project p on p.project_number=t.project_number 
        where `organization` is not null and organization != 'Oberon' and day>="{period.fromday}" {untilclause} 
        group by `organization` 
        order by turnover desc'''
    result = dataframe(per_customer_query, database=db)
    result["turnover fixed"] = result.apply(lambda a: float(fixed_price_dict.get(a["customer"], 0)), axis=1)
    result["turnover per hour"] = (result["turnover hours"] + result["turnover fixed"]) / result["hours"]
    result["margin"] = result['turnover hours'] + result['turnover fixed'] - result['costs of hours']
    result["margin per hour"] = result["margin"] / result["hours"]
    result = result.sort_values(by='margin', ascending=False)
    return result


def winst_per_project(period: Period) -> DataFrame:
    db = get_middleware_db()
    fixed_price_query = f'''
        select p.project_number as number, sum(price-service_costs) as `turnover fixed`
        from project p 
        join service s on s.project_id=p.project_id
        where p.project_number is not null and p.project_number not like 'OBE-%' 
          and (s.end_date is null or s.end_date >'{period.fromday}')
        group by p.project_id
        having `turnover fixed` != 0'''
    fixed_price_dict = {rec['number']: rec['turnover fixed'] for rec in db.query(fixed_price_query)}

    untilclause = f' and day<"{period.untilday}"' if period.untilday else ''
    per_project_query = f'''
        select p.project_number as number, project_name as name, sum(hours) as hours, sum(turnover) as `turnover hours`, 
               sum(hours*hourly_costs) as `costs of hours`
        from timesheet t
        left join employee e on t.employee=e.name
        left join project p on p.project_number = t.project_number
        where p.project_number is not null and p.project_number not like 'OBE-%' 
          and day>="{period.fromday}" {untilclause} 
        group by p.project_number'''

    result = dataframe(per_project_query, database=db)
    result["turnover fixed"] = result.apply(lambda a: float(fixed_price_dict.get(a["number"], 0)), axis=1)
    result["turnover per hour"] = (result["turnover hours"] + result["turnover fixed"]) / result["hours"]
    result["margin"] = result['turnover hours'] + result['turnover fixed'] - result['costs of hours']
    result["margin per hour"] = result["margin"] / result["hours"]
    result = result.sort_values(by='margin', ascending=False)
    return result


def winst_per_persoon(period: Period) -> DataFrame:
    db = get_middleware_db()
    untilclause = f' and day<"{period.untilday}"' if period.untilday else ''
    per_person_query = f'''
        select e.name as employee, sum(hours) as hours, sum(turnover) as turnover, 
               sum(hours*hourly_costs) as costs
        from timesheet t
        left join employee e on t.employee=e.name
        where e.name != 'Freelancer' and day>="{period.fromday}" {untilclause} 
        group by e.name'''
    result = dataframe(per_person_query, database=db)
    result["margin"] = result['turnover'] - result['costs']
    result = result.drop(['costs'], axis=1).sort_values(by='margin', ascending=False)
    return result


def main_test():
    os.chdir("..")
    # use_cache = False
    period = Period("2022-01-01")
    pk = winst_per_klant(period)
    ppr = winst_per_project(period)
    pp = winst_per_persoon(period)
    print(pp)
    # pp = winst_per_persoon(period).sort_values(by="employee")
    # print(pp)


if __name__ == "__main__":
    main_test()
