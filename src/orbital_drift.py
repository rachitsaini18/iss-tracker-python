"""
orbital_drift.py
=================

Demonstrates how to analyze long-term changes in the ISS's orbital
elements (inclination, eccentricity, orbital period) over time.

A full analysis requires a series of historical TLEs (e.g. one per day,
from an archive such as Space-Track.org). This module provides:

- A function that reads historical TLE files from a directory, if available
- A fallback that generates representative sample data for demonstration,
  so the plotting and analysis code can be exercised without historical data
"""

import os
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import numpy as np
from skyfield.api import EarthSatellite, load


def load_historical_tles(tle_dir):
    """
    Load historical ISS TLE files from a directory.

    Each file is expected to contain three lines: the satellite name,
    TLE line 1, and TLE line 2. The observation date is taken from the
    filename, expected in the form 'iss_YYYY-MM-DD.txt'.

    Parameters
    ----------
    tle_dir : str
        Path to a directory containing historical TLE files.

    Returns
    -------
    dict
        Dictionary with keys 'dates', 'inclinations', 'eccentricities',
        each a list aligned by index.
    """
    ts = load.timescale()

    dates, inclinations, eccentricities = [], [], []

    if not os.path.isdir(tle_dir):
        return {"dates": [], "inclinations": [], "eccentricities": []}

    for filename in sorted(os.listdir(tle_dir)):
        if not filename.endswith(".txt"):
            continue

        path = os.path.join(tle_dir, filename)
        with open(path, "r") as f:
            lines = [line.strip() for line in f.readlines()]

        if len(lines) < 3:
            continue

        try:
            satellite = EarthSatellite(lines[1], lines[2], lines[0], ts)
            date_str = filename.replace("iss_", "").replace(".txt", "")
            dates.append(datetime.strptime(date_str, "%Y-%m-%d"))
            inclinations.append(satellite.model.inclo * 180.0 / np.pi)
            eccentricities.append(satellite.model.ecco)
        except Exception as e:
            print(f"Skipping {filename}: {e}")

    return {"dates": dates, "inclinations": inclinations, "eccentricities": eccentricities}


def generate_sample_drift_data(days=30, seed=42):
    """
    Generate representative sample orbital-element data for demonstration,
    when no historical TLE archive is available.

    Parameters
    ----------
    days : int
        Number of daily data points to generate.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    dict
        Dictionary with 'dates', 'inclinations', 'eccentricities', 'periods'.
    """
    rng = np.random.default_rng(seed)

    start_date = datetime(2024, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(days)]

    inclinations = 51.64 + rng.uniform(-0.01, 0.01, size=days)
    eccentricities = 0.0002 + rng.uniform(-0.00005, 0.00005, size=days)
    periods = 92.0 + rng.uniform(-0.1, 0.1, size=days)

    return {
        "dates": dates,
        "inclinations": inclinations,
        "eccentricities": eccentricities,
        "periods": periods,
    }


def plot_orbital_drift(drift_data, save_path=None):
    """
    Plot inclination, eccentricity, and orbital period over time.

    Parameters
    ----------
    drift_data : dict
        As returned by generate_sample_drift_data() or
        load_historical_tles() (with a 'periods' key added if available).
    save_path : str, optional
    """
    dates = drift_data["dates"]

    fig, axes = plt.subplots(3, 1, figsize=(12, 9))

    axes[0].plot(dates, drift_data["inclinations"], marker="o", linestyle="-", markersize=4)
    axes[0].set_title("ISS orbital inclination over time")
    axes[0].set_ylabel("Inclination (deg)")
    axes[0].grid(True)

    axes[1].plot(dates, drift_data["eccentricities"], marker="o", linestyle="-",
                  markersize=4, color="orange")
    axes[1].set_title("ISS orbital eccentricity over time")
    axes[1].set_ylabel("Eccentricity")
    axes[1].grid(True)

    if "periods" in drift_data:
        axes[2].plot(dates, drift_data["periods"], marker="o", linestyle="-",
                      markersize=4, color="green")
        axes[2].set_title("ISS orbital period over time")
        axes[2].set_ylabel("Period (min)")
        axes[2].set_xlabel("Date")
        axes[2].grid(True)
    else:
        axes[2].set_visible(False)

    for ax in axes:
        ax.tick_params(axis="x", rotation=45)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300)
        print(f"Saved orbital drift plot to {save_path}")

    plt.show()


if __name__ == "__main__":
    # Use historical TLEs if available, otherwise fall back to sample data
    drift = load_historical_tles("historical_tles")
    if not drift["dates"]:
        print("No historical TLE archive found - using representative sample data.")
        drift = generate_sample_drift_data()

    plot_orbital_drift(drift, save_path="figures/orbital_drift.png")
