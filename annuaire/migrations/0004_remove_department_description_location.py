# Generated manually

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annuaire', '0003_add_phone_unique_constraint'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='department',
            name='description',
        ),
        migrations.RemoveField(
            model_name='department',
            name='location',
        ),
    ]
