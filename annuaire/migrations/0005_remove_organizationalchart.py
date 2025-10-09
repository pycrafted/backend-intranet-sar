# Generated manually

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annuaire', '0004_remove_department_description_location'),
    ]

    operations = [
        migrations.DeleteModel(
            name='OrganizationalChart',
        ),
    ]
