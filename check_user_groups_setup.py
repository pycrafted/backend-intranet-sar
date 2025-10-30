import os
import sys


def main():
    # Préparer Django
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(project_root)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "master.settings")

    import django
    django.setup()

    from django.core import management
    from django.contrib.auth.models import Group, Permission

    # Exécuter la commande de setup (idempotente)
    management.call_command("setup_default_groups", verbosity=0)

    # Vérifications minimales
    expected_groups = ["administrateur", "communication", "utilisateur simple"]
    missing = [g for g in expected_groups if not Group.objects.filter(name=g).exists()]
    if missing:
        print("KO - Groupes manquants:", ", ".join(missing))
        sys.exit(1)

    admin = Group.objects.get(name="administrateur")
    if Permission.objects.count() and admin.permissions.count() == 0:
        print("KO - Le groupe administrateur n'a aucune permission")
        sys.exit(1)

    print("OK - Groupes par défaut présents et permissions assignées.")


if __name__ == "__main__":
    main()


