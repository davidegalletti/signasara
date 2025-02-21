from django import forms
from .models import  Mouvement  , Tarif  , Expense , Transfer
from scuelo.models import UniformReservation 
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from django.contrib.auth.models import User, Group 
from django.contrib.auth.forms import UserCreationForm
from scuelo.models import AnneeScolaire
class PaiementPerStudentForm(forms.ModelForm):
    class Meta:
        model = Mouvement
        fields = ['montant', 'date_paye', 'note', 'causal']  # Include date_paye and other necessary fields
        widgets = {
            'montant': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter amount'}),
            'date_paye': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'YYYY-MM-DD'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Additional notes'}),
            'causal': forms.Select(attrs={'class': 'form-control'})  # Dropdown for causal choices
        }
        # You can add custom attributes or initial values if needed
class MouvementForm(forms.ModelForm):
    class Meta:
        model = Mouvement
        fields = ['montant', 'causal', 'date_paye', 'note', 'inscription']
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
        
class ChangeSchoolYearForm(forms.Form):
    new_annee_scolaire = forms.ModelChoiceField(
        queryset=AnneeScolaire.objects.filter(nom="2023 2024"), # Filter by name
        label="New School Year",
        required=True,
    )
        
class TarifForm(forms.ModelForm):
    class Meta:
        model = Tarif
        fields = ['causal', 'montant', 'date_expiration']
        widgets = {
            'date_expiration': forms.TextInput(attrs={'type': 'date'}),
        }

from .models import Cashier         
'''class ExpenseForm(forms.ModelForm):
    c_sco_balance = forms.DecimalField(
        label="C_SCO Balance",
        max_digits=10,
        decimal_places=2,
        disabled=True,  # Make it read-only
        required=False,
    )

    class Meta:
        model = Expense
        fields = ['description', 'amount', 'date', 'note']  # Exclude cashier since it's auto-assigned

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add custom attributes for Bootstrap styling
        self.fields['description'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter expense description'})
        self.fields['amount'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter amount'})
        self.fields['date'].widget.attrs.update({'class': 'form-control'})
        self.fields['note'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Additional notes (optional)'})
        self.fields['c_sco_balance'].widget.attrs.update({'class': 'form-control', 'readonly': True})

        # Fetch the default cashier (C_SCO) and calculate its balance
        c_sco_cashier = Cashier.get_default_cashier()
        if c_sco_cashier:
            self.fields['c_sco_balance'].initial = c_sco_cashier.balance()'''
            
class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['description', 'amount', 'date', 'note']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter description'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter amount'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter notes'}),
        }
            
class TransferForm(forms.ModelForm):
    class Meta:
        model = Transfer
        fields = ['amount', 'from_cashier', 'to_cashier', 'note']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Apply Bootstrap styling to all fields
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

        # Customize specific fields (optional)
        self.fields['note'].widget = forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        self.fields['amount'].widget.attrs.update({'placeholder': 'Enter Amount', 'min': 0})
        self.fields['from_cashier'].label = "From"
        self.fields['to_cashier'].label = "To"


        # Filter the 'to_cashier' queryset based on the 'from_cashier' value
        if 'from_cashier' in self.data:
            try:
                from_cashier_id = int(self.data.get('from_cashier'))
                self.fields['to_cashier'].queryset = Cashier.objects.exclude(pk=from_cashier_id)
            except (ValueError, TypeError):
                pass  # Invalid input, ignore
        else:
            # Initial state: Exclude no cashiers
            self.fields['to_cashier'].queryset = Cashier.objects.all()
class CashierForm(forms.ModelForm):
    class Meta:
        model = Cashier
        fields = ['name', 'type', 'note', 'is_default']  # Specify the fields you want

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

        # Optionally, customize individual fields further
        self.fields['note'].widget = forms.Textarea(attrs={'class': 'form-control', 'rows': 3})  # For better note input
        self.fields['is_default'].widget.attrs.update({'class': 'form-check-input'}) #style the is_default checkbox