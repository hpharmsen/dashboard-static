import os
import datetime
import requests
import pandas as pd
from sources.database import get_travelbase_db, dataframe
from model.caching import reportz
from model.trendline import trends

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

BRANDS = ['waterland', 'ameland', 'schier', 'texel']
GOOGLE_SHEETS_APP = (
    'https://script.google.com/macros/s/AKfycbyFjOJY2OaCHouEuPRtOYMzwv1vnoIaP1iEKWY27PNDuakt5IIrKoyCGlvbMUn16N0MmQ/exec'
)


def get_bookings_per_week(type: str, only_complete_weeks=False):
    db = get_travelbase_db()
    dfs = []
    mysql_week_mode = 5  # Week 1 is the first week with a Monday in this year
    for brand in BRANDS:
        sql = f'''select YEAR(created_at) as year, WEEK(created_at, {mysql_week_mode}) as week, count(*) as aantal 
                  from {type} 
                  where brand="{brand}" and status in ('accepted', 'cancelled-guest', 'cancelled-partner', 'no-show')
                  group by year, week 
                  order by year, week'''
        df = dataframe(sql, db).set_index(['year', 'week'])
        if only_complete_weeks:
            df = df[:-1]
        dfs += [df]
    all = pd.concat(dfs, axis=1).fillna(0)
    all.columns = BRANDS
    all = all.reset_index()
    all['day'] = all.apply(
        lambda a: datetime.datetime.strptime(f"{int(a['year'])}-W{int(a['week'])}-1", "%Y-W%W-%w").date(), axis=1
    )

    # Save to trends
    if type == 'tickets':
        trend_name = 'travelbase_tickets_' + brand
    else:
        trend_name = 'travelbase_' + brand
    for index, row in all.iterrows():
        for brand in BRANDS:
            trends.update(trend_name, int(row[brand]), row['day'])

    return all


# @reportz(hours=6)
def update_bookings_per_day(type: str):
    db = get_travelbase_db()
    for brand in BRANDS:
        day, value = get_latest(type, brand)
        day_constraint = f'and created_at>="{day}"' if day else ''
        sql = f'''select DATE(created_at) as day, count(*) as aantal 
                  from {type} 
                  where brand="{brand}" {day_constraint} and status in ('accepted', 'cancelled-guest', 'cancelled-partner')
                  group by day 
                  order by day'''
        df = dataframe(sql, db)
        for index, row in df.iterrows():
            if row['day'] != day or row['value'] != value:
                save_value(type, brand, row['day'], row['aantal'])
    return True


def get_latest(type, brand):
    name = brand
    if type == 'tickets':
        name += '_tickets'
    url = GOOGLE_SHEETS_APP + '?name=' + name
    result = requests.get(url).text
    try:
        day, value = result.split(',')
    except:
        return (None, None)
    return (day, value)


def save_value(type: str, brand: str, day, value):
    name = brand
    if type == 'tickets':
        name += '_tickets'
    url = GOOGLE_SHEETS_APP + f'?name={name}&date={day}&value={value}'
    result = requests.get(url).text
    print(result)


if __name__ == '__main__':
    os.chdir('..')
    sql = f'''select count(*) as aantal 
                  from bookings 
                  where status in ('accepted', 'cancelled-guest', 'cancelled-partner')'''
    db = get_travelbase_db()
    print(db.execute(sql))
    update_bookings_per_day(type='tickets')
    update_bookings_per_day(type='bookings')
    get_bookings_per_week(type='tickets')
