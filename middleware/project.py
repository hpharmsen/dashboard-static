from middleware.base_table import BaseTable, PROJECT_NUMBER, SIMPLICATE_ID, EMPLOYEE_NAME, panic
from middleware.middleware_utils import singleton
from sources.simplicate import simplicate


@singleton
class Project(BaseTable):
    def __init__(self):
        self.table_name = 'project'
        self.table_definition = f"""
               project_id {SIMPLICATE_ID} NOT NULL,
               organization VARCHAR(80) NOT NULL,
               my_organization_profile VARCHAR(40) NOT NULL,
               project_name VARCHAR(80) NOT NULL,
               project_number {PROJECT_NUMBER} NOT NULL,
               pm {EMPLOYEE_NAME} NOT NULL,
               status varchar(20) NOT NULL,
               start_date DATETIME,
               end_date DATETIME,
            """
        self.primary_key = 'project_id'
        self.index_fields = 'organization project_number start_date end_date status'
        super().__init__()

    def get_data(self):
        sim = simplicate()
        projects = sim.project()
        if not projects:
            panic('Could not get projects from Simplicate')
        for project in projects:
            if project['my_organization_profile'] == 'Qikker Online B.V.':
                continue
            try:
                pm = project['project_manager']['name']
            except KeyError:
                pm = ''
            yield {
                'project_id': project['id'],
                'organization': project['organization']['name'],
                'my_organization_profile': project['my_organization_profile']['organization']['name'],
                'project_name': project['name'],
                'project_number': project['project_number'],
                'pm': pm,
                'status': project['project_status']['label'][5:],  # tab_pactive -> active
                'start_date': project.get('start_date'),
                'end_date': project.get('end_date'),
            }


if __name__ == '__main__':
    project_table = Project()
    project_table.repopulate()
