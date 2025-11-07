from django.db import models
from django.db.models import Sum
from django.utils import timezone


class Article(models.Model):
    TYPE_CHOICES = [
        ('news', 'Actualité'),
        ('announcement', 'Annonce'),
    ]
    
    
    # Champs communs
    id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=1000, blank=True, null=True, help_text='Titre de l\'article (optionnel)')
    content = models.TextField(blank=True, null=True, help_text='Contenu de l\'article (optionnel)')
    date = models.DateField(default=timezone.now, help_text='Date de publication (par défaut: maintenant)')
    time = models.TimeField(default=timezone.now, help_text='Heure de publication (par défaut: maintenant)')
    image = models.ImageField(upload_to='articles/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Nouveaux champs pour les cartes adaptatives
    video = models.FileField(upload_to='videos/', blank=True, null=True, help_text='Fichier vidéo uploadé')
    video_poster = models.ImageField(upload_to='video_posters/', blank=True, null=True, help_text='Image de couverture pour la vidéo')
    content_type = models.CharField(
        max_length=20,
        choices=[
            ('text_only', 'Texte seul'),
            ('image_only', 'Image seule'),
            ('text_image', 'Texte + Image'),
            ('video', 'Vidéo'),
        ],
        default='text_only',
        help_text='Type de contenu pour adapter l\'affichage de la carte'
    )
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        title = self.title or "Sans titre"
        return f"{self.get_type_display()}: {title}"


