from django.apps import AppConfig


class BrockerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'brocker'
    def ready(self):
        import brocker.signals  # Ensure signals are imported and registered
