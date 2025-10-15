# Generated manually
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annuaire', '0008_remove_manager_field'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='employee',
            name='hire_date',
        ),
    ]

