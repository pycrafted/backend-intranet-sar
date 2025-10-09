# Generated manually
from django.db import migrations, models
import django.db.models.deletion


def migrate_position_to_department_and_title(apps, schema_editor):
    """Migrer les données de Position vers Department et position_title"""
    Employee = apps.get_model('annuaire', 'Employee')
    Department = apps.get_model('annuaire', 'Department')
    Position = apps.get_model('annuaire', 'Position')
    
    # Créer un département par défaut si nécessaire
    default_department, created = Department.objects.get_or_create(
        name='Département par défaut',
        defaults={'name': 'Département par défaut'}
    )
    
    # Migrer les employés existants
    for employee in Employee.objects.all():
        if hasattr(employee, 'position') and employee.position:
            # Assigner le département du poste
            employee.department = employee.position.department
            # Assigner le titre du poste
            employee.position_title = employee.position.title
        else:
            # Assigner le département par défaut
            employee.department = default_department
            employee.position_title = 'Poste non spécifié'
        
        employee.save()


def reverse_migrate_department_to_position(apps, schema_editor):
    """Migration inverse - ne peut pas être complètement inversée"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('annuaire', '0005_remove_organizationalchart'),
    ]

    operations = [
        # Ajouter le champ department à Employee (nullable temporairement)
        migrations.AddField(
            model_name='employee',
            name='department',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='employees',
                to='annuaire.department',
                verbose_name='Département',
                null=True,
                blank=True
            ),
        ),
        
        # Ajouter le champ position_title à Employee
        migrations.AddField(
            model_name='employee',
            name='position_title',
            field=models.CharField(
                max_length=100,
                verbose_name='Titre du poste',
                blank=True,
                default=''
            ),
        ),
        
        # Migrer les données existantes
        migrations.RunPython(
            migrate_position_to_department_and_title,
            reverse_migrate_department_to_position
        ),
        
        # Rendre le champ department obligatoire
        migrations.AlterField(
            model_name='employee',
            name='department',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='employees',
                to='annuaire.department',
                verbose_name='Département'
            ),
        ),
    ]
