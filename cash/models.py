from django.db import models
from django.utils import timezone
from django.db.models import Q, Sum
from model_utils.models import TimeStampedModel
from django.contrib.auth.models import User
from datetime import datetime

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
        """
        Dynamically calculates the balance based on Mouvement (income) and Expense (outflows).
        Optionally filters by school year.
        """
        filters = {"cashier": self}
        if annee_scolaire:
            filters["annee_scolaire"] = annee_scolaire
        # income or expense type should be removed 
        # the incomes and the outcomes should be determined 
        # automatically based onto the transaction made 
        total_income = Mouvement.objects.filter(type="R", **filters).aggregate(total=Sum('montant'))['total'] or 0
        total_expenses = Expense.objects.filter(**filters).aggregate(total=Sum('amount'))['total'] or 0
        return total_income - total_expenses

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
    def progressive_payments_py(self):
        """
        Returns a dictionary of progressive payments for PY students.
        Key: Deadline date
        Value: Amount to be paid by each PY student at that deadline.
        """
        payments = {}
        if self.causal in ["INS", "SCO1", "SCO2", "SCO3"]:
            payments[self.date_expiration] = self.montant
        return payments

    @property
    def num_py_conf(self):
        """
        Returns the number of PY students who have confirmed their enrollment (CONF status).
        """
        return Eleve.objects.filter(
            inscription__classe=self.classe,
            condition_eleve="CONF",
            cs_py="P"
        ).count()

    @property
    def num_cs_conf(self):
        """
        Returns the number of CS students who have confirmed their enrollment (CONF status).
        """
        return Eleve.objects.filter(
            inscription__classe=self.classe,
            condition_eleve="CONF",
            cs_py="C"
        ).count()

    @property
    def expected_collection(self):
        """
        Returns the total amount the school expects to collect for the class at various deadlines.
        """
        return self.montant * self.num_py_conf

    @property
    def tenues_ordered_py(self):
        """
        Returns the number of uniforms ordered by PY students.
        """
        return UniformReservation.objects.filter(
            student__inscription__classe=self.classe,
            student__cs_py="P"
        ).count()

    @property
    def tenues_ordered_cs(self):
        """
        Returns the number of uniforms ordered by CS students.
        """
        return UniformReservation.objects.filter(
            student__inscription__classe=self.classe,
            student__cs_py="C"
        ).count()

    @property
    def expected_total_class(self):
        """
        Returns the total amount expected for the entire class (PY + CS students).
        """
        return self.montant * (self.num_py_conf + self.num_cs_conf)

    @property
    def actual_total_received(self):
        """
        Returns the total amount actually received for the entire class (PY + CS students).
        """
        total_received = Mouvement.objects.filter(
            tarif=self,
            type="R"  # Income
        ).aggregate(total=Sum('montant'))['total'] or 0
        return total_received

    @property
    def expected_total_tenues_py(self):
        """
        Returns the total amount expected from PY students for uniforms.
        """
        uniform_cost = 2000  # Example cost per uniform
        return uniform_cost * self.tenues_ordered_py

    @property
    def actual_total_received_tenues_py(self):
        """
        Returns the total amount actually received from PY students for uniforms.
        """
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
    
    
class Mouvement(TimeStampedModel):
    '''    TYPE = (
        ("R", "Revenus"),  # Income
        ("D", "Dépenses"),  # Expense
    )'''
    CAUSAL = (
        ("INS", "Inscription"),
        ("SCO1", "Scolarite 1"),
        ("SCO2", "Scolarite 2"),
        ("SCO3", "Scolarite 3"),
        ("TEN", "Tenue"),
        ("CAN", "Cantine"),
    )
    #type = models.CharField(max_length=1, choices=TYPE, db_index=True)
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
    
    
class Expense(TimeStampedModel):
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
    
    
class Transfer(TimeStampedModel):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    from_cashier = models.ForeignKey(Cashier, on_delete=models.CASCADE, related_name="transfers_out")
    to_cashier = models.ForeignKey(Cashier, on_delete=models.CASCADE, related_name="transfers_in")
    note = models.TextField(blank=True, null=True)

    #date format should be fixed 
    
    def __str__(self):
        return f"Transfer of {self.amount:,} from {self.from_cashier} to {self.to_cashier}"    
    