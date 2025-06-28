from django.db import migrations, models
from datetime import timedelta


def convert_to_duration(apps, schema_editor):
    Moviedata = apps.get_model("movies", "Moviedata")
    for movie in Moviedata.objects.all():
        if isinstance(movie.duration, int):  # Only convert if it's still an integer
            movie.duration = timedelta(minutes=movie.duration)
            movie.save()


def convert_to_minutes(apps, schema_editor):
    Moviedata = apps.get_model("movies", "Moviedata")
    for movie in Moviedata.objects.all():
        if isinstance(movie.duration, timedelta):  # Only convert if it's a timedelta
            movie.duration = int(movie.duration.total_seconds() / 60)
            movie.save()


class Migration(migrations.Migration):
    dependencies = [
        ("movies", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="moviedata",
            name="duration",
            field=models.DurationField(
                help_text="Format: HH:MM:SS or D days, HH:MM:SS", blank=True, null=True
            ),
        ),
        migrations.RunPython(convert_to_duration, convert_to_minutes),
    ]
