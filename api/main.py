# pylint: disable=E0611,E0401
from configparser import ConfigParser
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from tortoise.expressions import Q

from models import Employee_Pydantic, Employee

app = FastAPI(title="Tortoise ORM FastAPI example")


@app.get("/users", response_model=List[Employee_Pydantic])
async def get_users(active: Optional[bool] = None, intern: Optional[bool] = None):
    q_object = Q()

    if active is not None:
        q_object = q_object & Q(active=active)

    if intern is not None:
        interns = ['stagiair', 'stagiaire', 'intern']
        if intern:
            q_object = q_object & Q(function__in=interns)
        else:
            q_object = q_object & ~Q(function__in=interns)

    return await Employee_Pydantic.from_queryset(Employee.filter(q_object))


def create_db_url(inifile_section: str):
    ini = ConfigParser()
    ini.read(Path(__file__).resolve().parent.parent / 'sources' / 'credentials.ini')
    db = ini[inifile_section]
    port = db.get('port', '3306')
    db_url = f"mysql://{db['dbuser']}:{db['dbpass']}@{db['dbhost']}:{port}/{db['dbname']}"
    return db_url


register_tortoise(
    app,
    db_url=create_db_url('aws-dashboard'),
    modules={"models": ["models"]},
    generate_schemas=False,
    add_exception_handlers=True,
)
