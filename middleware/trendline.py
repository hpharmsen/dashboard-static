import datetime
from collections import defaultdict

from layout.chart import ScatterChart, ChartConfig
from middleware.base_table import BaseTable
from middleware.middleware_utils import singleton
from model.utilities import Day
from sources.database import get_db


@singleton
class TrendLines(BaseTable):
    def __init__(self):
        self.db = get_db()  # Nog uit extranet
        self.table_name = "trends"
        self.table_definition = """
               trendline VARCHAR(30) NOT NULL,
               `date` DATE NOT NULL,
               value FLOAT NOT NULL,
            """
        self.primary_key = 'trendline, date'
        self.index_fields = ""
        super().__init__()
        self.trends = defaultdict(list)
        self.load()

    def update(self, trendname, value, day: Day = None):
        if not self.db:
            return  # An error occurred. No use to continue.
        if not day:
            day = Day()
        self.db.updateinsert(
            "trends",
            {"trendline": trendname, "date": str(day)},
            {"trendline": trendname, "date": str(day), "value": value},
        )

        # Try to update the trend
        trend = self.trends[trendname]
        for i in reversed(range(len(trend))):
            if trend and trend[i][0] == day:
                trend[i][1] = value
                return
        # If date not found in trend: add this value.
        trend += [[day, value]]

    def last_registered_day(self, trendname):
        trend = self.trends.get(trendname)
        if not trend:
            y = datetime.datetime.today().year
            return Day(f"{y - 1}-12-31")
        return trend[-1][0]
        # return max([t[0] for t in trend])

    def second_last_registered_day(self, trendname):
        trend = self.trends.get(trendname)
        if not trend:
            y = datetime.datetime.today().year
            return Day(f"{y - 1}-12-31")
        if len(trend) >= 2:
            return trend[-2][0]
        else:
            return trend[-1][0]

    def load(self):
        if not self.db:
            return []  # An error occurred. No use to continue
        trenddata = self.db.execute("select * from trends order by date")
        for d in trenddata:
            trendname = d["trendline"]
            if not self.trends.get(trendname):
                self.trends[trendname] = []
            self.trends[trendname] += [[Day(d["date"]), d["value"]]]

    # def save(self):
    #     # with open(self.trendfile, 'w') as f:
    #     #    f.write(json.dumps(self.trends,
    #     #                       indent=4))
    #     exit()
    #     db = get_db()
    #     for trendname, values in self.trends.items():
    #         for date, value in values:
    #             db.updateinsert(
    #                 'trends',
    #                 {'trendline': trendname, 'date': date},
    #                 {'trendline': trendname, 'date': date, 'value': value},
    #             )

    def chart(self, trendname, width, height, x_start="", min_y_axis=None, max_y_axis=None):
        xy = [{"x": a[0], "y": a[1]} for a in self.trends[trendname] if a[0] >= x_start]
        chart_config = ChartConfig(
            width=width,
            height=height,
            colors=["#6666cc", "#ddeeff"],
            x_type="date",
            min_y_axis=min_y_axis,
            max_y_axis=max_y_axis,
            y_axis_max_ticks=5,
        )
        return ScatterChart(xy, chart_config)


if __name__ == "__main__":
    pass
