# Weather Dashboard

A Django full-stack take-home project for JWT authentication, OpenWeatherMap weather search, 5-day forecasts, and per-user favorite cities.

## Features

- Register with name, email, and password
- Login with email and password
- JWT-secured API endpoints
- Current weather by city
- 5-day forecast by city
- Up to 3 favorite cities per user
- Current weather shown for saved favorites
- Responsive Django template frontend
- Tests for auth, protected access, and favorites

## Tech Stack

- Django
- Django REST Framework
- djangorestframework-simplejwt
- SQLite for local persistence
- Vanilla JavaScript frontend
- OpenWeatherMap Current Weather and Forecast APIs

## Setup in PyCharm

1. Open this folder in PyCharm:

   `C:\Users\vinsn\Documents\webAppOpenAi`

2. Create a virtual environment, or use the one created in `.venv` if present.

3. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env`, then set your OpenWeatherMap API key:

   ```powershell
   OPENWEATHER_API_KEY=your-openweathermap-api-key
   ```

   PyCharm users can add these variables in `Run > Edit Configurations > Environment variables`.

5. Run migrations:

   ```powershell
   python manage.py migrate
   ```

6. Start the development server:

   ```powershell
   python manage.py runserver
   ```

7. Open:

   `http://127.0.0.1:8000/`

## Environment Variables

- `DJANGO_SECRET_KEY`: Django secret key. A development fallback is provided.
- `DJANGO_DEBUG`: `True` or `False`.
- `DJANGO_ALLOWED_HOSTS`: Comma-separated host list. Defaults to `127.0.0.1,localhost`.
- `OPENWEATHER_API_KEY`: Required for live weather and forecast requests.
- `OPENWEATHER_UNITS`: Optional. Defaults to `metric`.
- `OPENWEATHER_TIMEOUT_SECONDS`: Optional. Defaults to `8`.

## API Endpoints

All endpoints except register and login require a bearer token:

```text
Authorization: Bearer <access_token>
```

| Method | Endpoint | Body |
| --- | --- | --- |
| POST | `/api/auth/register` | `{ "name": "...", "email": "...", "password": "..." }` |
| POST | `/api/auth/login` | `{ "email": "...", "password": "..." }` |
| GET | `/api/weather/{city}` | None |
| GET | `/api/forecast/{city}` | None |
| POST | `/api/favorites` | `{ "city": "Nairobi" }` |
| GET | `/api/favorites` | None |
| DELETE | `/api/favorites/{city}` | None |

## Tests

Run:

```powershell
python manage.py test
```

## Postman

Import the collection at:

`postman/Weather_Dashboard.postman_collection.json`

The collection includes variables for `base_url`, `access_token`, `refresh_token`, and `city`. Register or login first; the scripts store JWT tokens automatically.

## Assumptions

- City searches use OpenWeatherMap city-name lookup through the `q` parameter.
- Forecasts are grouped from OpenWeatherMap 3-hour forecast entries into the first 5 available dates.
- Favorite city names are stored per user and validated through the current weather endpoint before saving.
- The frontend stores JWT tokens in `localStorage` for this take-home implementation.
