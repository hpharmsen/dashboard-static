import json
import math
import os
import datetime
import urllib
import calendar

from dateutil.relativedelta import relativedelta

from model import log
from model.caching import load_cache, reportz
from layout.block import TextBlock, Page, VBlock, HBlock, Grid
from layout.table import Table, TableConfig
from layout.chart import StackedBarChart, ScatterChart, ChartConfig
from layout.basic_layout import defsize, midsize, headersize
from settings import get_output_folder, GREEN, YELLOW, ORANGE, RED, BLACK, GRAY, dependent_color, MAANDEN, BOLD, \
    TOPLINE, DOUBLE_TOPLINE
from model.organisatie import aantal_mensen, aantal_fte, aantal_fte_begroot, verzuimpercentage, vrije_dagen_pool
from model.productiviteit import (
    productiviteit_perc_productie,
    productiviteit_perc_iedereen,
    billable_perc_productie,
    billable_perc_iedereen,
    percentage_directe_werknemers,
    corrections_percentage,
    largest_corrections,
)
from model.resultaat import (
    omzet_begroot,
    bruto_marge_werkelijk,
    omzet_verschil_percentage,
    winst_begroot,
    winst_werkelijk,
    winst_verschil,
    top_x_klanten_laatste_zes_maanden,
    update_omzet_per_week,
    vulling_van_de_planning,
)
from model.finance import debiteuren_30_60_90_yuki, gemiddelde_betaaltermijn
from model.sales import sales_waarde, top_x_sales
from model.travelbase import get_bookings_per_week, BRANDS
from model.trendline import trends
from sources.googlesheet import HeaderSheet
from sources.simplicate import onderhanden_werk
from sources.yuki import yuki
from view.resultaat_berekening import add_row
from view.travelbase import scatterchart as travelbase_scatterchart

# Wat ik zou verwachten in jullie maandrapportage is het volgende (van uitgaande dat er eerst een goede maandafsluiting heeft plaatsgevonden):
# Om mee te beginnen (geconsolideerd en per entiteit):

# Winst-en-verliesrekening
def render_maandrapportage(output_folder, year, month):
    page = Page([VBlock([TextBlock(f'Maandrapportage {MAANDEN[month - 1].lower()}, {year}', headersize),
                         profit_and_loss_block(year, month),
                         balance_block(year, month)])])
    page.render(output_folder / f'monthly{year}_{month:02}.html')


def profit_and_loss_block(year, month):
    maand = MAANDEN[month - 1]
    begroting = HeaderSheet('Begroting 2021', 'Begroting', header_col=2, header_row=2)
    omzetplanning = HeaderSheet('Begroting 2021', 'Omzetplanning')

    grid = Grid(cols=8, has_header=False,
                aligns=['left', 'right', 'right', 'right', '', 'right', 'right', 'right'])

    def add_normal_row(title, result, budget=None):
        if budget:
            budget_month = TextBlock(budget[0], format='.', color=GRAY)
            budget_ytd = TextBlock(budget[1], format='.', color=GRAY)
        else:
            budget_month, budget_ytd = 0, 0
        grid.add_row([TextBlock(title), TextBlock(result[0], format='.'), '',budget_month,'', TextBlock(result[1], format='.'), '', budget_ytd])

    def add_subtotal_row(title, subtotal, budget=None, style=TOPLINE):
        if budget:
            budget_month = TextBlock(budget[0], format='.', color=GRAY, style=BOLD)
            budget_ytd = TextBlock(budget[1], format='.', color=GRAY, style=BOLD)
        else:
            budget_month, budget_ytd = 0, 0
        grid.add_row([TextBlock(title, style=BOLD),'',
                     TextBlock(subtotal[0], format='.', style=BOLD), budget_month, '','',
                     TextBlock(subtotal[1], format='.', style=BOLD), budget_ytd],
                     styles = ['', style, style, '', '', style, style, ''])

    def yuki_figures(post, year, month, negate=False):
        date = last_date_of_month(year, month)
        prev_date = last_date_of_month(year, month - 1) if month > 1 else last_date_of_month(year - 1, 12)
        negation = -1 if negate else 1
        ytd = yuki().post(post, date) * negation
        monthly = ytd - yuki().post(post, prev_date) * negation
        return (monthly, ytd)

    def turnover_planning(begroting_posts):

        def budget_ytd(sheet, post):
            return sum([get_int(sheet[post, MAANDEN[m - 1]]) for m in range(1, month + 1)])

        if type(begroting_posts) != list:
            begroting_posts = [begroting_posts]
        planned_month = sum([budget_column(omzetplanning, post) for post in begroting_posts])
        planned_ytd = sum([budget_ytd(omzetplanning, post) for post in begroting_posts])
        return (planned_month, planned_ytd)

    def budgeted(begroting_posts):

        def budget_month(sheet, post):
            return get_int(sheet[post,maand]) - get_int(sheet[post,MAANDEN[month - 2]]) if month else budget_column(post)

        if type(begroting_posts) != list:
            begroting_posts = [begroting_posts]
        planned_month = sum([budget_month(begroting, post) for post in begroting_posts]) * 1000
        planned_ytd = sum([budget_column(begroting, post) for post in begroting_posts]) * 1000
        return (planned_month, planned_ytd)

    def get_int(str):
        return int(str.replace('.', '')) if str else 0

    def budget_column(sheet, post):
        return get_int(sheet[post, maand])


    # Header
    grid.add_row(['', '', TextBlock(maand, style=BOLD), TextBlock('begroot', color=GRAY),'','',TextBlock('ytd', style=BOLD), TextBlock('begroot', color=GRAY)],
                 styles=['width:160px;','','','','width:80px;'])

    # Product propositie
    omzet_projecten = yuki_figures('productproposition', year, month, negate=True)
    add_normal_row('Omzet projecten', omzet_projecten)

    projectkosten =  yuki_figures('project_expenses', year, month, negate=True)
    add_normal_row('Projectkosten', projectkosten)

    product_propositie = tuple_add(omzet_projecten, projectkosten)
    product_propositie_budgeted = turnover_planning('Projectklanten totaal')
    add_subtotal_row('Productpropositie', product_propositie, product_propositie_budgeted)
    grid.add_row()

    # Team propositie
    omzet_trajecten = yuki_figures('teamproposition', year, month, negate=True)
    add_normal_row('Omzet trajecten', omzet_trajecten)

    uitbesteed_werk =  yuki_figures('outsourcing_expenses', year, month, negate=True)
    add_normal_row('Uitbesteed werk', uitbesteed_werk)

    team_propositie = tuple_add(omzet_trajecten, uitbesteed_werk)
    team_propositie_budgeted = turnover_planning('Trajectklanten totaal')
    add_subtotal_row('Teampropositie', team_propositie, team_propositie_budgeted)
    grid.add_row()

    # Service
    service = yuki_figures('service', year, month, negate=True)
    service_budgeted = turnover_planning( 'Service totaal')
    add_subtotal_row('Service', service, service_budgeted)
    grid.add_row()

    # Hosting
    omzet_hosting = yuki_figures('hosting', year, month, negate=True)
    add_normal_row('Omzet hosting', omzet_hosting)

    hostingkosten =  yuki_figures('hosting_expenses', year, month, negate=True)
    add_normal_row('Hostingkosten', hostingkosten)

    hosting = tuple_add(omzet_hosting, hostingkosten)
    hosting_budgeted = turnover_planning('Hosting totaal')
    add_subtotal_row('Hosting', hosting, hosting_budgeted)
    grid.add_row()

    # Travelbase
    travelbase = (0,0)
    travelbase_budgeted = turnover_planning('Travelbase totaal')
    add_subtotal_row('Travelbase', travelbase, travelbase_budgeted)
    grid.add_row()

    # Overige inkomsten
    other = yuki_figures('other_income', year, month, negate=True)
    other_budgeted = (0,0)
    add_subtotal_row('Overige inkomsten', other, other_budgeted)
    grid.add_row()

    # BRUTO MARGE
    grid.add_row()
    margin = tuple_add(product_propositie, team_propositie, service, hosting, travelbase, other)
    margin_budgeted = tuple_add( product_propositie_budgeted, team_propositie_budgeted, service_budgeted, hosting_budgeted, travelbase_budgeted, other_budgeted)
    add_subtotal_row('BRUTO MARGE', margin, margin_budgeted, style=DOUBLE_TOPLINE)
    grid.add_row()
    grid.add_row()

    # Personeel
    wbso =  yuki_figures('subsidy', year, month)
    people = tuple(p-w for p,w in zip(yuki_figures('people', year, month), wbso))
    people_budgeted = budgeted(['Management','Medewerkers'])
    add_normal_row('Mensen', people, people_budgeted)

    wbso_budgeted = tuple (-x for x in budgeted( 'Subsidie'))
    add_normal_row('WBSO', wbso, wbso_budgeted)

    personnell = tuple_add(people, wbso)
    add_subtotal_row('Personeelskosten', personnell)
    grid.add_row()

    # Bedrijfskosten
    housing = yuki_figures('housing', year, month)
    housing_budgeted = budgeted( 'Huisvesting')
    add_normal_row('Mensen', housing, housing_budgeted)

    marketing =  yuki_figures('marketing', year, month)
    marketing_budgeted = budgeted( 'Marketing')
    add_normal_row('Sales / Marketing', marketing, marketing_budgeted)

    other_expenses =  yuki_figures('other_expenses', year, month)
    other_expenses_budgeted = budgeted( 'Overige kosten')
    add_normal_row('Overige kosten', other_expenses, other_expenses_budgeted)

    company_costs = tuple_add(housing, marketing, other_expenses)
    add_subtotal_row('Bedrijfskosten', company_costs)
    grid.add_row()

    # BEDRIJFSLASTEN
    operating_expenses = tuple_add(personnell, company_costs)
    operating_expenses_budgeted = tuple_add( people_budgeted, wbso_budgeted, housing_budgeted, marketing_budgeted, other_expenses_budgeted)
    add_subtotal_row('TOTAAL BEDRIJFSLASTEN', operating_expenses, operating_expenses_budgeted, style=DOUBLE_TOPLINE)
    grid.add_row()
    grid.add_row()

    # Deprecation
    depreciation = yuki_figures('depreciation', year, month, negate=True)
    depreciation_budgeted = budgeted( 'Afschrijvingen')
    add_subtotal_row('Afschrijvingen', depreciation, depreciation_budgeted, style='')

    # Financial
    financial = yuki_figures('financial_result', year, month, negate=True)
    financial_budgeted = (0,0)
    add_subtotal_row('Financieel resultaat', financial, financial_budgeted, style='')
    grid.add_row()

    # Winst
    total_costs =  tuple_add( operating_expenses, depreciation, financial )
    profit = [m-c for m,c in zip(margin,total_costs)]
    total_costs_budgeted =  tuple_add( operating_expenses_budgeted, depreciation_budgeted, financial_budgeted )
    profit_budgeted = [m-c for m,c in zip(margin_budgeted,total_costs_budgeted)]
    add_subtotal_row('Winst volgens de boekhouding', profit, profit_budgeted, style=DOUBLE_TOPLINE)

    wip_now, wip_last_month = get_work_in_progress(year, month)
    mutation_wip = (wip_now-wip_last_month,wip_now-0) # !! Die 0 is in 2021 het geval. Moet per 2022 wellicht anders.
    add_subtotal_row('Mutatie onderhanden werk', mutation_wip, style='')
    total_profit = tuple_add(profit, mutation_wip)
    grid.add_row([TextBlock('TOTAAL WINST', style=BOLD), '',
                  TextBlock(total_profit[0], format='.', style=BOLD), '', '', '',
                  TextBlock(total_profit[1], format='.', style=BOLD)],
                 styles=['', '', 'border:2px solid gray', '', '', '', 'border:2px solid gray'])


    return VBlock([TextBlock(f'Winst & verliesrekening', midsize), grid])

# Balans
def balance_block(year, month):
    maand = MAANDEN[month - 1]
    volgende_maand = MAANDEN[month] if month < 12 else MAANDEN[0]
    grid = Grid(cols=6, has_header=False, aligns=['left', 'right', 'right', '', 'right', 'right'])

    def add_normal_row(title, result):
        grid.add_row([TextBlock(title), TextBlock(result[0], format='.'), '', '', TextBlock(result[1], format='.', color="GRAY"), ''])


    def add_subtotal_row( title, subtotal, style=TOPLINE ):
        grid.add_row([TextBlock(title, style=BOLD), '',
                      TextBlock(subtotal[0], format='.', style=BOLD), '', '',
                      TextBlock(subtotal[1], format='.', style=BOLD, color="GRAY")],
                     styles=['', style, style, '', style, style])

    def yuki_figures(post, year, month):
        date = last_date_of_month(year, month)
        prev_date = last_date_of_month(year, month - 1) if month > 1 else last_date_of_month(year - 1, 12)
        current_value = yuki().post(post, date)
        previous_value = yuki().post(post, prev_date)
        return (current_value, previous_value)

    # Header
    grid.add_row(['', '', TextBlock(f'1 {volgende_maand.lower()}', style=BOLD),
                  '', '', TextBlock(f'1 {maand.lower()}', style=BOLD, color=GRAY)],
                 styles=['width:160px;','','','width:80px;'])

    # Materiele vaste activa
    tangible_fixed_assets = yuki_figures('tangible_fixed_assets', year, month)
    add_normal_row('Materiële vaste activa', tangible_fixed_assets)

    # Financiële vaste activa
    financial_fixed_assets = yuki_figures('financial_fixed_assets', year, month)
    add_normal_row('Financiële vaste activa', financial_fixed_assets)

    # Vaste activa
    fixed_assets = tuple_add(tangible_fixed_assets, financial_fixed_assets)
    add_subtotal_row( 'Vaste activa', fixed_assets)

    # Debiteuren
    debtors = yuki_figures('debtors', year, month)
    add_normal_row('Debiteuren',debtors )

    # Overige vorderingen
    other_receivables = yuki_figures('other_receivables', year, month)
    add_normal_row('Overige vorderingen',other_receivables )

    # Onderhanden werk
    work_in_progress = get_work_in_progress(year,month)
    add_normal_row('Onderhanden werk', work_in_progress )

    # Liquide middelen
    liquid_assets = yuki_figures('liquid_assets', year, month)
    add_normal_row('Liquide middelen', liquid_assets)

    # Vlottende activa
    current_assets = tuple_add(debtors, other_receivables, work_in_progress, liquid_assets )
    add_subtotal_row( 'Vlottende activa', current_assets)

    # TOTAAL ACTIVA
    total_assets = tuple_add(fixed_assets, current_assets)
    add_subtotal_row( 'TOTAAL ACTIVA', total_assets, style=DOUBLE_TOPLINE)
    grid.add_row([])

    # Aandelenkapitaal
    share_capital = yuki_figures('share_capital', year, month)
    add_normal_row('Aandelenkapitaal', share_capital)

    # Reserves
    reserves = yuki_figures('reserves', year, month)
    add_normal_row('Reserves', reserves)

    # Onverdeeld resultaat
    undistributed_result = yuki_figures('undistributed_result', year, month)
    add_normal_row('Onverdeeld resultaat', undistributed_result)

    # Eigen vermogen
    equity = tuple_add( share_capital, reserves, undistributed_result)
    add_subtotal_row('Eigen vermogen', equity)

    # Crediteuren
    creditors = yuki_figures('creditors', year, month)
    add_normal_row('Crediteuren', creditors)

    # Medewerkers
    employees = yuki_figures('debts_to_employees', year, month)
    add_normal_row('Medewerkers', employees)

    # Belasting
    taxes = yuki_figures('taxes', year, month)
    add_normal_row('Belastingen', taxes)

    # Overige schulden
    other_debts = yuki_figures('other_debts', year, month)
    add_normal_row('Overige schulden', other_debts)

    # Kortlopende schulden
    short_term_debt = tuple_add(creditors, employees, taxes, other_debts)
    add_subtotal_row('Kortlopende schulden', short_term_debt)

    # TOTAAL PASSIVA
    total_liabilities = tuple_add(equity, short_term_debt)
    add_subtotal_row('TOTAAL PASSVA', total_liabilities, style=DOUBLE_TOPLINE)
    grid.add_row([])

    # Tijd voor wat checks
    #assert total_assets == total_liabilities, f"Balans klopt niet {total_assets} != {total_liabilities}"

    return VBlock([TextBlock(f'Balans per 1 {volgende_maand.lower()} {year}', midsize), grid])


def tuple_add(*args):
    return [sum(l) for l in list(zip(*args))]

def get_work_in_progress(year, month):
    return (onderhanden_werk(year, month, calendar.monthrange(year, month)[1]),
            onderhanden_werk(year, month, calendar.monthrange(year, month - 1)[1]) if month > 1 else 0)  # !! Moet anders vanaf 2022

# Kasstroomoverzicht
# Deze dan ook in vergelijking met de vastgestelde begroting.
#
# In de maandrapportage zou ik dan geschreven toelichtingen verwachten omtrent afwijkingen van de begroting en belangrijke ontwikkelingen.
#
#
#
# Vervolgens aangevuld met voor jullie belangrijke KPI’s.
#
# Welke dat exact zijn, is sterk afhankelijk van jullie business plan.
#
# Als jullie in het business plan hebben opgenomen dat een bepaalde groei gerealiseerd moet worden, door bijvoorbeeld meer omzet, door meer uren te verkopen of de productiviteit te verhogen. Dan zou ik verwachten dat deze KPI’s terugkomen in de maandrapportage (weer in vergelijking met jullie normen/begroting), omdat je er dan ook daadwerkelijk tijdig kan bijsturen.
#
# Ik ken jullie business plan nog niet, maar ik zou zeker verwachten:
#
# Productiviteit (directe uren vs normuren, analyse indirecte uren)
# Brutomarge analyse op projectniveau, gerealiseerd gemiddeld uurtarief
# Overzicht afboekingen en afboekingspercentages.
# Ontwikkeling OHW met ouderdom, DOB (Days of billing: hoe snel wordt het OHW gefactureerd) DSO (Days of sales outstanding: ouderdom debiteuren).
# Voor wat betreft de overige bedrijfskosten: enkel nader aandacht indien deze afwijken van de begroting, meestal is dat redelijk stabiel en zeer voorspelbaar.
#
#
# Salesfunnel zou ik niet direct opnemen in de maandrapportage. Vaak zitten bij het salesoverleg weer andere mensen bij die wellicht niet alle financiële data hoeven te zien.
# Uiteraard kan als onderdeel van je maandelijks directieoverleg “sales” een belangrijk onderdeel zijn, maar is niet direct nodig voor een maandrapportage. Uiteraard is alles vormvrij.
#
#
#
# Een dergelijke maandrapportage moet ook gaan groeien, maar houd in beeld wat voor jullie belangrijk is om de ondernemingsdoelstellingen te kunnen monitoren en hierop te kunnen bijsturen indien nodig.
#
#
#
# In de maandcijfers van een betreffende maand is altijd zichtbaar de YTD (year to date) cijfers, alsook de betreffende maand. Vervolgens worden bij de maandcijfers de begroting opgeteld om te kunnen voorspellen of de doelstellingen voor dat jaar worden behaald, voor- of achter lopen.
#
# Grafieken kunnen handig zijn, fleuren vaak de presentatie wat op. Ik zou dit alleen doen als het zinvol is.

def last_date_of_month(year:int, month:int):
    return f'{year}-{month:02}-{calendar.monthrange(year, month)[1]:02}'

if __name__ == '__main__':
    os.chdir('..')
    load_cache()
    render_maandrapportage(get_output_folder(), 2021, 4)
