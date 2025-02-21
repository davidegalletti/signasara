from django.db import models
from django.utils import timezone
from django.db.models import Q, Sum
from model_utils.models import TimeStampedModel
from django.contrib.auth.models import User
from datetime import datetime

CONDITION_ELEVE = (
    ("CONF", "CONF"),
    ("ABAN", "ABAN"),
    ("PROP", "PROP"),
    ("TBD", "TBD"),
)

HAND = (
    ("DA", "DA"),
    ("DM", "DM"),
    ("DL", "DL"),
    ("DV", "DV"),
     ("DP", "DP"),
      ("TL", "TL"),
)
 
CS_PY = (
    ("C", "CS"),
    ("E", "EXTRA"),
    ("P", "PY"),
    ("A", "ACC"),
    ("B", "BRAVO"),
) 

SEX = (
    ("F", "F"),
    ("M", "M"),
)

TYPE_ECOLE = (
    ("M", "MATERNELLE"),
    ("P", "PRIMAIRE"),
    ("S", "SECONDAIRE"),
    ("L", "LYCEE"),
)

class TypeClasse(TimeStampedModel):
    nom = models.CharField(max_length=100, null=False)
    ordre = models.IntegerField(default=0)
    type_ecole = models.CharField(max_length=1, choices=TYPE_ECOLE, db_index=True)

    def __str__(self):
        return self.nom

class Ecole(TimeStampedModel):
    nom = models.CharField(max_length=100, null=False)
    ville = models.CharField(max_length=100, null=False)
    nom_du_referent = models.CharField(max_length=100, null=False)
    prenom_du_referent = models.CharField(max_length=100, null=False)
    email_du_referent = models.CharField(max_length=100, null=False)
    telephone_du_referent = models.CharField(max_length=100, null=False)
    note = models.TextField()
    externe = models.BooleanField(default=True)

    def __str__(self):
        return self.nom

class Classe(TimeStampedModel):
    ecole = models.ForeignKey(Ecole, on_delete=models.CASCADE)
    type = models.ForeignKey(TypeClasse, on_delete=models.CASCADE)
    nom = models.CharField(max_length=10, null=False)
    legacy_id = models.CharField(max_length=100, blank=True, null=True, db_index=True, unique=True)

    def __str__(self):
        return '%s %s' % (self.nom, self.type.get_type_ecole_display())

    @property
    def num_py_conf(self):
        return Eleve.objects.filter(
            inscriptions__classe=self,
            condition_eleve="CONF",
            cs_py="P"
        ).count()
    def get_latest_tariffs(self):
        return self.tarifs.order_by('-version').distinct('causal')

    def get_progressive_by_student(self):
        return self.tarifs.filter(causal__in=["SCO1", "SCO2", "SCO3"]).aggregate(total=Sum('montant'))['total'] or 0

    def get_progressive_by_class(self):
        confirmed_students = Eleve.objects.filter(
            inscription__classe=self,
            condition_eleve="CONF",
            cs_py="P"
        )
        return confirmed_students.count()

    def get_expected_payment(self):
        confirmed_students = Eleve.objects.filter(
            inscription__classe=self,
            condition_eleve="CONF",
            cs_py="P"
        )
        total_tarif = self.tarifs.filter(causal__in=["SCO1", "SCO2", "SCO3"]).aggregate(total=Sum('montant'))['total'] or 0
        return confirmed_students.count() * total_tarif

    def confirmed_py_count(self):
        return Eleve.objects.filter(
            inscription__classe=self,
            condition_eleve="CONF",
            cs_py="P"
        ).count()

    @property
    def sco_exigible(self):
        total_tarifs = Tarif.objects.filter(classe=self).aggregate(total=Sum('montant'))['total'] or 0
        return "{:,}".format(total_tarifs)

class Eleve(TimeStampedModel):
    nom = models.CharField(max_length=34, null=False)
    prenom = models.CharField(max_length=34, null=False)
    date_enquete = models.DateField(null=True, blank=True)
    condition_eleve = models.CharField(
        max_length=4,
        choices=CONDITION_ELEVE
    )
    sex = models.CharField(max_length=1, choices=SEX)
    date_naissance = models.DateField(blank=True, null=True)
    cs_py = models.CharField(max_length=7, choices=CS_PY, default="C")
    hand = models.CharField(max_length=2, choices=HAND, null=True, blank=True)
    annee_inscr = models.SmallIntegerField(blank=True, null=True)
    parent = models.CharField(max_length=100, blank=True, null=True)
    tel_parent = models.CharField(max_length=100, blank=True, null=True)
    note_eleve = models.TextField(blank=True, null=True, default='-')
    legacy_id = models.CharField(max_length=100, blank=True, null=True, db_index=True, unique=True)

    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.legacy_id})"
    @property
    def formatted_date_enquete(self):
        return self.date_enquete.strftime('%d/%m/%y') if self.date_enquete else None

    @property
    def formatted_date_naissance(self):
        return self.date_naissance.strftime('%d/%m/%y') if self.date_naissance else None

    @property
    def an_insc(self):
        return self.annee_inscr.year

    @property
    def current_class(self):
        current_year = AnneeScolaire.objects.get(actuel=True)
        try:
            inscription = Inscription.objects.filter(eleve=self, annee_scolaire=current_year).latest('date_inscription')
            return inscription.classe
        except Inscription.DoesNotExist:
            return None

    def get_queryset(self, request):
        queryset = Eleve.objects.all().prefetch_related('nom_classe')
        grouped_queryset = {}
        for eleve in queryset:
            classe = eleve.nom_classe.pk
            if classe not in grouped_queryset:
                grouped_queryset[classe] = []
            grouped_queryset[classe].append(eleve)
        return grouped_queryset

    def tenu_count(self):
        return self.paiement_set.filter(
            Q(causal='TEN') &
            (
                    Q(montant=4000) | Q(montant=4500) | Q(montant=2250) | Q(montant=2000)
            )
        ).count()

    class Meta:
        verbose_name = 'Eleve'
        verbose_name_plural = 'Eleves'

class AnneeScolaire(TimeStampedModel):
    nom = models.CharField(max_length=100)
    nom_bref = models.CharField(max_length=10, default='')
    date_initiale = models.DateField(blank=True, null=True)
    date_finale = models.DateField(blank=True, null=True)
    actuel = models.BooleanField(default=False)

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.actuel:
            AnneeScolaire.objects.filter(actuel=True).exclude(pk=self.pk).update(actuel=False)
    @classmethod
    def get_current_year(cls):
        return cls.objects.filter(actuel=True).first()  # Adjust based         

class Inscription(TimeStampedModel):
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE , related_name='inscriptions')
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, blank=True, null=True)
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE)
    date_inscription = models.DateTimeField(default=timezone.now)
    nombre_uniformes = models.IntegerField(default=0)

    def __str__(self):
        return '%s - %s - %s' % (self.annee_scolaire.nom_bref, self.classe, self.eleve)
    @property
    def formatted_date_inscription(self):
        return self.date_inscription.strftime('%d/%m/%y')
    def save(self, *args, **kwargs):
        if self.annee_scolaire.actuel:
            Inscription.objects.filter(eleve=self.eleve, annee_scolaire__actuel=True).exclude(pk=self.pk).delete()
        super().save(*args, **kwargs)

class UniformReservation(TimeStampedModel):
    STATUS_CHOICES = [
        ('reserved', 'Reserved'),
        ('delivered', 'Delivered'),
        ('paid', 'Paid')
    ]

    student = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name="uniform_reservations")
    student_type = models.CharField(max_length=2, choices=CS_PY, editable=False)
    quantity = models.PositiveIntegerField(default=2)
    cost_per_uniform = models.DecimalField(max_digits=10, decimal_places=2, help_text="Cost of each uniform")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='reserved')
    date_reserved = models.DateField(default=timezone.now)
    school_year = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, related_name="uniform_reservations")

    @property
    def total_cost(self):
        return "{:,}".format(self.quantity * self.cost_per_uniform)

    def save(self, *args, **kwargs):
        if self.student:
            self.student_type = self.student.cs_py

        if not self.school_year:
            current_school_year = AnneeScolaire.objects.filter(actuel=True).first()
            if not current_school_year:
                raise Exception("No current school year is defined.")
            self.school_year = current_school_year

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Reservation for {self.student} - {self.quantity} uniforms"


class StudentLog(TimeStampedModel):
    student = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name='logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(default=timezone.now)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Log for {self.student.nom} by {self.user.username if self.user else 'System'}"

    @property
    def formatted_timestamp(self):
        return self.timestamp.strftime('%d/%m/%y')