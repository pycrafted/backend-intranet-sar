# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annuaire', '0014_add_phone_types'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='phone_fixed',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Téléphone fixe'),
        ),
        migrations.AlterField(
            model_name='employee',
            name='phone_mobile',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Téléphone mobile'),
        ),
    ]

