from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Moviedata,
    Genre,
    Review,
)
from django.utils.translation import gettext_lazy as _


class GenreInline(admin.TabularInline):
    """Improved genre inline with better display"""

    model = Moviedata.genres.through
    extra = 1
    autocomplete_fields = ["genre"]  # Enable search for genres
    verbose_name = "Genre Assignment"
    verbose_name_plural = "Genre Assignments"


class ReviewInline(admin.TabularInline):
    """Enhanced review inline with more controls"""

    model = Review
    extra = 0  # Don't show empty forms by default
    readonly_fields = ("user", "created_at", "preview_comment")
    fields = ("user", "rating", "preview_comment", "created_at")

    def preview_comment(self, obj):
        return obj.comment[:50] + "..." if len(obj.comment) > 50 else obj.comment

    preview_comment.short_description = "Comment Preview"


@admin.register(Moviedata)
class MoviedataAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "year",
        "display_genres",
        "average_rating",
        "director",
        "formatted_duration",  # Added formatted duration
        "poster_preview",
    )
    list_filter = ("genres", "year", "average_rating")
    search_fields = ("title", "director", "actors", "genres__name")
    filter_horizontal = ("genres",)
    inlines = [ReviewInline]
    readonly_fields = (
        "poster_preview",
        "year",
        "formatted_duration_readonly",
        "average_rating",
    )
    list_per_page = 20
    list_select_related = True

    fieldsets = (
        (
            "Basic Info",
            {"fields": ("title", "description", "poster_url", "poster_preview")},
        ),
        (
            "Details",
            {
                "fields": (
                    "duration",
                    "formatted_duration_readonly",
                    "release_date",
                    "average_rating",
                ),
                "classes": ("collapse",),
            },
        ),
        ("People", {"fields": ("director", "actors")}),
        ("Genres", {"fields": ("genres",), "classes": ("collapse",)}),
    )

    def display_genres(self, obj):
        return ", ".join([genre.name for genre in obj.genres.all()[:3]]) + (
            "..." if obj.genres.count() > 3 else ""
        )

    display_genres.short_description = "Genres"

    def formatted_duration(self, obj):
        if obj.duration:
            total_seconds = int(obj.duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}h {minutes}m"
        return "-"

    formatted_duration.short_description = "Duration"

    def formatted_duration_readonly(self, obj):
        return self.formatted_duration(obj)

    formatted_duration_readonly.short_description = "Duration"

    def poster_preview(self, obj):
        if obj.poster_url:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.poster_url.url,
            )
        return "-"

    poster_preview.short_description = "Poster Preview"

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("genres")


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name", "movie_count", "popularity_indicator")
    search_fields = ("name",)
    list_per_page = 20
    ordering = ["name"]

    def movie_count(self, obj):
        return obj.movies.count()

    movie_count.short_description = "Movies"
    movie_count.admin_order_field = "moviedata__count"  # Enable sorting

    def popularity_indicator(self, obj):
        count = obj.movies.count()
        return format_html(
            '<div style="width:{}px; height:10px; background-color:{}"></div>',
            min(count, 20),
            "green" if count > 5 else "orange",
        )

    popularity_indicator.short_description = "Popularity"


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("movie", "user", "rating_stars", "created_at", "short_comment")
    list_filter = ("rating", "created_at")
    search_fields = ("movie__title", "user__username", "comment")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"
    list_per_page = 20

    def rating_stars(self, obj):
        return format_html("⭐" * int(obj.rating) + "☆" * (5 - int(obj.rating)))

    rating_stars.short_description = "Rating"

    def short_comment(self, obj):
        return obj.comment[:50] + "..." if len(obj.comment) > 50 else obj.comment

    short_comment.short_description = "Comment"
