# Generated manually
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annuaire', '0012_remove_user_account'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='employee',
            name='is_active',
        ),
    ]
