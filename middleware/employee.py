""" Handles the Employee class and employee table """
import pymysql

from middleware.base_table import BaseTable, EMPLOYEE_NAME
from middleware.middleware_utils import singleton, panic
from sources.simplicate import simplicate


@singleton
class Employee(BaseTable):
    def __init__(self):
        self.table_name = 'employee'
        self.table_definition = f"""
               name {EMPLOYEE_NAME} NOT NULL,
               `function` VARCHAR(40) NOT NULL,
               active TINYINT NOT NULL,
            """
        self.primary_key = 'name'
        self.index_fields = ''
        super().__init__()

    def get_data(self):
        sim = simplicate()
        for employee in sim.employee():
            name = employee.get('name')
            if not name:
                continue
            function = employee.get('function', '')
            active = 1 if employee['employment_status'] == 'active' else 0
            yield {'name': name, 'function': function, 'active': active}

    def active_employees(self, include_interns=True):
        query = 'select * from employee where active=1'
        if not include_interns:
            query += ' and function != "Stagiair"'
        result = self.execute(query)
        return [res['name'] for res in result]

    def interns(self) -> list:
        try:
            result = self.select(self.table_name, {'function': 'Stagiair'})
        except pymysql.err.OperationalError:
            # Todo: Retry en panic op een lager niveau implementeren. Bijvoorbeeld self.select en self.execute in base_table
            panic('Lost connection to MySQL server during select in function employee.py interns()')
        return [res['name'] for res in result]

    def __getitem__(self, employee_name):
        query = f'select * from employee where name="{employee_name}"'
        result = self.execute(query)
        if not result:
            raise KeyError(f'{employee_name} not found in employee database')
        return result[0]

    def update_salaries(self):
        pass  # todo: invullen, read from salary Google sheet


if __name__ == '__main__':
    employee_table = Employee()
    print(employee_table.db.execute('select * from employee'))
