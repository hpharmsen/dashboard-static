from middleware.base_table import BaseTable
from middleware.middleware_utils import singleton
from sources.simplicate import simplicate


@singleton
class Project(BaseTable):
    def __init__(self):
        self.table_name = 'project'
        self.table_definition = """
            CREATE TABLE IF NOT EXISTS project (
               project_id VARCHAR(50) NOT NULL,
               organization VARCHAR(255) NOT NULL,
               my_organization_profile VARCHAR(40) NOT NULL,
               project_name VARCHAR(255) NOT NULL,
               project_number VARCHAR(10) NOT NULL,
               pm varchar(40) NOT NULL,
               status varchar(20) NOT NULL,
               start_date DATETIME,
               end_date DATETIME,
               updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
               PRIMARY KEY(project_id) 
            )"""
        self.index_fields = 'organization project_number start_date end_date status'
        super().__init__()

    def update(self):
        self._create_project_table(force_recreate=1)
        sim = simplicate()
        projects = [
            flatten_project_data(project)
            for project in sim.project()
            if project['my_organization_profile'] != 'Qikker Online B.V.'
        ]
        self.insert_dicts(projects)


def flatten_project_data(project):
    try:
        pm = project['project_manager']['name']
    except KeyError:
        pm = ''
    return {
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
    project_table.update()
