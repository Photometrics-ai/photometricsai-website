"""
Twilight Processor - GUI-friendly wrapper for twilight_times.py

Provides callback-based processing for yearly twilight calculations.
"""

import csv
from datetime import date, timedelta

import pytz
from timezonefinder import TimezoneFinder

from twilight_times import CSV_HEADER, twilight_row


def generate_twilight_with_progress(
    lat: float,
    lon: float,
    year: int,
    output_path: str,
    progress_callback
) -> dict:
    """
    Generate CSV with nautical twilight times for an entire year.

    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees
        year: Year to calculate for
        output_path: Path to output CSV file
        progress_callback: Function called with (current_day, total_days, timezone_name)

    Returns:
        Statistics dictionary
    """
    # Get timezone from coordinates
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lat=lat, lng=lon)
    if tz_name is None:
        raise ValueError(f"Could not determine timezone for coordinates ({lat}, {lon})")

    tz = pytz.timezone(tz_name)

    # Generate all dates for the year
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    current_date = start_date

    # Count total days
    total_days = (end_date - start_date).days + 1

    stats = {
        'total_days': 0,
        'valid_days': 0,
        'polar_days': 0,
        'timezone': tz_name
    }

    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADER)

        while current_date <= end_date:
            stats['total_days'] += 1

            row, valid = twilight_row(lat, lon, current_date, tz)
            writer.writerow(row)
            if valid:
                stats['valid_days'] += 1
            else:
                stats['polar_days'] += 1

            # Progress callback for each day
            progress_callback(stats['total_days'], total_days, tz_name)

            current_date += timedelta(days=1)

    return stats
