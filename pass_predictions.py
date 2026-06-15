"""
pass_predictions.py
====================

Predict ISS pass times (rise, culmination, set) over one or more
observer locations using Skyfield.

Includes:
- calculate_passes(): pass events for a single location
- predict_passes_for_locations(): pass events for multiple locations,
  tabulated with pandas
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytz
from skyfield.api import Topos

from iss_tracker import load_iss_satellite


def calculate_passes(satellite, ts, latitude, longitude, days_ahead=2,
                      min_altitude_deg=10.0, timezone="Asia/Kolkata"):
    """
    Calculate ISS pass events (rise, culmination, set) for a single
    observer location.

    Parameters
    ----------
    satellite : EarthSatellite
    ts : skyfield.timelib.Timescale
    latitude, longitude : float
        Observer coordinates in degrees.
    days_ahead : int
        Number of days ahead to search for passes.
    min_altitude_deg : float
        Minimum elevation above the horizon to count as a visible pass.
    timezone : str
        IANA timezone name used to convert event times for display.

    Returns
    -------
    list[dict]
        One dict per completed pass, with rise/culmination/set times,
        peak altitude, and duration.
    """
    observer = Topos(latitude_degrees=latitude, longitude_degrees=longitude)

    t0 = ts.now()
    t1 = ts.utc(t0.utc_datetime() + timedelta(days=days_ahead))

    t, events = satellite.find_events(observer, t0, t1, altitude_degrees=min_altitude_deg)

    if len(events) == 0:
        return []

    tz = pytz.timezone(timezone)
    passes = []
    current = {}

    for ti, event in zip(t, events):
        name = ("rise", "culmination", "set")[event]
        local_time = ti.astimezone(tz)

        if name == "rise":
            current = {"rise_time": local_time}
        elif name == "culmination" and "rise_time" in current:
            topocentric = observer.at(ti).observe(satellite)
            alt, az, _ = topocentric.altaz()
            current["culmination_time"] = local_time
            current["max_altitude_deg"] = round(alt.degrees, 1)
            current["azimuth_deg"] = round(az.degrees, 0)
        elif name == "set" and "rise_time" in current and "culmination_time" in current:
            current["set_time"] = local_time
            duration = (current["set_time"] - current["rise_time"]).total_seconds() / 60
            current["duration_min"] = round(duration, 2)
            passes.append(current)
            current = {}

    return passes


def predict_passes_for_locations(satellite, ts, locations, days_ahead=1,
                                  min_altitude_deg=10.0):
    """
    Predict and tabulate ISS passes for multiple locations.

    Parameters
    ----------
    satellite : EarthSatellite
    ts : skyfield.timelib.Timescale
    locations : list[dict]
        Each dict must have 'name', 'latitude', 'longitude', and
        optionally 'timezone' (defaults to 'Asia/Kolkata').
    days_ahead : int
    min_altitude_deg : float

    Returns
    -------
    pandas.DataFrame
        One row per pass, including the location name.
    """
    rows = []

    for loc in locations:
        timezone = loc.get("timezone", "Asia/Kolkata")
        passes = calculate_passes(
            satellite, ts,
            latitude=loc["latitude"],
            longitude=loc["longitude"],
            days_ahead=days_ahead,
            min_altitude_deg=min_altitude_deg,
            timezone=timezone,
        )

        if not passes:
            rows.append({
                "Location": loc["name"],
                "Rise Time": "No pass",
                "Culmination": "No pass",
                "Set Time": "No pass",
                "Duration (min)": "N/A",
                "Peak Altitude (deg)": "N/A",
            })
            continue

        for p in passes:
            rows.append({
                "Location": loc["name"],
                "Rise Time": p["rise_time"].strftime("%Y-%m-%d %H:%M:%S %Z"),
                "Culmination": p["culmination_time"].strftime("%Y-%m-%d %H:%M:%S %Z"),
                "Set Time": p["set_time"].strftime("%Y-%m-%d %H:%M:%S %Z"),
                "Duration (min)": p["duration_min"],
                "Peak Altitude (deg)": p["max_altitude_deg"],
            })

    return pd.DataFrame(rows)


EXAMPLE_LOCATIONS = [
    {"name": "Delhi, India", "latitude": 28.6139, "longitude": 77.2090, "timezone": "Asia/Kolkata"},
    {"name": "Bengaluru, India", "latitude": 12.9716, "longitude": 77.5946, "timezone": "Asia/Kolkata"},
    {"name": "New York, USA", "latitude": 40.7128, "longitude": -74.0060, "timezone": "America/New_York"},
    {"name": "London, UK", "latitude": 51.5074, "longitude": -0.1278, "timezone": "Europe/London"},
    {"name": "Sydney, Australia", "latitude": -33.8688, "longitude": 151.2093, "timezone": "Australia/Sydney"},
]


if __name__ == "__main__":
    satellite, ts = load_iss_satellite()

    if satellite:
        df = predict_passes_for_locations(satellite, ts, EXAMPLE_LOCATIONS, days_ahead=2)
        print("\nISS pass predictions:")
        print(df.to_string(index=False))
    else:
        print("Could not load ISS satellite data.")
