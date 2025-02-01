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
        filters = {"cashier": self}
        if annee_scolaire:
            filters["annee_scolaire"] = annee_scolaire
        total_income = Mouvement.objects.filter(causal__in=["INS", "SCO1", "SCO2", "SCO3"], **filters).aggregate(total=Sum('montant'))['total'] or 0
        total_expenses = Expense.objects.filter(**filters).aggregate(total=Sum('amount'))['total'] or 0
        return total_income - total_expenses

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
    
class Tarif(models.Model):
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
    def progressive_payments_py(self):
        payments = {}
        if self.causal in ["INS", "SCO1", "SCO2", "SCO3"]:
            payments[self.date_expiration] = self.montant
        return payments

    @property
    def num_py_conf(self):
        return Eleve.objects.filter(
            inscription__classe=self.classe,
            condition_eleve="CONF",
            cs_py="P"
        ).count()

    @property
    def num_cs_conf(self):
        return Eleve.objects.filter(
            inscription__classe=self.classe,
            condition_eleve="CONF",
            cs_py="C"
        ).count()

    @property
    def expected_collection(self):
        return self.montant * self.num_py_conf

    @property
    def tenues_ordered_py(self):
        return UniformReservation.objects.filter(
            student__inscription__classe=self.classe,
            student__cs_py="P"
        ).count()

    @property
    def tenues_ordered_cs(self):
        return UniformReservation.objects.filter(
            student__inscription__classe=self.classe,
            student__cs_py="C"
        ).count()

    @property
    def expected_total_class(self):
        return self.montant * (self.num_py_conf + self.num_cs_conf)

    @property
    def actual_total_received(self):
        total_received = Mouvement.objects.filter(
            tarif=self,
            type="R"  # Income
        ).aggregate(total=Sum('montant'))['total'] or 0
        return total_received

    @property
    def expected_total_tenues_py(self):
        uniform_cost = 2000  # Example cost per uniform
        return uniform_cost * self.tenues_ordered_py

    @property
    def actual_total_received_tenues_py(self):
        total_received = Mouvement.objects.filter(
            tarif=self,
            type="R",  # Income
            causal="TEN",  # Uniform fee
            inscription__eleve__cs_py="P"  # Only PY students
        ).aggregate(total=Sum('montant'))['total'] or 0
        return total_received   
    
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
    
    
class Mouvement(models.Model):
  
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

    @property
    def formatted_date_paye(self):
        return self.date_paye.strftime('%d/%m/%y')
    
    
class Expense(models.Model):
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
    
    
class Transfer(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    from_cashier = models.ForeignKey(Cashier, on_delete=models.CASCADE, related_name="transfers_out")
    to_cashier = models.ForeignKey(Cashier, on_delete=models.CASCADE, related_name="transfers_in")
    note = models.TextField(blank=True, null=True)

    #date format should be fixed 
    
    def __str__(self):
        return f"Transfer of {self.amount:,} from {self.from_cashier} to {self.to_cashier}"    
    