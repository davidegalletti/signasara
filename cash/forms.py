from django import forms
from .models import  Mouvement  , Tarif 
from scuelo.models import UniformReservation 
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
        
class TarifForm(forms.ModelForm):
    class Meta:
        model = Tarif
        fields = ['causal', 'montant', 'date_expiration']
        widgets = {
            'date_expiration': forms.TextInput(attrs={'type': 'date'}),
        }

        
        
