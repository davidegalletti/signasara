import logging
from django.core.management.base import BaseCommand
from django.db.models import Count # Import models!
from scuelo.models import Eleve, Inscription
from cash.models import Mouvement

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("remove_duplicate_sics.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Removes duplicate Eleve and Mouvement entries based on legacy_id."

    def handle(self, *args, **options):
        self.remove_duplicate_eleves()
        self.remove_duplicate_mouvements()
        logger.info("Duplicate removal process completed.")

    def remove_duplicate_eleves(self):
        """Removes duplicate Eleve entries based on legacy_id."""
        logger.info("Starting duplicate Eleve removal...")

        duplicate_legacy_ids = (
            Eleve.objects.values('legacy_id')
            .annotate(count=Count('legacy_id'))
            .filter(count__gt=1)
            .values_list('legacy_id', flat=True)
        )

        for legacy_id in duplicate_legacy_ids:
            duplicates = Eleve.objects.filter(legacy_id=legacy_id).order_by('pk')

            if duplicates.count() > 1:
                first_eleve = duplicates.first()
                for duplicate in duplicates[1:]:
                    logger.info(f"Removing duplicate Eleve: legacy_id={duplicate.legacy_id}, pk={duplicate.pk}, name={duplicate.nom}, prenom={duplicate.prenom}")

                    inscriptions = Inscription.objects.filter(eleve=duplicate)
                    if inscriptions.exists():
                        logger.info(f"Re-associating {inscriptions.count()} Inscriptions from Eleve pk={duplicate.pk} to Eleve pk={first_eleve.pk}")
                        inscriptions.update(eleve=first_eleve)

                    duplicate.delete()
                logger.info(f"Removed {duplicates.count() - 1} duplicate Eleve records with legacy_id={legacy_id}")
        logger.info("Duplicate Eleve removal completed.")

    def remove_duplicate_mouvements(self):
        """Removes duplicate Mouvement entries based on legacy_id."""
        logger.info("Starting duplicate Mouvement removal...")

        duplicate_legacy_ids = (
            Mouvement.objects.values('legacy_id')  # Changed 'legacy_id' to 'sics_id'
            .annotate(count=Count('legacy_id'))    # Changed 'legacy_id' to 'sics_id'
            .filter(count__gt=1)
            .values_list('legacy_id', flat=True)   # Changed 'legacy_id' to 'sics_id'
        )

        for legacy_id in duplicate_legacy_ids:
            duplicates = Mouvement.objects.filter(sics_id=legacy_id).order_by('pk') # Changed 'legacy_id' to 'sics_id'

            if duplicates.count() > 1:
                first_mouvement = duplicates.first()
                for duplicate in duplicates[1:]:
                    logger.info(f"Removing duplicate Mouvement: legacy_id={duplicate.legacy_id}, pk={duplicate.pk}, causal={duplicate.causal}, montant={duplicate.montant}") # Changed 'legacy_id' to 'sics_id'
                    duplicate.delete()
                logger.info(f"Removed {duplicates.count() - 1} duplicate Mouvement records with legacy_id={legacy_id}")
        logger.info("Duplicate Mouvement removal completed.")
