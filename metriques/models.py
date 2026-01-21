from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class UserLogin(models.Model):
    """
    Modèle pour tracker les connexions des utilisateurs
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='logins',
        verbose_name="Utilisateur"
    )
    login_time = models.DateTimeField(
        default=timezone.now,
        verbose_name="Heure de connexion"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="Adresse IP"
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
        verbose_name="User Agent"
    )
    logout_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Heure de déconnexion"
    )
    session_duration = models.DurationField(
        null=True,
        blank=True,
        verbose_name="Durée de session"
    )

    class Meta:
        ordering = ['-login_time']
        verbose_name = "Connexion utilisateur"
        verbose_name_plural = "Connexions utilisateurs"
        indexes = [
            models.Index(fields=['-login_time']),
            models.Index(fields=['user', '-login_time']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.login_time.strftime('%Y-%m-%d %H:%M:%S')}"

    def calculate_duration(self):
        """Calcule la durée de la session si logout_time est défini"""
        if self.logout_time:
            self.session_duration = self.logout_time - self.login_time
            self.save(update_fields=['session_duration'])


class AppMetric(models.Model):
    """
    Modèle pour stocker des métriques générales de l'application
    """
    METRIC_TYPE_CHOICES = [
        ('daily_active_users', 'Utilisateurs actifs quotidiens'),
        ('weekly_active_users', 'Utilisateurs actifs hebdomadaires'),
        ('monthly_active_users', 'Utilisateurs actifs mensuels'),
        ('total_users', 'Total utilisateurs'),
        ('total_articles', 'Total articles'),
        ('total_documents', 'Total documents'),
        ('total_forum_posts', 'Total messages forum'),
    ]

    metric_type = models.CharField(
        max_length=50,
        choices=METRIC_TYPE_CHOICES,
        verbose_name="Type de métrique"
    )
    value = models.IntegerField(
        default=0,
        verbose_name="Valeur"
    )
    date = models.DateField(
        default=timezone.now,
        verbose_name="Date"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = "Métrique application"
        verbose_name_plural = "Métriques application"
        unique_together = [['metric_type', 'date']]
        indexes = [
            models.Index(fields=['metric_type', '-date']),
        ]

    def __str__(self):
        return f"{self.get_metric_type_display()} - {self.date}: {self.value}"
