# Generated manually on 2025-12-16

from django.db import migrations


def force_activate_all_inactive_users(apps, schema_editor):
    """
    Migration de données : Force is_active=True pour tous les utilisateurs inactifs
    """
    # Utiliser apps.get_model pour obtenir le modèle User dans le contexte de migration
    User = apps.get_model('authentication', 'User')
    
    # Mettre à jour tous les utilisateurs inactifs
    updated_count = User.objects.filter(
        is_active=False
    ).update(is_active=True)
    
    print(f"✅ {updated_count} utilisateur(s) inactif(s) activé(s) avec is_active=True")


def reverse_force_activate(apps, schema_editor):
    """
    Migration inverse : Ne fait rien car on ne peut pas vraiment inverser cette opération
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0009_force_activate_all_users'),
    ]

    operations = [
        migrations.RunPython(
            force_activate_all_inactive_users,
            reverse_force_activate,
        ),
    ]

