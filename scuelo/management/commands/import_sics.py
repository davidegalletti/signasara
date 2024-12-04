import logging
from django.core.management.base import BaseCommand
from openpyexcel import load_workbook
from pathlib import Path
from scuelo.models import AnneeScolaire, Eleve, Inscription, Classe, Mouvement
from datetime import datetime

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("import_sics.log"),
        logging.StreamHandler()  # Logs to console
    ]
)

# Get logger instance
logger = logging.getLogger(__name__)

def parse_date(date_str):
    if isinstance(date_str, datetime):
        return date_str.date()
    
    if isinstance(date_str, str):
        # Remove non-breaking spaces and other unnecessary characters 
        date_str = date_str.strip().replace('\xa0', '')

        if not date_str:  # If the date string is empty after cleaning 
            return None

        try:
            # Try the standard YYYY-MM-DD format
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            try:
                # Try the DD/MM/YYYY format
                return datetime.strptime(date_str, '%d/%m/%Y').date()
            except ValueError:
                return None  # If both formats fail, return None
    return None

class Command(BaseCommand):
    help = '''Imports data from "Export SICS 2.1.75.xlsx" file.'''

    def handle(self, *args, **options):
        BASE_DIR = str(Path(__file__).resolve().parent.parent.parent)
        full_path = f'{BASE_DIR}/export_sics/Export SICS 2.1.75 V2.xlsx'
        
        logger.info(f'Starting import from {full_path}')
        
        try:
            wb = load_workbook(full_path)
        except FileNotFoundError:
            logger.error(f"File not found: {full_path}")
            return
        
        annee_scolaire_actuel = AnneeScolaire.objects.get(actuel=True)
        derniere_annee_scolaire = AnneeScolaire.objects.filter(actuel=False).order_by('-date_initiale').first()

        if not derniere_annee_scolaire:
            logger.error("No previous school year found.")
            return

        # Load worksheets
        ws_eleve = wb['Eleve']
        ws_paiement = wb['Paiement']

        # Process Eleve
        columns_eleve = {}
        for row in ws_eleve.iter_rows(min_row=1):
            row_values = [cell.value for cell in row]  # Extract values manually

            if len(columns_eleve.keys()) == 0:
                for column_index, column_name in enumerate(row_values):
                    columns_eleve[column_name] = column_index
            else:
                try:
                    classe_legacy_id = row_values[columns_eleve['__FK_Classe_ID']]
                    eleve_id = row_values[columns_eleve['_PK_Eleve_ID']]
                    
                    if Classe.objects.filter(legacy_id=classe_legacy_id).exists():
                        if not Eleve.objects.filter(legacy_id=eleve_id).exists():
                            new_e = Eleve()
                            new_e.legacy_id = eleve_id
                            new_e.date_enquete = parse_date(row_values[columns_eleve['D_enquete']])
                            new_e.nom = row_values[columns_eleve['Nom']]
                            new_e.prenom = row_values[columns_eleve['Prenom']]
                            new_e.condition_eleve = row_values[columns_eleve['Condition_eleve']]
                            new_e.sex = row_values[columns_eleve['Sex']]
                            new_e.date_naissance = parse_date(row_values[columns_eleve['Date-Naissance']])
                            new_e.cs_py = row_values[columns_eleve['CS_PY']]
                            new_e.hand = row_values[columns_eleve['Hand']]
                            new_e.annee_inscr = row_values[columns_eleve['A_inscr']]
                            new_e.parent = row_values[columns_eleve['Parent']]
                            new_e.tel_parent = row_values[columns_eleve['Tel_parent']]
                            new_e.save()

                            # Create inscription
                            inscription = Inscription()
                            inscription.eleve = new_e
                            inscription.annee_scolaire = derniere_annee_scolaire
                            inscription.classe = Classe.objects.get(legacy_id=classe_legacy_id)
                            inscription.save()
                            logger.info(f"Student {new_e.nom} {new_e.prenom} imported successfully.")
                        else:
                            logger.info(f"Eleve {eleve_id} already exists.")
                    else:
                        logger.error(f"Class with legacy_id {classe_legacy_id} not found for student {row_values[columns_eleve['Nom']]}.")
                except Exception as ex:
                    logger.error(f"Error importing student {row_values[columns_eleve['Nom']]}: {str(ex)}")

        # Process Paiement
        columns_paiement = {}
        for row in ws_paiement.iter_rows(min_row=1):
            row_values = [cell.value for cell in row]  # Extract values manually

            if len(columns_paiement.keys()) == 0:
                for column_index, column_name in enumerate(row_values):
                    columns_paiement[column_name] = column_index
            else:
                try:
                    eleve_legacy_id = row_values[columns_paiement['__FK_Eleve']]
                    try:
                        eleve = Eleve.objects.get(legacy_id=eleve_legacy_id)
                        inscription = Inscription.objects.get(annee_scolaire=derniere_annee_scolaire, eleve=eleve)

                        new_p = Mouvement()
                        new_p.legacy_id = row_values[columns_paiement['_PK_Paiement_ID']]
                        new_p.causal = row_values[columns_paiement['Causal_Paiement']]
                        new_p.montant = row_values[columns_paiement['Montant']]
                        parsed_date = parse_date(row_values[columns_paiement['Date_paiement']])

                        if parsed_date is None:
                            logger.error(f"Invalid date format for Eleve ID {eleve_legacy_id}: '{row_values[columns_paiement['Date_paiement']]}'")
                            continue  # Skip this payment if date is invalid
                        
                        new_p.date_paye = parsed_date
                        new_p.note = row_values[columns_paiement['Note_Paiement']]
                        new_p.inscription = inscription
                        new_p.save()
                        logger.info(f"Payment for {eleve.nom} {eleve.prenom} imported successfully.")
                    except Eleve.DoesNotExist:
                        logger.error(f"Eleve with ID {eleve_legacy_id} does not exist.")
                    except Inscription.DoesNotExist:
                        logger.error(f"Inscription for Eleve ID {eleve_legacy_id} in {derniere_annee_scolaire.nom} not found.")
                except Exception as ex:
                    logger.error(f"Error importing payment for Eleve ID {row_values[columns_paiement['__FK_Eleve']]}: {str(ex)}")

        logger.info('Import SICS END')
