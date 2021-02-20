import os
import sys
from datetime import datetime
import pandas as pd

from sources.googlesheet import sheet_tab, sheet_value, to_int, to_float
from sources import database as db
from model.caching import reportz

# from model.productiviteit import productiviteit_overzicht
from model.utilities import fraction_of_the_year_past
from model.resultaat import virtuele_maand

MT_SALARIS = 122024


def parse_date(date_str):
    d, m, y = date_str.split()
    d = int(d)
    m = ['jan.', 'feb.', 'mrt.', 'apr.', 'mei', 'jun.', 'jul.', 'aug.', 'sep.', 'okt.', 'nov.', 'dec.'].index(m) + 1
    y = int(y)
    return d, m, y


# @reportz(hours=60)
def loonkosten_per_persoon():
    """Dict met gegevens uit het contracten sheet met user als key
    en velden:
    - bruto: Bruto maandsalaris
    - kosten_ft: Maandelijkse kosten voor Oberon op basis van fulltime
    - uren: Aantal uur per week
    - kosten_jaar: Werkelijke kosten dit jaar rekening houdend met startdatum en part time"""
    contracten = sheet_tab('Contracten werknemers', 'Fixed')
    ex_werknemers = sheet_tab('Contracten werknemers', 'ex werknemers')
    id_col = contracten[0].index('Id')
    bruto_col = contracten[0].index('Bruto')
    kosten_col = contracten[0].index('Kosten voor Oberon obv full')
    uren_col = contracten[0].index('UrenPerWeek')
    start_date_col = contracten[0].index('InDienstGetreden')
    end_date_col = ex_werknemers[0].index('Einddatum')
    rdb = {'bruto': MT_SALARIS / 12, 'kosten_ft': MT_SALARIS / 12, 'uren': 40, 'kosten_jaar': MT_SALARIS}
    gert = {
        'bruto': MT_SALARIS / 12 * 4 / 5,
        'kosten_ft': MT_SALARIS / 12,
        'uren': 32,
        'kosten_jaar': MT_SALARIS * 4 / 5,
    }
    hph = rdb
    users = {'rdb': rdb, 'gert': gert, 'hph': hph}
    for line in contracten[1:] + ex_werknemers[1:]:
        if line[id_col]:
            d, m, y = parse_date(line[start_date_col])
            if y == datetime.today().year:
                start_year_fraction = (m - 1) / 12 + d / 365
            else:
                start_year_fraction = 0
            end_year_fraction = fraction_of_the_year_past()
            if line in ex_werknemers:
                try:
                    d, m, y = parse_date(line[end_date_col])
                except:
                    print('End date is not filled in for ' + line[2])
                    sys.exit()
                if y < datetime.today().year:
                    continue
                if y == datetime.today().year:
                    end_year_fraction = (m - 1) / 12 + d / 365

            kosten_ft = to_float(line[kosten_col]) if line[kosten_col] else 0
            users[line[id_col]] = {
                'bruto': to_float(line[bruto_col]),
                'kosten_ft': kosten_ft,
                'uren': to_int(line[uren_col]),
                'loonkosten': 12 * kosten_ft * to_int(line[uren_col]) / 40,
                'fraction_of_the_year_worked': end_year_fraction - start_year_fraction,
            }
    return users


@reportz(hours=24)
def overige_kosten_per_fte_per_maand():
    col = virtuele_maand() + 2
    tab = sheet_tab('Oberon key cijfers', 'Data')
    res = sheet_value(tab, 64, col) / (virtuele_maand())
    return res


@reportz(hours=24)
def uren_geboekt():
    y = datetime.today().year
    query = f'select user, sum(hours) as hours from timesheet where year(day)={y} group by user'
    return {rec['user']: rec['hours'] for rec in db.table(query)}


@reportz
def uren_geboekt_persoon(user):
    table = uren_geboekt()
    value = table.get(user, 0)
    return value


# @reportz(hours=60)
# def winst_per_persoon():
#     loonkosten_pp = loonkosten_per_persoon()
#     result = []
#     for line in productiviteit_overzicht():
#         user = line[0]
#         k = loonkosten_pp.get(user)
#         if not k:
#             continue
#         omzet = line[1]
#         loon_kosten = k['loonkosten'] * k['fraction_of_the_year_worked']
#         overige_kosten = overige_kosten_per_fte_per_maand() * k['fraction_of_the_year_worked'] * 12 * k['uren'] / 40
#         alle_kosten = loon_kosten + overige_kosten
#         kosten_per_uur = alle_kosten / uren_geboekt_persoon(user) if uren_geboekt_persoon(user) > 0 else 0
#         entry = [user, k['uren'], omzet, loon_kosten, overige_kosten, kosten_per_uur, omzet - alle_kosten]
#         result += [entry]
#     return sorted(result, key=lambda a: -a[6] / a[1])


@reportz
def uurkosten_per_persoon():
    loonkosten_pp = loonkosten_per_persoon()
    ov = overige_kosten_per_fte_per_maand()
    res = {}
    for user, kosten in loonkosten_pp.items():
        res[user] = (kosten['kosten_ft'] * kosten['uren'] / 40 + ov) * 12 / 45 / 40
    return res


@reportz(hours=24)
def gefactureerd_op_project(projectId):
    query = f'select ifnull(sum( invoice_amount),0) as turnover from invoice where project_id={projectId}'
    return db.value(query)


@reportz(hours=24)
def kosten_project_jaar(projectId, y):
    uurkosten_pp = uurkosten_per_persoon()
    kosten = 0
    query = f'select user, sum(hours) as hours from timesheet where projectId={projectId} and year(day)={y}'
    for rec in db.table(query):
        kosten += rec['hours'] * uurkosten_pp.get(rec['user'], 12.5 * 1.15)  # Default voor de uurloners
    return kosten


@reportz(hours=60)
def winst_per_project():
    y = datetime.today().year

    # Bereken uurkosten inclusief werkgeverslasten en overige personeelskosten
    hourly_user_costs = uurkosten_per_persoon()

    # Haal lijst met klanten/projecten op met daarbij welk percentage van de uren in dit jaar was
    query = f'''select p.id, c.name as klant, p.title as project, sum(if(year(day)={y}, hours,0)) as hours_this_year, 
                      sum(if(year(day)={y-1}, hours,0)) as hours_last_year
                from project p
                join timesheet ts on ts.projectid=p.id
                join customer c on c.id=p.customerId
                where p.year in ({y-1},{y}) and customerId not in (4,125)
                group by p.id
                having hours_this_year>0
                order by p.id'''
    projects = db.table(query)

    if not projects:
        return []

    # Loop door de projecten
    res = []
    for p in projects:
        uren_perc_dit_jaar = p['hours_this_year'] / (p['hours_this_year'] + p['hours_last_year'])
        omzet = gefactureerd_op_project(p['id']) * uren_perc_dit_jaar
        kosten = kosten_project_jaar(p['id'], y)
        res += [
            {
                'klant': p['klant'],
                'project': p['project'],
                'uren': p['hours_this_year'],
                'omzet': omzet,
                'kosten': kosten,
                'winst': omzet - kosten,
            }
        ]
    return pd.DataFrame(res)[['klant', 'project', 'uren', 'omzet', 'kosten', 'winst']].sort_values(
        by='winst', ascending=False
    )


@reportz(hours=60)
def winst_per_klant():
    return (
        winst_per_project()
        .groupby(['klant'])
        .agg({'uren': 'sum', 'omzet': 'sum', 'kosten': 'sum', 'winst': 'sum'})
        .reset_index()
        .sort_values(by='winst', ascending=False)
    )


if __name__ == '__main__':
    os.chdir('..')
    print(winst_per_project())
