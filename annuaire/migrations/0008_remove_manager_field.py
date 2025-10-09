# Generated manually
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annuaire', '0007_remove_position_model'),
    ]

    operations = [
        # Supprimer le champ manager de Employee
        migrations.RemoveField(
            model_name='employee',
            name='manager',
        ),
    ]
