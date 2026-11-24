from django.apps import AppConfig, apps


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        from auditlog.registry import auditlog

        from core.__PREFIX___models.base_model_with_activity_log import (
            BaseModelWithActivityLog,
        )

        # Log the changes of every concrete model that extends
        # BaseModelWithActivityLog, with all its fields
        for model in apps.get_models():
            if issubclass(model, BaseModelWithActivityLog):
                auditlog.register(model)
