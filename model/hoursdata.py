from middleware.timesheet import Timesheet
from model.productiviteit import beschikbare_uren_volgens_rooster
from model.utilities import Period


class HoursData:
    """Class to store and calculate the main production KPI's"""

    # rooster : float
    # verlof : float
    # verzuim : float
    # beschikbaar: float
    # op_klant_geboekt: float
    # billable: float
    # omzet: float

    def __init__(self, period: Period, employees: list = None):
        timesheet = Timesheet()
        self.rooster, self.verlof, self.verzuim = beschikbare_uren_volgens_rooster(
            period, employees
        )
        self.op_klant_geboekt_old = timesheet.geboekte_uren(
            period, users=employees, only_clients=1, only_billable=0
        )
        self.op_klant_geboekt = timesheet.geboekte_uren(
            period, users=employees, only_clients=1, only_billable=0
        )
        self.billable = timesheet.geboekte_uren(
            period,
            users=employees,
            only_clients=1,
            only_billable=1,
        )
        # self.omzet_old = geboekte_omzet_users(period, users=employees, only_clients=1, only_billable=0)
        self.omzet = timesheet.geboekte_omzet(
            period, users=employees, only_clients=1, only_billable=0
        )

    def beschikbaar(self) -> float:
        return self.rooster - self.verlof - self.verzuim

    def effectivity(self):
        return (
            100 * self.op_klant_geboekt / self.beschikbaar()
            if self.beschikbaar()
            else 0
        )

    def billable_perc(self):
        return 100 * self.billable / self.beschikbaar() if self.beschikbaar() else 0

    def correcties(self):
        return self.op_klant_geboekt - self.billable

    def correcties_perc(self):
        return (
            (self.op_klant_geboekt - self.billable) / self.op_klant_geboekt
            if self.op_klant_geboekt
            else 0
        )

    def uurloon(self):
        return self.omzet / self.op_klant_geboekt if self.op_klant_geboekt else 0
