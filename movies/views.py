from django.shortcuts import render, redirect, get_object_or_404
from rest_framework import viewsets
from .serializers import MovieSerializer, ReviewSerializer
from .models import Moviedata, Review, Genre, Watchlist
from django.db.models import Q, Count, Avg
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.models import User
from django.http import JsonResponse


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Moviedata.objects.all()
    serializer_class = MovieSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Get search parameters from query
        search_query = self.request.query_params.get("search", None)
        genre = self.request.query_params.get("genre", None)
        year = self.request.query_params.get("year", None)
        actor = self.request.query_params.get("actor", None)
        director = self.request.query_params.get("director", None)

        # Apply filters
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query)
                | Q(description__icontains=search_query)
                | Q(actors__icontains=search_query)
                | Q(director__icontains=search_query)
            )
        if genre:
            queryset = queryset.filter(
                genres__name__iexact=genre
            )  # Fixed: genres__name instead of genre
        if year:
            queryset = queryset.filter(year=year)
        if actor:
            queryset = queryset.filter(actors__icontains=actor)
        if director:
            queryset = queryset.filter(director__icontains=director)

        return queryset

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def add_review(self, request, pk=None):
        movie = self.get_object()
        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(movie=movie, user=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @action(detail=True, methods=["get"])
    def reviews(self, request, pk=None):
        movie = self.get_object()
        reviews = movie.reviews.all()
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)


def home_view(request):
    search_query = request.GET.get("q", "")
    genre_filter = request.GET.get("genre")
    year_filter = request.GET.get("year")

    movie_queryset = Moviedata.objects.all().prefetch_related("genres")

    if search_query:
        movie_queryset = movie_queryset.filter(
            Q(title__icontains=search_query)
            | Q(director__icontains=search_query)
            | Q(actors__icontains=search_query)
        )

    if genre_filter:
        movie_queryset = movie_queryset.filter(genres__name__iexact=genre_filter)

    if year_filter and year_filter.isdigit():
        movie_queryset = movie_queryset.filter(year=int(year_filter))

    trending_movies = movie_queryset.order_by("-release_date")[:8]
    top_rated_movies = movie_queryset.order_by("-average_rating")[:8]

    available_years = (
        Moviedata.objects.values_list("year", flat=True).distinct().order_by("-year")
    )

    return render(
        request,
        "movies/home.html",
        {
            "trending_movies": trending_movies,
            "top_rated_movies": top_rated_movies,
            "available_years": available_years,
            "search_query": search_query,
            "selected_genre": genre_filter,
            "selected_year": year_filter,
        },
    )


def movie_detail_view(request, movie_id):
    movie = get_object_or_404(
        Moviedata.objects.prefetch_related("genres", "reviews"), id=movie_id
    )
    has_reviewed = False
    if request.user.is_authenticated:
        has_reviewed = Review.objects.filter(movie=movie, user=request.user).exists()

    movie_in_watchlist = False
    if request.user.is_authenticated:
        movie_in_watchlist = Watchlist.objects.filter(
            movie=movie, user=request.user
        ).exists()

    return render(
        request,
        "movies/movie_detail.html",
        {
            "movie": movie,
            "reviews": movie.reviews.all(),
            "has_reviewed": has_reviewed,  # Pass this to template
            "movie_in_watchlist": movie_in_watchlist,
        },
    )


def genre_view(request, genre_name):
    genre = get_object_or_404(Genre, name__iexact=genre_name)

    # Get all filter parameters
    sort_by = request.GET.get("sort", "-release_date")
    year_filter = request.GET.get("year")

    # Validate sort options
    valid_sorts = {
        "-release_date": "Newest",
        "release_date": "Oldest",
        "-average_rating": "Highest Rated",
        "title": "A-Z",
    }

    if sort_by not in valid_sorts:
        sort_by = "-release_date"

    # Base queryset with prefetch
    movies = Moviedata.objects.filter(genres=genre).prefetch_related("genres")

    # Apply year filter
    if year_filter and year_filter.isdigit():
        movies = movies.filter(year=int(year_filter))

    # Apply sorting
    movies = movies.order_by(sort_by)

    # Get available years for this genre
    available_years = movies.values_list("year", flat=True).distinct().order_by("-year")

    # Pagination
    paginator = Paginator(movies, 4)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "movies/genre.html",
        {
            "genre": genre,
            "movies": page_obj,
            "sort_options": valid_sorts,
            "current_sort": sort_by,
            "available_years": available_years,
            "selected_year": year_filter,
            "paginator": paginator,  # Added paginator to context
            "page_obj": page_obj,
            "page_range": paginator.get_elided_page_range(
                page_obj.number, on_each_side=1, on_ends=1
            ),  # Better page range display
        },
    )


def search_view(request):
    # Get search parameters
    query = request.GET.get("q", "")
    genre = request.GET.get("genre", "")
    year = request.GET.get("year", "")
    min_rating = request.GET.get("min_rating", "")
    director = request.GET.get("director", "")
    actor = request.GET.get("actor", "")
    sort = request.GET.get("sort", "-average_rating")  # Default sort by highest rated

    # Start with base queryset
    movies = Moviedata.objects.all().prefetch_related("genres")

    # Apply filters
    if query:
        movies = movies.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(actors__icontains=query)
            | Q(director__icontains=query)
            | Q(genres__name__icontains=query)
            | Q(year__icontains=query)  # Search in genres too
        ).distinct()  # Add distinct to avoid duplicates

    if genre:
        movies = movies.filter(genres__name__iexact=genre)

    if year and year.isdigit():
        movies = movies.filter(year=int(year))

    if min_rating:
        try:
            movies = movies.filter(average_rating__gte=float(min_rating))
        except ValueError:
            pass  # Ignore invalid rating input

    if director:
        movies = movies.filter(director__icontains=director)

    if actor:
        movies = movies.filter(actors__icontains=actor)

    # Apply sorting
    valid_sorts = [
        "title",
        "-title",
        "average_rating",
        "-average_rating",
        "year",
        "-year",
    ]
    if sort in valid_sorts:
        movies = movies.order_by(sort)

    # Get all genres for dropdown
    all_genres = Genre.objects.annotate(movie_count=Count("movies")).filter(
        movie_count__gt=0
    )

    return render(
        request,
        "movies/search_results.html",
        {
            "movies": movies,
            "query": query,
            "filters": {
                "genre": genre,
                "year": year,
                "min_rating": min_rating,
                "director": director,
                "actor": actor,
            },
            "all_genres": all_genres,
            "current_sort": sort,
            "year": year,
        },
    )


@login_required
def add_review(request, movie_id):
    movie = get_object_or_404(Moviedata, id=movie_id)

    if request.method == "POST":
        if Review.objects.filter(movie=movie, user=request.user).exists():
            messages.warning(request, "You've already reviewed this movie.")
        else:
            try:
                Review.objects.create(
                    movie=movie,
                    user=request.user,
                    rating=request.POST["rating"],
                    comment=request.POST["comment"],
                )
                messages.success(request, "Thank you for your review!")
            except Exception as e:
                messages.error(request, f"Error submitting review: {str(e)}")

        return redirect("movies:movie_detail", movie_id=movie_id)

    # If not POST, show the movie detail page
    return redirect("movies:movie_detail", movie_id=movie_id)


@login_required
def profile(request):
    # Watchlist items

    # Get sort parameter from request (default: recently added first)
    sort_by = request.GET.get("sort_watchlist", "-")

    # Define valid sorting options
    SORT_OPTIONS = {
        "title": "movie__title",
        "-title": "-movie__title",
        "date": "added_on",
        "-date": "-added_on",  # Default: newest first
        "rating": "movie__average_rating",
        "-rating": "-movie__average_rating",
        "year": "movie__year",
        "-year": "-movie__year",
    }

    # Get the actual field to sort by
    sort_field = SORT_OPTIONS.get(sort_by, "-added_on")

    # Get and sort watchlist
    watchlist = (
        Watchlist.objects.filter(user=request.user)
        .select_related("movie")
        .order_by(sort_field)
    )

    # Get all reviews for stats calculation
    all_reviews = Review.objects.filter(user=request.user).select_related("movie")

    # Calculate stats
    review_stats = all_reviews.aggregate(
        avg_rating=Avg("rating"), total_reviews=Count("id")
    )

    # Get favorite genre
    favorite_genre = (
        Genre.objects.filter(movies__reviews__user=request.user)
        .annotate(review_count=Count("id"))
        .order_by("-review_count")
        .first()
    )

    # Paginate reviews
    review_page = request.GET.get("reviews_page", 1)
    paginator = Paginator(all_reviews.order_by("-created_at"), 3)
    reviews = paginator.get_page(review_page)

    # Get recommendations
    recommended_movies = Moviedata.objects.exclude(
        Q(watchlist__user=request.user) | Q(reviews__user=request.user)
    ).order_by("-average_rating")[:6]

    # Prepare all activities (combining watchlist additions and reviews)
    all_activities = []

    # Add watchlist activities
    watchlist_activities = Watchlist.objects.filter(user=request.user).select_related(
        "movie"
    )

    for item in watchlist_activities:
        all_activities.append(
            {
                "type": "watchlist",
                "text": f"Added {item.movie.title} to watchlist",
                "timestamp": item.added_on,
                "movie": item.movie,
            }
        )

    # Add review activities
    review_activities = Review.objects.filter(user=request.user).select_related("movie")

    for review in review_activities:
        all_activities.append(
            {
                "type": "review",
                "text": f"Reviewed {review.movie.title} with {review.rating}★",
                "timestamp": review.created_at,
                "movie": review.movie,
            }
        )

    # Sort combined activities by timestamp (newest first)
    all_activities.sort(key=lambda x: x["timestamp"], reverse=True)

    # Paginate activities (4 per page)
    activity_page = request.GET.get("activity_page", 1)
    activities_paginator = Paginator(all_activities, 4)
    recent_activities = activities_paginator.get_page(activity_page)

    return render(
        request,
        "movies/profile.html",
        {
            "user": request.user,
            "watchlist": watchlist,
            "current_sort": sort_by,
            "reviews": reviews,
            "avg_rating": (
                round(review_stats["avg_rating"], 1)
                if review_stats["avg_rating"]
                else None
            ),
            "total_reviews": review_stats["total_reviews"],
            "favorite_genre": favorite_genre.name if favorite_genre else None,
            "recommended_movies": recommended_movies,
            "recent_activities": recent_activities,
        },
    )


@login_required
def add_to_watchlist(request, movie_id):
    movie = get_object_or_404(Moviedata, id=movie_id)
    if Watchlist.objects.filter(user=request.user, movie=movie).exists():
        messages.warning(request, "This movie is already in your watchlist!")
    else:
        Watchlist.objects.create(user=request.user, movie=movie)
        messages.success(request, "Movie added to your watchlist!")
    return redirect("movies:movie_detail", movie_id=movie_id)


@login_required
def remove_from_watchlist(request, movie_id):
    Watchlist.objects.filter(user=request.user, movie_id=movie_id).delete()
    messages.success(request, "Movie removed from your watchlist!")
    return redirect("movies:movie_detail", movie_id=movie_id)


def logout_view(request):
    auth_logout(request)
    return redirect("account_logout")


@login_required
def edit_profile(request):
    if request.method == "POST":
        # Update basic user info
        request.user.first_name = request.POST.get("first_name", "")
        request.user.last_name = request.POST.get("last_name", "")
        request.user.save()

        # Handle profile picture
        if hasattr(request.user, "profile"):
            profile = request.user.profile
        else:
            profile = profile(user=request.user)

        if "avatar-clear" in request.POST:
            # Remove the avatar
            if profile.avatar:
                profile.avatar.delete()
            profile.avatar = None
        elif "avatar" in request.FILES:
            # Save new avatar
            if profile.avatar:
                profile.avatar.delete()  # Delete old avatar if exists
            profile.avatar = request.FILES["avatar"]

        profile.save()

        messages.success(request, "Profile updated successfully!")
        return redirect("movies:profile")

    return render(request, "movies/edit_profile.html", {"user": request.user})


@login_required
def sort_watchlist(request, sort_by):
    watchlist = Watchlist.objects.filter(user=request.user)
    if sort_by == "title":
        watchlist = watchlist.order_by("movie__title")
    elif sort_by == "date":
        watchlist = watchlist.order_by("-added_on")
    return render(
        request,
        "movies/profile.html",
        {"watchlist": watchlist, "reviews": Review.objects.filter(user=request.user)},
    )
