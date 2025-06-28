from rest_framework import serializers
from .models import Moviedata, Review


class MovieSerializer(serializers.ModelSerializer):
    poster_url = serializers.ImageField(max_length=None, use_url=True)

    class Meta:
        model = Moviedata
        fields = [
            "id",
            "title",
            "duration",
            "description",
            "release_date",
            "genre",
            "average_rating",
            "poster_url",
            "actors",
            "director",
            "year",
        ]


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = Review
        fields = ["id", "user", "rating", "comment", "created_at"]
