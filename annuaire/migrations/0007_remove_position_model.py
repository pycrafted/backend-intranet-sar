# Generated manually
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annuaire', '0006_add_department_to_employee'),
    ]

    operations = [
        # Supprimer la ForeignKey position de Employee
        migrations.RemoveField(
            model_name='employee',
            name='position',
        ),
        
        # Supprimer le modèle Position
        migrations.DeleteModel(
            name='Position',
        ),
    ]
