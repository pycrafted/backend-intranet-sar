#!/usr/bin/env python
"""
Script de pré-vérification des migrations:
- Vérifie s'il y a des changements de modèles non migrés (makemigrations --check)
- Affiche le plan de migration sans appliquer (migrate --plan)

Usage:
  python backend-intranet-sar/check_migrations_plan.py
"""
import os
import sys


def main():
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(project_root)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "master.settings")

    import django
    django.setup()

    from django.core import management

    print("=" * 80)
    print("🔎 Étape 1/2: Vérification de l'état des migrations (makemigrations --check)")
    print("=" * 80)
    try:
        # --check: renvoie un code d'erreur s'il y a des changements non migrés
        management.call_command("makemigrations", "--check", verbosity=1)
        print("✅ Aucun changement de modèle non migré détecté.")
    except SystemExit as e:
        # Django lève SystemExit avec code != 0 en cas de changements
        print("⚠️  Des changements de modèles non migrés ont été détectés.")
        print("   → Lancez: python manage.py makemigrations")
        # On continue quand même pour afficher le plan potentiel

    print("\n" + "=" * 80)
    print("🧭 Étape 2/2: Plan de migration (migrate --plan)")
    print("=" * 80)
    try:
        management.call_command("migrate", "--plan", verbosity=1)
        print("\n✅ Affichage du plan terminé. Aucune migration n'a été appliquée.")
    except Exception as e:
        print("✗ Erreur lors de l'affichage du plan de migration:", e)
        sys.exit(1)

    print("\nVous pouvez maintenant appliquer en toute sécurité avec:\n  python manage.py migrate")


if __name__ == "__main__":
    main()


