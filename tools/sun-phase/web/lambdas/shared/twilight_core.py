"""
Twilight Core - Extracted calculation logic for Lambda use.

Contains the pure calculation functions from twilight_times.py,
without CLI/argparse/file I/O dependencies.
"""

import csv
import io
from datetime import datetime, date, timedelta

import pytz
from timezonefinder import TimezoneFinder

from sun_utils import sun_position

NAUTICAL_ELEVATION = -6.0


def find_sun_elevation_time(lat, lon, target_date, target_elevation,
                            start_hour, end_hour, rising=True):
    """
    Binary search to find when sun reaches target elevation.

    Returns:
        Hour (UTC decimal) when sun reaches target elevation, or None if not found
    """
    year = target_date.year

    def get_elevation(hour):
        if hour >= 24:
            next_day = target_date + timedelta(days=1)
            return sun_position(lat, lon, year, next_day.timetuple().tm_yday, hour - 24)
        else:
            return sun_position(lat, lon, year, target_date.timetuple().tm_yday, hour)

    start_elev = get_elevation(start_hour)
    end_elev = get_elevation(end_hour)

    if rising:
        if start_elev >= target_elevation or end_elev <= target_elevation:
            return None
    else:
        if start_elev <= target_elevation or end_elev >= target_elevation:
            return None

    tolerance = 0.0001
    low, high = start_hour, end_hour
    while (high - low) > tolerance:
        mid = (low + high) / 2
        mid_elev = get_elevation(mid)

        if rising:
            if mid_elev < target_elevation:
                low = mid
            else:
                high = mid
        else:
            if mid_elev > target_elevation:
                low = mid
            else:
                high = mid

    return (low + high) / 2


def _utc_hour_to_local(utc_hour, target_date, tz):
    """Convert a UTC decimal hour to a local datetime, handling day wraparound."""
    if utc_hour is None:
        return None
    days_offset = int(utc_hour // 24)
    normalized = utc_hour % 24
    actual_date = target_date + timedelta(days=days_offset)
    total_minutes = round(normalized * 60)
    hour = (total_minutes // 60) % 24
    minute = total_minutes % 60
    dt_utc = datetime(actual_date.year, actual_date.month, actual_date.day,
                      hour, minute, tzinfo=pytz.UTC)
    return dt_utc.astimezone(tz)


def calculate_nautical_times(lat, lon, target_date, tz):
    """
    Calculate nautical dusk/dawn and sunrise/sunset times for a given date.

    Returns:
        Tuple of (dusk_local, dawn_local, sunrise_local, sunset_local) as datetime objects.
        Any value may be None for polar regions.
    """
    local_noon = tz.localize(datetime(target_date.year, target_date.month, target_date.day, 12, 0))
    utc_offset_hours = local_noon.utcoffset().total_seconds() / 3600
    solar_noon_utc = 12.0 - utc_offset_hours

    dusk_utc = find_sun_elevation_time(
        lat, lon, target_date, NAUTICAL_ELEVATION,
        start_hour=solar_noon_utc, end_hour=solar_noon_utc + 12.0, rising=False
    )

    dawn_utc = find_sun_elevation_time(
        lat, lon, target_date, NAUTICAL_ELEVATION,
        start_hour=solar_noon_utc + 12.0, end_hour=solar_noon_utc + 24.0, rising=True
    )

    sunrise_utc = find_sun_elevation_time(
        lat, lon, target_date, 0.0,
        start_hour=solar_noon_utc - 12.0, end_hour=solar_noon_utc, rising=True
    )

    sunset_utc = find_sun_elevation_time(
        lat, lon, target_date, 0.0,
        start_hour=solar_noon_utc, end_hour=solar_noon_utc + 12.0, rising=False
    )

    return (
        _utc_hour_to_local(dusk_utc, target_date, tz),
        _utc_hour_to_local(dawn_utc, target_date, tz),
        _utc_hour_to_local(sunrise_utc, target_date, tz),
        _utc_hour_to_local(sunset_utc, target_date, tz),
    )


def generate_twilight_csv(lat, lon, year):
    """
    Generate CSV string with nautical twilight times for an entire year.

    Returns:
        CSV content as string
    """
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lat=lat, lng=lon)
    if tz_name is None:
        raise ValueError(f"Could not determine timezone for coordinates ({lat}, {lon})")

    tz = pytz.timezone(tz_name)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['date', 'streetlights_off_time', 'sunrise', 'sunset',
                     'streetlights_on_time', 'streetlights_on_hours_morning',
                     'streetlights_on_hours_evening', 'streetlights_on_hours_total'])

    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    current_date = start_date

    while current_date <= end_date:
        dusk, dawn, sunrise, sunset = calculate_nautical_times(lat, lon, current_date, tz)

        if dusk and dawn:
            morning_hours = dawn.hour + dawn.minute / 60
            evening_hours = 24 - (dusk.hour + dusk.minute / 60)
            total_hours = morning_hours + evening_hours
            writer.writerow([
                current_date.isoformat(),
                dawn.strftime('%H:%M'),
                sunrise.strftime('%H:%M') if sunrise else 'N/A',
                sunset.strftime('%H:%M') if sunset else 'N/A',
                dusk.strftime('%H:%M'),
                f'{morning_hours:.2f}',
                f'{evening_hours:.2f}',
                f'{total_hours:.2f}'
            ])
        else:
            writer.writerow([
                current_date.isoformat(),
                'N/A',
                'N/A',
                'N/A',
                'N/A',
                'N/A',
                'N/A',
                'N/A'
            ])

        current_date += timedelta(days=1)

    return output.getvalue()
