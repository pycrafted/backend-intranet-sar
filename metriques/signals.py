from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.contrib.auth import get_user_model
from .models import UserLogin

User = get_user_model()


@receiver(user_logged_in)
def track_user_login(sender, request, user, **kwargs):
    """
    Signal pour tracker automatiquement les connexions utilisateurs
    """
    try:
        # Récupérer l'adresse IP
        ip_address = None
        if hasattr(request, 'META'):
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                ip_address = request.META.get('REMOTE_ADDR')
        
        # Récupérer le User Agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Créer l'enregistrement de connexion
        UserLogin.objects.create(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        # Logger l'erreur mais ne pas bloquer la connexion
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors du tracking de la connexion: {e}")


@receiver(user_logged_out)
def track_user_logout(sender, request, user, **kwargs):
    """
    Signal pour tracker les déconnexions et calculer la durée de session
    """
    try:
        # Lors de la déconnexion, user peut être None, donc on utilise request.user si disponible
        user_to_track = user
        if not user_to_track and hasattr(request, 'user'):
            user_to_track = request.user
        
        if user_to_track and hasattr(user_to_track, 'id'):
            # Trouver la dernière connexion sans déconnexion
            last_login = UserLogin.objects.filter(
                user=user_to_track,
                logout_time__isnull=True
            ).order_by('-login_time').first()
            
            if last_login:
                from django.utils import timezone
                last_login.logout_time = timezone.now()
                last_login.calculate_duration()
    except Exception as e:
        # Logger l'erreur mais ne pas bloquer la déconnexion
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors du tracking de la déconnexion: {e}")
