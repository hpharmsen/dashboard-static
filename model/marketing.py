import os

from settings import MAANDEN
from sources.googlesheet import HeaderSheet


class Marketing(HeaderSheet):
    def __init__(self, sheetname, tabname, header_row=1, header_col=1):
        super().__init__(sheetname, tabname, header_row, header_col)

        year = 2022
        self.column_headers = ["okt. 2021", "nov. 2021", "dec. 2021"]
        while True:
            for month in MAANDEN:
                monthstamp = (
                    f"mei {year}"
                    if month.lower() == "mei"
                    else f"{month.lower()}. {year}"
                )
                bijgewerkt = self["Bijgewerkt", monthstamp]
                if bijgewerkt and int(bijgewerkt):
                    self.column_headers += [monthstamp]
                else:
                    return
            year += 1

    def kpi_row(self, row_header: str):
        def normalize(value: str):
            value = value.replace("€ ", "").replace(".", "").replace(",", ".").strip()
            if not value:
                return 0
            try:
                return int(value)
            except ValueError:
                return value

        return [
            normalize(self[row_header, column_header])
            for column_header in self.column_headers
        ]

    def total(self, row_header: str) -> int:
        return sum(self.kpi_row(row_header))

    def last(self, row_header: str) -> int:
        return self.kpi_row(row_header)[-1]

    def last_month(self):
        stamp = self.column_headers[-1]
        month_str, year_str = stamp.split(". ")
        month = MAANDEN.index(month_str[0].upper() + month_str[1:]) + 1
        year = int(year_str)
        return year, month


if __name__ == "__main__":
    os.chdir("..")
    sheet = Marketing("Oberon - Budget + KPI's", "KPIs voor MT", 1, 1)
    print(sheet.kpi_row("Bereik"))
    print(sheet.kpi_row("€ Totaal"))
    print(sheet.column_headers)
