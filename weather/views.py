from urllib.parse import unquote

from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import FavoriteCity
from .serializers import (
    LoginSerializer,
    RegisterSerializer,
    tokens_for_user,
    user_payload,
)
from .services import WeatherAPIError, weather_client


# def dashboard_page(request):
#     return render(request, "dashboard.html")
def dashboard_page(request):
    city = request.GET.get("city")

    print("CITY:", city)

    context = {}

    if city:
        try:
            context["current"] = weather_client.get_current(city)
            context["forecast"] = weather_client.get_forecast(city)
            context["city"] = city
        except WeatherAPIError as e:
            context["error"] = str(e)

    return render(request, "dashboard.html", context)


def login_page(request):
    return render(request, "registration/login.html")


def register_page(request):
    return render(request, "registration/register.html")


class RegisterAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "user": user_payload(user),
                    "tokens": tokens_for_user(user),
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"detail": "Registration failed.", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class LoginAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            return Response(
                {
                    "user": user_payload(user),
                    "tokens": tokens_for_user(user),
                }
            )
        return Response(
            {"detail": "Login failed.", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class WeatherAPIView(APIView):
    def get(self, request, city):
        try:
            return Response(weather_client.get_current(unquote(city)))
        except WeatherAPIError as exc:
            return Response({"detail": exc.message}, status=exc.status_code)


class ForecastAPIView(APIView):
    def get(self, request, city):
        try:
            return Response(weather_client.get_forecast(unquote(city)))
        except WeatherAPIError as exc:
            return Response({"detail": exc.message}, status=exc.status_code)


class FavoriteListCreateAPIView(APIView):
    max_favorites = 3

    def get(self, request):
        favorites = request.user.favorite_cities.all()
        payload = []

        for favorite in favorites:
            item = {"city": favorite.city_name, "created_at": favorite.created_at}
            try:
                item["weather"] = weather_client.get_current(favorite.city_name)
            except WeatherAPIError as exc:
                item["weather"] = None
                item["error"] = exc.message
            payload.append(item)

        return Response({"count": favorites.count(), "favorites": payload})

    def post(self, request):
        raw_city = request.data.get("city") or request.data.get("city_name")
        if not raw_city or not raw_city.strip():
            return Response(
                {"detail": "City is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        city = raw_city.strip()
        existing = request.user.favorite_cities.filter(city_name__iexact=city).first()
        if existing:
            return Response(
                {"detail": "This city is already in your favorites."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.user.favorite_cities.count() >= self.max_favorites:
            return Response(
                {"detail": "You can save up to 3 favorite cities."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            weather = weather_client.get_current(city)
        except WeatherAPIError as exc:
            return Response({"detail": exc.message}, status=exc.status_code)

        normalized_city = weather.get("city") or city
        if request.user.favorite_cities.filter(city_name__iexact=normalized_city).exists():
            return Response(
                {"detail": "This city is already in your favorites."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        favorite = FavoriteCity.objects.create(
            user=request.user,
            city_name=normalized_city,
        )
        return Response(
            {
                "city": favorite.city_name,
                "weather": weather,
            },
            status=status.HTTP_201_CREATED,
        )


class FavoriteDestroyAPIView(APIView):
    def delete(self, request, city):
        favorite = request.user.favorite_cities.filter(city_name__iexact=unquote(city)).first()
        if not favorite:
            return Response(
                {"detail": "Favorite city not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
