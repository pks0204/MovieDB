# Generated by Django 5.1.2 on 2025-04-14 05:42

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Genre',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=100, unique=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Moviedata',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(db_index=True, max_length=200)),
                ('duration', models.PositiveIntegerField(help_text='Duration in minutes', validators=[django.core.validators.MinValueValidator(1)])),
                ('description', models.TextField()),
                ('release_date', models.DateField()),
                ('rating', models.FloatField(help_text='Rating from 0-10', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)])),
                ('poster_url', models.ImageField(default='default_poster.jpg', upload_to='movie_posters/')),
                ('actors', models.TextField(blank=True, help_text='Comma-separated list of actors')),
                ('director', models.CharField(blank=True, db_index=True, max_length=200)),
                ('year', models.PositiveIntegerField(editable=False)),
                ('genres', models.ManyToManyField(blank=True, related_name='movies', to='movies.genre')),
            ],
            options={
                'verbose_name_plural': 'Movie Data',
                'ordering': ['-release_date'],
            },
        ),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.IntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)])),
                ('comment', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('movie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='movies.moviedata')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('movie', 'user')},
            },
        ),
    ]
