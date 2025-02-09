# cash/management/commands/create_cashiers_and_transfers.py
from django.core.management.base import BaseCommand
from cash.models import Cashier, Transfer
import random

class Command(BaseCommand):
    help = 'Creates C_BF cashier (if it does not exist) and makes 10 transfers'

    def handle(self, *args, **options):
        # 1. Get or Create C_BF Cashier
        c_bf, created_bf = Cashier.objects.get_or_create(
            name='C_BF',
            type='BF'
        )
        if created_bf:
            self.stdout.write(self.style.SUCCESS('Successfully created C_BF cashier'))
        else:
            self.stdout.write(self.style.WARNING('C_BF cashier already exists'))

        # 2. Get C_SCO Cashier (Assume it exists)
        try:
            c_sco = Cashier.objects.get(name='C_SCO')
        except Cashier.DoesNotExist:
            self.stdout.write(self.style.ERROR('C_SCO cashier does not exist. Please create it manually or adjust the command.'))
            return  # Stop the command if C_SCO doesn't exist

        # 3. Make 10 Transfers
        for i in range(10):
            amount = random.randint(1, 499999)  # Amount between 1 and 499,999

            # Randomly choose from_cashier and to_cashier (C_SCO or C_BF)
            from_cashier = random.choice([c_sco, c_bf])
            to_cashier = c_sco if from_cashier == c_bf else c_bf  # Ensure transfer is between different cashiers
            try:
                transfer = Transfer.objects.create(
                    from_cashier=from_cashier,
                    to_cashier=to_cashier,
                    amount=amount,
                    note=f'Test Transfer {i+1}',
                )
                self.stdout.write(self.style.SUCCESS(f'Successfully created transfer {i+1}: From {from_cashier} to {to_cashier}, Amount: {amount}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating transfer {i+1}: {e}'))
