from collections import Generator

from pymysql import OperationalError

from middleware.middleware_utils import get_middleware_db, panic

SIMPLICATE_ID = 'VARCHAR(50)'
PROJECT_NUMBER = 'VARCHAR(10)'
EMPLOYEE_NAME = 'VARCHAR(40)'
HOURS = 'DECIMAL(6,2)'
MONEY = 'DECIMAL(9,2)'


class BaseTable:
    def __init__(self):
        if not hasattr(self, 'db'):
            self.db = get_middleware_db()

    def create_table(self, force_recreate=0):
        """Creates the table to store timesheet data plus it's indexes"""

        if force_recreate:
            for field in self.index_fields.split():
                try:
                    self.db.execute(f'DROP INDEX {self.table_name}_{field} ON {self.table_name}')
                except:
                    pass
            self.db.execute(f'DROP TABLE IF EXISTS {self.table_name}')

        primary_key_definition = f', PRIMARY KEY({self.primary_key.replace("__", ",")})' if self.primary_key else ''
        sql = f'''CREATE TABLE IF NOT EXISTS {self.table_name} (
              {self.table_definition}
              updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
              {primary_key_definition} )
              CHARACTER SET utf8'''
        self.db.execute(sql)
        self.db.commit()

    def create_indexes(self):
        for field in self.index_fields.split():
            try:
                self.db.execute(
                    f"CREATE INDEX {self.table_name}_{field} ON {self.table_name} ({field.replace('__', ',')})")
            except OperationalError:
                pass  # Index already existent
        self.db.commit()

    def insert_dicts(self, data: Generator[dict, None, None]):
        for dict in data():
            fields = []
            value_strings = []
            for field, value in dict.items():
                fields += [field]
                if value is None:
                    value_str = 'NULL'
                elif isinstance(value, bool):
                    value = 1 and value or 0
                    value_str = str(value)
                else:
                    value_str = '"' + str(value).replace('\\', '\\\\').replace("'", r"\'").replace('"', r'\"') + '"'
                value_strings += [value_str]
            values = ",".join(value_strings)
            query = f'INSERT INTO {self.table_name} (`{"`, `".join(fields)}`) values ({values});'
            try:
                self.db.execute(query)
            except ConnectionResetError:
                panic('Connnection reset by peer in base_tabel.py insert_dicts() while trying to execute query', query)
        self.db.commit()

    def repopulate(self):
        self.create_table(force_recreate=1)
        self.insert_dicts(self.get_data)
        self.create_indexes()

