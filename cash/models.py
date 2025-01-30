from django.db import models
from django.utils import timezone
from django.db.models import Q, Sum
from model_utils.models import TimeStampedModel
from django.contrib.auth.models import User
from datetime import datetime
from scuelo.models import (Classe , AnneeScolaire , Inscription)
# Create your models here.

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
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE)
    date_expiration = models.DateField("Date d'expiration or tranche dates")

    def __str__(self):
        return f"{self.causal} {self.montant:,} {self.classe}"
    
    
class Mouvement(TimeStampedModel):
    TYPE = (
        ("R", "Revenus"),
        ("D", "Dépenses"),
    )
    CAUSAL = (
         ("INS", "Inscription"),
         ("SCO1", "Scolarite 1"),
        ("SCO2", "Scolarite 2"),
        ("SCO3", "Scolarite 3"),
        ("TEN", "Tenue"),
        ("CAN", "Cantine"),
    )
    type = models.CharField(max_length=1, choices=TYPE, db_index=True)
    causal = models.CharField(max_length=5, choices=CAUSAL, db_index=True, null=True, blank=True)
    montant = models.PositiveBigIntegerField()
    date_paye = models.DateField(db_index=True, default="")
    note = models.CharField(max_length=200, null=True, blank=True)
    inscription = models.ForeignKey(Inscription, on_delete=models.CASCADE, blank=True, null=True)
    legacy_id = models.CharField(max_length=100, blank=True, null=True, db_index=True, unique=True)
    tarif = models.ForeignKey(Tarif, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = 'Mouvement'
        verbose_name_plural = 'Mouvements'
        ordering = ["-date_paye"]

    def __str__(self):
        return f"{self.causal} {self.montant:,}"

    @property
    def formatted_date_paye(self):
        return self.date_paye.strftime('%d/%m/%y')