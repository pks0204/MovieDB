from django.urls import path
from . import views

app_name = "movies"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("genre/<str:genre_name>/", views.genre_view, name="genre"),
    path("movie/<int:movie_id>/", views.movie_detail_view, name="movie_detail"),
    path("movie/<int:movie_id>/add-review/", views.add_review, name="add_review"),
    path("search/", views.search_view, name="search"),
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("profile/sort/<str:sort_by>/", views.sort_watchlist, name="sort_watchlist"),
    path(
        "watchlist/add/<int:movie_id>/", views.add_to_watchlist, name="add_to_watchlist"
    ),
    path(
        "watchlist/remove/<int:movie_id>/",
        views.remove_from_watchlist,
        name="remove_watchlist",
    ),
    path("logout/", views.logout_view, name="logout"),
]
