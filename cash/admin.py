from django.contrib import admin
from scuelo.admin import sics_site 
from .models import Cashier, Mouvement, Expense, Transfer ,Tarif


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


class CashierAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'is_default', 'balance')
    list_filter = ('type', 'is_default' )
    search_fields = ('name', 'note' )



class MouvementAdmin(admin.ModelAdmin):
    list_display = ('causal', 'montant', 'date_paye', 'inscription', 'tarif', 'cashier', 'annee_scolaire')
    list_filter = ('causal', 'cashier', 'annee_scolaire')
    search_fields = ('inscription__eleve__nom', 'inscription__eleve__prenom', 'causal')
    #readonly_fields = ('type',)  # Ensure type is always "R" (Revenus)

    def get_queryset(self, request):
        # Optimize database queries by prefetching related objects
        return super().get_queryset(request).select_related('inscription', 'tarif', 'cashier', 'annee_scolaire')


class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('description', 'amount', 'date', 'cashier', 'annee_scolaire')
    list_filter = ('cashier', 'annee_scolaire')
    search_fields = ('description', 'note')
    readonly_fields = ('cashier', 'annee_scolaire')  # Automatically assigned fields

    def get_queryset(self, request):
        # Optimize database queries by prefetching related objects
        return super().get_queryset(request).select_related('cashier', 'annee_scolaire')


class TransferAdmin(admin.ModelAdmin):
    list_display = ('amount', 'date', 'from_cashier', 'to_cashier')
    list_filter = ('from_cashier', 'to_cashier')
    search_fields = ('note',)
    readonly_fields = ('date',)  # Automatically assigned field

    def get_queryset(self, request):
        # Optimize database queries by prefetching related objects
        return super().get_queryset(request).select_related('from_cashier', 'to_cashier')
    
    

class TarifAdmin(admin.ModelAdmin):
    list_display = (
        'causal', 'montant', 'classe', 'annee_scolaire', 'date_expiration'
    )
    '''    'expected_total_class', 'actual_total_received',
        'expected_total_tenues_py', 'actual_total_received_tenues_py'''
        
    list_filter = ('causal', 'classe', 'annee_scolaire')
    search_fields = ('classe__nom', 'annee_scolaire__nom')
    '''    readonly_fields = (
        'expected_total_class', 'actual_total_received',
        'expected_total_tenues_py', 'actual_total_received_tenues_py'
    )'''

    def get_queryset(self, request):
        # Optimize database queries by prefetching related objects
        return super().get_queryset(request).select_related('classe', 'annee_scolaire')
    
    
sics_site.register(Tarif ,TarifAdmin )   
sics_site.register(Transfer ,TransferAdmin )   
sics_site.register(Expense  , ExpenseAdmin)
sics_site.register(Mouvement, MouvementAdmin)
sics_site.register(Cashier, CashierAdmin) 