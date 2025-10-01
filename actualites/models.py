from django.db import models
from django.db.models import Sum
from django.utils import timezone


class Article(models.Model):
    TYPE_CHOICES = [
        ('news', 'Actualité'),
        ('announcement', 'Annonce'),
    ]
    
    CATEGORY_CHOICES = [
        ('Toutes', 'Toutes'),
        ('Sécurité', 'Sécurité'),
        ('Finance', 'Finance'),
        ('Formation', 'Formation'),
        ('Production', 'Production'),
        ('Partenariat', 'Partenariat'),
        ('Environnement', 'Environnement'),
        ('RH', 'Ressources Humaines'),
    ]
    
    # Champs communs
    id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200, blank=True, null=True, help_text='Titre de l\'article (optionnel)')
    content = models.TextField(blank=True, null=True, help_text='Contenu de l\'article (optionnel)')
    date = models.DateField(default=timezone.now, help_text='Date de publication (par défaut: maintenant)')
    time = models.TimeField(default=timezone.now, help_text='Heure de publication (par défaut: maintenant)')
    author = models.CharField(max_length=100, blank=True, null=True, help_text='Auteur de l\'article (optionnel)')
    author_role = models.CharField(max_length=100, blank=True, null=True, help_text='Rôle de l\'auteur (optionnel)')
    author_avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    image = models.ImageField(upload_to='articles/', blank=True, null=True)
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    
    # Nouveaux champs pour les cartes adaptatives
    gallery_images = models.JSONField(blank=True, null=True, help_text='Liste des URLs des images de la galerie')
    gallery_title = models.CharField(max_length=200, blank=True, null=True, help_text='Titre de la galerie de photos')
    video = models.FileField(upload_to='videos/', blank=True, null=True, help_text='Fichier vidéo uploadé')
    video_poster = models.ImageField(upload_to='video_posters/', blank=True, null=True, help_text='Image de couverture pour la vidéo')
    content_type = models.CharField(
        max_length=20,
        choices=[
            ('text_only', 'Texte seul'),
            ('image_only', 'Image seule'),
            ('text_image', 'Texte + Image'),
            ('gallery', 'Galerie de photos'),
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


