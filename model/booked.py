from middleware.middleware_utils import get_middleware_db
from model.organisatie import roster_hours_per_user
from model.utilities import Period, Day


def booked(period: Period):
    db = get_middleware_db()
    query = f"""select employee, sum(hours) as hours, 
                       if(type != 'normal', type, 
                            if(label = 'internal' or  project_number = 'OBE-1', 'internal', 
                                if(turnover > 0, 'billable', 'nonbillable')
                            )
                        ) as what
                from timesheet where day >= '{period.fromday}' and day < '{period.untilday}'
                group by employee, what
                having hours > 0
                order by employee, what"""

    roster_hours = roster_hours_per_user(period)
    hourtypes = ["billable", "nonbillable", "internal", "absence", "leave"]
    series = {
        hourtype: [] for hourtype in hourtypes + ["roster_free"]
    }  # {hourtype: list of hours per user}
    name_labels = []
    name = ""
    for rec in db.query(query):
        if rec["employee"] != name:
            name = rec["employee"]
            for hourtype in hourtypes:
                series[hourtype] += [0]
            series["roster_free"] += [40 - roster_hours[name]]
            name_labels += [name]
        series[rec["what"]][-1] = float(rec["hours"])
    return name_labels, series


if __name__ == "__main__":
    until = Day().last_monday()
    start = until.plus_days(-7)
    b = booked(Period(start, until))
