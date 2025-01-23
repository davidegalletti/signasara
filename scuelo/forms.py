from django import forms
from .models import Eleve, Inscription, AnneeScolaire  , Mouvement , Ecole , Classe , Tarif ,UniformReservation , TypeClasse
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from django.contrib.auth.models import User, Group 
from django.contrib.auth.forms import UserCreationForm


class PaiementPerStudentForm(forms.ModelForm):
    class Meta:
        model = Mouvement
        fields = ['tarif', 'montant', 'date_paye', 'note']
        widgets = {
            'date_paye': forms.DateInput(attrs={'type': 'date'}),
            'tarif' : forms.Select(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),

        }

    def __init__(self, *args, **kwargs):
        # Expecting a `classe` keyword argument to be passed in the view
        classe = kwargs.pop('classe', None)
        super().__init__(*args, **kwargs)
        
        if classe:
            self.fields['tarif'].queryset = Tarif.objects.filter(classe=classe)

class EleveUpdateForm(forms.ModelForm):
    classe = forms.ModelChoiceField(queryset=Classe.objects.all(), required=True)
    annee_scolaire = forms.ModelChoiceField(queryset=AnneeScolaire.objects.all(), required=True)

    class Meta:
        model = Eleve
        fields = [
            'nom', 'prenom', 'condition_eleve', 'sex', 'date_naissance', 
            'cs_py', 'hand', 'annee_inscr', 'parent', 'tel_parent', 
            'note_eleve', 'classe', 'annee_scolaire'
        ]
        
class ClasseCreateForm(forms.ModelForm):
    class Meta:
        model = Classe
        fields = ['nom', 'type', 'legacy_id']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'legacy_id': forms.TextInput(attrs={'class': 'form-control'}),
        }    
    
'''class ClassUpgradeForm(forms.Form):
    new_school = forms.ModelChoiceField(queryset=Ecole.objects.all(), required=True, label="Nouvelle École")
    new_class = forms.ModelChoiceField(queryset=Classe.objects.none(), required=True, label="Nouvelle Classe")

    def __init__(self, *args, **kwargs):
        super(ClassUpgradeForm, self).__init__(*args, **kwargs)
        if 'new_school' in self.data:
            try:
                school_id = int(self.data.get('new_school'))
                self.fields['new_class'].queryset = Classe.objects.filter(ecole_id=school_id).order_by('nom')
            except (ValueError, TypeError):
                self.fields['new_class'].queryset = Classe.objects.none()
        else:
            self.fields['new_class'].queryset = Classe.objects.none()
'''
       
'''class ClassUpgradeForm(forms.Form):
    new_school = forms.ModelChoiceField(
        queryset=Ecole.objects.all(),
        label="Select School",
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    new_class = forms.ModelChoiceField(
        queryset=Classe.objects.none(),  # Initially empty, will be populated via AJAX
        label="Select Class",
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate the new_class field based on the selected school
        if 'new_school' in self.data:
            try:
                school_id = int(self.data.get('new_school'))
                self.fields['new_class'].queryset = Classe.objects.filter(ecole_id=school_id)
            except (ValueError, TypeError):
                pass     '''     
                
class ClassUpgradeForm(forms.Form):
    new_class = forms.ModelChoiceField(
        queryset=Classe.objects.all(),
        label="Select Class",
        required=True,
        widget=forms.HiddenInput()  # Hidden because selection happens in the table
    )               
class SchoolChangeForm(forms.Form):
    new_school = forms.ModelChoiceField(queryset=Ecole.objects.all(), required=True, label="Nouvelle École")

class InscriptionForm(forms.ModelForm):
    class Meta:
        model = Inscription
        fields = ['classe', 'annee_scolaire']

class EcoleCreateForm(forms.ModelForm):
    class Meta:
        model = Ecole
        fields = ['nom', 'ville', 'nom_du_referent', 'prenom_du_referent', 'email_du_referent', 'telephone_du_referent', 'note', 'externe']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'ville': forms.TextInput(attrs={'class': 'form-control'}),
            'nom_du_referent': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom_du_referent': forms.TextInput(attrs={'class': 'form-control'}),
            'email_du_referent': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone_du_referent': forms.TextInput(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'externe': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
class UserForm(UserCreationForm):
    email = forms.EmailField(required=True)
    groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all(), required=False, widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'groups']

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'permissions']
        widgets = {
            'permissions': forms.CheckboxSelectMultiple,
        }
   
class InscriptionPerStudentForm(forms.ModelForm):
    class Meta:
        model = Inscription
        fields = ['classe', 'annee_scolaire']

class EleveCreateForm(forms.ModelForm):
    classe = forms.ModelChoiceField(queryset=Classe.objects.all(), required=True, label="Classe")
    annee_scolaire = forms.ModelChoiceField(queryset=AnneeScolaire.objects.all(), required=True, label="Année Scolaire")

    class Meta:
        model = Eleve
        fields = [
            'nom', 'prenom', 'date_enquete', 'condition_eleve', 'sex',
            'date_naissance', 'cs_py', 'hand', 'annee_inscr', 'parent',
            'tel_parent', 'note_eleve', 'classe', 'annee_scolaire'
        ]
        widgets = {
            'date_enquete': forms.DateInput(attrs={'type': 'date'}),
            'date_naissance': forms.DateInput(attrs={'type': 'date'}),
            'annee_inscr': forms.NumberInput(attrs={'min': 1900, 'max': 2100}),
            'note_eleve': forms.Textarea(attrs={'rows': 4}),
        }

class InscriptionForm(forms.ModelForm):
    class Meta:
        model = Inscription
        fields = ['eleve', 'classe', 'annee_scolaire']
        widgets = {
            'eleve': forms.Select(attrs={'class': 'form-control'}),
            'classe': forms.Select(attrs={'class': 'form-control'}),
            'annee_scolaire': forms.Select(attrs={'class': 'form-control'}),

        }


class AnneeScolaireForm(forms.ModelForm):
    class Meta:
        model = AnneeScolaire
        fields = ['nom', 'nom_bref', 'date_initiale', 'date_finale', 'actuel']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'nom_bref': forms.TextInput(attrs={'class': 'form-control'}),
            'date_initiale': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_finale': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'actuel': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
class TarifForm(forms.ModelForm):
    class Meta:
        model = Tarif
        fields = ['causal', 'montant', 'date_expiration']
        widgets = {
            'date_expiration': forms.TextInput(attrs={'type': 'date'}),
        }

class MouvementForm(forms.ModelForm):
    class Meta:
        model = Mouvement
        fields = ['montant', 'type', 'causal', 'date_paye', 'note', 'inscription']
        widgets = {
            'date_paye': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'montant': forms.NumberInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'causal': forms.Select(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={
                'class': 'form-control note-field',
                'rows': 4,  # Height control
                'style': 'width: 100%;',  # Full width
            }),
            'inscription': forms.Select(attrs={'class': 'form-control select2'}),  # Added `select2` class
        }
        
class ClasseCreateForm(forms.ModelForm):
    class Meta:
        model = Classe
        fields = ['nom', 'type']  # Remove 'ecole' since it's set automatically

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['type'].queryset = TypeClasse.objects.all()

from django import forms
from django.utils import timezone
from .models import UniformReservation, Eleve, AnneeScolaire
class UniformReservationForm(forms.ModelForm):
    class Meta:
        model = UniformReservation
        fields = ['student', 'quantity', 'cost_per_uniform', 'status', 'school_year']
