""" Class to represent the Yuki account model """

import sys
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from model.caching import load_cache
from model.onderhanden_werk import ohw_sum
from model.resultaat import last_day_of_month
from model.utilities import Day
from sources.yuki import Yuki


@dataclass
class Item:
    description: str
    sub_codes: set[str]
    amount: Optional[float]

    def add_subcodes(self, codes: list[str]):
        self.sub_codes.update(codes)


class YukiAccountModel:
    def __init__(self, day: Day = None):

        self.yuki = Yuki()
        self.items = {}
        self.categories = {}
        self.aliases = {}
        self.load_schema()

        if day:
            self.fill(day)

    def load_schema(self):
        for row in self.yuki.account_scheme():
            code = row["Code"]
            if not code:
                continue
            category_code = row["RGS Code"]
            if not category_code:
                continue

            # Split in main categories like 'WPerLesLoo' and add them if needed
            main_categories = split_on_caps(category_code)
            for index in range(len(main_categories)):
                sub_categories = (
                    [main_categories[index + 1]]
                    if index < len(main_categories) - 1
                    else []
                )
                self.add_category(main_categories[index], "", sub_categories)

            # Add the category as new category or add the item to the categoruy
            self.add_category(category_code, row["RGS Omschrijving"], [code])

            # Add the item
            self.add_post(code, row["Omschrijving"])

        # W&V
        self.describe("WOmz", "Omzet volgens de boekhouding")
        self.alias("turnover", "Omzet!", ["WOmz", "-80070"])  # Onderverhuur eruit
        self.describe("60351", "Projectkosten")
        self.describe("60350", "Uitbesteed werk")
        self.describe("60352", "Hostingkosten")
        self.alias("bbi", "BBI", ["turnover", "60350", "60351", "60352"])
        self.alias(
            "other_income", "Overige inkomsten", ["80070"]
        )  # Onderverhuur er weer bij
        self.alias("total_income", "Totaal bruto marge", ["bbi", "other_income"])

        self.alias(
            "people",
            "Mensen",
            ["WPer", "-WPerLesLoo", "-WPerWkg", "WPerWkgOsc", "WBedOvp"],
        )
        # Personeel -/- Reis- en verblijfskosten algemeen -/- WBSO + Overig personeel

        self.describe("WPerLesLoo", "WBSO")
        self.alias("personell", "Personeelskosten", ["people", "WPerLesLoo"])
        self.alias("housing", "Huisvesting", ["WBedHui", "WBedEemRoi"])
        self.describe("WBedVkk", "Sales/marketing")
        self.alias(
            "other_expenses",
            "Overige kosten",
            [
                "WBed",
                "WPerWkg",
                "-WPerWkgOsc",
                "-WBedHui",
                "-WBedVkk",
                "-WBedOvp",
                "-WBedEemRoi",
                "WKprBtkBed",
            ],
        )
        # WKprBtkBed = Ontvangen betalingskortingen

        self.alias(
            "company_costs", "Bedrijfkosten", ["housing", "WBedVkk", "other_expenses"]
        )
        self.alias(
            "operating_expenses",
            "TOTAAL BEDRIJFSLASTEN",
            ["company_costs", "personell"],
        )

        self.describe("WAfs", "Afschrijvingen")
        self.describe("WFbe", "Financiëel resultaat")
        self.alias(
            "profit",
            "Winst volgens de boekhouding",
            ["total_income", "operating_expenses", "WAfs", "WFbe"],
        )

        # Balans
        self.describe("BMva", "Materiële vaste activa")
        self.describe("13000", "Debiteuren")
        self.alias(
            "financial_fixed_assets", "Financiële vaste activa", ["BVorOvrWbs"]
        )  # Waarborgsommen
        self.alias("fixed_assets", "Vaste activa", ["BMva", "financial_fixed_assets"])
        self.describe("BVorDeb", "Debiteuren")
        self.alias("question_posts", "Vraagposten", ["23020"])
        self.alias(
            "overlopende_activa", "Overlopende activa", ["BVorOva", "-question_posts"]
        )  # Overlopend minus vraagposten
        self.alias(
            "other_receivables",
            "Overige vorderingen",
            [
                "BVor",
                "-BVorDeb",
                "-overlopende_activa",
                "-question_posts",
                "-BVorOvrWbs",
            ],
        )  # Waarborgsommen
        self.describe("BVrd", "Onderhanden werk")
        self.alias(
            "liquid_assets", "Liquide middelen", ["BLim", "-BLimKru"]
        )  # Minus betalingen onderweg
        self.alias(
            "current_assets",
            "Vlottende activa",
            [
                "BVorDeb",
                "overlopende_activa",
                "other_receivables",
                "BVrd",
                "liquid_assets",
            ],
        )
        self.alias("total_assets", "TOTAAL ACTIVA", ["current_assets", "fixed_assets"])

        self.describe("BEivGok", "Aandelen")
        self.alias("reserves", "Reserves", ["BEiv", "-BEivGok"])
        self.alias("equity", "Eigen vermogen", ["BEivGok", "reserves", "profit"])
        self.describe("BSchCre", "Crediteuren")
        self.describe("BSchSal", "Medewerkers")
        self.alias("taxes", "Belastingen", ["BSchBep", "BSchBtw"])
        self.alias(
            "other_debts", "Overige schulden", ["BSchOvs", "BLimKruCra"]
        )  # Overig kortlopend en Visa / Schulden aan banken
        self.alias(
            "overlopende_passiva",
            "Overlopende passiva",
            ["BSchOpa", "question_posts", "BLimKruSto"],
        )  # Betalingen onderweg
        # todo: overlopende passiva apart
        self.alias(
            "short_term_debt",
            "Kortlopende schulden",
            ["overlopende_passiva", "BSchSal", "BSchCre", "taxes", "other_debts"],
        )
        self.alias("total_liabilities", "TOTAAL PASSIVA", ["equity", "short_term_debt"])

        # Cashflow analysis
        self.alias("cashflow", "Cashflow", ["-profit", "WAfs"])
        self.alias(
            "receivables",
            "Toegenomen vorderingen",
            ["BVorDeb", "other_receivables", "overlopende_activa"],
        )
        self.alias(
            "working_capital",
            "Verandering van netto werkkapitaal",
            ["receivables", "BVrd", "BSchCre"],
        )
        self.alias(
            "operational_cash",
            "Operationele kasstroom",
            ["cashflow", "-working_capital"],
        )
        self.alias("investments", "Investeringen", ["02110", "02200", "02300", "02400"])
        self.alias(
            "net_cashflow", "Netto kasstroom", ["operational_cash", "investments"]
        )

    def add_post(self, code, description, amount=None):
        self.items[code] = Item(description, set(), amount)

    def add_category(self, category_code: str, description: str, subcodes: list[str]):
        category_item = self.items.get(category_code)
        if category_item:
            category_item.add_subcodes(subcodes)
        else:
            self.items[category_code] = Item(description, set(subcodes), None)

    def describe(self, code: str, new_description: str):
        self.items[code].description = new_description

    def alias(self, alias_code: str, description: str, subcodes: list[str]):
        self.aliases[alias_code] = Item(description, set(subcodes), None)

    def fill(self, day):
        balance = {d["code"]: d["amount"] for d in self.yuki.day_balance(day)}

        def fill_value(code: str, item: Item):
            if item.sub_codes:
                amount = None
                for sub_code in item.sub_codes:
                    sub_item = self.items[sub_code]
                    if sub_item.amount is not None:
                        if amount is None:
                            amount = 0  # Initialize
                        amount += sub_item.amount
            else:
                amount = balance.get(code)
            item.amount = amount
            # return amount

        self.walk(fill_value, depth_first=True)

    def add_ohw(self, amount):
        """Voegt onderhanden werk toe aan de structuur zoals die uit Yuki komt"""
        balans_categories = ["30100"] + split_on_caps("BVrdOweVoo")
        wv_categories = ["80062"] + split_on_caps("WOmzGrpGr1")
        for post in balans_categories:
            if self.items[post].amount is None:
                self.items[post].amount = 0
            self.items[post].amount += Decimal(amount)
        for post in wv_categories:
            if self.items[post].amount is None:
                self.items[post].amount = 0
            self.items[post].amount -= Decimal(amount)

    def post(self, code: str) -> (float, str):
        """Returns the value of the specified post
        code can either be an alias or an item code
        """
        negative = False
        if code[0] == "-":
            negative = True
            code = code[1:]
        alias = self.aliases.get(code)
        if alias:
            amount = sum([self.post(sub_code)[0] for sub_code in alias.sub_codes])
            description = alias.description
        else:
            try:
                amount = self.items[code].amount
            except KeyError:
                print(f"Code {code} niet gevonden in het rekeningschema")
                sys.exit(1)
            description = self.items[code].description
        if not amount:
            amount = 0
        if negative:
            amount = -amount
        return amount, description

    def walk(self, function, code: str = "", depth_first=False):
        if not code:
            self.walk(function, "B", depth_first=depth_first)
            self.walk(function, "W", depth_first=depth_first)
        else:
            item = self.items[code]
            if not depth_first:
                function(code, item)
            for subcode in list(item.sub_codes):
                self.walk(function, subcode, depth_first=depth_first)
            if depth_first:
                function(code, item)


def split_on_caps(category_name):
    """Splits WFbeOrlOrl to ['W','WFbe','WFbeOrl','WFbeOrlOrl']"""
    res = category_name[0]
    for letter in category_name[1:]:
        if letter.isupper():
            res += "|"
        res += letter
    chunks = res.split("|")
    result = ["".join(chunks[0 : index + 1]) for index in range(len(chunks))]
    return result


def print_with_subs(code: str, item: Item, level: int = 0):
    amount = f"€ {item.amount}" if item.amount is not None else ""
    print("  " * level, code, item.description, amount)


def balans_en_wv(year, month):
    day = Day(last_day_of_month(year, month))
    model = YukiAccountModel()
    model.fill(day)
    model.add_ohw(ohw_sum(day, 1000))

    afschrijvingen, _ = model.post("-WAfs")
    if not afschrijvingen:
        print("DE BOEKHOUDING VAN DEZE MAAND IS NOG NIET COMPLEET\n")

    last_m = month - 1
    last_y = year
    if last_m == 0:
        last_m = 12
        last_y -= 1
    last_day = Day(last_day_of_month(last_y, last_m))
    last_month = YukiAccountModel()
    last_month.fill(last_day)
    last_month.add_ohw(ohw_sum(last_day, 1000))

    def balans(code: str):
        amount, descr = model.post(code)
        if not descr:
            descr = code
        amount2, _ = last_month.post(code)
        print(f"{descr:40} {amount:>10.2f} {amount2:>10.2f}")

    def wv(code: str):
        amount, descr = model.post(code)
        if month == 1:
            amount2 = 0
        else:
            amount2, _ = last_month.post(code)
        print(f"{descr:40} {amount - amount2:>10.2f} {amount:>10.2f}")

    def cash(code: str):
        amount, descr = model.post(code)
        amount2, _ = last_month.post(code)
        print(f"{descr:40} {amount - amount2:>10.2f}")

    print("WINST EN VERLIESREKENING                      maand        YTD")
    print("                                              -----      -----")
    wv("-turnover")  # Omzet
    wv("-60351")  # Projectkosten
    wv("-60350")  # Uitbesteed werk
    wv("-60352")  # Hostingkosten
    print("---------------------")
    wv("-bbi")  # Bruto Bureau inkomem
    wv("-other_income")
    print("---------------------")
    wv("-total_income")  # Totaal bruto marge
    print()
    print()

    wv("people")
    wv("WPerLesLoo")
    print("---------------------")
    wv("personell")
    print()
    wv("housing")
    wv("WBedVkk")
    wv("other_expenses")
    print("---------------------")
    wv("company_costs")
    print()
    print("---------------------")
    wv("operating_expenses")
    print()
    wv("-WAfs")  # Afschrijvingen
    wv("-WFbe")  # Financieel resultaat
    print()
    print("---------------------")
    wv("-profit")
    print()
    print()

    print("BALANS                                        Maand     Vorige")
    print("                                              -----      -----")
    balans("BMva")  # Materiële vaste activa
    balans("financial_fixed_assets")
    print("---------------------")
    balans("fixed_assets")
    print()
    balans("BVorDeb")  # Debiteuren
    balans("other_receivables")
    balans("overlopende_activa")
    balans("BVrd")  # Onderhanden werk
    balans("liquid_assets")
    print("---------------------")
    balans("current_assets")
    print("---------------------")
    balans("total_assets")
    print()
    print()

    balans("-BEivGok")  # Aandelen
    balans("-reserves")
    balans("-profit")
    print("---------------------")
    balans("-equity")
    print()
    balans("-BSchCre")  # Crediteuren
    balans("-BSchSal")  # Medewerkers
    balans("-taxes")
    balans("-overlopende_passiva")
    balans("-other_debts")
    print("---------------------")
    balans("-short_term_debt")  # Kortlopende schulden
    print("---------------------")
    balans("-total_liabilities")
    print()
    print()

    print("CASHFLOW ANALYSE")
    print()
    cash("-profit")  # Materiële vaste activa
    cash("WAfs")  # Materiële vaste activa
    print("---------------------")
    cash("cashflow")  # Materiële vaste activa
    print()
    cash("-receivables")
    cash("-BVrd")  # Onderhanden werk
    cash("-BSchCre")  # Crediteuren
    print("---------------------")
    cash("-working_capital")
    print("---------------------")
    cash("operational_cash")
    cash("-investments")
    # todo: hier komt mutaties eigen vermogen
    cash("net_cashflow")
    cash("liquid_assets")

    # Checks
    total_assets, _ = model.post("total_assets")
    total_liabilities, _ = model.post("total_liabilities")
    if total_assets != -total_liabilities:
        print()
        print(
            f"Total assets {total_assets} != total liabilities {-total_liabilities}."
            + "Difference of {abs(total_assets + total_liabilities)}"
        )


if __name__ == "__main__":
    load_cache()
    balans_en_wv(2022, 3)
    # model.walk( print_with_subs)
