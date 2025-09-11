from django.contrib import admin
from salas.models import Sala, LimpezaRegistro


class SalaAdmin(admin.ModelAdmin):
    """Define a interface de administração para o modelo Sala.

    Como esta classe está vazia, o modelo `Sala` será exibido na interface
    de administração com suas configurações padrão.
    """
    pass

class LimpezaRegistroAdmin(admin.ModelAdmin):
    """Define a interface de administração para o modelo LimpezaRegistro.

    Como esta classe está vazia, o modelo `LimpezaRegistro` será exibido
    na interface de administração com suas configurações padrão.
    """
    pass


admin.site.register(Sala, SalaAdmin)
admin.site.register(LimpezaRegistro, LimpezaRegistroAdmin)