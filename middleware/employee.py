""" Handles the Employee class and employee table """
from decimal import Decimal
from os import chdir

from middleware.base_table import BaseTable, EMPLOYEE_NAME
from middleware.middleware_utils import singleton
from sources.googlesheet import HeaderSheet
from sources.simplicate import simplicate

MT_FEE_PER_HOUR = Decimal(110000 / 45 / 40)
OVERIGE_KOSTEN_PER_FTE_PER_UUR = 1000 * 12 / 45 / 40
OVERIGE_KOSTEN_PER_FREELANCER_PER_UUR = (
        (139 + 168 + 47) / 4 / 40
)  # Overige personeelskosten, kantoorkosten (niet huur), Afschrijvingen (niet kantoor)
PRODUCTIVITEIT = 0.85


@singleton
class Employee(BaseTable):
    def __init__(self):
        super().__init__()
        self.table_name = "employee"
        self.table_definition = f"""
               name {EMPLOYEE_NAME} NOT NULL,
               `function` VARCHAR(40) NOT NULL,
               active TINYINT NOT NULL,
               hourly_costs DECIMAL(5,2) DEFAULT 0,
            """
        self.primary_key = "name"
        self.index_fields = ""

    def get_data(self):
        hourly_costs_per_user = self.employee_hour_costs()
        sim = simplicate()
        for employee in sim.employee():
            name = employee.get("name")
            if not name:
                continue
            hourly_costs = hourly_costs_per_user.get(name, 0)
            function = employee.get("function", "")
            active = 1 if employee["employment_status"] == "active" else 0
            yield {
                "name": name,
                "function": function,
                "active": active,
                "hourly_costs": hourly_costs,
            }

    def employee_hour_costs(self):
        def sheet_data(tab, field):
            employees = HeaderSheet(
                "Contracten werknemers", tab, header_row=1, header_col=3
            )
            result = {}
            for name, values in employees.rows().items():
                value = values[field].replace("€", "").replace(",", ".").strip()
                if not value:
                    value = 0
                else:
                    value = float(value)
                value += (
                    OVERIGE_KOSTEN_PER_FREELANCER_PER_UUR
                    if tab in ("Freelance", "Flex")
                    else OVERIGE_KOSTEN_PER_FTE_PER_UUR
                )
                result[name] = Decimal(round(value / PRODUCTIVITEIT, 2))
            return result

        employees = (
                sheet_data("ex werknemers", "Kosten per uur")
                | sheet_data("Freelance", "BrutoPerUur")
                | sheet_data("Stage", "Kosten per uur")
                | sheet_data("Flex", "BrutoPerUur")
                | sheet_data("Fixed", "Kosten per uur")
        )
        for employee in [
            "Hans-Peter Harmsen",
            "Gert Braun",
            "Richard de Boer",
            "Joost Cornelissen",
        ]:
            employees[employee] = MT_FEE_PER_HOUR
        return employees

    def active_employees(self, include_interns=True):
        query = "select * from employee where active=1"
        if not include_interns:
            query += ' and function != "Stagiair"'
        result = self.db.query(query)
        return [res["name"] for res in result]

    def interns(self) -> list:
        result = self.db.select(self.table_name, {"function": "Stagiair"})
        return [res["name"] for res in result]

    def __getitem__(self, employee_name):
        query = f'select * from employee where name="{employee_name}"'
        result = self.db.query(query)
        if not result:
            raise KeyError(f"{employee_name} not found in employee database")
        return result[0]


if __name__ == "__main__":
    chdir("..")
    employee_table = Employee()
    employee_table.repopulate()
    for e in employee_table.db.query("select * from employee where active=1"):
        print(e)
