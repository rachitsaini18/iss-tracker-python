"""
ground_track.py
================

Plot the ISS ground track (the path of its sub-point over the Earth's
surface) for a given time window, optionally marking an observer location.
"""

from datetime import timedelta

import matplotlib.pyplot as plt
from skyfield.api import Topos

from iss_tracker import load_iss_satellite


def plot_ground_track(satellite, ts, minutes_ahead=120,
                       observer_location=None, save_path=None):
    """
    Plot the ISS ground track for the next `minutes_ahead` minutes.

    Parameters
    ----------
    satellite : EarthSatellite
    ts : skyfield.timelib.Timescale
    minutes_ahead : int
        Length of the prediction window, in minutes.
    observer_location : Topos, optional
        If provided, the observer's location is marked on the plot.
    save_path : str, optional
        If provided, the figure is saved to this path.
    """
    t0 = ts.now()
    times = ts.utc([
        t0.utc_datetime() + timedelta(minutes=i)
        for i in range(0, minutes_ahead + 1)
    ])

    geocentric = satellite.at(times)
    subpoint = geocentric.subpoint()
    latitudes = subpoint.latitude.degrees
    longitudes = subpoint.longitude.degrees

    plt.figure(figsize=(12, 6))

    plt.axhline(y=0, color="lightgray", linestyle="-", alpha=0.5)
    plt.axvline(x=0, color="lightgray", linestyle="-", alpha=0.5)
    for lat in (-60, -30, 30, 60):
        plt.axhline(y=lat, color="lightgray", linestyle="--", alpha=0.3)
    for lon in (-120, -60, 60, 120):
        plt.axvline(x=lon, color="lightgray", linestyle="--", alpha=0.3)

    plt.plot(longitudes, latitudes, "r-", linewidth=2, label="ISS ground track")
    plt.scatter(longitudes[0], latitudes[0], color="green", s=100,
                 marker="o", label="Current position", zorder=5)
    plt.scatter(longitudes[-1], latitudes[-1], color="blue", s=100,
                 marker="s", label=f"Position in {minutes_ahead} min", zorder=5)

    if observer_location is not None:
        plt.scatter(observer_location.longitude.degrees,
                     observer_location.latitude.degrees,
                     color="orange", s=150, marker="*",
                     label="Observer location", zorder=5)

    plt.xlim(-180, 180)
    plt.ylim(-90, 90)
    plt.xlabel("Longitude (deg)")
    plt.ylabel("Latitude (deg)")
    plt.title(f"ISS ground track - next {minutes_ahead} minutes "
              f"(from {t0.utc_datetime().strftime('%Y-%m-%d %H:%M:%S UTC')})")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.gca().set_aspect("equal", adjustable="box")
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300)
        print(f"Saved ground track plot to {save_path}")

    plt.show()


if __name__ == "__main__":
    satellite, ts = load_iss_satellite()

    if satellite:
        observer = Topos(latitude_degrees=28.6139, longitude_degrees=77.2090)  # Delhi
        plot_ground_track(satellite, ts, minutes_ahead=90,
                           observer_location=observer,
                           save_path="figures/iss_ground_track.png")
    else:
        print("Could not load ISS satellite data.")
