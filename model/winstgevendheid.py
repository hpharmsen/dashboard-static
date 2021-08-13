import os
import sys
from datetime import datetime
import pandas as pd
from functools import partial

#from model import errors
from model.log import log_error
from sources.googlesheet import sheet_tab, sheet_value, to_int, to_float
from sources import database as db
from model.caching import reportz

# from model.productiviteit import productiviteit_overzicht
from model.utilities import fraction_of_the_year_past
#from model.resultaat import virtuele_maand
from sources.simplicate import hours_dataframe, simplicate, DATE_FORMAT

MT_SALARIS = 122024
OVERIGE_KOSTEN_PER_FTE_PER_MAAND = 1000
USER_MAPPING = {
    "geertjan": "geert-jan",
    "raymond": "ray",
    "jeroen": "jeroens",
    "robinveer": "robin",
    "vinz.timmermans":"vinz",
    "jordy.boelhouwer":"jordy"
}  # Map Simplicate name to oberon id


def parse_date(date_str):
    d, m, y = date_str.split()
    d = int(d)
    m = ['jan.', 'feb.', 'mrt.', 'apr.', 'mei', 'jun.', 'jul.', 'aug.', 'sep.', 'okt.', 'nov.', 'dec.'].index(m) + 1
    y = int(y)
    return d, m, y


@reportz(hours=60)
def loonkosten_per_persoon():
    """Dict met gegevens uit het contracten sheet met user als key
    en velden:
    - bruto: Bruto maandsalaris
    - kosten_ft: Maandelijkse kosten voor Oberon op basis van fulltime
    - uren: Aantal uur per week
    - kosten_jaar: Werkelijke kosten dit jaar rekening houdend met startdatum en part time"""
    contracten = sheet_tab('Contracten werknemers', 'Fixed')
    if not contracten:
        return []  # Error in the spreadsheet
    ex_werknemers = sheet_tab('Contracten werknemers', 'ex werknemers')
    if not ex_werknemers:
        return []  # Error in the spreadsheet
    id_col = contracten[0].index('Id')
    bruto_col = contracten[0].index('Bruto')
    kosten_col = contracten[0].index('Kosten voor Oberon obv full')
    uren_col = contracten[0].index('UrenPerWeek')
    start_date_col = contracten[0].index('InDienstGetreden')
    end_date_col = ex_werknemers[0].index('Einddatum')
    rdb = {'bruto': MT_SALARIS / 12, 'kosten_ft': MT_SALARIS / 12, 'uren': 40, 'kosten_jaar': MT_SALARIS}
    gert = {
        'bruto': MT_SALARIS / 12 * 32 / 40,
        'kosten_ft': MT_SALARIS / 12,
        'uren': 32,
        'kosten_jaar': MT_SALARIS * 32 / 40,
    }
    joost = {
        'bruto': MT_SALARIS * 104 / 110 / 12 * 36 / 40,
        'kosten_ft': MT_SALARIS * 104 / 110 / 12,
        'uren': 36,
        'kosten_jaar': MT_SALARIS * 36 / 40,
    }
    hph = rdb
    users = {'rdb': rdb, 'gert': gert, 'hph': hph, 'joost': joost}
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
                    log_error(
                        'winstgevendheid.py', 'loonkosten_per_persoon()', 'End date is not filled in for ' + line[2]
                    )
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


# @reportz(hours=24)
# def uren_geboekt():
#     y = datetime.today().year
#     query = f'select user, sum(hours) as hours from timesheet where year(day)={y} group by user'
#     return {rec['user']: rec['hours'] for rec in db.table(query)}
#
#
# @reportz
# def uren_geboekt_persoon(user):
#     table = uren_geboekt()
#     value = table.get(user, 0)
#     return value


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


#@reportz
def uurkosten_per_persoon():
    employees = simplicate().employee()
    name2user = {
        t["name"]: get_oberon_id_from_email(t["work_email"])
        for t in employees
        if t.get("name") and t.get('work_email')
    }
    user2name = {value: key for key, value in name2user.items()}
    loonkosten_pp = loonkosten_per_persoon()
    loonkosten_pp = {user2name[key]:val for key, val in loonkosten_pp.items()}
    res = {}
    for user, kosten in loonkosten_pp.items():
        res[user] = round((kosten['kosten_ft'] + OVERIGE_KOSTEN_PER_FTE_PER_MAAND) * 12 / 45 / 40, 2)
    return res

def get_oberon_id_from_email(email):
    # Based on the e-mail address from Simplicate, get the username used in extranet planning database
    id = email.split("@")[0]
    return USER_MAPPING.get(id, id)

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

def calculate_turnover_fixed( projects, row ):
    if row['hours'] and row['turnover hours'] <= 0: # Fixed price. Hours booked but not on hoursturnover
        return projects[row.name]['budget']
    return 0

@reportz(hours=60)
def winst_per_project():
    result = (project_results()
              .drop( 'customer', axis=1 )
              .query('hours >= 10')
              .sort_values(by='margin', ascending=False)
              [['number', 'name', 'hours', 'turnover hours', 'turnover fixed', 'costs of hours', 'margin']]
    )
    result['turnover per hour'] = result.apply( lambda p: round((p['turnover hours']+p['turnover fixed']) / p['hours'],2), axis=1)
    result['margin per hour'] = result.apply( lambda p: round(p['margin'] / p['hours'],2), axis=1)
    return result


@reportz(hours=60)
def winst_per_klant(from_date:datetime=None):
    result = (project_results(from_date)
        .replace(['QS Ventures', 'KV New B.V.'], 'Capital A')
        .replace(['T-Mobile Netherlands B.V.'], 'Ben')
        .groupby(['customer'])[['hours', 'turnover hours', 'turnover fixed', 'costs of hours', 'margin']]
        .sum()
        .query('hours >= 10')
        .sort_values(by='margin', ascending=False)
        .reset_index()
        [['customer', 'hours', 'turnover hours', 'turnover fixed', 'costs of hours', 'margin']]
    )
    result['turnover per hour'] = (result['turnover hours'] + result['turnover fixed']) / result['hours']
    result['margin per hour'] = result['margin'] / result['hours']
    return result


@reportz(hours=60)
def project_results(from_date:datetime=None):

    uurkosten = uurkosten_per_persoon()
    simplicate_projects = simplicate().project()
    projects = {p['id']: {'name':p['name'],
                          'customer':p['organization']['name'],
                          'number':p['project_number'],
                          'budget': max(p['budget']['total']['value_budget'],p['budget']['total']['value_spent'])}
                for p in simplicate_projects}

    filter = 'type=="normal" and employee != "Freelancer" and organization != "Oberon"'
    #filter += ' and project_number.str.contains("CAP-")'
    if from_date:
        filter += f' and day>="{from_date.strftime(DATE_FORMAT)}"'
    df = hours_dataframe().query(filter)
    pd.options.mode.chained_assignment = None # Ignore 'A value is trying to be set on a copy of a slice from a DataFrame' error
    df['costs of hours'] = df.apply(lambda a: uurkosten.get(a['employee'],0) * a['hours'], axis=1)

    result = (df.groupby(['project_id'])[['hours', 'turnover', 'costs of hours']]
                .sum()
                .rename(columns={'turnover':'turnover hours'})
              )
    result['customer'] = result.apply( lambda p: projects[p.name]['customer'], axis=1)
    result['name'] = result.apply(lambda p: projects[p.name]['name'], axis=1)
    result['number'] = result.apply( lambda p: projects[p.name]['number'], axis=1)
    result = result[~result.number.isin(['TRAV-1','QIKK-1','SLIM-28','TOR-3'])]
    result['turnover fixed'] = result.apply( partial( calculate_turnover_fixed, projects), axis=1)
    result.loc[result.number=='CAP-8', ['hours','costs of hours','turnover fixed']] = 20, 20*75, 6000 # Fix for CAP-8 since it cannot be edited in Simplicate
    result['margin'] = result['turnover hours'] + result['turnover fixed'] - result['costs of hours']
    return result


if __name__ == '__main__':
    os.chdir('..')
    u = uurkosten_per_persoon()
    print(winst_per_project())
