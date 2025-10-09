# Generated manually
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annuaire', '0011_remove_office_location_work_schedule'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='employee',
            name='user_account',
        ),
    ]
