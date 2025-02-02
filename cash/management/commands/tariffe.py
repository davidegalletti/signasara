from django.core.management.base import BaseCommand
from scuelo.models import Classe,  AnneeScolaire
from django.utils import timezone
from cash.models import Tarif
from datetime import datetime

class Command(BaseCommand):
    help = "Upload tariffs into classes for the 2023-2024 school year."

    def handle(self, *args, **options):
        # Get the current school year
        try:
            annee_scolaire = AnneeScolaire.objects.get(nom='Année scolaire 2023-24')
        except AnneeScolaire.DoesNotExist:
            self.stdout.write(self.style.ERROR("Année scolaire 2023-24 not found."))
            return

        # Define school fees
        primary_tariffs = {
            'CP1': {'scolarite_1': 15000, 'scolarite_2': 7500, 'scolarite_3': 7500},
            'CP2': {'scolarite_1': 15000, 'scolarite_2': 7500, 'scolarite_3': 7500},
            'CE1': {'scolarite_1': 15000, 'scolarite_2': 7500, 'scolarite_3': 7500},
            'CE2': {'scolarite_1': 15000, 'scolarite_2': 7500, 'scolarite_3': 7500},
            'CM1': {'scolarite_1': 17500, 'scolarite_2': 7500, 'scolarite_3': 7500},
            'CM2': {'scolarite_1': 17500, 'scolarite_2': 7500, 'scolarite_3': 7500},
        }
        
        bisongo_tariff = {'scolarite_1': 10000, 'scolarite_2': 8000, 'scolarite_3': 7000}
        
        # Payment deadlines
        expiration_dates = {
            'SCO1': datetime(2023, 11, 30),
            'SCO2': datetime(2024, 1, 31),
            'SCO3': datetime(2024, 2, 28)
        }
        
        # Process primary school classes
        for class_name, tarifs in primary_tariffs.items():
            self.create_class_tariffs(class_name, tarifs, annee_scolaire, expiration_dates)
        
        # Process BISONGO class
        self.create_class_tariffs('BISONGO', bisongo_tariff, annee_scolaire, expiration_dates, bisongo=True)
    
    def create_class_tariffs(self, class_name, tarifs, annee_scolaire, expiration_dates, bisongo=False):
        """Helper function to create tariffs for a given class."""
        try:
            classe = Classe.objects.filter(nom=class_name).first()
            if not classe:
                self.stdout.write(self.style.ERROR(f'Class {class_name} not found'))
                return
            
            # Create tariffs
            self.create_tarif(classe, 'INS', 500, annee_scolaire, None)
            self.create_tarif(classe, 'SCO1', tarifs['scolarite_1'], annee_scolaire, expiration_dates['SCO1'])
            self.create_tarif(classe, 'SCO2', tarifs['scolarite_2'], annee_scolaire, expiration_dates['SCO2'])
            self.create_tarif(classe, 'SCO3', tarifs['scolarite_3'], annee_scolaire, expiration_dates['SCO3'])
            
            if bisongo:
                self.create_tarif(classe, 'CANTINE', 4000, annee_scolaire, None)
                self.create_tarif(classe, 'TENUE', 4000, annee_scolaire, None)
            else:
                self.create_tarif(classe, 'TENUE', 4500, annee_scolaire, None)
            
            self.stdout.write(self.style.SUCCESS(f'Tariffs uploaded for {class_name}'))
        
        except Classe.MultipleObjectsReturned:
            self.stdout.write(self.style.ERROR(f'Multiple classes found with the name {class_name}, please refine the query'))
    
    def create_tarif(self, classe, causal, montant, annee_scolaire, expiration_date):
        """Helper function to create a Tarif entry."""
        Tarif.objects.get_or_create(
            classe=classe,
            annee_scolaire=annee_scolaire,
            causal=causal,
            defaults={
                'montant': montant,
                'date_expiration': expiration_date or timezone.now() + timezone.timedelta(days=90)
            }
        )
