from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


GROUPS = {
    "administrateur": {
        "all_perms": True,
    },
    "communication": {
        "models": {
            # app_label: [actions]
            "actualites": ["add", "change", "delete", "view"],
            "documents": ["add", "change", "delete", "view"],
        },
    },
    "utilisateur simple": {
        "models": {
            # accès lecture seule généralisé aux principaux modules
            "actualites": ["view"],
            "documents": ["view"],
            "annuaire": ["view"],
            "organigramme": ["view"],
        },
    },
}


class Command(BaseCommand):
    help = "Crée ou met à jour les groupes par défaut (administrateur, communication, utilisateur simple) et leurs permissions."

    def handle(self, *args, **options):
        created_or_updated = []

        for group_name, config in GROUPS.items():
            group, _ = Group.objects.get_or_create(name=group_name)

            if config.get("all_perms"):
                # Donne toutes les permissions disponibles
                all_perms = Permission.objects.all()
                group.permissions.set(all_perms)
                created_or_updated.append((group_name, f"{all_perms.count()} permissions"))
                continue

            # Sinon, donner des permissions ciblées par app/model
            desired_perms = []
            models_cfg = config.get("models", {})
            for app_label, actions in models_cfg.items():
                content_types = ContentType.objects.filter(app_label=app_label)
                for ct in content_types:
                    for action in actions:
                        codename = f"{action}_{ct.model}"
                        perm = Permission.objects.filter(codename=codename, content_type=ct).first()
                        if perm:
                            desired_perms.append(perm)

            # Appliquer les permissions (idempotent)
            group.permissions.set(desired_perms)
            created_or_updated.append((group_name, f"{len(desired_perms)} permissions"))

        # Résumé
        for name, info in created_or_updated:
            self.stdout.write(self.style.SUCCESS(f"Groupe '{name}': {info}"))

        self.stdout.write(self.style.SUCCESS("Groupes par défaut configurés avec succès."))







