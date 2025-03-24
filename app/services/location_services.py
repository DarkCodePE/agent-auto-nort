# location/location_services.py
import logging
import os
import requests
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv

# Get Google Maps API key from environment
load_dotenv()
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

logger = logging.getLogger(__name__)


@dataclass
class Plant:
    """Represents a plant location with all relevant details."""
    id: str
    name: str
    address: str
    phone: str
    hours: str
    coordinates: str  # Format: "lat,lng"


# Plant database
PLANTS = {
    "sjl": Plant(
        id="sjl",
        name="PLANTA SJL 2",
        address="Av. El Sol 891 (cruce con Av. Santa Rosa, a 1 cdra. del Penal Lurigancho)",
        phone="908 879 791 / 989 279 922 / 01 715 8727",
        hours="Lunes a Sábado de 7:00am a 9:00pm",
        coordinates="-12.0188,-76.9744"
    ),
    "trapiche": Plant(
        id="trapiche",
        name="PLANTA TRAPICHE",
        address="Av. Alfredo Mendiola Mz. E-6 Lt. 9 (Antes del cruce Panam. Norte con desvío a Trapiche)",
        phone="01 710-9245 / 01 710-9246",
        hours="Lunes a Sábado de 7:00am a 9:00pm",
        coordinates="-11.9511,-77.0603"
    ),
    "carabayllo": Plant(
        id="carabayllo",
        name="PLANTA CARABAYLLO",
        address="Av. Tupac Amaru km. 22 Carretera Lima - Canta (Frente al Paradero San Antonio)",
        phone="908 879 729 / 989 279 929",
        hours="Lunes a Sábado de 7:00am a 9:00pm",
        coordinates="-11.8503,-77.0344"
    ),
    "jicamarca": Plant(
        id="jicamarca",
        name="PLANTA JICAMARCA",
        address="Av. Mar del Norte Mz.C, Lt.4 (Antes del portón)",
        phone="946 309 951 / 989 279 922",
        hours="Lunes a Sábado de 7:00am a 9:00pm",
        coordinates="-11.9350,-76.8954"
    ),
    "chosica": Plant(
        id="chosica",
        name="PLANTA CHOSICA",
        address="Carretera Central Km. 37.5 (Antes del desvío a Santa Eulalia)",
        phone="989 279 927 / 989 279 922",
        hours="Lunes a Sábado de 7:00am a 9:00pm",
        coordinates="-11.9419,-76.7056"
    ),
    "callao1": Plant(
        id="callao1",
        name="PLANTA CALLAO 1",
        address="Av. Néstor Gambeta #8595 (Paradero - Puente Oquendo)",
        phone="946 311 128 / 01 715-1748 / 01 715-1749",
        hours="Lunes a Sábado de 7:00am a 9:00pm",
        coordinates="-11.9167,-77.1117"
    ),
    "callao2": Plant(
        id="callao2",
        name="PLANTA CALLAO 2",
        address="Av. Néstor Gambeta #1160 (Antes del cruce con Morales Duárez)",
        phone="908 879 721 / 01 713-1881",
        hours="Lunes a Sábado de 7:00am a 9:00pm, Domingos: 8:00am - 2:00pm",
        coordinates="-12.0348,-77.1258"
    ),
    "ate": Plant(
        id="ate",
        name="PLANTA ATE",
        address="Av. Separadora Industrial #2631 (Intersección con Av. Huarochirí)",
        phone="960 159 264 / 01 715 3757 / 01 715 3756",
        hours="Lunes a Sábado de 7:00am a 9:00pm, Domingos: 8:00am - 2:00pm",
        coordinates="-12.0544,-76.9439"
    ),
    "ate2": Plant(
        id="ate2",
        name="PLANTA ATE 2",
        address="Av. Asturias 307 - Ate",
        phone="989 279 922 / 960 157 673",
        hours="Lunes a Sábado de 7:00am a 9:00pm",
        coordinates="-12.0262,-76.9183"
    ),
    "naranjal": Plant(
        id="naranjal",
        name="PLANTA NARANJAL",
        address="Las Fraguas #399 esquina con Av. Alfredo Mendiola # 4820 - Independencia",
        phone="017192871 / 908 879 592",
        hours="Lunes a Sábado de 7:00am a 9:00pm",
        coordinates="-11.9803,-77.0600"
    ),
    "sanluis": Plant(
        id="sanluis",
        name="PLANTA SAN LUIS",
        address="Av. Circunvalación #2100 (Frente al Policlínico San Luis)",
        phone="908 879 601 / 989 279 922 / 01 715 6912",
        hours="Lunes a Sábado de 7:00am a 9:00pm, Domingos de 8:00am a 2:00pm",
        coordinates="-12.0786,-76.9765"
    ),
    "atocongo": Plant(
        id="atocongo",
        name="PLANTA ATOCONGO",
        address="Carretera Panamericana Sur km. 11.3 (Frente al Mall del Sur)",
        phone="908 879 597 / 01 714 1183 / 01 714 1182",
        hours="Lunes a Sábado de 7:00am a 9:00pm, Domingos de 8:00am a 2:00pm",
        coordinates="-12.1554,-76.9814"
    ),
    "surco": Plant(
        id="surco",
        name="PLANTA SURCO",
        address="Jr. Catalino Miranda #137 (Frente a la Peña del Carajo)",
        phone="989 279 921 / 01 715 8325 / 01 715 8326",
        hours="Lunes a Sábado de 7:00am a 9:00pm, Domingos de 8:00am a 2:00pm",
        coordinates="-12.1383,-76.9966"
    ),
    "villamaria": Plant(
        id="villamaria",
        name="PLANTA VILLA MARIA DEL TRIUNFO",
        address="Jose Pardo 385, Villa María del Triunfo (a la altura del paradero Ícaros)",
        phone="908 879 787 / 01 717 3010 / 01 717 3011",
        hours="Lunes a Sábado de 7:00am a 9:00pm, Domingos de 8:00am a 2:00pm",
        coordinates="-12.1661,-76.9420"
    ),
    "lurin": Plant(
        id="lurin",
        name="PLANTA LURIN",
        address="Av. Panamericana Sur - Sub Lt. 4 Mz. U - Huertos de Lurín (con calle Los Laureles)",
        phone="989 860 137 / 989 279 922",
        hours="Lunes a Sábado de 7:00am a 9:00pm, Domingos: 8:00am - 2:00pm",
        coordinates="-12.2524,-76.8971"
    )
}


def get_district_coordinates(location: str) -> Tuple[float, float]:
    """
    Get coordinates (latitude, longitude) for a location using Google Maps Geocoding API.

    Args:
        location: A string representing a location (address, district, etc.)

    Returns:
        Tuple of (latitude, longitude) as floats
    """
    try:
        # Append ", Lima, Peru" to ensure we get locations in Lima
        search_location = f"{location}, Lima, Peru"

        # Call Google Maps Geocoding API
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={search_location}&key={GOOGLE_MAPS_API_KEY}"
        response = requests.get(url)
        data = response.json()

        # Check if we got valid results
        if data["status"] == "OK" and data["results"]:
            # Get the first result's coordinates
            result = data["results"][0]
            lat = result["geometry"]["location"]["lat"]
            lng = result["geometry"]["location"]["lng"]

            logger.info(f"Found coordinates for '{location}': {lat}, {lng}")
            return (lat, lng)
        else:
            logger.warning(f"Could not geocode location '{location}'. Status: {data['status']}")
            # Default to central Lima coordinates
            return (-12.0464, -77.0428)

    except Exception as e:
        logger.error(f"Error geocoding location '{location}': {str(e)}")
        # Default to central Lima coordinates as fallback
        return (-12.0464, -77.0428)


def calculate_distances(origin_lat: float, origin_lng: float, plants: List[Plant]) -> List[Dict[str, Any]]:
    """
    Calculate distances from origin to multiple plants using Google Maps Distance Matrix API.

    Args:
        origin_lat: Latitude of origin point
        origin_lng: Longitude of origin point
        plants: List of Plant objects

    Returns:
        List of dictionaries with plant information and distances
    """
    try:
        # Format origin coordinates
        origins = f"{origin_lat},{origin_lng}"

        # Format destinations (all plant coordinates)
        destinations = "|".join([plant.coordinates for plant in plants])

        # Call Google Maps Distance Matrix API
        url = (
            f"https://maps.googleapis.com/maps/api/distancematrix/json"
            f"?origins={origins}&destinations={destinations}"
            f"&mode=driving&language=es&key={GOOGLE_MAPS_API_KEY}"
        )

        response = requests.get(url)
        data = response.json()
        logger.info("Distance Matrix API response: " + str(data))
        # Process results
        results = []

        if data["status"] == "OK" and "rows" in data and data["rows"]:
            elements = data["rows"][0]["elements"]

            for i, (plant, element) in enumerate(zip(plants, elements)):
                if element["status"] == "OK":
                    # Get distance in kilometers and duration in minutes
                    distance_km = element["distance"]["value"] / 1000  # Convert meters to km
                    duration_min = element["duration"]["value"] / 60  # Convert seconds to minutes

                    results.append({
                        "id": plant.id,
                        "name": plant.name,
                        "address": plant.address,
                        "phone": plant.phone,
                        "hours": plant.hours,
                        "distance_km": distance_km,
                        "duration_min": duration_min,
                        "distance_text": element["distance"]["text"],
                        "duration_text": element["duration"]["text"]
                    })
                else:
                    # Fallback to direct distance calculation if API fails for this destination
                    logger.warning(f"Distance Matrix API failed for plant {plant.name}: {element['status']}")

                    # Add placeholder distance
                    results.append({
                        "id": plant.id,
                        "name": plant.name,
                        "address": plant.address,
                        "phone": plant.phone,
                        "hours": plant.hours,
                        "distance_km": 999,  # High distance so it's ranked last
                        "duration_min": 999,
                        "distance_text": "No disponible",
                        "duration_text": "No disponible"
                    })
        else:
            logger.error(f"Distance Matrix API error: {data['status']}")
            # Fallback - just return the plants without distance info
            for plant in plants:
                results.append({
                    "id": plant.id,
                    "name": plant.name,
                    "address": plant.address,
                    "phone": plant.phone,
                    "hours": plant.hours,
                    "distance_km": 999,
                    "duration_min": 999,
                    "distance_text": "No disponible",
                    "duration_text": "No disponible"
                })

        return results

    except Exception as e:
        logger.error(f"Error calculating distances: {str(e)}")
        # Fallback - just return the plants without distance info
        return [
            {
                "id": plant.id,
                "name": plant.name,
                "address": plant.address,
                "phone": plant.phone,
                "hours": plant.hours,
                "distance_km": 999,
                "duration_min": 999,
                "distance_text": "No disponible",
                "duration_text": "No disponible"
            }
            for plant in plants
        ]
