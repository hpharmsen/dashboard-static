from gspread import WorksheetNotFound

from layout.basic_layout import MID_SIZE
from layout.block import Grid, TextBlock, VBlock
from maandrapportage.yuki_results import YukiResult, tuple_add, last_date_of_month
from settings import MAANDEN, GRAY, TOPLINE, BOLD, DOUBLE_TOPLINE, RED, ITALIC
from sources.googlesheet import HeaderSheet


# Winst-en-verliesrekening
def profit_and_loss_block(yuki_result: YukiResult, year: int, month: int):
    maand = MAANDEN[month - 1]
    last_date_this_month = last_date_of_month(year, month)
    begroting = HeaderSheet('Begroting 2021', 'Begroting', header_col=2, header_row=2)
    omzetplanning = HeaderSheet('Begroting 2021', 'Omzetplanning')
    toelichtingen = []
    try:
        toelichting_sheet = HeaderSheet('Begroting 2021', str(month))
    except WorksheetNotFound:
        toelichting_sheet = None

    grid = Grid(
        cols=8,
        has_header=False,
        line_height=0,
        aligns=['left', 'right', 'right', 'right', '', 'right', 'right', 'right'],
    )

    def add_normal_row(title, result, budget=None):
        if budget:
            budget_month = TextBlock(budget[0], text_format='.', color=GRAY)
            budget_ytd = TextBlock(budget[1], text_format='.', color=GRAY)
        else:
            budget_month, budget_ytd = 0, 0
        grid.add_row(
            [
                TextBlock(title),
                TextBlock(result[0], text_format='.'),
                '',
                budget_month,
                '',
                TextBlock(result[1], text_format='.'),
                '',
                budget_ytd,
            ]
        )
        if toelichting_sheet:
            toelichting = toelichting_sheet[title, 'Toelichting']
            if toelichting:
                b = toelichtingen  # zeer merkwaardige constructie maar krijg een foutmelding als ik direct iets toevoeg aan toelichtingen
                b += [(title, toelichting)]

    def add_subtotal_row(title, subtotal, budget=None, style=TOPLINE):
        if budget:
            budget_month = TextBlock(budget[0], text_format='.', color=GRAY, style=BOLD)
            budget_ytd = TextBlock(budget[1], text_format='.', color=GRAY, style=BOLD)
        else:
            budget_month, budget_ytd = 0, 0
        grid.add_row(
            [
                TextBlock(title, style=BOLD),
                '',
                TextBlock(subtotal[0], text_format='.', style=BOLD),
                budget_month,
                '',
                '',
                TextBlock(subtotal[1], text_format='.', style=BOLD),
                budget_ytd,
            ],
            styles=['', style, style, '', '', style, style, ''],
        )

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
            return (
                get_int(sheet[post, maand]) - get_int(sheet[post, MAANDEN[month - 2]]) if month else budget_column(post)
            )

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
    grid.add_row(
        [
            '',
            '',
            TextBlock(maand, style=BOLD),
            TextBlock('begroot', color=GRAY),
            '',
            '',
            TextBlock('ytd', style=BOLD),
            TextBlock('begroot', color=GRAY),
        ],
        styles=['width:160px;', '', '', '', 'width:80px;'],
    )
    # Omzet
    add_normal_row('Omzet', yuki_result.omzet())
    add_normal_row('Projectkosten', yuki_result.projectkosten())
    add_normal_row('Uitbesteed werk', yuki_result.uitbesteed_werk())
    add_normal_row('Hostingkosten', yuki_result.month_ytd('hosting_expenses'))
    turnover_budgeted = budgeted(['Omzet'])  # turnover_planning('TOTAAL OMZET')
    add_subtotal_row('BBI', yuki_result.bbi(), turnover_budgeted)
    grid.add_row()

    # Overige inkomsten
    other_income = yuki_result.month_ytd('other_income')
    other_budgeted = (0, 0)
    add_subtotal_row('Overige inkomsten', other_income, other_budgeted)
    grid.add_row()

    # TOTAAL INKOMSTEN
    grid.add_row()
    margin_budgeted = tuple_add(turnover_budgeted, other_budgeted)
    total_income = tuple_add(yuki_result.bbi(), yuki_result.other_income())
    add_subtotal_row('Totaal bruto marge', total_income, margin_budgeted, style=DOUBLE_TOPLINE)
    grid.add_row()
    grid.add_row()

    # Personeel
    people_budgeted = budgeted(['Management', 'Medewerkers'])
    add_normal_row('Mensen', yuki_result.people(), people_budgeted)

    wbso_budgeted = tuple(-x for x in budgeted('Subsidie'))
    add_normal_row('WBSO', yuki_result.wbso(), wbso_budgeted)

    add_subtotal_row('Personeelskosten', yuki_result.personnell())
    grid.add_row()

    # Bedrijfskosten
    housing_budgeted = budgeted('Huisvesting')
    add_normal_row('Huisvesting', yuki_result.housing(), housing_budgeted)

    marketing_budgeted = budgeted('Marketing')
    add_normal_row('Sales / Marketing', yuki_result.marketing(), marketing_budgeted)

    other_expenses_budgeted = budgeted('Overige kosten')
    add_normal_row('Overige kosten', yuki_result.other_expenses(), other_expenses_budgeted)

    add_subtotal_row('Bedrijfskosten', yuki_result.company_costs())
    grid.add_row()

    # BEDRIJFSLASTEN
    operating_expenses_budgeted = tuple_add(
        people_budgeted, wbso_budgeted, housing_budgeted, marketing_budgeted, other_expenses_budgeted
    )
    add_subtotal_row(
        'TOTAAL BEDRIJFSLASTEN', yuki_result.operating_expenses(), operating_expenses_budgeted, style=DOUBLE_TOPLINE
    )
    grid.add_row()
    grid.add_row()

    # Deprecation
    depreciation_budgeted = budgeted('Afschrijvingen')
    depreciation_budgeted = (-depreciation_budgeted[0], -depreciation_budgeted[1])
    add_subtotal_row('Afschrijvingen', yuki_result.depreciation(), depreciation_budgeted, style='')

    # Financial
    financial_budgeted = (0, 0)
    add_subtotal_row('Financieel resultaat', yuki_result.financial(), financial_budgeted, style='')
    grid.add_row()

    # Winst
    # total_costs =  [oe+d-f for oe,d,f in zip(operating_expenses, depreciation, financial)]
    total_costs_budgeted = tuple_add(operating_expenses_budgeted, depreciation_budgeted, financial_budgeted)
    profit_budgeted = [m - c for m, c in zip(margin_budgeted, total_costs_budgeted)]
    add_subtotal_row('Winst volgens de boekhouding', yuki_result.profit(), None, style=DOUBLE_TOPLINE)

    add_subtotal_row('Mutatie onderhanden werk', yuki_result.mutation_wip(last_date_this_month), style='')
    # total_profit = tuple_add(profit, mutation_wip)
    # gtotal_profit = total_profit  # save for balance
    total_profit_month, total_profit_ytd = yuki_result.total_profit()
    grid.add_row(
        [
            TextBlock('TOTAAL WINST', style=BOLD),
            '',
            TextBlock(total_profit_month, text_format='.', style=BOLD),
            TextBlock(profit_budgeted[0], text_format='.', style=BOLD, color=GRAY),
            '',
            '',
            TextBlock(total_profit_ytd, text_format='.', style=BOLD),
            TextBlock(profit_budgeted[1], text_format='.', style=BOLD, color=GRAY),
        ],
        styles=['', '', 'border:2px solid gray', '', '', '', 'border:2px solid gray'],
    )

    contents = [TextBlock(f'Winst & verliesrekening', MID_SIZE), grid, toelichting_block(toelichtingen)]
    return VBlock(contents, css_class="page-break-before", style="page-break-before: always;")


# Balans
def balance_block(yuki_result: YukiResult, year: int, month: int):
    maand = MAANDEN[month - 1]
    vorige_maand = MAANDEN[month - 2] if month >= 2 else f'Begin {year}'
    last_date_this_month = last_date_of_month(year, month)
    grid = Grid(cols=6, has_header=False, aligns=['left', 'right', 'right', '', 'right', 'right'])
    toelichtingen = []
    try:
        toelichting_sheet = HeaderSheet('Begroting 2021', str(month))
    except WorksheetNotFound:
        toelichting_sheet = None  # !! Same code as above. Refactor.

    def add_normal_row(title, result):
        grid.add_row(
            [
                TextBlock(title),
                TextBlock(result[0], text_format='.'),
                '',
                '',
                TextBlock(result[1], text_format='.', color="GRAY"),
                '',
            ]
        )
        if toelichting_sheet:
            toelichting = toelichting_sheet[title, 'Toelichting']
            if toelichting:
                b = toelichtingen  # zeer merkwaardige constructie maar krijg een foutmelding als ik direct iets toevoeg aan toelichtingen
                b += [(title, toelichting)]

    def add_subtotal_row(title, subtotal, style=TOPLINE):
        grid.add_row(
            [
                TextBlock(title, style=BOLD),
                '',
                TextBlock(subtotal[0], text_format='.', style=BOLD),
                '',
                '',
                TextBlock(subtotal[1], text_format='.', style=BOLD, color="GRAY"),
            ],
            styles=['', style, style, '', style, style],
        )

    # Header
    grid.add_row(
        [
            '',
            '',
            TextBlock(f'{maand.lower()}', style=BOLD),
            '',
            '',
            TextBlock(f'{vorige_maand.lower()}', style=BOLD, color=GRAY),
        ],
        styles=['width:160px;', '', '', 'width:80px;'],
    )

    # Materiele vaste activa
    tangible_fixed_assets = yuki_result.month_prev('tangible_fixed_assets')
    add_normal_row('Materiële vaste activa', tangible_fixed_assets)

    # Financiële vaste activa
    financial_fixed_assets = yuki_result.month_prev('financial_fixed_assets')
    add_normal_row('Financiële vaste activa', financial_fixed_assets)

    # Vaste activa
    fixed_assets = tuple_add(tangible_fixed_assets, financial_fixed_assets)
    add_subtotal_row('Vaste activa', fixed_assets)

    # Debiteuren
    debtors = yuki_result.month_prev(
        'debtors',
    )
    add_normal_row('Debiteuren', debtors)

    # Overige vorderingen
    other_receivables = yuki_result.other_receivables()
    add_normal_row('Overige vorderingen', other_receivables)

    # Onderhanden werk
    work_in_progress = yuki_result.get_work_in_progress(last_date_this_month)
    add_normal_row('Onderhanden werk', work_in_progress)

    # Liquide middelen
    liquid_assets = yuki_result.month_prev('liquid_assets')
    add_normal_row('Liquide middelen', liquid_assets)

    # Vlottende activa
    current_assets = tuple_add(debtors, other_receivables, work_in_progress, liquid_assets)
    add_subtotal_row('Vlottende activa', current_assets)

    # TOTAAL ACTIVA
    total_assets = tuple_add(fixed_assets, current_assets)
    add_subtotal_row('TOTAAL ACTIVA', total_assets, style=DOUBLE_TOPLINE)
    grid.add_row([])

    # Aandelenkapitaal
    share_capital = yuki_result.month_prev('share_capital')
    add_normal_row('Aandelenkapitaal', share_capital)

    # Reserves
    reserves = yuki_result.month_prev('reserves')
    add_normal_row('Reserves', reserves)

    # Onverdeeld resultaat
    undistributed_result_last_year = yuki_result.month_prev('undistributed_result')
    # # undistributed_result = tuple_add(undistributed_result_last_year, gtotal_profit)
    # profit_month, profit_last_month = yuki_result.total_profit()
    # undistributed_result = (
    #     undistributed_result_last_year[0] + profit_month,
    #     undistributed_result_last_year[0] + profit_last_month,
    # )
    # undistributed_result = tuple_add(undistributed_result, yuki_result.profit()) # Add this years profit

    # a = yuki_result.profit()
    result_until_this_month = yuki_result.profit()[1]
    last_date_last_month = last_date_of_month(year, month - 1) if month > 1 else last_date_of_month(year - 1, 12)
    #b = yuki_result.profit(last_date_last_month)
    result_until_last_month = yuki_result.profit(last_date_last_month)[1]

    # work_in_progress_last_month = yuki_result.get_work_in_progress(last_date_last_month)

    undistributed_result = tuple_add(
        undistributed_result_last_year, (result_until_this_month, result_until_last_month), work_in_progress
    )
    add_normal_row('Onverdeeld resultaat', undistributed_result)

    # Eigen vermogen
    equity = tuple_add(share_capital, reserves, undistributed_result)
    add_subtotal_row('Eigen vermogen', equity)

    # Crediteuren
    add_normal_row('Crediteuren', yuki_result.creditors())

    # Medewerkers
    add_normal_row('Medewerkers', yuki_result.debt_to_employees())

    # Belasting
    add_normal_row('Belastingen', yuki_result.taxes())

    # Overige schulden
    add_normal_row('Overige schulden', yuki_result.other_debts())

    # Kortlopende schulden
    add_subtotal_row('Kortlopende schulden', yuki_result.short_term_debt())

    # TOTAAL PASSIVA
    total_liabilities = tuple_add(equity, yuki_result.short_term_debt())
    add_subtotal_row('TOTAAL PASSVA', total_liabilities, style=DOUBLE_TOPLINE)

    # Tijd voor wat checks
    if total_assets[0] != total_liabilities[0]:
        grid.add_row(
            [TextBlock(f"Balansverschil in {maand} van {abs(total_assets[0] - total_liabilities[0])}", color=RED)]
        )
    if total_assets[1] != total_liabilities[1]:
        grid.add_row(
            [
                TextBlock(
                    f"Balansverschil in {vorige_maand} van {abs(total_assets[1] - total_liabilities[1])}", color=RED
                )
            ]
        )

    return VBlock(
        [TextBlock(f'Balans per einde {maand.lower()} {year}', MID_SIZE), grid, toelichting_block(toelichtingen)],
        css_class="page-break-before",
        style="page-break-before: always;",
    )


# Kasstroomoverzicht
# Deze dan ook in vergelijking met de vastgestelde begroting.
def cashflow_analysis_block(yuki_result, year, month):
    grid = Grid(cols=3, has_header=False, aligns=['left', 'right', 'right'])

    def add_normal_row(title, value, shift=False, value_color=None):
        row = [TextBlock(title)]
        value_text = TextBlock(value, text_format='.', color=value_color)
        if shift:
            row += ['', value_text]
        else:
            row += [value_text, '']
        grid.add_row(row)

    def add_subtotal_row(title, value, style=TOPLINE):
        grid.add_row(
            [
                TextBlock(title, style=BOLD),
                '',
                TextBlock(value, text_format='.', style=BOLD),
            ],
            styles=['', style, style],
        )

    # def yuki_figure(post, year, month, negate=False):
    #     date = last_date_of_month(year, month)
    #     prev_date = last_date_of_month(year, month - 1) if month > 1 else last_date_of_month(year - 1, 12)
    #     negation = -1 if negate else 1
    #     ytd = yuki().post(post, date) * negation
    #     monthly = ytd - yuki().post(post, prev_date) * negation
    #     return monthly

    # Winst
    profit = yuki_result.total_profit()[0]
    add_normal_row('Nettowinst', profit)

    # Afschrijvingen
    deprecation = -yuki_result.depreciation()[0]
    add_normal_row('Afschrijvingen', deprecation)

    # Cashflow
    cashflow = profit + deprecation
    add_subtotal_row('Cashflow', cashflow)
    grid.add_row([])

    # Toename vorderingen
    debtors = yuki_result.month_prev(
        'debtors',
    )
    other_receivables = yuki_result.other_receivables()
    financial_fixed_assets = yuki_result.month_prev('financial_fixed_assets')
    increase_receivables = (
        debtors[0]
        + other_receivables[0]
        + financial_fixed_assets[0]
        - debtors[1]
        - other_receivables[1]
        - financial_fixed_assets[1]
    )
    descr = 'Toegenomen vorderingen' if increase_receivables >= 0 else 'Afgenomen vorderingen'
    add_normal_row(descr, -increase_receivables)

    # Toename onderhanden werk
    in_progress = yuki_result.get_work_in_progress()
    increase_in_progress = in_progress[0] - in_progress[1]
    descr = 'Toegenomen onderhanden werk' if increase_in_progress >= 0 else 'Afgenomen onderhanden werk'
    add_normal_row(descr, -increase_in_progress)

    # Toename crediteuren
    short_term_debt = yuki_result.short_term_debt()
    increase_creditors = short_term_debt[0] - short_term_debt[1]
    descr = 'Toegenomen crediteuren' if increase_creditors >= 0 else 'Afgenomen crediteuren'
    add_normal_row(descr, increase_creditors)

    # Verandering van netto werkkapitaal
    increase_working_capital = -increase_receivables - increase_in_progress + increase_creditors
    add_subtotal_row('Verandering van netto werkkapitaal', increase_working_capital)
    grid.add_row([])

    # Operationele kasstroom
    operating_cash_flow = cashflow + increase_working_capital
    add_subtotal_row('Operationele kasstroom', operating_cash_flow)

    # Investeringen
    investment_in_assets = yuki_result.month_prev('investments')
    investments = investment_in_assets[0] - investment_in_assets[1]  # This month - last month = investments
    add_normal_row('Investeringen', -investments, shift=True)

    # Mutaties eigen vermogen
    equity_mutations = 0
    add_normal_row('Mutaties eigen vermogen', equity_mutations, shift=True)

    # Netto kasstroom
    net_cash_flow = operating_cash_flow - investments + equity_mutations
    add_subtotal_row('Netto kasstroom', net_cash_flow)

    # Toename liquide middelen
    liquid_assets = yuki_result.month_prev('liquid_assets')
    increase_liquid_assets = liquid_assets[0] - liquid_assets[1]
    color = RED if increase_liquid_assets != net_cash_flow else None
    add_normal_row('Toename liquide middelen', increase_liquid_assets, shift=True, value_color=color)

    return VBlock(
        [TextBlock(f'Cashflow analyse', MID_SIZE), grid],
        css_class="page-break-before",
        style="page-break-before: always;",
    )


def toelichting_block(toelichtingen):
    if not toelichtingen:
        return
    toelichting_grid = Grid(cols=2)
    for t in toelichtingen:
        toelichting_grid.add_row([TextBlock(t[0], style=BOLD), TextBlock(t[1], style=ITALIC)])
    return VBlock([TextBlock(f'Toelichting', style=BOLD), toelichting_grid])
