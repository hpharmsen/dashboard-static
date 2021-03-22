import os
import datetime
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
# STATTUS:
# 'pending' -> In aanvraag, maar die zouden nooit in deze view moeten staan
# 'accepted' -> De "goed" status
# 'declined' -> Afgewezen aanvraag, zou ook niet in deze view moeten voorkomen
# 'cancelled-guest' -> Geannuleerd, schuld/kosten voor gast via Travelbase
# 'cancelled-partner' -> Geannuleerd, schuld/kosten voor partner via Travelbase
# 'cancelled-external' -> Geannuleerd, geen schuld/kosten of buiten Travelbase om geregeld
# 'waived' -> Vervallen
# 'no-show' -> Boeking was in orde, maar gast is nooit komen opdagen (heeft op dit moment geen technische gevolgen, puur administratief)

BRANDS = ['waterland', 'ameland']


def get_bookings():
    db = get_travelbase_db()
    dfs = []
    for brand in BRANDS:
        sql = f'''select YEAR(created_at) as year, WEEK(created_at) as week, count(*) as aantal 
                  from bookings 
                  where brand="{brand}" and status in ('accepted', 'cancelled-guest', 'cancelled-partner', 'no-show')
                  group by year, week 
                  order by year, week'''
        df = dataframe(sql, db).set_index(['year', 'week'])
        dfs += [df]
    all = pd.concat(dfs, axis=1).fillna(0)
    all.columns = BRANDS
    all = all.reset_index()
    all['day'] = all.apply(
        lambda a: datetime.datetime.strptime(f"{int(a['year'])}-W{int(a['week'])}-1", "%Y-W%W-%w").date(), axis=1
    )

    # Save to trends
    for index, row in all.iterrows():
        for brand in BRANDS:
            trends.update('travelbase_' + brand, int(row[brand]), row['day'])

    return all


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.dirname(__file__)))
    get_bookings()
