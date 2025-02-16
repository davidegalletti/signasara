from django.core.management.base import BaseCommand
from scuelo.models import Classe, AnneeScolaire
from django.utils import timezone
from cash.models import Tarif
from datetime import datetime

class Command(BaseCommand):
    help = "Upload tariffs into classes for the 2024-2025 school year."

    def handle(self, *args, **options):
        # Get the current school year
        try:
            annee_scolaire = AnneeScolaire.objects.get(nom='Année scolaire 2024-25')
        except AnneeScolaire.DoesNotExist:
            self.stdout.write(self.style.ERROR("Année scolaire 2024-25 not found."))
            return

        # Define school fees
        tariffs_data = {
            'CP1-Nas_Pri': {'SCO1': 15000, 'SCO2': 7500, 'SCO3': 7500, 'TEN': 4500},
            'CP2-Nas_Pri': {'SCO1': 15000, 'SCO2': 7500, 'SCO3': 7500, 'TEN': 4500},
            'CE1-Nas_Pri': {'SCO1': 15000, 'SCO2': 7500, 'SCO3': 7500, 'TEN': 4500},
            'CE2-Nas_Pri': {'SCO1': 15000, 'SCO2': 7500, 'SCO3': 7500, 'TEN': 4500},
            'CM1-Nas_Pri': {'SCO1': 17500, 'SCO2': 7500, 'SCO3': 7500, 'TEN': 4500},
            'CM2-Nas_Pri': {'SCO1': 17500, 'SCO2': 7500, 'SCO3': 7500, 'TEN': 4500},
            'PS-Nas_Mat': {'SCO1': 10000, 'SCO2': 8000, 'SCO3': 7000, 'TEN': 4500, 'CAN': 4000},
            'MS-Nas_Mat': {'SCO1': 10000, 'SCO2': 8000, 'SCO3': 7000, 'TEN': 4500, 'CAN': 4000},
            'GS-Nas_Mat': {'SCO1': 10000, 'SCO2': 8000, 'SCO3': 7000, 'TEN': 4500, 'CAN': 4000},
        }

        # Payment deadlines
        expiration_dates = {
            'SCO1': datetime(2024, 11, 30),
            'SCO2': datetime(2025, 1, 31),
            'SCO3': datetime(2025, 2, 28)
        }

        # Process each class and create tariffs
        for class_name, tariffs in tariffs_data.items():
            try:
                classe = Classe.objects.get(nom=class_name)
                self.create_class_tariffs(classe, tariffs, annee_scolaire, expiration_dates)
                self.stdout.write(self.style.SUCCESS(f'Tariffs uploaded for {class_name}'))

            except Classe.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Class {class_name} not found'))
            except Classe.MultipleObjectsReturned:
                self.stdout.write(self.style.ERROR(f'Multiple classes found with the name {class_name}, please refine the query'))

    def create_class_tariffs(self, classe, tariffs, annee_scolaire, expiration_dates):
        """Helper function to create tariffs for a given class."""

        # Create INS tariff
        Tarif.objects.get_or_create(
            classe=classe,
            annee_scolaire=annee_scolaire,
            causal='INS',
            defaults={
                'montant': 500,
                'date_expiration': timezone.now() + timezone.timedelta(days=90)
            }
        )

        # Create other tariffs
        for causal, montant in tariffs.items():
            if causal != 'TEN' and causal != 'CAN':
                Tarif.objects.get_or_create(
                    classe=classe,
                    annee_scolaire=annee_scolaire,
                    causal=causal,
                    defaults={
                        'montant': montant,
                        'date_expiration': expiration_dates.get(causal, timezone.now() + timezone.timedelta(days=90)).date()
                    }
                )
            else:
                 Tarif.objects.get_or_create(
                    classe=classe,
                    annee_scolaire=annee_scolaire,
                    causal=causal,
                    defaults={
                        'montant': montant,
                        'date_expiration':  (timezone.now() + timezone.timedelta(days=90)).date()
                    }
                )
