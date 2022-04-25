from abc import ABC, abstractmethod
from typing import Iterator

from middleware.middleware_utils import get_middleware_db

SIMPLICATE_ID = 'VARCHAR(50)'
PROJECT_NUMBER = 'VARCHAR(10)'
EMPLOYEE_NAME = 'VARCHAR(40)'
HOURS = 'DECIMAL(6,2)'
MONEY = 'DECIMAL(9,2)'


# TODO: Make this an abstract base class
class BaseTable(ABC):
    def __init__(self):
        super().__init__()
        if not hasattr(self, 'db'):
            self.db = get_middleware_db()
        self.index_fields = ''
        self.table_name = ''
        self.table_definition = ''
        self.primary_key = ''

    @abstractmethod
    def get_data(self, day=None) -> Iterator[dict]:
        pass

    def create_table(self, force_recreate=0):
        """Creates the table to store timesheet data plus it's indexes"""

        if force_recreate:
            for field in self.index_fields.split():
                # try:
                self.db.execute(f'DROP INDEX {self.table_name}_{field} ON {self.table_name}')
                # except: WELKE exceptie?
                #    pass
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
            self.db.execute(
                f"CREATE INDEX {self.table_name}_{field} ON {self.table_name} ({field.replace('__', ',')})"
            )
        self.db.commit()

    def insert_dicts(self, data: Iterator[dict]):
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
            self.db.execute(query)
        self.db.commit()

    def repopulate(self):
        self.create_table(force_recreate=1)
        self.insert_dicts(self.get_data)
        self.create_indexes()

    # def first(self, query):
    #     try:
    #         return self.db.first(query)
    #     except SQL_ERRORS:
    #         panic('Lost connection to MySQL while executing query ' + query)
    #
    # def query(self, query) -> Generator:
    #     """For running a select query"""
    #     try:
    #         yield from self.db.query(query)
    #     except SQL_ERRORS:
    #         panic('Lost connection to MySQL while executing query ' + query)
    #
    # def execute(self, query, continue_on_error=False):
    #     """For executing a sql command"""
    #     try:
    #         return self.db.execute(query)
    #     except SQL_ERRORS:
    #         if continue_on_error:
    #             return
    #         panic('Lost connection to MySQL while executing query ' + query)
    #
    # def select(self, conditions) -> Generator:
    #     try:
    #         yield from self.db.select(self.table_name, conditions)
    #     except SQL_ERRORS:
    #         panic(f'Lost connection to MySQL while executing select on {self.table_name} ' + str(conditions))
    #
    # def commit(self):
    #     self.db.commit()
