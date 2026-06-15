"""
iss_tracker.py
==============

Core utilities for tracking the International Space Station (ISS) using
Skyfield and live Two-Line Element (TLE) data from CelesTrak.

This module provides the foundational building blocks used by the other
scripts in this project:

- fetch_iss_tle(): retrieve the latest TLE for the ISS
- load_iss_satellite(): build a Skyfield EarthSatellite object from the TLE
- get_current_position(): report the ISS's current sub-point and altitude
"""

from datetime import datetime

import requests
from skyfield.api import EarthSatellite, load


CELESTRAK_URL = "https://celestrak.org/NORAD/elements/stations.txt"


def fetch_iss_tle():
    """
    Fetch the current Two-Line Element (TLE) data for the ISS from CelesTrak.

    Returns
    -------
    list[str] | None
        A list of three strings [name, line1, line2] if successful,
        otherwise None.
    """
    try:
        response = requests.get(CELESTRAK_URL, timeout=15)
        response.raise_for_status()

        lines = response.text.strip().split("\n")

        for i in range(0, len(lines) - 2, 3):
            if "ISS" in lines[i].upper() and "ZARYA" in lines[i].upper():
                name = lines[i].strip()
                line1 = lines[i + 1].strip()
                line2 = lines[i + 2].strip()
                return [name, line1, line2]

        print("ISS TLE data not found in response.")
        return None

    except requests.RequestException as e:
        print(f"Error fetching ISS TLE data: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error while fetching TLE data: {e}")
        return None


def load_iss_satellite(ts=None):
    """
    Fetch the latest ISS TLE and return a Skyfield EarthSatellite object.

    Parameters
    ----------
    ts : skyfield.timelib.Timescale, optional
        A Skyfield timescale object. If not provided, one is created.

    Returns
    -------
    tuple[EarthSatellite | None, Timescale]
        The satellite object (or None if loading failed) and the
        timescale used to create it.
    """
    if ts is None:
        ts = load.timescale()

    tle = fetch_iss_tle()
    if not tle:
        return None, ts

    name, line1, line2 = tle
    satellite = EarthSatellite(line1, line2, name, ts)
    print(f"Loaded ISS satellite data: {name}")
    return satellite, ts


def get_current_position(satellite, ts):
    """
    Get the ISS's current geographic sub-point and altitude.

    Parameters
    ----------
    satellite : EarthSatellite
    ts : skyfield.timelib.Timescale

    Returns
    -------
    dict
        latitude (deg), longitude (deg), altitude_km, and the UTC
        timestamp of the observation.
    """
    t = ts.now()
    geocentric = satellite.at(t)
    subpoint = geocentric.subpoint()

    return {
        "latitude": subpoint.latitude.degrees,
        "longitude": subpoint.longitude.degrees,
        "altitude_km": subpoint.elevation.km,
        "timestamp_utc": t.utc_datetime(),
    }


if __name__ == "__main__":
    iss, ts = load_iss_satellite()
    if iss:
        position = get_current_position(iss, ts)
        print("\nCurrent ISS position:")
        print(f"  Latitude:  {position['latitude']:.4f} deg")
        print(f"  Longitude: {position['longitude']:.4f} deg")
        print(f"  Altitude:  {position['altitude_km']:.1f} km")
        print(f"  Time (UTC): {position['timestamp_utc'].strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("Could not load ISS satellite data.")
