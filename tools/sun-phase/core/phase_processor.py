"""
Phase Processor - GUI-friendly wrapper for phase_calculator.py

Provides callback-based processing for CSV files with progress updates.
"""

from typing import Dict, List, Optional

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from pathlib import Path
from timezonefinder import TimezoneFinder

from phase_calculator import calculate_phase_for_row


def detect_csv_columns(file_path: str) -> List[str]:
    """
    Read CSV header and return column names for dropdown population.

    Args:
        file_path: Path to CSV file

    Returns:
        List of column names
    """
    df = pd.read_csv(file_path, nrows=0)
    return list(df.columns)


def auto_detect_columns(columns: List[str]) -> Dict[str, Optional[str]]:
    """
    Attempt to auto-detect common column names for lat/lon/date/time.

    Args:
        columns: List of column names from CSV

    Returns:
        Dict with keys 'lat', 'lon', 'date', 'time' and detected column names or None
    """
    detected = {'lat': None, 'lon': None, 'date': None, 'time': None}

    # Common patterns for each field (case-insensitive matching)
    patterns = {
        'lat': ['lat', 'latitude', 'y', 'lat_'],
        'lon': ['lon', 'lng', 'longitude', 'long', 'x', 'lon_'],
        'date': ['date', 'dt', 'day', 'date_'],
        'time': ['time', 'tm', 'hour', 'time_']
    }

    columns_lower = {col.lower(): col for col in columns}

    for field, field_patterns in patterns.items():
        for pattern in field_patterns:
            for col_lower, col_original in columns_lower.items():
                if pattern in col_lower:
                    detected[field] = col_original
                    break
            if detected[field]:
                break

    return detected


def process_csv_with_progress(
    input_path: str,
    output_path: str,
    lat_col: str,
    lon_col: str,
    date_col: str,
    time_col: str,
    chunk_size: int,
    progress_callback
) -> dict:
    """
    Process CSV file and add sun elevation / twilight phase columns.

    Args:
        input_path: Path to input CSV file
        output_path: Path to output CSV file
        lat_col: Name of latitude column
        lon_col: Name of longitude column
        date_col: Name of date column
        time_col: Name of time column
        chunk_size: Number of rows to process per chunk
        progress_callback: Function called with (current_row, total_rows, stats)

    Returns:
        Statistics dictionary
    """
    tf = TimezoneFinder()

    # Count total rows
    total_rows = sum(1 for _ in open(input_path, encoding='utf-8')) - 1

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

    first_chunk = True
    last_callback_row = 0
    callback_interval = max(100, total_rows // 100)  # Update at most 100 times

    for chunk in pd.read_csv(input_path, chunksize=chunk_size, low_memory=False):
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

            # Throttled progress callback
            if stats['total'] - last_callback_row >= callback_interval:
                progress_callback(stats['total'], total_rows, stats.copy())
                last_callback_row = stats['total']

        # Add results to chunk and write as GeoPackage
        results_df = pd.DataFrame(results)
        chunk = pd.concat([chunk.reset_index(drop=True), results_df], axis=1)

        # Create Point geometries from lat/lon
        geometry = [Point(lon, lat) for lon, lat in zip(chunk[lon_col], chunk[lat_col])]
        gdf = gpd.GeoDataFrame(chunk, geometry=geometry, crs="EPSG:4326")

        if first_chunk:
            gdf.to_file(output_path, driver="GPKG", mode='w')
        else:
            gdf.to_file(output_path, driver="GPKG", mode='a')
        first_chunk = False

    # Final callback
    progress_callback(stats['total'], total_rows, stats.copy())

    return stats
