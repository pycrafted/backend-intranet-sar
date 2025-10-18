# Generated manually

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('actualites', '0004_remove_article_gallery_fields'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='article',
            name='is_pinned',
        ),
    ]



