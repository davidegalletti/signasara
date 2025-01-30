from django.contrib import admin

from scuelo.admin import sics_site 

# Register your models here.
class PaiementAdmin(admin.ModelAdmin):
    list_display = [
        'get_causal_display', 'montant',
        'date_paye', 'inscription'
    ]
    search_fields = ['inscription__eleve__nom', 'inscription__eleve__prenom']
    list_select_related = ['inscription']
    list_filter = ['inscription__annee_scolaire', 'causal']

    def get_causal_display(self, obj):
        return obj.get_causal_display()

    get_causal_display.short_description = 'Causal'
