import os
import warnings

import pandas as pd

from model.caching import cache
from model.utilities import Day
from sources import database as db
from sources.yuki import yuki


#################### DEBITEUREN ################################################


def debiteuren_leeftijd_analyse():
    df = (
        debiteuren_leeftijd_analyse_yuki()
            .groupby(["factuuradres"])
            .agg({'open': 'sum', 'a30': 'sum', "a60": 'sum', 'a90': 'sum', "90plus": 'sum'})
            .reset_index()
            .sort_values("open", ascending=False)
    )
    return df


@cache(hours=24)
def debiteuren_leeftijd_analyse_extranet():
    query = 'select * from age_analysis_view order by 90plus desc, a90 desc, a60 desc'
    warnings.filterwarnings("ignore")
    result = db.dataframe(query)
    return result


@cache(hours=24)
def debiteuren_leeftijd_analyse_yuki():
    debiteuren = yuki().debtors()
    df = pd.DataFrame(debiteuren)
    df = df.drop(df[df.open <= 0].index)
    # df = df.drop( 'open <= 0', axis=1)
    df['a30'] = df.apply(lambda row: row.open if row.days < 30 else 0, axis=1)
    df['a60'] = df.apply(lambda row: row.open if 30 <= row.days < 60 else 0, axis=1)
    df['a90'] = df.apply(lambda row: row.open if 60 <= row.days < 90 else 0, axis=1)
    df['90plus'] = df.apply(lambda row: row.open if row.days >= 90 else 0, axis=1)
    df.rename(columns={'customer': 'factuuradres'}, inplace=True)
    df = (
        df.groupby(["factuuradres"])
        .agg({'open': 'sum', 'a30': 'sum', "a60": 'sum', 'a90': 'sum', "90plus": 'sum'})
        .reset_index()
    )
    df = df.sort_values("open", ascending=False)
    return df


@cache(hours=24)
def debiteuren_openstaand():
    dla = debiteuren_leeftijd_analyse()
    return dla['open'].sum()


@cache(hours=24)
def debiteuren_30_60_90():
    dla = debiteuren_leeftijd_analyse()
    a30 = dla['a30'].sum()
    a60 = dla['a60'].sum()
    a90 = dla['a90'].sum()
    plus90 = dla['90plus'].sum()
    return (a30, a60, a90, plus90)


def debiteuren_30_60_90_extranet():
    dla = debiteuren_leeftijd_analyse_extranet()
    a30 = dla['a30'].sum()
    a60 = dla['a60'].sum()
    a90 = dla['a90'].sum()
    plus90 = dla['90plus'].sum()
    return (a30, a60, a90, plus90)


def debiteuren_30_60_90_yuki():
    dla = debiteuren_leeftijd_analyse_yuki()
    a30 = int(dla['a30'].sum())
    a60 = int(dla['a60'].sum())
    a90 = int(dla['a90'].sum())
    plus90 = int(dla['90plus'].sum())
    return (a30, a60, a90, plus90)


def gemiddelde_betaaltermijn(days=90):
    query = f'''select avg(datediff(payment_date,invoice_date)) as days
                from invoice where payment_date >= DATE(NOW()) - INTERVAL {days} DAY'''
    return db.value(query)


#################### CASH EN WERKKAPITAAL ################################################
CASH_ACCOUNTS = (
    '11000',  # RC
    '12000',  # Spaaar
    '12001',  # Salarisrekeninb
    '12002',  # G-Rekening
    '23101',  # Kruisposten
)
DEBITEUREN = ('13000',)
CREDITEUREN = ('16000',)
OVERIGE_VLOTTENDE_ACTIVA = (
    '13300',  # Nog te ontvangen
    '13350',  # Vooruitbetalingen
    '13460',  # Waarborgsommen
    '13999',  # Overige kortlopende vorderingen (bedrag op de Qikker rekening)
    '18900',  # Lokale BTW in andere EU landen
    '23020',  # Vraagposten
    '23310',  # Tussenrekening creditcardbetalingen
)
OVERIGE_VLOTTENDE_PASSIVA = (
    '15000',  # VISA card 15000
    '16100',  # Nog te ontvangen facturen 16100
    '16999',  # Overige kortlopende schulden (Nog af te betalen aan Michiel)
    '17000',  # Te betalen lonen 17000
    '17100',  # Loonheffing 17100
    '17105',  # Ingehouden loonheffing 17105
    '17110',  # Belastinschuld LB 17110
    '17500',  # Reservering voor vakantiegeld 17500
    '17900',  # Tussenrekening VPB 17900
    '18000',  # Btw over leveringen/diensten belast met hoog tarief 18000
    '18600',  # Leveringen buiten de EU 18600
    '18611',  # Leveringen binnen de EU 18611
    '18700',  # Leveringen uit landen buiten de EU (invoer) 18700
    '18750',  # Verwervingen uit landen binnen de EU 18750
    '18800',  # Btw voorbelasting 18800
    '18990',  # Overboekingsrekening btw-aangiftes 18990
    '20000',  # RC personeel 20000
    '23000',  # Betalingen onderweg 23000
    '24000',  # Belastingschuld BTW 24000
    '24010',  # Belastingshuld VPB 24010
)


@cache(hours=6)
def balans_full(day: Day = None):
    balans = yuki().account_balance(balance_type='B', day=day)
    all_balance_accounts = (
            CASH_ACCOUNTS + DEBITEUREN + CREDITEUREN + OVERIGE_VLOTTENDE_ACTIVA + OVERIGE_VLOTTENDE_PASSIVA
    )
    # for b in balans:
    #     if b['code'][0] != '0' and b['code'] not in all_balance_accounts and abs(b['amount']) > 6000:
    #         log.log_error(
    #             'finance.py', 'balans_full()', f'Onbekende balanspost {b["code"]} {b["description"]} € {b["amount"]}.'
    #         )
    return balans


def balans_bedrag(rekeningnummers, day: Day = None):
    if type(rekeningnummers) == str:
        rekeningnummers = {rekeningnummers}
    rekeningen = [rekening for rekening in balans_full(day) if rekening['code'] in rekeningnummers]
    result = sum([rekening['amount'] for rekening in rekeningen])
    return result


def cash(day: Day = None):
    cash = balans_bedrag(CASH_ACCOUNTS, day=day)
    return cash


def debiteuren(day: Day = None):
    debiteuren = balans_bedrag(DEBITEUREN, day=day)
    return debiteuren


def crediteuren(day: Day = None):
    return -balans_bedrag(CREDITEUREN, day=day)


def bruto_werkkapitaal(day: Day = None):
    # Bruto werkkapitaal is debiteuren -/- crediteuren
    return debiteuren(day) - crediteuren(day)


def netto_werkkapitaal(day: Day = None):
    # Netto werkkapitaal is vlottende activa -/- vlottende passiva
    return vlottende_activa(day) - vlottende_passiva(day)


def vlottende_activa(day: Day = None):
    return cash(day) + debiteuren(day) + balans_bedrag(OVERIGE_VLOTTENDE_ACTIVA, day=day)


def vlottende_passiva(day: Day = None):
    return crediteuren(day) + balans_bedrag(OVERIGE_VLOTTENDE_PASSIVA, day=day)


if __name__ == '__main__':
    os.chdir('..')
    print('cash', cash())
    print('debiteuren', debiteuren())
    print('crediteuren ', crediteuren())
    print('Bruto werkkapitaal', bruto_werkkapitaal())
    print('Netto werkkapitaal', netto_werkkapitaal())
