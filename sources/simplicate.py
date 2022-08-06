import datetime
import os

import pandas as pd
from pysimplicate import Simplicate

from model.caching import cache
from model.log import log_error
from settings import ini

_simplicate = None  # Singleton
_simplicate_hours_dataframe = pd.DataFrame()

USER_MAPPING = {
    "geertjan": "geert-jan",
    "raymond": "ray",
    "jeroen": "jeroens",
    "robinveer": "robin",
    "vinz.timmermans": "vinz",
    "jordy.boelhouwer": "jordy",
}  # Map Simplicate name to oberon id


def simplicate():
    global _simplicate
    if not _simplicate:
        subdomain = ini["simplicate"]["subdomain"]
        api_key = ini["simplicate"]["api_key"]
        api_secret = ini["simplicate"]["api_secret"]

        _simplicate = Simplicate(subdomain, api_key, api_secret)
        _simplicate.ini = ini
    return _simplicate


def calculate_turnover(row):
    if row["project_number"] == "TOR-3" and not row["service"].count(
        "ase 2"
    ):  # !! For TOR only count fase 2 services
        # Changed service_name to service
        return 0
    tariff = row.get(
        "tariff", 0
    )  # If not tariff per user then take the tariff per service
    return (row["hours"] + row["corrections"]) * tariff


def complement_hours_dataframe(df):
    if df.empty:
        df["turnover"] = ""
        df["week"] = ""
        df["corrections_value"] = ""
    else:
        df["turnover"] = df.apply(calculate_turnover, axis=1)
        df["week"] = df.apply(
            lambda a: datetime.datetime.strptime(a["day"], "%Y-%m-%d").isocalendar()[1],
            axis=1,
        )
        df["corrections_value"] = df.apply(
            lambda a: (a["corrections"]) * a["tariff"], axis=1
        )


def flatten_hours_data(data):
    def convert(d):
        tariff = d.get("tariff")
        if tariff is None:
            log_error(
                "sources/simplicate.py",
                "flatten_hours_data",
                f"{d['project']['name']} has no tariff for {d['employee']['name']}",
            )
            tariff = 0
        return {
            "hours_id": d["id"],
            "employee": d["employee"]["name"],
            "project_id": d["project"]["id"],
            "project_number": d["project"].get("project_number", ""),
            "service": d["projectservice"]["name"],
            "service_id": d["projectservice"]["id"],
            "type": d["type"]["type"],
            "service_tariff": float(d["type"]["tariff"]),
            "label": d["type"]["label"],
            "billable": d["billable"],
            "tariff": tariff,
            "hours": d["hours"],
            "day": d["start_date"].split()[0],
            "status": d.get(
                "status", "projectmanager_approved"
            ),  # Dat status niet ingevuld is, kan waarschijnlijk alleen bij mijn eigen uren
            "corrections": d["corrections"]["amount"],
            "created_at": d["created_at"],
        }

    result = [convert(d) for d in data]
    return result


@cache(hours=1)
def name2user():
    employees = simplicate().employee()
    return {
        t["name"]: get_oberon_id_from_email(t["work_email"])
        for t in employees
        if t.get("name") and t.get("work_email")
    }


@cache(hours=1)
def user2name():
    return {value: key for key, value in name2user().items()}


def get_oberon_id_from_email(email):
    # Based on the e-mail address from Simplicate, get the username used in extranet planning database
    oberon_id = email.split("@")[0]
    return USER_MAPPING.get(oberon_id, oberon_id)


if __name__ == "__main__":
    os.chdir("..")
