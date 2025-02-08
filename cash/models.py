from django.db import models
from django.utils import timezone
from django.db.models import Q, Sum
from model_utils.models import TimeStampedModel
from django.contrib.auth.models import User
from datetime import datetime
import uuid
from scuelo.models import (
    Classe , AnneeScolaire , Inscription ,UniformReservation
    ,Eleve
    )

class Cashier(TimeStampedModel):
    name = models.CharField(max_length=100, null=False)
    type = models.CharField(max_length=10, null=False)  # e.g., "SCO", "BF"
    note = models.TextField(blank=True, null=True)
    is_default = models.BooleanField(default=False)  # Indicates if this is the default cashier (C_SCO)

    def __str__(self):
        return self.name
    def balance(self, annee_scolaire=None):
        filters = {"cashier": self}
        if annee_scolaire:
            filters["annee_scolaire"] = annee_scolaire
        
        # Calculate total income and expenses
        total_income = Mouvement.objects.filter(causal__in=["INS", "SCO1", "SCO2", "SCO3"], **filters).aggregate(total=Sum('montant'))['total'] or 0
        total_expenses = Expense.objects.filter(**filters).aggregate(total=Sum('amount'))['total'] or 0
        
        # Calculate total transfers affecting this cashier
        total_transfers_out = Transfer.objects.filter(from_cashier=self).aggregate(total=Sum('amount'))['total'] or 0
        total_transfers_in = Transfer.objects.filter(to_cashier=self).aggregate(total=Sum('amount'))['total'] or 0
        
        # Calculate balance
        return total_income - total_expenses - total_transfers_out + total_transfers_in
   
    '''    def balance(self, annee_scolaire=None):
            filters = {"cashier": self}
            if annee_scolaire:
                filters["annee_scolaire"] = annee_scolaire
            total_income = Mouvement.objects.filter(causal__in=["INS", "SCO1", "SCO2", "SCO3"], **filters).aggregate(total=Sum('montant'))['total'] or 0
            total_expenses = Expense.objects.filter(**filters).aggregate(total=Sum('amount'))['total'] or 0
            return total_income - total_expenses
    '''
    '''    def transfer_to_bf(self, amount, to_cashier):
        """
        Transfer money from C_SCO to C_BF when balance exceeds forecasted expenses.
        """
        # Ensure transfer is only from SCO to BF
        if self.type == "SCO" and to_cashier.type == "BF":
            if self.balance() > amount:
                transfer = Transfer.objects.create(
                    amount=amount,
                    from_cashier=self,
                    to_cashier=to_cashier,
                    note="Transfer due to excess balance in C_SCO"
                )
                return transfer
            else:
                raise ValueError("Insufficient balance in C_SCO for transfer.")
        else:
            raise ValueError("Invalid cashier types for transfer.")
    
    def transfer_from_bf(self, amount, to_cashier):
        """
        Transfer money from C_BF to C_SCO when balance is low.
        """
        if self.type == "BF" and to_cashier.type == "SCO":
            forecasted_expenses = ExpenditureForecast.objects.filter(
                annee_scolaire=self.annee_scolaire, period__in=["Apr-Sep"]).aggregate(total=Sum('amount'))['total'] or 0
            if self.balance(annee_scolaire=self.annee_scolaire) < forecasted_expenses:
                transfer = Transfer.objects.create(
                    amount=amount,
                    from_cashier=self,
                    to_cashier=to_cashier,
                    note="Transfer from BF to SCO due to low balance"
                )
                return transfer
            else:
                raise ValueError("Balance in BF is sufficient for current period.")
        else:
            raise ValueError("Invalid cashier types for transfer.")'''
    @classmethod
    def get_default_cashier(cls):
        # Returns the default cashier (C_SCO)
        return cls.objects.filter(is_default=True).first()
    
class Tarif(TimeStampedModel):
    CAUSAL = (
        ("INS", "Inscription"),
        ("SCO1", "Scolarite 1"),
        ("SCO2", "Scolarite 2"),
        ("SCO3", "Scolarite 3"),
        ("TEN", "Tenue"),
        ("CAN", "Cantine"),
    )
    causal = models.CharField(max_length=5, choices=CAUSAL, db_index=True)
    montant = models.PositiveBigIntegerField()
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='tarifs', blank=True, null=True)
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE)  # Link to school year
    date_expiration = models.DateField("Date d'expiration or tranche dates")

    def __str__(self):
        return f"{self.causal} {self.montant:,} {self.classe} ({self.annee_scolaire})"
   
    @property
    def num_py_conf(self):
        return Eleve.objects.filter(
            inscriptions__classe=self,
            condition_eleve="CONF",
            cs_py="P"
        ).count() #Ensure it returns an integer, not a queryset


    @property
    def progressive_fee_1(self):
        """Returns the first installment (SCO1)."""
        sco1 = Tarif.objects.filter(classe=self.classe, annee_scolaire=self.annee_scolaire, causal='SCO1').first()
        return sco1.montant if sco1 else 0

    @property
    def progressive_fee_2(self):
        """Returns the cumulative fee for SCO1 + SCO2."""
        sco1 = Tarif.objects.filter(classe=self.classe, annee_scolaire=self.annee_scolaire, causal='SCO1').first()
        sco2 = Tarif.objects.filter(classe=self.classe, annee_scolaire=self.annee_scolaire, causal='SCO2').first()
        return (sco1.montant if sco1 else 0) + (sco2.montant if sco2 else 0)

    @property
    def progressive_fee_3(self):
        """Returns the cumulative fee for SCO1 + SCO2 + SCO3."""
        sco1 = Tarif.objects.filter(classe=self.classe, annee_scolaire=self.annee_scolaire, causal='SCO1').first()
        sco2 = Tarif.objects.filter(classe=self.classe, annee_scolaire=self.annee_scolaire, causal='SCO2').first()
        sco3 = Tarif.objects.filter(classe=self.classe, annee_scolaire=self.annee_scolaire, causal='SCO3').first()
        return (sco1.montant if sco1 else 0) + (sco2.montant if sco2 else 0) + (sco3.montant if sco3 else 0)
    
    @property
    def total_fee_1st(self):
        """Total amount for the 1st installment for 40 students"""
        sco1 = Tarif.objects.filter(classe=self.classe, annee_scolaire=self.annee_scolaire, causal='SCO1').first()
        return (sco1.montant if sco1 else 0) * self.num_py_conf  # num_py_conf should be an integer, not a queryset


    @property
    def total_fee_2nd(self):
        """Total amount for the 2nd installment for 40 students"""
        sco1 = Tarif.objects.filter(classe=self.classe, annee_scolaire=self.annee_scolaire, causal='SCO1').first()
        sco2 = Tarif.objects.filter(classe=self.classe, annee_scolaire=self.annee_scolaire, causal='SCO2').first()
        return ((sco1.montant if sco1 else 0) + (sco2.montant if sco2 else 0)) * self.num_py_conf

    @property
    def total_fee_3rd(self):
        """Total amount for the 3rd installment for 40 students"""
        sco1 = Tarif.objects.filter(classe=self.classe, annee_scolaire=self.annee_scolaire, causal='SCO1').first()
        sco2 = Tarif.objects.filter(classe=self.classe, annee_scolaire=self.annee_scolaire, causal='SCO2').first()
        sco3 = Tarif.objects.filter(classe=self.classe, annee_scolaire=self.annee_scolaire, causal='SCO3').first()
        return ((sco1.montant if sco1 else 0) + (sco2.montant if sco2 else 0) + (sco3.montant if sco3 else 0)) * self.num_py_conf
    
    '''
    :progressive par eleve par tranche 
    :PY & CONF 
    :progressive par classe par tranche PY & CONF 
    :nombre tenu PY 
    :nombre tenu CS & CONF
    :total frais aujordhui 
    
    
    some other computed fields should be added 
    for the late payment we will have :
    :sco_paid
    :sco_exigible
    :diff_sco
    :can_paid
    :can_exigible
    :diff_can
    :retard
    :percentage_paid
    
    
    
    
    '''
    
    #date format should be added for the dat expiration

    def __str__(self):
        return f"{self.causal} {self.montant:,} {self.classe}"
    
    
class Mouvement(TimeStampedModel):
  
    CAUSAL = (
        ("INS", "Inscription"),
        ("SCO1", "Scolarite 1"),
        ("SCO2", "Scolarite 2"),
        ("SCO3", "Scolarite 3"),
        ("TEN", "Tenue"),
        ("CAN", "Cantine"),
    )
  
    causal = models.CharField(max_length=5, choices=CAUSAL, db_index=True, null=True, blank=True)
    montant = models.PositiveBigIntegerField()
    date_paye = models.DateField(db_index=True, default=timezone.now)
    note = models.CharField(max_length=200, null=True, blank=True)
    inscription = models.ForeignKey(Inscription, on_delete=models.CASCADE, blank=True, null=True)
    tarif = models.ForeignKey(Tarif, on_delete=models.SET_NULL, null=True, blank=True)
    cashier = models.ForeignKey(Cashier, on_delete=models.CASCADE, null=True, blank=True)
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, null=True, blank=True)  # Add this field
    
    #mouvement is a student base payment registering model 
    # 
    def save(self, *args, **kwargs):
        # Automatically assign the default cashier (C_SCO) if not specified
        if not self.cashier:
            self.cashier = Cashier.get_default_cashier()
        
        # Automatically assign the current school year if not specified
        if not self.annee_scolaire:
            self.annee_scolaire = AnneeScolaire.objects.filter(actuel=True).first()
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.causal} {self.montant:,}"
     # New method for progressive amount
    def get_progressive_amount(self):
        """
        Calculate the cumulative income (progressive amount) up to this payment's date.
        """
        return Mouvement.objects.filter(
            date_paye__lte=self.date_paye  # Include all payments up to this date
        ).aggregate(total=Sum('montant'))['total'] or 0

    def __str__(self):
        return f"{self.causal} {self.montant:,}"

    @property
    def formatted_date_paye(self):
        return self.date_paye.strftime('%d/%m/%y')
    
    
class Expense(TimeStampedModel):
    legacy_id = models.CharField(max_length=36, unique=True ,default='')  # Store UUIDs here
    description = models.CharField(max_length=200, null=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    cashier = models.ForeignKey(Cashier, on_delete=models.CASCADE, null=True, blank=True)
    note = models.TextField(blank=True, null=True)
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, null=True, blank=True)  # Add this field

    def save(self, *args, **kwargs):
        # Automatically assign the default cashier (C_SCO) if not specified
        if not self.cashier:
            self.cashier = Cashier.get_default_cashier()
        
        # Automatically assign the current school year if not specified
        if not self.annee_scolaire:
            self.annee_scolaire = AnneeScolaire.objects.filter(actuel=True).first()
        
        super().save(*args, **kwargs)
    # date format should be managed automatically 
    def __str__(self):
        return f"{self.description} - {self.amount:,}"    
    
    @property
    def formatted_date(self):
        # Format the date as "DD/MM/YYYY"
        return self.date.strftime('%d/%m/%Y')
class Transfer(TimeStampedModel):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    from_cashier = models.ForeignKey(Cashier, on_delete=models.CASCADE, related_name="transfers_out")
    to_cashier = models.ForeignKey(Cashier, on_delete=models.CASCADE, related_name="transfers_in")
    note = models.TextField(blank=True, null=True)

    #date format should be fixed 
    
    def __str__(self):
        return f"Transfer of {self.amount:,} from {self.from_cashier} to {self.to_cashier}"    
    