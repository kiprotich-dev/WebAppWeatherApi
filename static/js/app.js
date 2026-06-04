const accessToken = localStorage.getItem("weatherAccessToken");
const currentUser = JSON.parse(localStorage.getItem("weatherUser") || "null");

const searchForm = document.querySelector("#search-form");
const cityInput = document.querySelector("#city-input");
const currentWeatherEl = document.querySelector("#current-weather");
const forecastListEl = document.querySelector("#forecast-list");
const favoritesListEl = document.querySelector("#favorites-list");
const favoriteCountEl = document.querySelector("#favorite-count");
const saveFavoriteButton = document.querySelector("#save-favorite-button");
const globalMessage = document.querySelector("#global-message");
const logoutButton = document.querySelector("#logout-button");
const welcomeHeading = document.querySelector("#welcome-heading");

let activeCity = "";

if (!accessToken) {
    window.location.href = "/login/";
}

if (currentUser?.name) {
    welcomeHeading.textContent = `Dashboard for ${currentUser.name}`;
}

function showGlobalMessage(text, type = "error") {
    globalMessage.textContent = text || "";
    globalMessage.classList.remove("error", "success");
    if (text) {
        globalMessage.classList.add(type);
    }
}

function clearSession() {
    localStorage.removeItem("weatherAccessToken");
    localStorage.removeItem("weatherRefreshToken");
    localStorage.removeItem("weatherUser");
}

function weatherIcon(icon) {
    return icon ? `https://openweathermap.org/img/wn/${icon}@2x.png` : "";
}

function temp(value) {
    if (value === null || value === undefined) {
        return "N/A";
    }
    return `${Math.round(value)} C`;
}

function formatDate(value) {
    return new Intl.DateTimeFormat("en", {
        month: "short",
        day: "numeric",
    }).format(new Date(`${value}T12:00:00`));
}

async function apiFetch(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${localStorage.getItem("weatherAccessToken")}`,
            ...(options.headers || {}),
        },
    });

    let payload = null;
    if (response.status !== 204) {
        payload = await response.json();
    }

    if (response.status === 401) {
        clearSession();
        window.location.href = "/login/";
        throw new Error("Session expired.");
    }

    if (!response.ok) {
        throw new Error(payload?.detail || "Request failed.");
    }

    return payload;
}

function setLoading(isLoading) {
    const searchButton = searchForm.querySelector("button[type='submit']");
    searchButton.disabled = isLoading;
    if (isLoading) {
        currentWeatherEl.textContent = "Loading current weather...";
        forecastListEl.textContent = "Loading forecast...";
        forecastListEl.classList.add("empty-state");
    }
}

function renderCurrentWeather(data) {
    activeCity = data.city;
    saveFavoriteButton.classList.remove("hidden");
    currentWeatherEl.classList.remove("empty-state");
    currentWeatherEl.innerHTML = `
        <div class="weather-summary">
            ${data.icon ? `<img class="weather-icon" src="${weatherIcon(data.icon)}" alt="${data.condition}">` : ""}
            <div>
                <h3>${data.city}${data.country ? `, ${data.country}` : ""}</h3>
                <div class="temperature">${temp(data.temperature)}</div>
                <p>${data.condition || "Condition unavailable"}</p>
            </div>
        </div>
        <div class="meta-grid">
            <div class="meta-item">
                <span class="meta-label">Humidity</span>
                <span class="meta-value">${data.humidity ?? "N/A"}%</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Wind</span>
                <span class="meta-value">${data.wind_speed ?? "N/A"} m/s</span>
            </div>
        </div>
    `;
}

function renderForecast(data) {
    if (!data.forecast?.length) {
        forecastListEl.textContent = "No forecast available.";
        forecastListEl.classList.add("empty-state");
        return;
    }

    forecastListEl.classList.remove("empty-state");
    forecastListEl.innerHTML = data.forecast.map((day) => `
        <article class="forecast-card">
            <h3>${formatDate(day.date)}</h3>
            ${day.icon ? `<img src="${weatherIcon(day.icon)}" alt="${day.condition}">` : ""}
            <p>${day.condition || "Unavailable"}</p>
            <div class="forecast-temp">
                <span>High ${temp(day.high_temperature)}</span>
                <span>Low ${temp(day.low_temperature)}</span>
            </div>
        </article>
    `).join("");
}

async function loadCity(city) {
    const encodedCity = encodeURIComponent(city);
    showGlobalMessage("");
    setLoading(true);

    try {
        const [weather, forecast] = await Promise.all([
            apiFetch(`/api/weather/${encodedCity}`),
            apiFetch(`/api/forecast/${encodedCity}`),
        ]);
        renderCurrentWeather(weather);
        renderForecast(forecast);
    } catch (error) {
        saveFavoriteButton.classList.add("hidden");
        currentWeatherEl.textContent = error.message;
        currentWeatherEl.classList.add("empty-state");
        forecastListEl.textContent = "No forecast loaded.";
        forecastListEl.classList.add("empty-state");
        showGlobalMessage(error.message);
    } finally {
        setLoading(false);
    }
}

async function loadFavorites() {
    try {
        const payload = await apiFetch("/api/favorites");
        favoriteCountEl.textContent = `${payload.count}/3`;

        if (!payload.favorites.length) {
            favoritesListEl.textContent = "No saved cities.";
            favoritesListEl.classList.add("empty-state");
            return;
        }

        favoritesListEl.classList.remove("empty-state");
        favoritesListEl.innerHTML = payload.favorites.map((item) => {
            const weather = item.weather;
            return `
                <article class="favorite-card">
                    <div class="favorite-top">
                        <h3>${item.city}</h3>
                        <button class="remove-button" type="button" data-city="${item.city}">Remove</button>
                    </div>
                    ${
                        weather
                            ? `<div class="favorite-weather">
                                ${weather.icon ? `<img src="${weatherIcon(weather.icon)}" alt="${weather.condition}">` : ""}
                                <span>${temp(weather.temperature)} - ${weather.condition}</span>
                            </div>`
                            : `<p class="message error">${item.error || "Weather unavailable."}</p>`
                    }
                </article>
            `;
        }).join("");
    } catch (error) {
        favoritesListEl.textContent = error.message;
        favoritesListEl.classList.add("empty-state");
    }
}

searchForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const city = cityInput.value.trim();
    if (city) {
        loadCity(city);
    }
});

saveFavoriteButton.addEventListener("click", async () => {
    if (!activeCity) {
        return;
    }
    saveFavoriteButton.disabled = true;
    try {
        await apiFetch("/api/favorites", {
            method: "POST",
            body: JSON.stringify({city: activeCity}),
        });
        showGlobalMessage(`${activeCity} saved.`, "success");
        await loadFavorites();
    } catch (error) {
        showGlobalMessage(error.message);
    } finally {
        saveFavoriteButton.disabled = false;
    }
});

favoritesListEl.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-city]");
    if (!button) {
        return;
    }
    button.disabled = true;
    try {
        await apiFetch(`/api/favorites/${encodeURIComponent(button.dataset.city)}`, {
            method: "DELETE",
        });
        await loadFavorites();
    } catch (error) {
        showGlobalMessage(error.message);
        button.disabled = false;
    }
});

logoutButton.addEventListener("click", () => {
    clearSession();
    window.location.href = "/login/";
});

loadFavorites();
