import datetime
import os

import pandas as pd

from middleware.trendline import TrendLines
from model.caching import cache
from model.utilities import Day
from sources.database import get_travelbase_db, dataframe
from sources.googlesheet import get_spreadsheet, fill_range

VALID_STATUSES = (
    "accepted",
    "cancelled-guest",
    "cancelled-partner",
    "cancelled-external",
)

# STRUCTUUR:
# [{'arrival_date': d   atetime.date(2021, 5, 24),
#   'brand': 'ameland',
#   'created_at': datetime.datetime(2021, 3, 20, 17, 12, 53),
#   'departure_date': datetime.date(2021, 6, 4),
#   'id': 18092,
#   'status': 'accepted'},
#  {'arrival_date': datetime.date(2021, 4, 19),
#   'brand': 'ameland',
#   'created_at': datetime.datetime(2021, 3, 20, 17, 28, 19),
#   'departure_date': datetime.date(2021, 4, 23),
#   'id': 18093,
#   'status': 'accepted'}]
#
# STATUS:
# 'pending' -> In aanvraag, maar die zouden nooit in deze view moeten staan
# 'accepted' -> De "goed" status
# 'declined' -> Afgewezen aanvraag, zou ook niet in deze view moeten voorkomen
# 'cancelled-guest' -> Geannuleerd, schuld/kosten voor gast via Travelbase
# 'cancelled-partner' -> Geannuleerd, schuld/kosten voor partner via Travelbase
# 'cancelled-external' -> Geannuleerd, geen schuld/kosten of buiten Travelbase om geregeld
# 'waived' -> Vervallen
# 'no-show' -> Boeking was in orde, maar gast is nooit komen opdagen (heeft op dit moment geen technische gevolgen, puur administratief)
#
# Boekingen in de view 'tickets' hebben alleen 'accepted' en 'waived' als mogelijke status.

BRANDS = ["waterland", "ameland", "schier", "texel", "terschelling"]
GOOGLE_SHEETS_APP = "https://script.google.com/macros/s/AKfycbyFjOJY2OaCHouEuPRtOYMzwv1vnoIaP1iEKWY27PNDuakt5IIrKoyCGlvbMUn16N0MmQ/exec"


@cache(hours=6)
def get_bookings_per_week(booking_type: str = "bookings", only_complete_weeks=False):
    """Get the full list of all booking amounts per brand per week and return it as a DataFrame"""
    # Todo: Uit Middleware halen
    db = get_travelbase_db()
    dfs = []
    mysql_week_mode = 5  # Week 1 is the first week with a Monday in this year
    if only_complete_weeks:
        curyear = Day().y
        curweek = Day().week_number()
        date_clause = f"and (YEAR(created_at) < {curyear} or WEEK(created_at, {mysql_week_mode}) < {curweek})"
    else:
        date_clause = ""
    for brand in BRANDS:
        sql = f"""select YEAR(created_at) as year, WEEK(created_at, {mysql_week_mode}) as week, count(*) as aantal 
                  from {booking_type} 
                  where brand="{brand}" and status in {VALID_STATUSES} {date_clause}
                  group by year, week 
                  order by year, week"""
        df = dataframe(sql, db)
        if not isinstance(df, pd.DataFrame):
            return []  # Error occurred, no use to continue
        df = df.set_index(["year", "week"])
        dfs += [df]
    all = pd.concat(dfs, axis=1).fillna(0)
    all.columns = BRANDS
    all = all.reset_index()
    all["day"] = all.apply(
        lambda a: datetime.datetime.strptime(
            f"{int(a['year'])}-W{int(a['week'])}-1", "%Y-W%W-%w"
        ).date(),
        axis=1,
    )
    all = all.sort_values(by=["year", "week"], ascending=[True, True])

    # Save to trends database
    trends = TrendLines()
    if booking_type == "tickets":
        trend_name = "travelbase_tickets_" + brand
    else:
        trend_name = "travelbase_" + brand
    for index, row in all.iterrows():
        for brand in BRANDS:
            trends.update(trend_name, int(row[brand]), row["day"])
    return all


def update_bookings_per_month():
    db = get_travelbase_db()
    sheetname = "Travelbase dashboard"
    sheet = get_spreadsheet(sheetname)
    if not sheet:
        print(f"Could not open {sheetname}")
        return
    curyear = datetime.datetime.now().year
    curmonth = datetime.datetime.now().month
    for brand in BRANDS:
        # Initialize month data to 0
        month_data = {}
        for year in range(2021, curyear + 1):
            start_month = 2 if year == 2021 else 1
            end_month = curmonth if year == curyear else 12
            for month in range(start_month, end_month + 1):
                month_data[(year, month)] = {"bookings": 0, "tickets": 0}
        # Fill month_data with data from database
        for booking_type in ["bookings", "tickets"]:
            sql = f"""select YEAR(DATE(created_at)) as year, MONTH(DATE(created_at)) as month, count(*) as aantal 
                      from {booking_type} 
                      where brand="{brand}" and status in {VALID_STATUSES}
                      group by year, month 
                      order by year, month"""
            for rec in db.query(sql):
                year = rec["year"]
                month = rec["month"]
                month_data[(year, month)][booking_type] = rec["aantal"]
        #
        data = [
            [format_month(*key), value["bookings"], value["tickets"]]
            for key, value in month_data.items()
        ]
        tab = sheet.worksheet(brand)
        fill_range(tab, 3, 1, data)
    return True


def format_month(year, month):
    return (
            "jan feb mrt apr mei jun jul aug sep okt nov dec".split()[month - 1]
            + " "
            + str(year)
    )


if __name__ == "__main__":
    os.chdir("..")
    # update_bookings_per_month()
    get_bookings_per_week(booking_type="bookings", only_complete_weeks=True)
