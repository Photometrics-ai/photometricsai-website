"""
Twilight Times Calculator - Calculate nautical twilight times for a year.

Calculates the daily streetlight operating window (nautical dusk to nautical dawn)
for a given location across an entire year, along with sunrise and sunset times.

Usage:
    python twilight_times.py --lat 36.7456 --lon -93.4712 --year 2026 --output times.csv

Output columns:
    date:                   The date (YYYY-MM-DD)
    streetlights_off_time:  Time when sun rises to -6° (streetlights OFF, morning)
    sunrise:                Time of sunrise (sun crosses 0°, rising)
    sunset:                 Time of sunset (sun crosses 0°, setting)
    streetlights_on_time:   Time when sun drops to -6° (streetlights ON, evening)
    streetlights_on_hours_morning: Hours from midnight to streetlights OFF (decimal)
    streetlights_on_hours_evening: Hours from streetlights ON to midnight (decimal)
    streetlights_on_hours_total:   Sum of morning + evening (decimal, summable)

Author: Evari Labs
"""

import argparse
import csv
import sys
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional

import pytz
from timezonefinder import TimezoneFinder

from sun_utils import sun_position

# Nautical twilight threshold (degrees below horizon)
NAUTICAL_ELEVATION = -6.0


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
    total_minutes = round(normalized * 60)
    hour = (total_minutes // 60) % 24
    minute = total_minutes % 60
    dt_utc = datetime(actual_date.year, actual_date.month, actual_date.day,
                      hour, minute, tzinfo=pytz.UTC)
    return dt_utc.astimezone(tz)


def calculate_nautical_times(lat: float, lon: float, target_date: date, tz: pytz.timezone) -> tuple:
    """
    Calculate nautical dusk/dawn and sunrise/sunset times for a given date.

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

    # Find nautical dawn (next morning, sun rising past -6°)
    dawn_utc = find_sun_elevation_time(
        lat, lon, target_date, NAUTICAL_ELEVATION,
        start_hour=solar_noon_utc + 12.0, end_hour=solar_noon_utc + 24.0, rising=True
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


def generate_yearly_report(lat: float, lon: float, year: int, output_path: str) -> dict:
    """
    Generate CSV with nautical twilight times for an entire year.

    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees
        year: Year to calculate for
        output_path: Path to output CSV file

    Returns:
        Statistics dictionary
    """
    print(f"\nCalculating nautical twilight times for {year}")
    print(f"Location: ({lat}, {lon})")
    print("-" * 50)

    # Get timezone from coordinates
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lat=lat, lng=lon)
    if tz_name is None:
        print(f"Error: Could not determine timezone for coordinates ({lat}, {lon})")
        sys.exit(1)

    tz = pytz.timezone(tz_name)
    print(f"Timezone: {tz_name}")

    # Generate all dates for the year
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    current_date = start_date

    stats = {
        'total_days': 0,
        'valid_days': 0,
        'polar_days': 0
    }

    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['date', 'streetlights_off_time', 'sunrise', 'sunset',
                         'streetlights_on_time', 'streetlights_on_hours_morning',
                         'streetlights_on_hours_evening', 'streetlights_on_hours_total'])

        while current_date <= end_date:
            stats['total_days'] += 1

            dusk, dawn, sunrise, sunset = calculate_nautical_times(lat, lon, current_date, tz)

            if dusk and dawn:
                stats['valid_days'] += 1
                # Per-calendar-date darkness hours
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
                # Polar region - sun doesn't cross nautical threshold
                stats['polar_days'] += 1
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

            # Progress indicator
            if stats['total_days'] % 30 == 0:
                print(f"\rProcessed: {stats['total_days']} days", end='', flush=True)

            current_date += timedelta(days=1)

    print(f"\rProcessed: {stats['total_days']} days")
    print("-" * 50)

    return stats


def print_summary(stats: dict, output_path: str):
    """Print summary statistics."""
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Total days:     {stats['total_days']}")
    print(f"Valid days:     {stats['valid_days']}")
    if stats['polar_days'] > 0:
        print(f"Polar days:     {stats['polar_days']} (no nautical twilight)")
    print(f"\nOutput saved to: {output_path}")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(
        description='Calculate nautical twilight times for a year.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python twilight_times.py --lat 36.7456 --lon -93.4712 --output hartville_mo.csv
    python twilight_times.py --lat 34.0522 --lon -118.2437 --output la_times.csv

Output:
    CSV file with columns: date, streetlights_off_time, sunrise, sunset,
    streetlights_on_time, streetlights_on_duration
    Times are in local timezone (auto-detected from coordinates)

Notes:
    - streetlights_off_time: When sun rises to -6° (streetlights turn OFF, morning)
    - sunrise: When sun crosses 0° (rising)
    - sunset: When sun crosses 0° (setting)
    - streetlights_on_time: When sun drops to -6° (streetlights turn ON, evening)
    - streetlights_on_hours_morning: Hours from midnight to streetlights OFF
    - streetlights_on_hours_evening: Hours from streetlights ON to midnight
    - streetlights_on_hours_total: Sum of morning + evening
    - Polar regions may show N/A for days without nautical twilight
        """
    )

    parser.add_argument('--lat', type=float, required=True,
                        help='Latitude in degrees (-90 to 90)')
    parser.add_argument('--lon', type=float, required=True,
                        help='Longitude in degrees (-180 to 180)')
    parser.add_argument('--year', type=int, default=datetime.now().year,
                        help=f'Year to calculate (default: {datetime.now().year})')
    parser.add_argument('--output', '-o', required=True,
                        help='Output CSV file path')

    args = parser.parse_args()

    # Validate coordinates
    if not (-90 <= args.lat <= 90):
        print(f"Error: Latitude must be between -90 and 90 (got {args.lat})")
        sys.exit(1)
    if not (-180 <= args.lon <= 180):
        print(f"Error: Longitude must be between -180 and 180 (got {args.lon})")
        sys.exit(1)

    # Generate report
    stats = generate_yearly_report(args.lat, args.lon, args.year, args.output)
    print_summary(stats, args.output)


if __name__ == '__main__':
    main()
