from middleware.middleware_utils import get_middleware_db
from model.organisatie import roster_hours_per_user
from model.utilities import Period, Day


def booked(period: Period):
    db = get_middleware_db()
    query = f"""select employee, sum(hours) as hours, if(type != 'normal', type, if(label = 'internal' or 
                    project_number = 'OBE-1', 'internal', if(turnover > 0, 'billable', 'nonbillable'))) as what
                from timesheet where day >= '{period.fromday}' and day < '{period.untilday}'
                group by employee, what
                having hours > 0
                order by employee, what"""

    # data: {
    #                 datasets: [{
    #                                     label: 'billlable',
    #                                     data: [62, 52, 56, 51, 60.9, 52.2, 60.2, 58.3, 62.5, 57.9],
    #                                     backgroundColor: 'green',
    #                                     datalabels: {display: false }
    #                                   },{
    #                                     label: 'nonbillable',
    #                                     data: [9.8, 12.0, 12.5, 11.2, 7.4, 7.6, 4.2, 5.0, 4.5, 2.9],
    #                                     backgroundColor: '#c00',
    #                                     datalabels: {display: false }
    #                                   }],
    #                 labels: ['angela', 'caspar', 'chris', 'eva']

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
