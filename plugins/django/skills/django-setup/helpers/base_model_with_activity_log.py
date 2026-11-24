from core.__PREFIX___models.base_model import BaseModel


class BaseModelWithActivityLog(BaseModel):
    """
    The concrete subclasses are registered with django-auditlog in
    CoreConfig.ready() (core/apps.py).
    """

    class Meta:
        abstract = True
