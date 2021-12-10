''' Handles the Employee class and employee table '''

from middleware.middleware import singleton, get_middleware_db
from sources.simplicate import simplicate


@singleton
class Employee():
    def __init__(self):
        self.db = get_middleware_db()
        self._create_employee_table()
        # self.update()

    def _create_employee_table(self):
        ''' Creates the table to store employee data plus it's indexes '''

        # self.db.execute('DROP TABLE IF EXISTS employee;')
        self.db.execute("""CREATE TABLE IF NOT EXISTS employee (
                           name VARCHAR(40) NOT NULL,
                           `function` VARCHAR(40) NOT NULL,
                           active TINYINT NOT NULL,
                           
                           updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

                           PRIMARY KEY(name) )
                   """)
        # try:
        #     for field in 'week employee organization project_number type updated'.split():
        #         self.db.execute(f'CREATE INDEX timesheet_{field} ON timesheet ({field})')
        #     self.db.execute(f'CREATE INDEX timesheet_year_week ON timesheet (year,week)')
        # except OperationalError:
        #     pass  # Index already existent

    def update(self):

        # Find newest day in database
        sim = simplicate()
        employees = sim.employee()
        query = f'delete from employee;'
        self.db.execute(query)
        query = ' '
        for employee in employees:
            name = employee.get('name')
            if not name:
                continue
            function = employee.get('function', '')
            active = 1 if employee['employment_status'] == 'active' else 0
            query = f'''INSERT INTO employee (name, `function`, active) VALUES ("{name}", "{function}", {active});'''
            self.db.execute(query)
        self.db.commit()

    def active_employees(self, include_interns=True):
        query = 'select * from employee where active=1'
        if not include_interns:
            query += ' and function != "intern"'
        result = self.db.execute(query)
        return [res['name'] for res in result]

    def interns(self):
        result = self.db.select('employee', {'function': 'Stagiair'})
        return [res['name'] for res in result]

    def __getitem__(self, employee_name):
        query = f'select * from employee where name="{employee_name}"'
        result = self.db.execute(query)
        if not result:
            raise KeyError(f'{employee_name} not found in employee database')
        return result[0]

    def update_salaries(self):
        pass
