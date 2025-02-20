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

class Cashier(models.Model):
    name = models.CharField(max_length=100, null=False)
    type = models.CharField(max_length=10, null=False)  # e.g., "SCO", "BF"
    note = models.TextField(blank=True, null=True)
    is_default = models.BooleanField(default=False)  # Indicates if this is the default cashier (C_SCO)

    def __str__(self):
        return self.name

    def balance(self, annee_scolaire=None):
        """Calculates the balance for the cashier, optionally filtered by school year."""
        # IMPORTANT:  Use *relative* imports to avoid circular dependencies.
        from .models import Mouvement, Expense, Transfer  # Relative imports

        filters = {"cashier": self}
        if annee_scolaire:
            filters["annee_scolaire"] = annee_scolaire

        # Calculate total income (ignoring causal)
        total_income = Mouvement.objects.filter(causal__in = ['SCO'] ,**filters).aggregate(total=Sum('montant'))['total'] or 0

        # Calculate total expenses
        total_expenses = Expense.objects.filter(**filters).aggregate(total=Sum('amount'))['total'] or 0

        # Calculate total transfers affecting this cashier
        total_transfers_out = Transfer.objects.filter(from_cashier=self).aggregate(total=Sum('amount'))['total'] or 0
        total_transfers_in = Transfer.objects.filter(to_cashier=self).aggregate(total=Sum('amount'))['total'] or 0

        # Calculate balance: Income - Expenses + Transfers In - Transfers Out
        return total_income - total_expenses #+ total_transfers_in - total_transfers_out

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
   
    
    #date format should be added for the dat expiration

    def __str__(self):
        return f"{self.causal} {self.montant:,} {self.classe}"
    
    
class Mouvement(TimeStampedModel):
  
    CAUSAL = (
        ("INS", "Inscription"),
     ("SCO", "SCO"),
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
    