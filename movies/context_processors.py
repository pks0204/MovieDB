# movies/context_processors.py
from .models import Genre
from django.db.models import Count


def genres_context(request):
    genres = (
        Genre.objects.annotate(movie_count=Count("movies"))
        .filter(movie_count__gt=0)
        .order_by("name")
    )
    return {"all_genres": genres}
