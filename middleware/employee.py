''' Handles the Employee class and employee table '''

from middleware.base_table import BaseTable
from middleware.middleware_utils import singleton
from sources.simplicate import simplicate


@singleton
class Employee(BaseTable):
    def __init__(self):
        self.table_name = 'employee'
        self.table_definition = """
            CREATE TABLE IF NOT EXISTS employee (
               name VARCHAR(40) NOT NULL,
               `function` VARCHAR(40) NOT NULL,
               active TINYINT NOT NULL,
               
               updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

               PRIMARY KEY(name) )
            """
        self.index_fields = ''
        super().__init__()

    def update(self):
        self._create_project_table(force_recreate=1)
        sim = simplicate()
        employees = []
        for employee in sim.employee():
            name = employee.get('name')
            if not name:
                continue
            function = employee.get('function', '')
            active = 1 if employee['employment_status'] == 'active' else 0
            employees += [{'name': name, 'function': function, 'active': active}]

        self.insert_dicts(employees)

    def active_employees(self, include_interns=True):
        query = 'select * from employee where active=1'
        if not include_interns:
            query += ' and function != "intern"'
        result = self.db.execute(query)
        return [res['name'] for res in result]

    def interns(self) -> list:
        result = self.db.select('employee', {'function': 'Stagiair'})
        return [res['name'] for res in result]

    def __getitem__(self, employee_name):
        query = f'select * from employee where name="{employee_name}"'
        result = self.db.execute(query)
        if not result:
            raise KeyError(f'{employee_name} not found in employee database')
        return result[0]

    def update_salaries(self):
        pass  # todo: invullen


if __name__ == '__main__':
    employee_table = Employee()
