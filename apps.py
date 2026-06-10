from django.apps import AppConfig


class SmartavtoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'smartavto'
    verbose_name = 'SmartAvtoServis'

    def ready(self):
        pass  # signals would be imported here
