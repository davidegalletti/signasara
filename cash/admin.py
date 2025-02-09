from django.contrib import admin
from scuelo.admin import sics_site 
from scuelo.models import AnneeScolaire
from .forms import  ChangeSchoolYearForm
from .models import Cashier, Mouvement, Expense, Transfer ,Tarif
from django.db import models
from django.contrib import messages
from django.shortcuts import redirect
from django.shortcuts import render
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
    actions = ['remove_duplicates'] # Add the custom action
    #readonly_fields = ('type',)  # Ensure type is always "R" (Revenus)
    @admin.action(description='Remove duplicate Mouvement entries (CAREFUL! Requires Confirmation)')
    def remove_duplicates(self, request, queryset):
        """
        Admin action to remove duplicate Mouvement entries across all records.
        Requires confirmation from the user.
        """
        if request.POST.get('confirm'):  # If the user has confirmed
            # 1. Get the criteria that define a duplicate (Adjust to match your definition)
            duplicate_groups = (
                Mouvement.objects.values('causal', 'montant', 'date_paye', 'inscription')
                .annotate(count=models.Count('id'))
                .filter(count__gt=1)
            )

            total_deleted = 0
            for group in duplicate_groups:
                # Find all Mouvement entries matching the duplicate group within the selected queryset
                duplicates = Mouvement.objects.filter(
                    causal=group['causal'],
                    montant=group['montant'],
                    date_paye=group['date_paye'],
                    inscription=group['inscription'],
                ).order_by('pk') # Order by primary key

                # Keep the first, delete the rest
                if duplicates.count() > 1:
                    first_mouvement = duplicates.first()  # The one we keep
                    deleted_count = 0
                    for duplicate in duplicates[1:]:
                        duplicate.delete()
                        deleted_count += 1
                    total_deleted += deleted_count
                    self.message_user(request, f"Removed {deleted_count} duplicate Mouvement entries with causal={group['causal']}, montant={group['montant']}, date_paye={group['date_paye']}, inscription={group['inscription']}", level=messages.SUCCESS)

            self.message_user(request, f"Successfully removed {total_deleted} duplicate Mouvement entries.", level=messages.SUCCESS)
            return  # Exit to prevent rendering the confirmation page again

        # 2. Render the confirmation page
        return render(
            request,
            'admin/cash/mouvement/confirm_duplicate_removal.html',  # Create this template
            context={'action': 'remove_duplicates',
                     'queryset': queryset.count(),
                     'title':"Remove All Duplicates"}
        )
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
    actions = ['change_school_year']
    def get_form(self, request, obj=None, **kwargs):
        if request.method == 'GET' and 'action' in request.GET and request.GET['action'] == 'change_school_year':
            self.form = ChangeSchoolYearForm
        else:
            self.form = None
        return super().get_form(request, obj, **kwargs)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}

        if request.method == 'POST' and 'action' in request.POST and request.POST['action'] == 'change_school_year':
            form = ChangeSchoolYearForm(request.POST)

            if form.is_valid():
                new_annee_scolaire = form.cleaned_data['new_annee_scolaire']

                selected = request.POST.getlist('_selected_action')
                queryset = self.model.objects.filter(pk__in=selected)

                updated_count = 0
                for tarif in queryset:
                    tarif.annee_scolaire = new_annee_scolaire
                    tarif.save()
                    updated_count += 1

                self.message_user(request, f"Successfully updated the school year for {updated_count} tariffs to {new_annee_scolaire}", level=messages.SUCCESS)
                return redirect("admin:cash_tarif_changelist")

            else:
                extra_context['form'] = form
                messages.error(request, "There was an error in the form. Please correct it.")
        else:
            form = ChangeSchoolYearForm()
            extra_context['form'] = form

        return super().changelist_view(request, extra_context=extra_context)

    @admin.action(description='Change school year for selected tariffs to 2023 2024')
    def change_school_year(self, request, queryset):
        """
        Admin action to change the annee_scolaire for selected Tarif entries to "2023 2024"
        """
        # Get the target AnneeScolaire instance
        try:
            target_annee_scolaire = AnneeScolaire.objects.get(nom="2023 2024")
        except AnneeScolaire.DoesNotExist:
            self.message_user(request, "Error: No AnneeScolaire found with name '2023 2024'.", level=messages.ERROR)
            return

        # Update the selected Tarif entries
        updated_count = queryset.update(annee_scolaire=target_annee_scolaire)
        self.message_user(request, f"Successfully updated the school year for {updated_count} tariffs to '2023 2024'.", level=messages.SUCCESS)
    def get_queryset(self, request):
        # Optimize database queries by prefetching related objects
        return super().get_queryset(request).select_related('classe', 'annee_scolaire')
    
    
sics_site.register(Tarif ,TarifAdmin )   
sics_site.register(Transfer ,TransferAdmin )   
sics_site.register(Expense  , ExpenseAdmin)
sics_site.register(Mouvement, MouvementAdmin)
sics_site.register(Cashier, CashierAdmin) 