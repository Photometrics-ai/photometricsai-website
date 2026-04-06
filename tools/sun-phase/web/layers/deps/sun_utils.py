"""
Sun Position Utilities - Shared astronomical calculations for sun position tools.

This module provides the core sun position calculation used by both:
- phase_calculator.py (determine twilight phase for timestamped records)
- twilight_times.py (calculate nautical twilight times for a year)

Author: Evari Labs
"""

import math
from datetime import datetime


def sun_position(lat: float, lon: float, year: int, day_of_year: int, hour: float) -> float:
    """
    Calculate sun elevation angle in degrees.

    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees
        year: Year for calculation (affects Julian date)
        day_of_year: Day of year (1-366)
        hour: Hour in UTC as decimal (e.g., 14.5 for 2:30 PM)

    Returns:
        Sun elevation angle in degrees (positive = above horizon)
    """
    lat_rad = math.radians(lat)

    # Julian date calculation
    delta = year - 1949
    leap = delta // 4
    jd = 32916.5 + delta * 365 + leap + day_of_year + hour / 24
    t = jd - 51545

    # Solar position calculations
    mnlong_deg = (280.460 + 0.9856474 * t) % 360
    mnanom_rad = math.radians((357.528 + 0.9856003 * t) % 360)
    eclong = math.radians((mnlong_deg +
                           1.915 * math.sin(mnanom_rad) +
                           0.020 * math.sin(2 * mnanom_rad)) % 360)
    oblqec_rad = math.radians(23.439 - 0.0000004 * t)

    # Right ascension
    num = math.cos(oblqec_rad) * math.sin(eclong)
    den = math.cos(eclong)
    ra_rad = math.atan(num / den)
    if den < 0:
        ra_rad += math.pi
    elif num < 0:
        ra_rad += 2 * math.pi

    # Declination
    dec_rad = math.asin(math.sin(oblqec_rad) * math.sin(eclong))

    # Hour angle
    gmst = (6.697375 + 0.0657098242 * t + hour) % 24
    lmst = (gmst + lon / 15.0) % 24
    lmst_rad = math.radians(15 * lmst)
    ha_rad = lmst_rad - ra_rad
    if ha_rad < -math.pi:
        ha_rad += 2 * math.pi
    if ha_rad > math.pi:
        ha_rad -= 2 * math.pi

    # Elevation
    elev_rad = math.asin(math.sin(dec_rad) * math.sin(lat_rad) +
                         math.cos(dec_rad) * math.cos(lat_rad) * math.cos(ha_rad))

    return math.degrees(elev_rad)
