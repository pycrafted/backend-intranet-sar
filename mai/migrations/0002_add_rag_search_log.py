# Generated manually for RAGSearchLog model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mai', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='RAGSearchLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('query', models.TextField(help_text='Requête de recherche')),
                ('method', models.CharField(choices=[('vectorial', 'Recherche Vectorielle'), ('heuristic', 'Recherche Heuristique'), ('hybrid', 'Mode Hybride')], help_text='Méthode de recherche utilisée', max_length=20)),
                ('results_count', models.PositiveIntegerField(default=0, help_text='Nombre de résultats trouvés')),
                ('response_time_ms', models.FloatField(help_text='Temps de réponse en millisecondes')),
                ('similarity_threshold', models.FloatField(default=0.7, help_text='Seuil de similarité utilisé')),
                ('success', models.BooleanField(default=True, help_text='Recherche réussie ou non')),
                ('error_message', models.TextField(blank=True, help_text='Message d\'erreur si échec', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'RAG Search Log',
                'verbose_name_plural': 'RAG Search Logs',
                'db_table': 'rag_search_log',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='ragsearchlog',
            index=models.Index(fields=['created_at'], name='mai_ragsearchlog_created_at_idx'),
        ),
        migrations.AddIndex(
            model_name='ragsearchlog',
            index=models.Index(fields=['method'], name='mai_ragsearchlog_method_idx'),
        ),
        migrations.AddIndex(
            model_name='ragsearchlog',
            index=models.Index(fields=['success'], name='mai_ragsearchlog_success_idx'),
        ),
    ]
