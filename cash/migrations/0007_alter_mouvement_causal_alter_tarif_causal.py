# Generated by Django 4.2 on 2025-02-19 18:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cash', '0006_remove_cashier_created_remove_cashier_modified_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mouvement',
            name='causal',
            field=models.CharField(blank=True, choices=[('INS', 'Inscription'), ('SCO', 'SCO'), ('TEN', 'Tenue'), ('CAN', 'Cantine')], db_index=True, max_length=5, null=True),
        ),
        migrations.AlterField(
            model_name='tarif',
            name='causal',
            field=models.CharField(choices=[('INS', 'Inscription'), ('SCO1', 'Scolarite 1'), ('SCO2', 'Scolarite 2'), ('SCO3', 'Scolarite 3'), ('TEN', 'Tenue'), ('CAN', 'Cantine')], db_index=True, max_length=5),
        ),
    ]
