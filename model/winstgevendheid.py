import os
from datetime import datetime
import pandas as pd
from functools import partial

from model.log import log_error
from sources.googlesheet import sheet_tab, to_int, to_float
from model.caching import reportz, use_cache

from model.utilities import fraction_of_the_year_past
from sources.simplicate import hours_dataframe, simplicate, DATE_FORMAT, user2name, name2user

MT_SALARIS = 110000
OVERIGE_KOSTEN_PER_FTE_PER_MAAND = 1000
OVERIGE_KOSTEN_PER_FREELANCE_FTR_PER_UUR = (
    (139 + 168 + 47) / 4 / 40
)  # Overige personeelskosten, kantoorkosten (niet huur), Afschrijvingen (niet kantoor)
PRODUCTIVITEIT = 0.85


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
    - maand_kosten_ft: Maandelijkse kosten voor Oberon op basis van fulltime
    - uren: Aantal uur per week
    - kosten_jaar: Werkelijke kosten dit jaar rekening houdend met startdatum en part time"""
    contracten = sheet_tab('Contracten werknemers', 'Fixed')
    if not contracten:
        return []  # Error in the spreadsheet
    ex_werknemers = sheet_tab('Contracten werknemers', 'ex werknemers')
    if not ex_werknemers:
        return []  # Error in the spreadsheet

    # Mensen die een managementfee factureren
    rdb = {'bruto': MT_SALARIS / 12, 'maand_kosten_ft': MT_SALARIS / 12, 'uren': 40}
    gert = {
        'bruto': MT_SALARIS / 12 * 32 / 40,
        'maand_kosten_ft': MT_SALARIS / 12,
        'uren': 32,
    }
    joost = {
        'bruto': MT_SALARIS * 104 / 110 / 12 * 36 / 40,
        'maand_kosten_ft': MT_SALARIS * 104 / 110 / 12,
        'uren': 36,
    }
    hph = rdb
    users = {'rdb': rdb, 'gert': gert, 'hph': hph, 'joost': joost}
    for k in users.keys():
        users[k]['kosten_jaar'] = (MT_SALARIS * users[k]['uren'] / 40,)
        users[k]['jaar_kosten_pt'] = 12 * users[k]['maand_kosten_ft'] * users[k]['uren'] / 40
        users[k]['fraction_of_the_year_worked'] = fraction_of_the_year_past()
    sum_directie = sum([users[k]['jaar_kosten_pt'] for k in users.keys()]) * fraction_of_the_year_past()

    # Werknemers en ex werknemers
    id_col = contracten[0].index('Id')
    bruto_col = contracten[0].index('Bruto')
    kosten_col = contracten[0].index('Kosten voor Oberon obv full')
    uren_col = contracten[0].index('UrenPerWeek')
    start_date_col = contracten[0].index('InDienstGetreden')
    end_date_col = ex_werknemers[0].index('Einddatum')
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

            maand_kosten_ft = (
                to_float(line[kosten_col]) if line[kosten_col] else 0
            )  # Kosten_col zit LH, vakantiegeld etc. al bij in
            users[line[id_col]] = {
                'bruto': to_float(line[bruto_col]),
                'maand_kosten_ft': maand_kosten_ft,
                'uren': to_int(line[uren_col]),
                'jaar_kosten_pt': 12 * maand_kosten_ft * to_int(line[uren_col]) / 40,
                'fraction_of_the_year_worked': end_year_fraction - start_year_fraction,
            }
    sum_all = sum([users[k]['jaar_kosten_pt'] * users[k]['fraction_of_the_year_worked'] for k in users.keys()])
    sum_employees = sum_all - sum_directie

    return users


@reportz(hours=60)
def uurkosten_per_persoon():

    # Vaste werknemers
    loonkosten_pp = loonkosten_per_persoon()
    loonkosten_pp = {user2name()[key]: val for key, val in loonkosten_pp.items() if user2name().get(key)}
    res = {}
    for user, kosten in loonkosten_pp.items():
        res[user] = round(
            (kosten['maand_kosten_ft'] + OVERIGE_KOSTEN_PER_FTE_PER_MAAND) * 12 / 45 / 40 / PRODUCTIVITEIT, 2
        )

    # Freelancers
    freelancers = sheet_tab('Contracten werknemers', 'Freelance')
    if not freelancers:
        log_error(
            'winstgevendheid.py', 'uurkosten_per_persoon', 'kan niet bij Freelance tab in contracten sheet'
        )  # Error in the spreadsheet
        return res
    id_col = freelancers[0].index('Id')
    bruto_per_uur_col = freelancers[0].index('BrutoPerUur')
    for line in freelancers[1:]:
        if line[id_col]:
            name = user2name().get(line[id_col])
            if name:
                res[name] = round(
                    float(line[bruto_per_uur_col].replace(',', '.')) + OVERIGE_KOSTEN_PER_FREELANCE_FTR_PER_UUR, 2
                )

    # Flex
    flex = sheet_tab('Contracten werknemers', 'Flex')
    if not flex:
        log_error(
            'winstgevendheid.py', 'uurkosten_per_persoon', 'kan niet bij Flex tab in contracten sheet'
        )  # Error in the spreadsheet
        return res
    id_col = flex[0].index('Id')
    bruto_per_uur_col = flex[0].index('BrutoPerUur')
    for line in flex[1:]:
        if line[id_col]:
            name = user2name().get(line[id_col])
            if name:
                res[name] = round(
                    float(line[bruto_per_uur_col].replace(',', '.')) + OVERIGE_KOSTEN_PER_FREELANCE_FTR_PER_UUR, 2
                )

    return res


def calculate_turnover_fixed(projects, row):
    if row['hours'] and row['turnover hours'] <= 0:  # Fixed price. Hours booked but not on hoursturnover
        return projects[row.name]['budget']
    return 0


@reportz(hours=60)
def winst_per_project():
    result = (
        project_results()
        .drop('customer', axis=1)
        .query('hours >= 10')
        .sort_values(by='margin', ascending=False)[
            ['number', 'name', 'hours', 'turnover hours', 'turnover fixed', 'costs of hours', 'margin']
        ]
    )
    result['turnover per hour'] = result.apply(
        lambda p: round((p['turnover hours'] + p['turnover fixed']) / p['hours'], 2), axis=1
    )
    result['margin per hour'] = result.apply(lambda p: round(p['margin'] / p['hours'], 2), axis=1)
    return result


@reportz(hours=60)
def winst_per_klant(from_date: datetime = None):
    result = (
        project_results(from_date)
        .replace(['QS Ventures', 'KV New B.V.'], 'Capital A')
        .replace(['T-Mobile Netherlands B.V.'], 'Ben')
        .groupby(['customer'])[['hours', 'turnover hours', 'turnover fixed', 'costs of hours', 'margin']]
        .sum()
        .query('hours >= 10')
        .sort_values(by='margin', ascending=False)
        .reset_index()[['customer', 'hours', 'turnover hours', 'turnover fixed', 'costs of hours', 'margin']]
    )
    result['turnover per hour'] = (result['turnover hours'] + result['turnover fixed']) / result['hours']
    result['margin per hour'] = result['margin'] / result['hours']
    return result


@reportz(hours=24)
def project_results(from_date: datetime = None):

    simplicate_projects = simplicate().project()
    projects = {
        p['id']: {
            'name': p['name'],
            'customer': p['organization']['name'],
            'number': p['project_number'],
            'budget': max(p['budget']['total']['value_budget'], p['budget']['total']['value_spent']),
        }
        for p in simplicate_projects
    }

    df = hours_filtered(from_date)
    uurkosten = uurkosten_per_persoon()
    pd.options.mode.chained_assignment = (
        None  # Ignore 'A value is trying to be set on a copy of a slice from a DataFrame' error
    )
    df['costs of hours'] = df.apply(lambda a: uurkosten.get(a['employee'], 0) * a['hours'], axis=1)

    result = (
        df.groupby(['project_id'])[['hours', 'turnover', 'costs of hours']]
        .sum()
        .rename(columns={'turnover': 'turnover hours'})
    )
    result['customer'] = result.apply(lambda p: projects[p.name]['customer'], axis=1)
    result['name'] = result.apply(lambda p: projects[p.name]['name'], axis=1)
    result['number'] = result.apply(lambda p: projects[p.name]['number'], axis=1)
    result = result[~result.number.isin(['TRAV-1', 'QIKK-1', 'SLIM-28', 'TOR-3'])]
    result['turnover fixed'] = result.apply(partial(calculate_turnover_fixed, projects), axis=1)
    result.loc[result.number == 'CAP-8', ['hours', 'costs of hours', 'turnover fixed']] = (
        20,
        20 * 75,
        6000,
    )  # Fix for CAP-8 since it cannot be edited in Simplicate
    result['margin'] = result['turnover hours'] + result['turnover fixed'] - result['costs of hours']
    return result


@reportz(hours=24)
def winst_per_persoon(from_date: datetime = None):  # Get hours and hours turnover per person

    # Get hours and hours turnover per person
    result = (
        hours_filtered(from_date)
        .groupby(['employee'])[['hours', 'turnover']]
        .sum()
        .rename(columns={'turnover': 'turnover hours'})
        .reset_index()
    )
    # Voeg mensen toe die geen uren boeken
    for employee in ['Angela Duijs', 'Lunah Smits', 'Mel Schuurman', 'Martijn van Klaveren']:
        result = result.append({'employee': employee, 'hours': 0, 'turnover hours': 0}, ignore_index=True)

    # Add results from fixed price projects
    result['turnover fixed'] = 0
    for index, project in fixed_projects(from_date).iterrows():
        person_hours = hours_per_person(index)
        for _, ph in person_hours.iterrows():
            turnover = project['turnover fixed'] / project['hours'] * ph['hours']
            result.loc[result.employee == ph['employee'], 'turnover fixed'] += turnover

    result.loc[result.employee == 'Paulo Nuno da Cruz Moreno', 'employee'] = "Paulo Nuno Da Cruz Moreno"  # !! temporary

    # Add the salary and office costs per person
    result['costs'] = result.apply(calculate_employee_costs, axis=1)

    # Calculate the margin per person
    result['turnover'] = result['turnover hours'] + result['turnover fixed']
    result['margin'] = result['turnover'] - result['costs']
    result = result.sort_values(by='margin', ascending=False)
    return result[['employee', 'hours', 'turnover', 'margin']]


@reportz(hours=24)
def calculate_employee_costs(row):
    user = name2user()[row['employee']]
    loonkosten_user = loonkosten_per_persoon().get(user)
    if loonkosten_user:
        costs = (loonkosten_user['jaar_kosten_pt'] + OVERIGE_KOSTEN_PER_FTE_PER_MAAND * 12) * loonkosten_user[
            'fraction_of_the_year_worked'
        ]
    else:
        # Freelance
        uurkosten = uurkosten_per_persoon().get(row['employee'])
        if not uurkosten:
            return 0
        costs = row['hours'] * (uurkosten + OVERIGE_KOSTEN_PER_FREELANCE_FTR_PER_UUR)
    return costs


def fixed_projects(from_date: datetime):
    return project_results(from_date).query('`turnover fixed` > 0')[['number', 'name', 'hours', 'turnover fixed']]


def hours_per_person(project_id):
    df = hours_dataframe().query(f'project_id=="{project_id}"').groupby(['employee'])[['hours']].sum().reset_index()
    return df


@reportz(hours=24)
def hours_filtered(from_date: datetime = None):
    filter = 'type=="normal" and employee != "Freelancer" and organization != "Oberon"'
    if from_date:
        filter += f' and day>="{from_date.strftime(DATE_FORMAT)}"'
    df = hours_dataframe().query(filter)
    return df


if __name__ == '__main__':
    os.chdir('..')
    use_cache = False
    pp = winst_per_persoon().sort_values(by="employee")
    print(pp)
