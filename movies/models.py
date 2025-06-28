from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg, Count, Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile


class Genre(models.Model):
    """Model to represent individual genres"""

    name = models.CharField(
        max_length=100, unique=True, db_index=True
    )  # Added db_index for faster lookups

    class Meta:
        ordering = ["name"]  # Always order alphabetically

    def __str__(self):
        return self.name.title()  # Ensure proper capitalization


class Profile(models.Model):
    """Extended user profile information"""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    avatar = models.ImageField(upload_to="profile_pics/", null=True, blank=True)
    bio = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if self.avatar:
            img = Image.open(self.avatar)
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)

                thumb_io = BytesIO()
                img.save(thumb_io, format=img.format)

                self.avatar.save(
                    self.avatar.name, ContentFile(thumb_io.getvalue()), save=False
                )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    @property
    def avatar_url(self):
        if self.avatar and hasattr(self.avatar, "url"):
            return self.avatar.url
        return None


# Signal to create/update profile when User is created/updated
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, "profile"):
        instance.profile.save()
    else:
        Profile.objects.create(user=instance)


class Moviedata(models.Model):
    title = models.CharField(max_length=200, db_index=True)
    duration = models.DurationField(
        help_text="Format: HH:MM:SS or D days, HH:MM:SS", blank=True, null=True
    )
    description = models.TextField()
    release_date = models.DateField()
    genres = models.ManyToManyField(
        Genre,
        related_name="movies",  # Added for reverse lookups
        blank=True,  # Allow movies without genres
    )
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    poster_url = models.ImageField(
        upload_to="movie_posters/", default="default_poster.jpg"  # More specific path
    )
    actors = models.TextField(blank=True, help_text="Comma-separated list of actors")
    director = models.CharField(max_length=200, blank=True, db_index=True)
    year = models.PositiveIntegerField(editable=False)  # Made non-editable

    class Meta:
        ordering = ["-release_date"]  # Default ordering
        verbose_name_plural = "Movie Data"  # Better admin display

    def __str__(self):
        return f"{self.title} ({self.year})"

    def save(self, *args, **kwargs):
        """Auto-set year from release_date"""
        if self.release_date:
            self.year = self.release_date.year
        super().save(*args, **kwargs)

    def get_actors_list(self):
        """Returns cleaned list of actors"""
        return [actor.strip() for actor in self.actors.split(",") if actor.strip()]

    def display_genres(self):
        """Formatted string of genres for admin/templates"""
        return ", ".join(genre.name for genre in self.genres.all())

    display_genres.short_description = "Genres"

    def update_rating(self):
        reviews = self.reviews.all()
        if reviews:
            self.average_rating = sum(review.rating for review in reviews) / len(
                reviews
            )
        else:
            self.average_rating = 0
        self.save()

    @property
    def rating(self):
        """Public-facing rating (same as average_rating)"""
        return self.average_rating

    def update_rating(self):
        """Updates average_rating from reviews"""
        result = self.reviews.aggregate(Avg("rating"))
        self.average_rating = result["rating__avg"] or 0
        self.save()


class Review(models.Model):
    movie = models.ForeignKey(
        Moviedata, on_delete=models.CASCADE, related_name="reviews"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("movie", "user")

    def __str__(self):
        return f"{self.user.username}'s review for {self.movie.title}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # More efficient rating update
        avg_rating = self.movie.reviews.aggregate(Avg("rating"))["rating__avg"] or 0
        Moviedata.objects.filter(pk=self.movie.pk).update(average_rating=avg_rating)

    def delete(self, *args, **kwargs):
        movie_pk = self.movie.pk
        super().delete(*args, **kwargs)
        # Update rating after deletion
        avg_rating = (
            Review.objects.filter(movie_id=movie_pk).aggregate(Avg("rating"))[
                "rating__avg"
            ]
            or 0
        )
        Moviedata.objects.filter(pk=movie_pk).update(average_rating=avg_rating)


class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="watchlist")
    movie = models.ForeignKey(Moviedata, on_delete=models.CASCADE)
    added_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "movie")  # Prevents duplicates
        ordering = ["-added_on"]

    def __str__(self):
        return f"{self.user.username}'s watchlist: {self.movie.title}"
