import os
from typing import Iterable

from gspread import WorksheetNotFound

from layout.basic_layout import MID_SIZE
from layout.block import Grid, TextBlock, VBlock
from maandrapportage.yuki_results import YukiResult, tuple_add
from settings import MAANDEN, GRAY, TOPLINE, BOLD, DOUBLE_TOPLINE, RED, ITALIC
from sources.googlesheet import HeaderSheet


# Winst-en-verliesrekening


class Explanation:
    """Class to collect explanations from Begroting sheet and list them when needed"""

    def __init__(self, year, month):
        self.explanation_lines = []
        try:
            self.explanation_sheet = HeaderSheet(f"Begroting {year}", str(month))
        except WorksheetNotFound:
            self.explanation_sheet = None
        self.current = 0  # For iteration

    def update(self, title):
        if self.explanation_sheet.data:
            description = self.explanation_sheet[title, "Toelichting"]
            if description:
                self.explanation_lines += [(title, description)]

    def __len__(self):
        return len(self.explanation_lines)

    def __iter__(self):  # Make Explanation an iterator
        return self

    def __next__(self):
        if self.current == len(self.explanation_lines):
            raise StopIteration
        self.current += 1
        return self.explanation_lines[self.current - 1]


def profit_and_loss_block(yuki_result: YukiResult):
    month = yuki_result.month
    maand = MAANDEN[month - 1]
    begroting = HeaderSheet(
        f"Begroting {yuki_result.year}", "Begroting", header_col=2, header_row=2
    )
    # omzetplanning = HeaderSheet('Begroting 2021', 'Omzetplanning')
    explanations = Explanation(yuki_result.year, month)

    grid = Grid(
        cols=8,
        has_header=False,
        line_height=0,
        aligns=["left", "right", "right", "right", "", "right", "right", "right"],
    )

    def add_normal_row(title, code, budget=None):
        result = yuki_result.month_ytd(code)
        if budget:
            budget_month = TextBlock(budget[0], text_format=".", color=GRAY)
            budget_ytd = TextBlock(budget[1], text_format=".", color=GRAY)
        else:
            budget_month, budget_ytd = 0, 0
        grid.add_row(
            [
                TextBlock(title),
                TextBlock(result[0], text_format="."),
                "",
                budget_month,
                "",
                TextBlock(result[1], text_format="."),
                "",
                budget_ytd,
            ]
        )
        explanations.update(title)

    def add_subtotal_row(title, code, budget=None, style=TOPLINE):
        subtotal = yuki_result.month_ytd(code)
        # if budget:
        #    budget_month = TextBlock(budget[0], text_format=".", color=GRAY, style=BOLD)
        #    budget_ytd = TextBlock(budget[1], text_format=".", color=GRAY, style=BOLD)
        # else:
        #    budget_month, budget_ytd = 0, 0
        grid.add_row(
            [
                TextBlock(title, style=BOLD),
                "",
                TextBlock(subtotal[0], text_format=".", style=BOLD),
                # budget_month,
                "",
                "",
                TextBlock(subtotal[1], text_format=".", style=BOLD),
                # budget_ytd,
            ],
            styles=["", style, style, "", "", style, style, ""],
        )
        explanations.update(title)

    # def turnover_planning(begroting_posts):
    #     def budget_ytd(sheet, post):
    #         return sum([get_int(sheet[post, MAANDEN[m - 1]]) for m in range(1, month + 1)])
    #
    #     if type(begroting_posts) != list:
    #         begroting_posts = [begroting_posts]
    #     planned_month = sum([budget_column(omzetplanning, post) for post in begroting_posts])
    #     planned_ytd = sum([budget_ytd(omzetplanning, post) for post in begroting_posts])
    #     return (planned_month, planned_ytd)

    def budgeted(begroting_posts):
        def budget_month(sheet, post):
            if month:
                res = get_int(sheet[post, MAANDEN[month - 1]])
                if month > 1:
                    res -= get_int(sheet[post, MAANDEN[month - 2]])
                return res
            return budget_column(sheet, post)

        if type(begroting_posts) != list:
            begroting_posts = [begroting_posts]
        planned_month = (
            sum([budget_month(begroting, post) for post in begroting_posts]) * 1000
        )
        planned_ytd = (
            sum([budget_column(begroting, post) for post in begroting_posts]) * 1000
        )
        return planned_month, planned_ytd

    def get_int(string):
        return int(string.replace(".", "")) if string else 0

    def budget_column(sheet, post):
        return get_int(sheet[post, maand])

    # Header
    grid.add_row(
        [
            "",
            "",
            TextBlock(maand, style=BOLD),
            # TextBlock("begroot", color=GRAY),
            "",
            "",
            TextBlock("ytd", style=BOLD),
            # TextBlock("begroot", color=GRAY),
        ],
        styles=["width:160px;", "", "", "", "width:80px;"],
    )
    # Omzet
    add_normal_row("Omzet", "-turnover")
    add_normal_row("Verandering in onderhanden werk", "80062")
    add_normal_row("Projectkosten", "-60351")
    add_normal_row("Uitbesteed werk", "-60350")
    add_normal_row("Hostingkosten", "-60352")
    turnover_budgeted = budgeted(["Omzet"])  # turnover_planning('TOTAAL OMZET')
    add_subtotal_row("BBI", "-bbi", turnover_budgeted)
    grid.add_row()

    # Overige inkomsten
    other_budgeted = (0, 0)
    add_subtotal_row("Overige inkomsten", "-other_income", other_budgeted)

    # TOTAAL INKOMSTEN
    grid.add_row()
    margin_budgeted = tuple_add(turnover_budgeted, other_budgeted)
    add_subtotal_row(
        "Totaal bruto marge", "-total_income", margin_budgeted, style=DOUBLE_TOPLINE
    )
    grid.add_row()
    grid.add_row()

    # Personeel
    people_budgeted = budgeted(["Management", "Medewerkers"])
    add_normal_row("Mensen", "people", people_budgeted)

    wbso_budgeted = tuple(-x for x in budgeted("Subsidie"))
    add_normal_row("WBSO", "WPerLesLoo", wbso_budgeted)

    add_subtotal_row("Personeelskosten", "personell")
    grid.add_row()

    # Bedrijfskosten
    housing_budgeted = budgeted("Huisvesting")
    add_normal_row("Huisvesting", "WBedHui", housing_budgeted)

    marketing_budgeted = budgeted("Marketing")
    add_normal_row("Sales / Marketing", "WBedVkk", marketing_budgeted)

    other_expenses_budgeted = budgeted("Overige kosten")
    add_normal_row("Overige kosten", "other_expenses", other_expenses_budgeted)

    add_subtotal_row("Bedrijfskosten", "company_costs")
    grid.add_row()

    # BEDRIJFSLASTEN
    operating_expenses_budgeted = tuple_add(
        people_budgeted,
        wbso_budgeted,
        housing_budgeted,
        marketing_budgeted,
        other_expenses_budgeted,
    )
    add_subtotal_row(
        "TOTAAL BEDRIJFSLASTEN",
        "operating_expenses",
        operating_expenses_budgeted,
        style=DOUBLE_TOPLINE,
    )
    grid.add_row()
    grid.add_row()

    # Deprecation
    depreciation_budgeted = budgeted("Afschrijvingen")
    depreciation_budgeted = (-depreciation_budgeted[0], -depreciation_budgeted[1])
    add_subtotal_row("Afschrijvingen", "-WAfs", depreciation_budgeted, style="")

    # Financial
    financial_budgeted = (0, 0)
    add_subtotal_row("Financieel resultaat", "-WFbe", financial_budgeted, style="")
    grid.add_row()

    # Winst
    # total_costs =  [oe+d-f for oe,d,f in zip(operating_expenses, depreciation, financial)]
    total_costs_budgeted = tuple_add(
        operating_expenses_budgeted, depreciation_budgeted, financial_budgeted
    )
    profit_budgeted = [m - c for m, c in zip(margin_budgeted, total_costs_budgeted)]
    add_subtotal_row("Winst", "-profit", None, style=DOUBLE_TOPLINE)

    # add_subtotal_row('Mutatie onderhanden werk', yuki_result.mutation_wip(), style='')
    # total_profit = tuple_add(profit, mutation_wip)
    # gtotal_profit = total_profit  # save for balance
    # total_profit_month, total_profit_ytd = yuki_result.total_profit()
    # grid.add_row(
    #     [
    #         TextBlock('TOTAAL WINST', style=BOLD),
    #         '',
    #         TextBlock(total_profit_month, text_format='.', style=BOLD),
    #         TextBlock(profit_budgeted[0], text_format='.', style=BOLD, color=GRAY),
    #         '',
    #         '',
    #         TextBlock(total_profit_ytd, text_format='.', style=BOLD),
    #         TextBlock(profit_budgeted[1], text_format='.', style=BOLD, color=GRAY),
    #     ],
    #     styles=['', '', 'border:2px solid gray', '', '', '', 'border:2px solid gray'],
    # )

    contents = [
        TextBlock(f"Winst & verliesrekening", MID_SIZE),
        grid,
        toelichting_block(explanations),
    ]
    return VBlock(
        contents, css_class="page-break-before", style="page-break-before: always;"
    )


# Balans
def balance_block(yuki_result: YukiResult):
    year, month = yuki_result.year, yuki_result.month
    maand = MAANDEN[month - 1]
    vorige_maand = MAANDEN[month - 2] if month >= 2 else f"Begin {year}"
    grid = Grid(
        cols=6,
        has_header=False,
        aligns=["left", "right", "right", "", "right", "right"],
    )
    explanations = Explanation(yuki_result.year, month)

    def add_normal_row(title, code):
        result = yuki_result.month_prev(code)
        grid.add_row(
            [
                TextBlock(title),
                TextBlock(result[0], text_format="."),
                "",
                "",
                TextBlock(result[1], text_format=".", color="GRAY"),
                "",
            ]
        )
        explanations.update(title)

    def add_subtotal_row(title, code, style=TOPLINE):
        subtotal = yuki_result.month_prev(code)
        grid.add_row(
            [
                TextBlock(title, style=BOLD),
                "",
                TextBlock(subtotal[0], text_format=".", style=BOLD),
                "",
                "",
                TextBlock(subtotal[1], text_format=".", style=BOLD, color="GRAY"),
            ],
            styles=["", style, style, "", style, style],
        )
        explanations.update(title)

    # Header
    grid.add_row(
        [
            "",
            "",
            TextBlock(f"{maand.lower()}", style=BOLD),
            "",
            "",
            TextBlock(f"{vorige_maand.lower()}", style=BOLD, color=GRAY),
        ],
        styles=["width:160px;", "", "", "width:80px;"],
    )

    add_normal_row("Materiële vaste activa", "BMva")
    add_normal_row("Financiële vaste activa", "financial_fixed_assets")
    add_subtotal_row("Vaste activa", "fixed_assets")

    add_normal_row("Debiteuren", "BVorDeb")
    add_normal_row("Overige vorderingen", "other_receivables")
    add_normal_row("Onderhanden werk", "BVrd")
    add_normal_row("Liquide middelen", "liquid_assets")
    add_subtotal_row("Vlottende activa", "current_assets")

    # TOTAAL ACTIVA
    add_subtotal_row("TOTAAL ACTIVA", "total_assets", style=DOUBLE_TOPLINE)
    grid.add_row([])

    add_normal_row("Aandelenkapitaal", "-BEivGok")
    add_normal_row("Reserves", "-reserves")
    add_normal_row("Onverdeeld resultaat", "-profit")
    add_subtotal_row("Eigen vermogen", "-equity")

    add_normal_row("Crediteuren", "-BSchCre")
    add_normal_row("Medewerkers", "-BSchSal")
    add_normal_row("Belastingen", "-taxes")
    add_normal_row("Overlopende passiva", "-overlopende_passiva")
    add_normal_row("Overige schulden", "-other_debts")
    add_subtotal_row("Kortlopende schulden", "-short_term_debt")

    add_subtotal_row("TOTAAL PASSVA", "-total_liabilities", style=DOUBLE_TOPLINE)

    # Tijd voor wat checks
    total_assets = yuki_result.month_prev("total_assets")
    total_liabilities = yuki_result.month_prev("total_liabilities")
    if total_assets[0] != -total_liabilities[0]:
        grid.add_row(
            [
                TextBlock(
                    f"Balansverschil in {maand} van {abs(total_assets[0] + total_liabilities[0])}",
                    color=RED,
                )
            ]
        )
    if total_assets[1] != -total_liabilities[1]:
        grid.add_row(
            [
                TextBlock(
                    f"Balansverschil in {vorige_maand} van {abs(total_assets[1] + total_liabilities[1])}",
                    color=RED,
                )
            ]
        )

    return VBlock(
        [
            TextBlock(f"Balans per einde {maand.lower()} {year}", MID_SIZE),
            grid,
            toelichting_block(explanations),
        ],
        css_class="page-break-before",
        style="page-break-before: always;",
    )


# Kasstroomoverzicht
# Deze dan ook in vergelijking met de vastgestelde begroting.
def cashflow_analysis_block(yuki_result):
    grid = Grid(cols=3, has_header=False, aligns=["left", "right", "right"])

    def add_normal_row(title, code, shift=False, value_color=None):
        value = yuki_result.month_prev(code)[0]
        row = [TextBlock(title)]
        value_text = TextBlock(value, text_format=".", color=value_color)
        if shift:
            row += ["", value_text]
        else:
            row += [value_text, ""]
        grid.add_row(row)

    def add_subtotal_row(title, code, style=TOPLINE):
        value = yuki_result.month_prev(code)[0]
        grid.add_row(
            [
                TextBlock(title, style=BOLD),
                "",
                TextBlock(value, text_format=".", style=BOLD),
            ],
            styles=["", style, style],
        )

    add_normal_row("Nettowinst", "-profit")
    add_normal_row("Afschrijvingen", "-WAfs")
    add_subtotal_row("Cashflow", "cashflow")
    grid.add_row([])

    # Toename vorderingen
    debtors = yuki_result.month_prev(
        "debtors",
    )
    other_receivables = yuki_result.other_receivables()
    financial_fixed_assets = yuki_result.month_prev("financial_fixed_assets")
    increase_receivables = (
        debtors[0]
        + other_receivables[0]
        + financial_fixed_assets[0]
        - debtors[1]
        - other_receivables[1]
        - financial_fixed_assets[1]
    )
    descr = (
        "Toegenomen vorderingen"
        if increase_receivables >= 0
        else "Afgenomen vorderingen"
    )
    add_normal_row(descr, -increase_receivables)

    # Toename onderhanden werk
    in_progress = yuki_result.get_work_in_progress()
    increase_in_progress = in_progress[0] - in_progress[1]
    descr = (
        "Toegenomen onderhanden werk"
        if increase_in_progress >= 0
        else "Afgenomen onderhanden werk"
    )
    add_normal_row(descr, -increase_in_progress)

    # Toename crediteuren
    short_term_debt = yuki_result.short_term_debt()
    increase_creditors = short_term_debt[0] - short_term_debt[1]
    descr = (
        "Toegenomen crediteuren" if increase_creditors >= 0 else "Afgenomen crediteuren"
    )
    add_normal_row(descr, increase_creditors)

    # Verandering van netto werkkapitaal
    increase_working_capital = (
        -increase_receivables - increase_in_progress + increase_creditors
    )
    add_subtotal_row("Verandering van netto werkkapitaal", increase_working_capital)
    grid.add_row([])

    # Operationele kasstroom
    operating_cash_flow = cashflow + increase_working_capital
    add_subtotal_row("Operationele kasstroom", operating_cash_flow)

    # Investeringen
    investment_in_assets = yuki_result.month_prev("investments")
    investments = (
        investment_in_assets[0] - investment_in_assets[1]
    )  # This month - last month = investments
    add_normal_row("Investeringen", -investments, shift=True)

    # Mutaties eigen vermogen
    equity_mutations = 0
    add_normal_row("Mutaties eigen vermogen", equity_mutations, shift=True)

    # Netto kasstroom
    net_cash_flow = operating_cash_flow - investments + equity_mutations
    add_subtotal_row("Netto kasstroom", net_cash_flow)

    # Toename liquide middelen
    liquid_assets = yuki_result.month_prev("liquid_assets")
    increase_liquid_assets = liquid_assets[0] - liquid_assets[1]
    color = RED if increase_liquid_assets != net_cash_flow else None
    add_normal_row(
        "Toename liquide middelen",
        increase_liquid_assets,
        shift=True,
        value_color=color,
    )

    return VBlock(
        [TextBlock(f"Cashflow analyse", MID_SIZE), grid],
        css_class="page-break-before",
        style="page-break-before: always;",
    )


def toelichting_block(explanations: Iterable[tuple[str, str]]):
    if not explanations:
        return
    toelichting_grid = Grid(cols=2)
    for post, explanation in explanations:
        toelichting_grid.add_row(
            [TextBlock(post, style=BOLD), TextBlock(explanation, style=ITALIC)]
        )
    return VBlock([TextBlock(f"Toelichting", style=BOLD), toelichting_grid])
