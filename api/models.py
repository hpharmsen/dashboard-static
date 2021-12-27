from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.models import Model


class Employee(Model):  # Class name lowercase same as db table name
    """
    The Employee model
    """

    name = fields.CharField(max_length=40, pk=True)
    function = fields.CharField(max_length=40)
    active = fields.BooleanField()
    updated = fields.DatetimeField(auto_now=True)

    def full_name(self) -> str:
        """
        Returns the best name
        """
        # if self.name or self.family_name:
        #    return f"{self.name or ''} {self.family_name or ''}".strip()
        return self.name

    class PydanticMeta:
        computed = ["full_name"]
        # exclude = ["password_hash"]


Employee_Pydantic = pydantic_model_creator(Employee, name="Employee")
