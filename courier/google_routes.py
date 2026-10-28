import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class RouteServiceError(Exception):
    """The routing provider could not complete the request."""


class RouteNotFoundError(RouteServiceError):
    """An address or driving route could not be found."""


def _geoapify_get(endpoint, params):
    """Send a request without exposing the API key in error messages."""
    api_key = getattr(settings, "GEOAPIFY_API_KEY", None)

    if not api_key:
        raise RouteServiceError(
            "GEOAPIFY_API_KEY is not configured."
        )

    url = f"https://api.geoapify.com/v1/{endpoint}"

    try:
        response = requests.get(
            url,
            params={
                **params,
                "apiKey": api_key,
            },
            timeout=20,
        )
    except requests.exceptions.Timeout:
        raise RouteServiceError(
            "The location service timed out. Please try again."
        ) from None
    except requests.exceptions.RequestException:
        raise RouteServiceError(
            "Unable to connect to the location service."
        ) from None

    if not response.ok:
        # Do not log response.url: it contains the API key.
        logger.error(
            "Geoapify request failed: endpoint=%s status=%s",
            endpoint,
            response.status_code,
        )

        if response.status_code in (401, 403):
            message = (
                "The location service rejected the API credentials. "
                "Please check the server configuration."
            )
        elif response.status_code == 429:
            message = (
                "The location service request limit has been reached. "
                "Please try again later."
            )
        else:
            message = "Unable to calculate the route right now. Please check the addresses and try again."

        raise RouteServiceError(message)

    try:
        return response.json()
    except ValueError:
        raise RouteServiceError(
            "The location service returned an invalid response."
        ) from None


def _geocode_address(address):
    """Convert a Nigerian address into latitude and longitude."""
    data = _geoapify_get(
        "geocode/search",
        {
            "text": address,
            "format": "json",
            "limit": 1,
            # "filter": "countrycode:ng",
        },
    )

    results = data.get("results", [])

    if not results:
        raise RouteNotFoundError(
            f"No location was found for: {address}"
        )

    location = results[0]

    try:
        return {
            "lat": float(location["lat"]),
            "lon": float(location["lon"]),
            "formatted_address": location.get("formatted", address),
        }
    except (KeyError, TypeError, ValueError):
        raise RouteServiceError(
            "The location service returned invalid coordinates."
        ) from None


def get_route_info(pickup_address, destination_address):
    """Return driving distance and duration between two addresses."""
    if not isinstance(pickup_address, str) or not pickup_address.strip():
        raise RouteNotFoundError("Please provide a pickup address.")

    if (
        not isinstance(destination_address, str)
        or not destination_address.strip()
    ):
        raise RouteNotFoundError("Please provide a destination address.")

    pickup = _geocode_address(pickup_address.strip())
    destination = _geocode_address(destination_address.strip())

    # Geoapify expects latitude,longitude for each waypoint.
    waypoints = (
        f"{pickup['lat']},{pickup['lon']}|"
        f"{destination['lat']},{destination['lon']}"
    )

    data = _geoapify_get(
        "routing",
        {
            "waypoints": waypoints,
            "mode": "drive",
            "units": "metric",
            "format": "geojson",
        },
    )

    features = data.get("features", [])

    if not features:
        raise RouteNotFoundError(
            "No driving route was found between these locations."
        )

    properties = features[0].get("properties", {})

    try:
        distance_meters = float(properties["distance"])
        duration_seconds = float(properties["time"])
    except (KeyError, TypeError, ValueError):
        raise RouteServiceError(
            "The location service returned incomplete route details."
        ) from None

    return {
        "distance_km": round(distance_meters / 1000, 2),
        "duration_minutes": round(duration_seconds / 60, 2),
        "pickup_address": pickup["formatted_address"],
        "destination_address": destination["formatted_address"],
    }


def get_coordinates_from_location(location_name):
    """Convert a location name or address into latitude and longitude."""
    data = _geoapify_get(
        "geocode/search",
        {
            "text": location_name,
            "format": "json",
            "limit": 1,
        },
    )

    results = data.get("results", [])

    if not results:
        raise RouteNotFoundError(
            f"No location was found for: {location_name}"
        )

    location = results[0]

    try:
        return {
            "latitude": float(location["lat"]),
            "longitude": float(location["lon"]),
            "formatted_address": location.get(
                "formatted",
                location_name,
            ),
        }
    except (KeyError, TypeError, ValueError):
        raise RouteServiceError(
            "The location service returned invalid coordinates."
        ) from None