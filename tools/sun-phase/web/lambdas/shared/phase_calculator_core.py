"""
Phase Calculator Core - Extracted calculation logic for Lambda use.

Contains the pure calculation functions from phase_calculator.py,
without CLI/argparse/file I/O dependencies.
"""

from datetime import datetime

import pandas as pd
import pytz
from timezonefinder import TimezoneFinder

from sun_utils import sun_position


def get_twilight_phase(sun_elevation: float, is_dawn: bool = True) -> str:
    """
    Determine twilight phase based on sun elevation angle.

    Streetlights typically turn ON at nautical twilight (sun 6 below horizon).
    """
    if sun_elevation > 0:
        return "Day"
    elif -6 <= sun_elevation <= 0:
        return "Civil Dawn" if is_dawn else "Civil Dusk"
    elif -12 <= sun_elevation < -6:
        return "Nautical Dawn" if is_dawn else "Nautical Dusk"
    elif -18 <= sun_elevation < -12:
        return "Astronomical Dawn" if is_dawn else "Astronomical Dusk"
    else:
        return "Night"


def is_streetlights_on(phase: str) -> bool:
    """Returns True if streetlights would be ON during this phase."""
    return phase in ("Nautical Dawn", "Nautical Dusk",
                     "Astronomical Dawn", "Astronomical Dusk", "Night")


def calculate_phase_for_row(lat, lon, date_val, time_val, tf: TimezoneFinder) -> tuple:
    """
    Calculate sun elevation and twilight phase for a single record.

    Returns:
        Tuple of (sun_elevation, twilight_phase, streetlights_on, error_message)
    """
    try:
        if pd.isna(lat) or pd.isna(lon):
            return None, "Error: Missing coordinates", False, "Missing lat/lon"

        lat = float(lat)
        lon = float(lon)

        if lat == 0 and lon == 0:
            return None, "Null Island", False, "Null Island (0,0)"

        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return None, "Error: Out of bounds", False, "Coordinates out of bounds"

        if pd.isna(date_val) or pd.isna(time_val):
            return None, "Error: Missing date/time", False, "Missing date/time"

        # Handle different date formats
        if isinstance(date_val, str):
            date_formats = [
                "%Y %b %d %H:%M:%S %p",
                "%Y %b %d",
                "%m/%d/%Y",
                "%Y-%m-%d",
                "%d/%m/%Y",
                "%m/%d/%Y %H:%M:%S"
            ]
            for fmt in date_formats:
                try:
                    date_obj = datetime.strptime(date_val.strip(), fmt)
                    break
                except ValueError:
                    continue
            else:
                return None, "Error: Date parse failed", False, f"Could not parse date: {date_val}"
        elif isinstance(date_val, pd.Timestamp):
            date_obj = date_val.to_pydatetime()
        else:
            date_obj = date_val

        # Handle time - military time as integer (e.g., 1430 = 2:30 PM)
        if isinstance(time_val, (int, float)):
            time_int = int(time_val)
            hour = time_int // 100
            minute = time_int % 100
        elif isinstance(time_val, str):
            time_int = int(time_val)
            hour = time_int // 100
            minute = time_int % 100
        else:
            hour = time_val.hour
            minute = time_val.minute

        datetime_obj = datetime(date_obj.year, date_obj.month, date_obj.day, hour, minute)

        time_zone = tf.timezone_at(lat=lat, lng=lon)
        if time_zone is None:
            return None, "Error: Timezone not found", False, "Could not determine timezone"

        local_tz = pytz.timezone(time_zone)
        local_time = local_tz.localize(datetime_obj)
        utc_time = local_time.astimezone(pytz.utc)

        day_of_year = utc_time.timetuple().tm_yday
        hour_decimal = utc_time.hour + utc_time.minute / 60.0 + utc_time.second / 3600.0

        sun_elev = sun_position(lat, lon, utc_time.year, day_of_year, hour_decimal)

        is_dawn = hour < 12
        phase = get_twilight_phase(sun_elev, is_dawn)
        lights_on = is_streetlights_on(phase)

        return sun_elev, phase, lights_on, None

    except Exception as e:
        return None, "Error", False, str(e)


def auto_detect_columns(columns):
    """
    Attempt to auto-detect common column names for lat/lon/date/time.

    Supports two modes:
    - "combined": single date + military time columns (default)
    - "separate": individual year/month/day/hour/minute columns (e.g. FARS data)

    Returns:
        Dict with 'mode' and detected column names for each field, or None
    """
    detected = {
        'mode': 'combined',
        'lat': None, 'lon': None,
        'date': None, 'time': None,
        'year': None, 'month': None, 'day_of_month': None,
        'hour': None, 'minute': None
    }

    combined_patterns = {
        'lat': ['lat', 'latitude', 'y', 'lat_'],
        'lon': ['lon', 'lng', 'longitude', 'long', 'x', 'lon_'],
        'date': ['date', 'dt', 'date_'],
        'time': ['time', 'tm', 'time_']
    }

    separate_patterns = {
        'year': ['year'],
        'month': ['month', 'monthname'],
        'day_of_month': ['day', 'day_of_month'],
        'hour': ['hour'],
        'minute': ['minute']
    }

    columns_lower = {col.lower().strip(): col for col in columns}

    # Detect lat/lon (shared between both modes)
    for field in ('lat', 'lon'):
        for pattern in combined_patterns[field]:
            for col_lower, col_original in columns_lower.items():
                if pattern in col_lower:
                    detected[field] = col_original
                    break
            if detected[field]:
                break

    # Detect combined date/time fields
    for field in ('date', 'time'):
        for pattern in combined_patterns[field]:
            for col_lower, col_original in columns_lower.items():
                if pattern in col_lower:
                    detected[field] = col_original
                    break
            if detected[field]:
                break

    # Detect separate year/month/day/hour/minute fields
    # Use exact match only to avoid false positives (e.g. DAY_WEEK matching DAY)
    for field, field_patterns in separate_patterns.items():
        for pattern in field_patterns:
            for col_lower, col_original in columns_lower.items():
                if col_lower == pattern:
                    detected[field] = col_original
                    break
            if detected[field]:
                break

    # Determine mode: prefer "separate" when all 5 fields found
    separate_fields = [detected[f] for f in ('year', 'month', 'day_of_month', 'hour', 'minute')]
    if all(separate_fields):
        detected['mode'] = 'separate'
    elif detected['date'] and detected['time']:
        detected['mode'] = 'combined'

    return detected
