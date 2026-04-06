"""
Phase Calculator - Standalone Sun Position / Twilight Phase Tool
Calculates sun elevation and twilight phase for each record based on lat/long/date/time.

Usage:
    python phase_calculator.py input.csv output.csv --lat LAT --lon LON --date "DATE OCC" --time "TIME OCC"

Twilight Phases (based on sun elevation angle):
    Day:                    sun > 0°
    Civil Twilight:         -6° to 0°
    Nautical Twilight:      -12° to -6°   <-- Streetlights turn ON here
    Astronomical Twilight:  -18° to -12°
    Night:                  sun < -18°

Author: Evari Labs
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytz
from timezonefinder import TimezoneFinder

from sun_utils import sun_position


def get_twilight_phase(sun_elevation: float, is_dawn: bool = True) -> str:
    """
    Determine twilight phase based on sun elevation angle.

    Args:
        sun_elevation: Sun elevation angle in degrees
        is_dawn: True if before local noon (dawn), False if after (dusk)

    Streetlights typically turn ON at nautical twilight (sun 6° below horizon).
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


def calculate_phase_for_row(lat: float, lon: float, date_val, time_val, tf: TimezoneFinder) -> tuple:
    """
    Calculate sun elevation and twilight phase for a single record.

    Returns:
        Tuple of (sun_elevation, twilight_phase, streetlights_on, error_message)
    """
    try:
        # Validate coordinates
        if pd.isna(lat) or pd.isna(lon):
            return None, "Error: Missing coordinates", False, "Missing lat/lon"

        lat = float(lat)
        lon = float(lon)

        if lat == 0 and lon == 0:
            return None, "Null Island", False, "Null Island (0,0)"

        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return None, "Error: Out of bounds", False, "Coordinates out of bounds"

        # Parse date and time
        if pd.isna(date_val) or pd.isna(time_val):
            return None, "Error: Missing date/time", False, "Missing date/time"

        # Handle different date formats
        if isinstance(date_val, str):
            # Try common formats
            date_formats = [
                "%Y %b %d %H:%M:%S %p",  # "2010 Feb 20 12:00:00 AM" (LAPD format)
                "%Y %b %d",               # "2010 Feb 20"
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

        # Handle time - LAPD uses military time as integer (e.g., 1430 = 2:30 PM)
        if isinstance(time_val, (int, float)):
            time_int = int(time_val)
            hour = time_int // 100
            minute = time_int % 100
        elif isinstance(time_val, str):
            time_int = int(time_val)
            hour = time_int // 100
            minute = time_int % 100
        else:
            # Assume it's a time object
            hour = time_val.hour
            minute = time_val.minute

        # Combine date and time
        datetime_obj = datetime(date_obj.year, date_obj.month, date_obj.day, hour, minute)

        # Get timezone
        time_zone = tf.timezone_at(lat=lat, lng=lon)
        if time_zone is None:
            return None, "Error: Timezone not found", False, "Could not determine timezone"

        # Convert to UTC
        local_tz = pytz.timezone(time_zone)
        local_time = local_tz.localize(datetime_obj)
        utc_time = local_time.astimezone(pytz.utc)

        # Calculate sun position
        day_of_year = utc_time.timetuple().tm_yday
        hour_decimal = utc_time.hour + utc_time.minute / 60.0 + utc_time.second / 3600.0

        sun_elev = sun_position(lat, lon, utc_time.year, day_of_year, hour_decimal)

        # Determine dawn vs dusk based on local time (before/after noon)
        is_dawn = hour < 12
        phase = get_twilight_phase(sun_elev, is_dawn)
        lights_on = is_streetlights_on(phase)

        return sun_elev, phase, lights_on, None

    except Exception as e:
        return None, "Error", False, str(e)


def process_csv(input_path: str, output_path: str,
                lat_col: str, lon_col: str, date_col: str, time_col: str,
                chunk_size: int = 50000) -> dict:
    """
    Process CSV file and add sun elevation / twilight phase columns.

    Uses chunked processing to handle large files efficiently.
    """
    print(f"\nReading: {input_path}")
    print(f"Output:  {output_path}")
    print(f"Columns: lat={lat_col}, lon={lon_col}, date={date_col}, time={time_col}")
    print("-" * 60)

    tf = TimezoneFinder()

    # Count total rows first
    total_rows = sum(1 for _ in open(input_path, encoding='utf-8')) - 1  # -1 for header
    print(f"Total rows: {total_rows:,}")

    # Stats
    stats = {
        'total': 0,
        'processed': 0,
        'day': 0,
        'civil': 0,
        'nautical': 0,
        'astronomical': 0,
        'night': 0,
        'streetlights_on': 0,
        'errors': 0
    }

    # Process in chunks
    chunks_processed = 0
    first_chunk = True

    for chunk in pd.read_csv(input_path, chunksize=chunk_size, low_memory=False):
        chunks_processed += 1
        chunk_start = (chunks_processed - 1) * chunk_size

        # Calculate for each row
        results = []
        for idx, row in chunk.iterrows():
            sun_elev, phase, lights_on, error = calculate_phase_for_row(
                row.get(lat_col), row.get(lon_col),
                row.get(date_col), row.get(time_col), tf
            )
            results.append({
                'evSunElevAngle': sun_elev,
                'evPhase': phase,
                'evStreetlightsOn': lights_on
            })

            # Update stats
            stats['total'] += 1
            if error:
                stats['errors'] += 1
            else:
                stats['processed'] += 1
                if phase == "Day":
                    stats['day'] += 1
                elif phase in ("Civil Dawn", "Civil Dusk"):
                    stats['civil'] += 1
                elif phase in ("Nautical Dawn", "Nautical Dusk"):
                    stats['nautical'] += 1
                elif phase in ("Astronomical Dawn", "Astronomical Dusk"):
                    stats['astronomical'] += 1
                elif phase == "Night":
                    stats['night'] += 1
                if lights_on:
                    stats['streetlights_on'] += 1

        # Add results to chunk
        results_df = pd.DataFrame(results)
        chunk = pd.concat([chunk.reset_index(drop=True), results_df], axis=1)

        # Write to output
        chunk.to_csv(output_path, mode='w' if first_chunk else 'a',
                     header=first_chunk, index=False)
        first_chunk = False

        # Progress update
        progress = min(100, (stats['total'] / total_rows) * 100)
        print(f"\rProcessed: {stats['total']:,} / {total_rows:,} ({progress:.1f}%) | "
              f"Streetlights ON: {stats['streetlights_on']:,}", end='', flush=True)

    print("\n" + "-" * 60)
    return stats


def print_summary(stats: dict):
    """Print summary statistics."""
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    total = stats['total']
    processed = stats['processed']

    print(f"\nTotal records:     {total:,}")
    print(f"Successfully processed: {processed:,} ({100*processed/total:.1f}%)")
    print(f"Errors:            {stats['errors']:,}")

    print(f"\n--- Twilight Phase Distribution ---")
    print(f"Day:                   {stats['day']:,} ({100*stats['day']/processed:.1f}%)")
    print(f"Civil Twilight:        {stats['civil']:,} ({100*stats['civil']/processed:.1f}%)")
    print(f"Nautical Twilight:     {stats['nautical']:,} ({100*stats['nautical']/processed:.1f}%)")
    print(f"Astronomical Twilight: {stats['astronomical']:,} ({100*stats['astronomical']/processed:.1f}%)")
    print(f"Night:                 {stats['night']:,} ({100*stats['night']/processed:.1f}%)")

    lights_on = stats['streetlights_on']
    print(f"\n--- Streetlight Status ---")
    print(f"Streetlights ON (Nautical+Astro+Night): {lights_on:,} ({100*lights_on/processed:.1f}%)")
    print(f"Streetlights OFF (Day+Civil):           {processed-lights_on:,} ({100*(processed-lights_on)/processed:.1f}%)")

    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Calculate sun elevation and twilight phase for crime data.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python phase_calculator.py crime_data.csv output.csv --lat LAT --lon LON --date "DATE OCC" --time "TIME OCC"

Twilight Phases:
    Day:                    sun > 0°
    Civil Twilight:         -6° to 0°
    Nautical Twilight:      -12° to -6°   <-- Streetlights ON
    Astronomical Twilight:  -18° to -12°  <-- Streetlights ON
    Night:                  sun < -18°    <-- Streetlights ON
        """
    )

    parser.add_argument('input', help='Input CSV file path')
    parser.add_argument('output', help='Output CSV file path')
    parser.add_argument('--lat', required=True, help='Latitude column name')
    parser.add_argument('--lon', required=True, help='Longitude column name')
    parser.add_argument('--date', required=True, help='Date column name')
    parser.add_argument('--time', required=True, help='Time column name')
    parser.add_argument('--chunk-size', type=int, default=50000,
                        help='Chunk size for processing (default: 50000)')

    args = parser.parse_args()

    # Validate input file exists
    if not Path(args.input).exists():
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    # Process
    stats = process_csv(
        args.input, args.output,
        args.lat, args.lon, args.date, args.time,
        args.chunk_size
    )

    # Print summary
    print_summary(stats)

    print(f"\nOutput saved to: {args.output}")


if __name__ == '__main__':
    main()
