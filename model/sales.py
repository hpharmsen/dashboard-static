import os

from model.caching import cache
from model.trendline import trends
from sources.simplicate import simplicate


def to_int(s):
    if type(s) == int:
        return s
    return int(s.replace("€ ", "").replace(".", "").replace("%", ""))


def is_int(s):
    try:
        to_int(s)
        return True
    except:
        return False


@cache(hours=24)
def sales_waarde():
    res = sum([s["value"] for s in open_sales()])
    trends.update("sales_waarde", res)
    return res


@cache(hours=24)
def sales_waarde_details():
    # klant, project, grootte, kans, fase, waarde, bron

    sales = sorted(open_sales(), key=lambda a: -a["progress_position"])
    return [
        [
            s["organization"],
            s["subject"],
            s["expected_revenue"],
            s["chance_to_score"],
            s["progress_label"],
            s["value"],
            s["source"],
        ]
        for s in sales
    ]


@cache(hours=24)
def top_x_sales(number=99, minimal_amount=0):
    def format_project_name(line, maxlen):
        name = line["organization"].split()[0] + " - " + line["subject"]
        if len(name) > maxlen:
            name = name[: maxlen - 1] + ".."
        return name

    top = sorted(open_sales(), key=lambda a: -a["value"])
    return [
               [format_project_name(a, 35), a["value"]]
               for a in top
               if a["value"] > minimal_amount
           ][:number]


@cache(hours=24)
def open_sales():
    sim = simplicate()
    fl = sim.sales_flat()
    import pandas as pd

    df = pd.DataFrame(fl)
    return [s for s in sim.sales_flat() if 3 <= s["progress_position"] <= 7]


# MOET VERVANGEN DOOR SIMPLICATE
# @reportz(hours=24)
# def werk_in_pijplijn():
#     tab = sheet_tab('Sales - force', 'Kansen')
#     res = to_int(sheet_value(tab, 2, 9))
#     trends.update('werk_in_pijplijn', res)
#     return res

# MOET VERVANGEN DOOR SIMPLICATE
# @reportz(hours=24)
# def werk_in_pijplijn_details():
#     tab = sheet_tab('Sales - force', 'Kansen')
#     data_rows = [
#         row[:2] + [to_int(row[7])] + [to_int(row[8])] + [row[9]]
#         for row in tab[3:]
#         if is_int(row[8]) and to_int(row[8]) > 0
#     ]
#     return data_rows


if __name__ == "__main__":
    os.chdir("..")
    for s_ in top_x_sales(minimal_amount=20000):
        print(s_)
    # print(sales_waarde())
