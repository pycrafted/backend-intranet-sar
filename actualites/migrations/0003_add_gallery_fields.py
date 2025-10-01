# Generated manually for adaptive publication cards

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('actualites', '0002_alter_article_author_avatar_alter_article_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='gallery_images',
            field=models.JSONField(blank=True, null=True, help_text='Liste des URLs des images de la galerie'),
        ),
        migrations.AddField(
            model_name='article',
            name='gallery_title',
            field=models.CharField(blank=True, max_length=200, null=True, help_text='Titre de la galerie de photos'),
        ),
        migrations.AddField(
            model_name='article',
            name='content_type',
            field=models.CharField(
                choices=[
                    ('text_only', 'Texte seul'),
                    ('image_only', 'Image seule'),
                    ('text_image', 'Texte + Image'),
                    ('gallery', 'Galerie de photos'),
                    ('poll', 'Sondage'),
                    ('event', 'Événement'),
                ],
                default='text_only',
                max_length=20,
                help_text='Type de contenu pour adapter l\'affichage de la carte'
            ),
        ),
    ]



















