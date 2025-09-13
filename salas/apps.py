from django.apps import AppConfig

class SalasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'salas'

    def ready(self):
        """Importa os sinais da aplicação quando o Django está pronto."""
        import salas.signals