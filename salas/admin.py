from django.contrib import admin
from salas.models import Sala, LimpezaRegistro


class SalaAdmin(admin.ModelAdmin):
    pass

class LimpezaRegistroAdmin(admin.ModelAdmin):
    pass


admin.site.register(Sala, SalaAdmin)
admin.site.register(LimpezaRegistro, LimpezaRegistroAdmin)