# Generated manually

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('actualites', '0002_remove_article_author_remove_article_author_avatar_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='article',
            name='category',
        ),
    ]





