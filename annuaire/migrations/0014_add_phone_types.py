# Generated manually
from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('annuaire', '0013_remove_is_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='phone_fixed',
            field=models.CharField(blank=True, max_length=17, null=True, validators=[django.core.validators.RegexValidator(message="Format: '+999999999'. Maximum 15 chiffres.", regex='^\\+?1?\\d{9,15}$')], verbose_name='Téléphone fixe'),
        ),
        migrations.AddField(
            model_name='employee',
            name='phone_mobile',
            field=models.CharField(blank=True, max_length=17, null=True, validators=[django.core.validators.RegexValidator(message="Format: '+999999999'. Maximum 15 chiffres.", regex='^\\+?1?\\d{9,15}$')], verbose_name='Téléphone mobile'),
        ),
        migrations.RemoveField(
            model_name='employee',
            name='phone',
        ),
    ]
