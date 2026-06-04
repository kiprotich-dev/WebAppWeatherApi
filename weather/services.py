from collections import Counter, defaultdict

import requests
from django.conf import settings


class WeatherAPIError(Exception):
    def __init__(self, message, status_code=502):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class OpenWeatherClient:
    base_url = "https://api.openweathermap.org/data/2.5"

    def _get(self, endpoint, params):
        api_key = settings.OPENWEATHER_API_KEY
        if not api_key:
            raise WeatherAPIError(
                "OpenWeatherMap API key is not configured.",
                status_code=503,
            )

        query = {
            **params,
            "appid": api_key,
            "units": settings.OPENWEATHER_UNITS,
        }
        url = f"{self.base_url}/{endpoint}"

        try:
            response = requests.get(
                url,
                params=query,
                timeout=settings.OPENWEATHER_TIMEOUT_SECONDS,
            )
        except requests.RequestException:
            raise WeatherAPIError(
                "Weather service is unavailable. Please try again later.",
                status_code=502,
            )

        if response.status_code == 404:
            raise WeatherAPIError("City not found.", status_code=404)
        if response.status_code >= 500:
            raise WeatherAPIError(
                "Weather service is temporarily unavailable.",
                status_code=502,
            )
        if response.status_code >= 400:
            raise WeatherAPIError(
                "Weather service rejected the request.",
                status_code=400,
            )

        try:
            return response.json()
        except ValueError:
            raise WeatherAPIError(
                "Weather service returned an unexpected response.",
                status_code=502,
            )

    def get_current(self, city):
        data = self._get("weather", {"q": city})
        weather = data.get("weather", [{}])[0]
        main = data.get("main", {})
        wind = data.get("wind", {})
        sys = data.get("sys", {})

        return {
            "city": data.get("name", city),
            "country": sys.get("country", ""),
            "temperature": main.get("temp"),
            "condition": weather.get("description", "").title(),
            "humidity": main.get("humidity"),
            "wind_speed": wind.get("speed"),
            "icon": weather.get("icon", ""),
            "units": settings.OPENWEATHER_UNITS,
        }

    def get_forecast(self, city):
        data = self._get("forecast", {"q": city})
        entries = data.get("list", [])
        if not entries:
            raise WeatherAPIError(
                "Forecast data is unavailable for this city.",
                status_code=502,
            )

        grouped = defaultdict(list)
        for entry in entries:
            date = entry.get("dt_txt", "").split(" ")[0]
            if date:
                grouped[date].append(entry)

        forecast = []
        for date in sorted(grouped.keys())[:5]:
            day_entries = grouped[date]
            highs = [entry["main"]["temp_max"] for entry in day_entries if "main" in entry]
            lows = [entry["main"]["temp_min"] for entry in day_entries if "main" in entry]
            conditions = [
                entry.get("weather", [{}])[0].get("description", "").title()
                for entry in day_entries
            ]
            icons = [
                entry.get("weather", [{}])[0].get("icon", "")
                for entry in day_entries
            ]
            forecast.append(
                {
                    "date": date,
                    "high_temperature": max(highs) if highs else None,
                    "low_temperature": min(lows) if lows else None,
                    "condition": Counter(conditions).most_common(1)[0][0],
                    "icon": Counter(icons).most_common(1)[0][0],
                    "units": settings.OPENWEATHER_UNITS,
                }
            )

        city_info = data.get("city", {})
        return {
            "city": city_info.get("name", city),
            "country": city_info.get("country", ""),
            "forecast": forecast,
        }


weather_client = OpenWeatherClient()
