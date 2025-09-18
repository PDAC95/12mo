from django.apps import AppConfig


class SpacesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "spaces"
    verbose_name = "Spaces"

    def ready(self):
        import spaces.models  # This will register the signals
