from django.contrib import admin
from django.urls import path

from weather import views


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.dashboard_page, name="dashboard"),
    path("login/", views.login_page, name="login"),
    path("register/", views.register_page, name="register"),
    path("api/auth/register", views.RegisterAPIView.as_view(), name="api-register"),
    path("api/auth/login", views.LoginAPIView.as_view(), name="api-login"),
    path("api/weather/<str:city>", views.WeatherAPIView.as_view(), name="api-weather"),
    path("api/forecast/<str:city>", views.ForecastAPIView.as_view(), name="api-forecast"),
    path("api/favorites", views.FavoriteListCreateAPIView.as_view(), name="api-favorites"),
    path(
        "api/favorites/<str:city>",
        views.FavoriteDestroyAPIView.as_view(),
        name="api-favorite-detail",
    ),
]
