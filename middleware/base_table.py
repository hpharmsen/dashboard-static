from pymysql import OperationalError

from middleware.middleware_utils import get_middleware_db


class BaseTable:
    def __init__(self):
        if not hasattr(self, 'db'):
            self.db = get_middleware_db()
        self._create_project_table()

    def _create_project_table(self, force_recreate=0):
        """Creates the table to store timesheet data plus it's indexes"""

        if force_recreate:
            for field in self.index_fields.split():
                try:
                    self.db.execute(f'DROP INDEX {self.table_name}_{field} ON {self.table_name}')
                except:
                    pass

            self.db.execute(f'DROP TABLE IF EXISTS {self.table_name}')

        self.db.execute(self.table_definition)

        for field in self.index_fields.split():
            try:
                self.db.execute(f'CREATE INDEX {self.table_name}_{field} ON {self.table_name} ({field})')
            except OperationalError:
                pass  # Index already existent

    def insert_dicts(self, dicts):
        for dict in dicts:
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
