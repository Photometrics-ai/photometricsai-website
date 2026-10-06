"""
Twilight Core - Calculation logic for Lambda use.

Mirrors the calculation functions in tools/sun-phase/twilight_times.py
(find_sun_elevation_time, _utc_hour_to_local, calculate_nautical_times,
streetlight_hours, twilight_row, CSV_HEADER) without CLI/argparse/file I/O.
Keep them identical: tools/sun-phase/tests/test_twilight.py enforces it.
"""

import csv
import io
from datetime import datetime, date, time, timedelta
from typing import Optional

import pytz
from timezonefinder import TimezoneFinder

from sun_utils import sun_position

NAUTICAL_ELEVATION = -6.0

CSV_HEADER = ['date', 'streetlights_off_time', 'sunrise', 'sunset',
              'streetlights_on_time', 'streetlights_on_hours_morning',
              'streetlights_on_hours_evening', 'streetlights_on_hours_total']


def find_sun_elevation_time(
    lat: float,
    lon: float,
    target_date: date,
    target_elevation: float,
    start_hour: float,
    end_hour: float,
    rising: bool = True
) -> Optional[float]:
    """
    Binary search to find when sun reaches target elevation.

    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees
        target_date: The date to calculate for
        target_elevation: Target sun elevation in degrees
        start_hour: Start of search range (UTC decimal hours, can exceed 24 for next day)
        end_hour: End of search range (UTC decimal hours, can exceed 24 for next day)
        rising: True if looking for sun rising past threshold, False for setting

    Returns:
        Hour (UTC decimal) when sun reaches target elevation, or None if not found
    """
    year = target_date.year

    def get_elevation(hour):
        """Get sun elevation, handling hours >= 24 as next day."""
        if hour >= 24:
            next_day = target_date + timedelta(days=1)
            return sun_position(lat, lon, year, next_day.timetuple().tm_yday, hour - 24)
        else:
            return sun_position(lat, lon, year, target_date.timetuple().tm_yday, hour)

    # Check if target elevation is reached within the range
    start_elev = get_elevation(start_hour)
    end_elev = get_elevation(end_hour)

    if rising:
        # Sun should be below target at start, above at end
        if start_elev >= target_elevation or end_elev <= target_elevation:
            return None
    else:
        # Sun should be above target at start, below at end
        if start_elev <= target_elevation or end_elev >= target_elevation:
            return None

    # Binary search
    tolerance = 0.0001  # About 0.36 seconds precision
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


def _utc_hour_to_local(utc_hour: float, target_date: date, tz: pytz.timezone) -> Optional[datetime]:
    """Convert a UTC decimal hour to a local datetime, handling day wraparound."""
    if utc_hour is None:
        return None
    days_offset = int(utc_hour // 24)
    normalized = utc_hour % 24
    actual_date = target_date + timedelta(days=days_offset)
    # Add minutes as a timedelta so rounding up to 24:00 rolls into the next day
    total_minutes = round(normalized * 60)
    dt_utc = (datetime(actual_date.year, actual_date.month, actual_date.day, tzinfo=pytz.UTC)
              + timedelta(minutes=total_minutes))
    return dt_utc.astimezone(tz)


def calculate_nautical_times(lat: float, lon: float, target_date: date, tz: pytz.timezone) -> tuple:
    """
    Calculate nautical dusk/dawn and sunrise/sunset times for a given date.

    All four times fall on target_date: dawn and sunrise are that morning,
    sunset and dusk are that evening.

    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees
        target_date: The date to calculate for
        tz: Local timezone

    Returns:
        Tuple of (dusk_local, dawn_local, sunrise_local, sunset_local) as datetime objects.
        Any value may be None for polar regions where sun doesn't cross threshold.
    """
    # Get UTC offset from timezone to estimate search windows
    local_noon = tz.localize(datetime(target_date.year, target_date.month, target_date.day, 12, 0))
    utc_offset_hours = local_noon.utcoffset().total_seconds() / 3600

    # Solar noon in UTC (when local time is ~12:00)
    solar_noon_utc = 12.0 - utc_offset_hours

    # Find nautical dusk (evening, sun setting past -6°)
    dusk_utc = find_sun_elevation_time(
        lat, lon, target_date, NAUTICAL_ELEVATION,
        start_hour=solar_noon_utc, end_hour=solar_noon_utc + 12.0, rising=False
    )

    # Find nautical dawn (same morning, sun rising past -6°)
    dawn_utc = find_sun_elevation_time(
        lat, lon, target_date, NAUTICAL_ELEVATION,
        start_hour=solar_noon_utc - 12.0, end_hour=solar_noon_utc, rising=True
    )

    # Find sunrise (morning, sun rising past 0°)
    sunrise_utc = find_sun_elevation_time(
        lat, lon, target_date, 0.0,
        start_hour=solar_noon_utc - 12.0, end_hour=solar_noon_utc, rising=True
    )

    # Find sunset (evening, sun setting past 0°)
    sunset_utc = find_sun_elevation_time(
        lat, lon, target_date, 0.0,
        start_hour=solar_noon_utc, end_hour=solar_noon_utc + 12.0, rising=False
    )

    dusk_local = _utc_hour_to_local(dusk_utc, target_date, tz)
    dawn_local = _utc_hour_to_local(dawn_utc, target_date, tz)
    sunrise_local = _utc_hour_to_local(sunrise_utc, target_date, tz)
    sunset_local = _utc_hour_to_local(sunset_utc, target_date, tz)

    return dusk_local, dawn_local, sunrise_local, sunset_local


def streetlight_hours(dusk: datetime, dawn: datetime, target_date: date, tz: pytz.timezone) -> tuple:
    """
    Hours streetlights are on during one calendar date, as elapsed time.

    Measured in UTC so a clock change (DST) between local midnight and dawn,
    or between dusk and the next midnight, doesn't skew the result.

    Returns:
        Tuple of (morning, evening, total): local midnight to dawn,
        dusk to the next local midnight, and their sum.
    """
    midnight = tz.localize(datetime.combine(target_date, time.min))
    next_midnight = tz.localize(datetime.combine(target_date + timedelta(days=1), time.min))

    def elapsed(start, end):
        return (end.astimezone(pytz.UTC) - start.astimezone(pytz.UTC)).total_seconds() / 3600

    morning = elapsed(midnight, dawn)
    evening = elapsed(dusk, next_midnight)
    return morning, evening, morning + evening


def twilight_row(lat: float, lon: float, target_date: date, tz: pytz.timezone) -> tuple:
    """
    Build one CSV row (matching CSV_HEADER) for a date.

    Returns:
        Tuple of (row, valid). valid is False for polar days where the sun
        doesn't cross the nautical threshold; those rows are all N/A.
    """
    dusk, dawn, sunrise, sunset = calculate_nautical_times(lat, lon, target_date, tz)

    if not (dusk and dawn):
        return [target_date.isoformat()] + ['N/A'] * 7, False

    morning_hours, evening_hours, total_hours = streetlight_hours(dusk, dawn, target_date, tz)
    return [
        target_date.isoformat(),
        dawn.strftime('%H:%M'),
        sunrise.strftime('%H:%M') if sunrise else 'N/A',
        sunset.strftime('%H:%M') if sunset else 'N/A',
        dusk.strftime('%H:%M'),
        f'{morning_hours:.2f}',
        f'{evening_hours:.2f}',
        f'{total_hours:.2f}'
    ], True


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
    writer.writerow(CSV_HEADER)

    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    current_date = start_date

    while current_date <= end_date:
        row, _valid = twilight_row(lat, lon, current_date, tz)
        writer.writerow(row)
        current_date += timedelta(days=1)

    return output.getvalue()
