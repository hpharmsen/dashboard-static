import datetime
import os
import warnings

import pandas as pd

from model import errors
from model.caching import reportz
from sources import database as db
from sources.yuki import yuki
from model.trendline import trends

#################### DEBITEUREN ################################################


def debiteuren_leeftijd_analyse():
    df = debiteuren_leeftijd_analyse_extranet()
    yuki_result = debiteuren_leeftijd_analyse_yuki()
    df = df.append(yuki_result, ignore_index=True)
    df = (
        df.groupby(["factuuradres"])
        .agg({'open': 'sum', 'a30': 'sum', "a60": 'sum', 'a90': 'sum', "90plus": 'sum'})
        .reset_index()
    )
    df = df.sort_values("open", ascending=False)
    return df


@reportz(hours=24)
def debiteuren_leeftijd_analyse_extranet():
    query = 'select * from age_analysis_view order by 90plus desc, a90 desc, a60 desc'
    warnings.filterwarnings("ignore")
    result = db.dataframe(query)
    return result


@reportz(hours=24)
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


@reportz(hours=24)
def debiteuren_openstaand():
    dla = debiteuren_leeftijd_analyse()
    return dla['open'].sum()


@reportz(hours=24)
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
CASH_ACCOUNTS = ('11000', '12000', '12001', '12002', '23101')
DEBITEUREN = ('13000',)
CREDITEUREN = ('16000',)
OVERIGE_VLOTTENDE_ACTIVA = ('13300', '13350', '13460', '18900', '23020', '23310')
OVERIGE_VLOTTENDE_PASSIVA = (
    '15000',  # VISA card 15000
    '16100',  # Nog te ontvangen facturen 16100
    '17000',  # Te betalen lonen 17000
    '17100',  # Loonheffing 17100
    '17105',  # Ingehouden loonheffing 17105
    '17110',  # Belastinschuld LB 17110
    '17500',  # Reservering voor vakantiegeld 17500
    '17900',  # Tussenrekening VPB 17900
    '18000',  # Btw over leveringen/diensten belast met hoog tarief 18000
    '18600',  # Leveringen buiten de EU 18600
    '18611',  # Levereingen binnen de EU 18611
    '18700',  # Leveringen uit landen buiten de EU (invoer) 18700
    '18750',  # Verwervingen uit landen binnen de EU 18750
    '18800',  # Btw voorbelasting 18800
    '18990',  # Overboekingsrekening btw-aangiftes 18990
    '20000',  # RC personeel 20000
    '23000',  # Betalingen onderweg 23000
    '24000',  # Belastingschuld BTW 24000
    '24010',  # Belastingshuld VPB 24010
)


# @reportz(hours=6)
def balans_full(date_str=''):
    balans = yuki().account_balance(balance_type='B', date_str=date_str)
    all_balance_accounts = (
        CASH_ACCOUNTS + DEBITEUREN + CREDITEUREN + OVERIGE_VLOTTENDE_ACTIVA + OVERIGE_VLOTTENDE_PASSIVA
    )
    for b in balans:
        if b['code'][0] != '0' and b['code'] not in all_balance_accounts and abs(b['amount']) > 1:
            errors.log_error(
                'finance.py', 'balans_full()', f'Onbekende balanspost {b["code"]} {b["description"]} € {b["amount"]}.'
            )
    return balans


def balans_bedrag(rekeningnummers, date_str=''):
    if type(rekeningnummers) == str:
        rekeningnummers = {rekeningnummers}
    rekeningen = [rekening for rekening in balans_full(date_str) if rekening['code'] in rekeningnummers]
    result = sum([rekening['amount'] for rekening in rekeningen])
    return result


def cash(date_str=''):
    cash = balans_bedrag(CASH_ACCOUNTS, date_str=date_str)
    trends.update('cash', int(cash))
    return cash


def debiteuren(date_str=''):
    debiteuren = balans_bedrag(DEBITEUREN, date_str=date_str)
    return debiteuren


def crediteuren(date_str=''):
    return -balans_bedrag(CREDITEUREN, date_str=date_str)


def bruto_werkkapitaal(date_str=''):
    # Bruto werkkapitaal is debiteuren -/- crediteuren
    return debiteuren(date_str) - crediteuren(date_str)


def netto_werkkapitaal(date_str=''):
    # Netto werkkapitaal is vlottende activa -/- vlottende passiva
    return vlottende_activa(date_str) - vlottende_passiva(date_str)


def vlottende_activa(date_str=''):
    # Nog te ontvangen goederen en diensten 13300
    # Vooruitbetalingen 13350
    # Waarborgsommenn 13460
    # Lokale BTW in andere EU landen 18900
    # Vraagposten 23020
    # Tussenrekening creditcardbetalngen 23310
    return cash(date_str) + debiteuren(date_str) + balans_bedrag(OVERIGE_VLOTTENDE_ACTIVA, date_str=date_str)


def vlottende_passiva(date_str=''):
    return crediteuren(date_str) + balans_bedrag(OVERIGE_VLOTTENDE_PASSIVA, date_str=date_str)


if __name__ == '__main__':
    os.chdir('..')
    print('cash', cash())
    print('debiteuren', debiteuren())
    print('crediteuren ', crediteuren())
    print('Bruto werkkapitaal', bruto_werkkapitaal())
    print('Netto werkkapitaal', netto_werkkapitaal())
