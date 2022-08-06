import os

from pandas import DataFrame

from middleware.middleware_utils import get_middleware_db
from model.utilities import Period
from sources.database import dataframe


def winst_per_klant(period: Period) -> DataFrame:
    db = get_middleware_db()
    fixed_price_query = f"""
        select `organization` as customer, sum(price-service_costs) as `turnover fixed`
        from project p 
        join service s on s.project_id=p.project_id
        where `organization` is not null and (s.end_date is null or s.end_date >'{period.fromday}')
        group by `organization`
        having `turnover fixed` != 0"""
    fixed_price_dict = {
        rec["customer"]: rec["turnover fixed"] for rec in db.query(fixed_price_query)
    }

    untilclause = f' and day<"{period.untilday}"' if period.untilday else ""
    per_customer_query = f"""
        select `organization` as customer, sum(hours) as hours, sum(turnover) as `turnover hours`, 
               sum(hours*hourly_costs) as `costs of hours`
        from timesheet t
        left join employee e on t.employee=e.name
        left join project p on p.project_number=t.project_number 
        where `organization` is not null and organization != 'Oberon' and day>="{period.fromday}" {untilclause} 
        group by `organization` 
        order by turnover desc"""
    result = dataframe(per_customer_query, database=db)
    result["turnover fixed"] = result.apply(
        lambda a: float(fixed_price_dict.get(a["customer"], 0)), axis=1
    )
    result["turnover per hour"] = (
        result["turnover hours"] + result["turnover fixed"]
    ) / result["hours"]
    result["margin"] = (
        result["turnover hours"] + result["turnover fixed"] - result["costs of hours"]
    )
    result["margin per hour"] = result["margin"] / result["hours"]
    result = result.sort_values(by="margin", ascending=False)
    return result


def winst_per_project(period: Period) -> DataFrame:
    db = get_middleware_db()
    fixed_price_query = f"""
        select p.project_number as number, sum(price-service_costs) as `turnover fixed`
        from project p 
        join service s on s.project_id=p.project_id
        where p.project_number is not null and p.project_number not like 'OBE-%%' 
          and (s.end_date is null or s.end_date >'{period.fromday}')
        group by p.project_id
        having `turnover fixed` != 0"""
    fixed_price_dict = {
        rec["number"]: rec["turnover fixed"] for rec in db.query(fixed_price_query)
    }

    untilclause = f' and day<"{period.untilday}"' if period.untilday else ""
    per_project_query = f"""
        select p.project_number as number, project_name as name, sum(hours) as hours, sum(turnover) as `turnover hours`, 
               sum(hours*hourly_costs) as `costs of hours`
        from timesheet t
        left join employee e on t.employee=e.name
        left join project p on p.project_number = t.project_number
        where p.project_number is not null and p.project_number not like 'OBE-%' 
          and day>="{period.fromday}" {untilclause} 
        group by p.project_number"""

    result = dataframe(per_project_query, database=db)
    result["turnover fixed"] = result.apply(
        lambda a: float(fixed_price_dict.get(a["number"], 0)), axis=1
    )
    result["turnover per hour"] = (
        result["turnover hours"] + result["turnover fixed"]
    ) / result["hours"]
    result["margin"] = (
        result["turnover hours"] + result["turnover fixed"] - result["costs of hours"]
    )
    result["margin per hour"] = result["margin"] / result["hours"]
    result = result.sort_values(by="margin", ascending=False)
    return result


def winst_per_persoon(period: Period) -> DataFrame:
    db = get_middleware_db()
    untilclause = f' and day<"{period.untilday}"' if period.untilday else ""
    per_person_query = f"""
        select e.name as employee, sum(hours) as hours, sum(turnover) as turnover, 
               sum(hours*hourly_costs) as costs
        from timesheet t
        left join employee e on t.employee=e.name
        where e.name != 'Freelancer' and day>="{period.fromday}" {untilclause} 
        group by e.name"""
    result = dataframe(per_person_query, database=db)
    result["margin"] = result["turnover"] - result["costs"]
    result = result.drop(["costs"], axis=1).sort_values(by="margin", ascending=False)
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
