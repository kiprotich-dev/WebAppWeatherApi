from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from .models import FavoriteCity


User = get_user_model()


def weather_payload(city):
    return {
        "city": city,
        "country": "GB",
        "temperature": 18,
        "condition": "Clear Sky",
        "humidity": 55,
        "wind_speed": 3.4,
        "icon": "01d",
        "units": "metric",
    }


class AuthAPITests(APITestCase):
    def test_user_can_register_with_email_and_password(self):
        response = self.client.post(
            "/api/auth/register",
            {
                "name": "Ada Lovelace",
                "email": "ada@example.com",
                "password": "StrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertIn("access", response.data["tokens"])
        user = User.objects.get(email="ada@example.com")
        self.assertEqual(user.name, "Ada Lovelace")
        self.assertFalse(user.password == "StrongPass123!")

    def test_user_can_login_with_email_and_password(self):
        User.objects.create_user(
            name="Grace Hopper",
            email="grace@example.com",
            password="StrongPass123!",
        )

        response = self.client.post(
            "/api/auth/login",
            {"email": "grace@example.com", "password": "StrongPass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data["tokens"])


class ProtectedEndpointTests(APITestCase):
    def test_weather_endpoint_requires_valid_jwt(self):
        response = self.client.get("/api/weather/London")

        self.assertEqual(response.status_code, 401)


class FavoriteCityTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            name="Katherine Johnson",
            email="katherine@example.com",
            password="StrongPass123!",
        )
        self.client.force_authenticate(user=self.user)

    @patch("weather.views.weather_client.get_current")
    def test_user_can_save_up_to_three_favorites(self, mock_current_weather):
        mock_current_weather.side_effect = lambda city: weather_payload(city)

        for city in ["London", "Nairobi", "Tokyo"]:
            response = self.client.post("/api/favorites", {"city": city}, format="json")
            self.assertEqual(response.status_code, 201)

        response = self.client.post("/api/favorites", {"city": "Paris"}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(FavoriteCity.objects.filter(user=self.user).count(), 3)

    @patch("weather.views.weather_client.get_current")
    def test_favorites_list_includes_current_weather(self, mock_current_weather):
        FavoriteCity.objects.create(user=self.user, city_name="Nairobi")
        mock_current_weather.return_value = weather_payload("Nairobi")

        response = self.client.get("/api/favorites")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["favorites"][0]["city"], "Nairobi")
        self.assertEqual(response.data["favorites"][0]["weather"]["temperature"], 18)
