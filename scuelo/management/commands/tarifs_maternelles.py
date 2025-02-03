from django.core.management.base import BaseCommand
from scuelo.models import Classe, AnneeScolaire, TypeClasse
from django.utils import timezone
from cash.models import Tarif

class Command(BaseCommand):
    help = 'Upload tarifs for Maternelle'

    def handle(self, *args, **options):
        # Retrieve or create the current academic year
        annee_scolaire = AnneeScolaire.objects.get(actuel=True)

        # Define the tariff details for each class in Maternelle using abbreviations PS, MS, GS
        tarifs_data = [
            {
                "section": "PS",  # Petite Section
                "inscription": 500,
                "sco1": {"montant": 10000, "date_expiration": "2023-09-23"},
                "sco2": {"montant": 8000, "date_expiration": "2023-11-30"},
                "sco3": {"montant": 7000, "date_expiration": "2024-01-31"},
                "canteen": {"montant": 4000, "date_expiration": "2023-10-01"},
            },
            {
                "section": "MS",  # Moyenne Section
                "inscription": 500,
                "sco1": {"montant": 10000, "date_expiration": "2023-09-23"},
                "sco2": {"montant": 8000, "date_expiration": "2023-11-30"},
                "sco3": {"montant": 7000, "date_expiration": "2024-01-31"},
                "canteen": {"montant": 4000, "date_expiration": "2023-10-01"},
            },
            {
                "section": "GS",  # Grande Section
                "inscription": 500,
                "sco1": {"montant": 10000, "date_expiration": "2023-09-23"},
                "sco2": {"montant": 8000, "date_expiration": "2023-11-30"},
                "sco3": {"montant": 7000, "date_expiration": "2024-01-31"},
                "canteen": {"montant": 4000, "date_expiration": "2023-10-01"},
            }
        ]

        for tarif_data in tarifs_data:
            class_name = tarif_data["section"]

            # Find the class by abbreviation (PS, MS, GS)
            try:
                classe = Classe.objects.get(nom=class_name)
                # Create or update tariffs for each class
                self.create_or_update_tarif(classe, annee_scolaire, 'INS', tarif_data['inscription'], None)
                self.create_or_update_tarif(classe, annee_scolaire, 'SCO1', tarif_data['sco1']['montant'], tarif_data['sco1']['date_expiration'])
                self.create_or_update_tarif(classe, annee_scolaire, 'SCO2', tarif_data['sco2']['montant'], tarif_data['sco2']['date_expiration'])
                self.create_or_update_tarif(classe, annee_scolaire, 'SCO3', tarif_data['sco3']['montant'], tarif_data['sco3']['date_expiration'])
                self.create_or_update_tarif(classe, annee_scolaire, 'CAN', tarif_data['canteen']['montant'], tarif_data['canteen']['date_expiration'])

                self.stdout.write(self.style.SUCCESS(f'Tariffs uploaded for {class_name}'))
            except Classe.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Class {class_name} does not exist'))

    def create_or_update_tarif(self, classe, annee_scolaire, causal, montant, date_expiration):
        Tarif.objects.update_or_create(
            classe=classe,
            annee_scolaire=annee_scolaire,
            causal=causal,
            defaults={
                'montant': montant,
                'date_expiration': date_expiration or timezone.now().date(),
            }
        )
