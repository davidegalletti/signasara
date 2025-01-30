from django.contrib import admin
from .models import Classe, Eleve, AnneeScolaire, Inscription , StudentLog , UniformReservation
from django.contrib.auth.models import User, Group


class SicAdminArea(admin.AdminSite):
    site_header = 'SICS NASSARA'
    site_title = 'SICS NASSARA'
    index_title = 'SICS NASSARA'


sics_site = SicAdminArea(name='SICS NASSARA')


# class PaimentInline(admin.TabularInline):
#     model = Paiement
#     extra = 0
#     classes = ['collapse']


class InscriptionInline(admin.TabularInline):
    model = Inscription
    #list_display = [''
    autocomplete_fields = ['eleve']
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        # obj è il MediciZone
        formset = super(InscriptionInline, self).get_formset(request, obj, **kwargs)
        # formset.form.base_fields['a'].queryset
        self.eleve = obj
        return formset

    def get_queryset(self, request):
        qs = super(InscriptionInline, self).get_queryset(request)
        return qs
        # return qs.filter(annee_scolaire__actuel=True)


class EleveAdmin(admin.ModelAdmin):
    fieldsets = (
        ('INFORMATIONS DE  BASE', {
            'fields': ('nom', 'prenom', 'sex',
                       'date_naissance'
                       ),
        }
         ),
        ('INFORMATION SOCIALE', {
            'fields': ('condition_eleve', 'cs_py', 'hand'
                       , 'date_enquete'),
        }
         ),
        ('INFORMATION PARENT', {
            'fields': ('parent', 'tel_parent',
                       ),
        }
         )
    )
    list_display = ['id', 'nom', 'prenom', 'condition_eleve', 'sex', 'date_naissance', 'tot_pag' , 'tenues' , 'cs_py' , 'hand' , 'annee_inscr' ] #
    search_fields = ['nom', 'prenom' , 'cs_py' ]
    list_filter = ['annee_inscr']
    inlines = [InscriptionInline]

    def tot_pag(self, instance):
        return 'tot pag'
  
    tot_pag.short_description = "Tot pag"

    def tenues(self, instance):
        return 'What is it?'

    tenues.short_description = "Tenues"




class InscriptionAdmin(admin.ModelAdmin):
    autocomplete_fields = ['eleve']
    
    
@admin.register(UniformReservation)
class UniformReservationAdmin(admin.ModelAdmin):
    list_display = ('student', 'quantity', 'status', 'school_year')
    list_filter = ('status', 'school_year')    

# sics_site.register(Paiement, PaiementAdmin)
sics_site.register(Eleve, EleveAdmin)
sics_site.register(Classe)
sics_site.register(AnneeScolaire)
sics_site.register(Inscription, InscriptionAdmin)
sics_site.register(User)
sics_site.register(Group)
sics_site.register(StudentLog)