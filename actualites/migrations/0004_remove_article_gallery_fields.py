# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('actualites', '0003_remove_article_category'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='article',
            name='gallery_images',
        ),
        migrations.RemoveField(
            model_name='article',
            name='gallery_title',
        ),
        migrations.AlterField(
            model_name='article',
            name='content_type',
            field=models.CharField(
                choices=[
                    ('text_only', 'Texte seul'),
                    ('image_only', 'Image seule'),
                    ('text_image', 'Texte + Image'),
                    ('video', 'Vidéo'),
                ],
                default='text_only',
                help_text='Type de contenu pour adapter l\'affichage de la carte',
                max_length=20
            ),
        ),
    ]
