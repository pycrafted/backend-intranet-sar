# Generated manually
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annuaire', '0010_alter_employee_position_title'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='employee',
            name='office_location',
        ),
        migrations.RemoveField(
            model_name='employee',
            name='work_schedule',
        ),
    ]

