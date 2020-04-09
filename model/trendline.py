import os
from collections import defaultdict
import atexit
import json
import datetime

# from model.productiviteit import billable_perc_iedereen
from layout.chart import ScatterChart, ChartConfig

TREND_FILE = os.path.dirname(__file__) + '/trends.json'


class TrendLines:
    def __init__(self):
        self.trendfile = TREND_FILE
        self.trends = defaultdict(list)
        self.load()

    def update(self, trendname, value, date=None):
        if not date:
            date = datetime.date.today()
        datestr = date.strftime('%Y-%m-%d')
        trend = self.trends[trendname]
        for i in reversed(range(len(trend))):
            if trend and trend[i][0] == datestr:
                trend[i][1] = value
                return
        trend += [[datestr, value]]

    def last_registered_day(self, trendname):
        trend = self.trends.get(trendname)
        if not trend:
            y = datetime.datetime.today().year
            return f'{y - 1}-12-31'
        return trend[-1][0]
        # return max([t[0] for t in trend])

    def second_last_registered_day(self, trendname):
        trend = self.trends.get(trendname)
        if not trend:
            y = datetime.datetime.today().year
            return f'{y - 1}-12-31'
        if len(trend) >= 2:
            return trend[-2][0]
        else:
            return trend[-1[0]]

    def load(self):
        with open(self.trendfile) as f:
            trenddata = json.loads(f.read())
        for key, value in trenddata.items():
            self.trends[key] = value
        pass

    def save(self):
        with open(self.trendfile, 'w') as f:
            f.write(json.dumps(self.trends, indent=4))

    def chart(self, trendname, width, height, x_start='', min_y_axis=None, max_y_axis=None):
        xy = [{'x': a[0], 'y': a[1]} for a in self.trends[trendname] if a[0] >= x_start]
        chart_config = ChartConfig(
            width=width,
            height=height,
            colors=['#6666cc', '#ddeeff'],
            x_type='date',
            min_y_axis=min_y_axis,
            max_y_axis=max_y_axis,
            y_axis_max_ticks=5,
        )
        return ScatterChart(xy, chart_config)


trends = TrendLines()


def save_trends():
    global trends
    trends.save()


atexit.register(save_trends)

if __name__ == '__main__':
    # trends.update( 'newline', 10, datetime.datetime(2019,10,1))
    # trends.update( 'newline', 15, datetime.datetime(2019,10,3))
    # trends.update( 'newline', 12, datetime.datetime(2019,10,4))
    # trends.update( 'newline', 5, datetime.datetime(2019,10,8))
    # trends.update( 'newline', 19)
    # trends.update( 'other trend', 5)

    # for i in reversed(range(10)):
    #    day = datetime.datetime.today()-datetime.timedelta( days=30*i )
    #    trends.update( 'billable', billable_perc_iedereen(fromdate=day-datetime.timedelta(days=30), untildate=day), day)
    # save_trends()
    pass
