# Generated manually for video support

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('actualites', '0003_add_gallery_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='video',
            field=models.FileField(blank=True, help_text='Fichier vidéo uploadé', null=True, upload_to='videos/'),
        ),
        migrations.AddField(
            model_name='article',
            name='video_poster',
            field=models.ImageField(blank=True, help_text='Image de couverture pour la vidéo', null=True, upload_to='video_posters/'),
        ),
        migrations.AlterField(
            model_name='article',
            name='content_type',
            field=models.CharField(
                choices=[
                    ('text_only', 'Texte seul'),
                    ('image_only', 'Image seule'),
                    ('text_image', 'Texte + Image'),
                    ('gallery', 'Galerie de photos'),
                    ('video', 'Vidéo'),
                    ('poll', 'Sondage'),
                    ('event', 'Événement'),
                ],
                default='text_only',
                help_text='Type de contenu pour adapter l\'affichage de la carte',
                max_length=20
            ),
        ),
    ]








