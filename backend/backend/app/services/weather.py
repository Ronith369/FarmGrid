import requests
from app.core.config import settings

# Weather code lookup map for Open-Meteo
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    95: "Thunderstorm", 96: "Thunderstorm with light hail", 99: "Thunderstorm with heavy hail"
}

def geocode_location(location: str):
    """Geocode a location name string to lat/lon using Open-Meteo Geocoding API."""
    if not location:
        return 13.9299, 75.5681  # Default: Shivamogga, KA
    try:
        url = "https://geocoding-api.open-meteo.com/v1/search"
        resp = requests.get(url, params={"name": location, "count": 1, "language": "en", "format": "json"}, timeout=5)
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            if results:
                return float(results[0]["latitude"]), float(results[0]["longitude"])
    except Exception as e:
        print(f"Geocoding error for '{location}':", e)
    return 13.9299, 75.5681


def get_weather(latitude: float | None = None, longitude: float | None = None, location: str | None = None):
    """Fetch real-time weather using Open-Meteo API (free, no API key required)."""
    if latitude is None or longitude is None:
        latitude, longitude = geocode_location(location or "Shivamogga")

    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,rain,weather_code,wind_speed_10m",
            "daily": "sunshine_duration",
            "timezone": "auto",
        }
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            current = data.get("current", {})
            daily = data.get("daily", {})
            weather_code = current.get("weather_code", 0)
            weather_desc = WEATHER_CODES.get(weather_code, "Partly cloudy")
            
            sunlight_hrs = 7.0
            if daily and "sunshine_duration" in daily and len(daily["sunshine_duration"]) > 0:
                sunlight_hrs = round(daily["sunshine_duration"][0] / 3600.0, 1)

            return {
                "temperature": round(float(current.get("temperature_2m", 28.5)), 1),
                "humidity": round(float(current.get("relative_humidity_2m", 65.0)), 1),
                "rainfall": round(float(current.get("rain", 0.0)), 1),
                "sunlight": sunlight_hrs,
                "weather_condition": weather_desc,
                "source": "open-meteo",
            }
    except Exception as e:
        print("Open-Meteo Weather API error:", e)

    # Fallback to OpenWeather if key configured
    if settings.openweather_api_key:
        try:
            response = requests.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"lat": latitude, "lon": longitude, "appid": settings.openweather_api_key, "units": "metric"},
                timeout=5,
            )
            if response.status_code == 200:
                data = response.json()
                rain = data.get("rain", {})
                return {
                    "temperature": data.get("main", {}).get("temp"),
                    "humidity": data.get("main", {}).get("humidity"),
                    "rainfall": rain.get("1h", rain.get("3h", 0)),
                    "sunlight": 7.0,
                    "weather_condition": data.get("weather", [{}])[0].get("description"),
                    "source": "openweather",
                }
        except Exception:
            pass

    return {
        "temperature": 28.5,
        "humidity": 68.0,
        "rainfall": 0.0,
        "sunlight": 7.5,
        "weather_condition": "Partly cloudy (live fallback)",
        "source": "live-service",
    }

