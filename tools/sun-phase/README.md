# Sun Phase Tools

Tools for calculating sun position, twilight phases, and streetlight operating hours based on astronomical calculations.

## Tools

| Tool | Purpose |
|------|---------|
| `phase_calculator.py` | Add twilight phase to each record in a CSV with timestamps |
| `twilight_times.py` | Generate yearly schedule of streetlight operating hours for a location |

## Use Cases

- Analyze crime data to determine what percentage of events occurred when streetlights were ON
- Generate annual streetlight schedules for urban planning
- Calculate darkness hours for any location

## Quick Start

```bash
# 1. Clone and enter repo
cd tool-sun-phase

# 2. Create virtual environment
python -m venv venv

# 3. Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run analysis
python phase_calculator.py data/input/your_data.csv data/output/results.csv \
    --lat LAT --lon LON --date "DATE OCC" --time "TIME OCC"
```

## LAPD Crime Data Analysis

For analyzing Los Angeles crime data:

1. Download data to `data/input/`:
   - [2010-2019](https://data.lacity.org/Public-Safety/Crime-Data-from-2010-to-2019/63jg-8b9z)
   - [2020-Present](https://data.lacity.org/Public-Safety/Crime-Data-from-2020-to-Present/2nrs-mtv8)

2. Run (Windows):
   ```bash
   scripts\run_lapd_analysis.bat "Crime_Data_from_2010_to_2019.csv"
   ```

   Or directly:
   ```bash
   python phase_calculator.py data/input/Crime_Data_from_2010_to_2019.csv data/output/output.csv --lat LAT --lon LON --date "DATE OCC" --time "TIME OCC"
   ```

## Output Columns

| Column | Description |
|--------|-------------|
| `evSunElevAngle` | Sun elevation angle in degrees |
| `evPhase` | Twilight phase category |
| `evStreetlightsOn` | Boolean: True if streetlights would be ON |

## Twilight Times Tool

Generate a yearly schedule of streetlight operating hours for any location.

### Usage

```bash
python twilight_times.py --lat 36.7456 --lon -93.4712 --output hartville_mo.csv
python twilight_times.py --lat 34.0522 --lon -118.2437 --output la_times.csv
```

### Options

```
Required:
  --lat         Latitude in degrees (-90 to 90)
  --lon         Longitude in degrees (-180 to 180)
  --output, -o  Output CSV file path

Optional:
  --year        Year to calculate (default: current year)
```

### Output Columns

| Column | Description |
|--------|-------------|
| `date` | Date (YYYY-MM-DD) |
| `streetlights_off_time` | Time streetlights turn OFF (sun rises to -6°, morning) |
| `sunrise` | Time of sunrise (sun crosses 0°, rising) |
| `sunset` | Time of sunset (sun crosses 0°, setting) |
| `streetlights_on_time` | Time streetlights turn ON (sun drops to -6°, evening) |
| `streetlights_on_hours_morning` | Hours from midnight to streetlights OFF (decimal) |
| `streetlights_on_hours_evening` | Hours from streetlights ON to midnight (decimal) |
| `streetlights_on_hours_total` | Total darkness hours for the date (decimal, summable) |

Times are in local timezone (auto-detected from coordinates) with DST adjustments.

---

## Twilight Phases

| Phase | Sun Elevation | Streetlights |
|-------|---------------|--------------|
| Day | > 0° | OFF |
| Civil Twilight | -6° to 0° | OFF |
| Nautical Twilight | -12° to -6° | **ON** |
| Astronomical Twilight | -18° to -12° | **ON** |
| Night | < -18° | **ON** |

Streetlights typically turn ON at nautical dusk (sun 6° below horizon) and OFF at nautical dawn.

## Folder Structure

```
tool-sun-phase/
├── sun_utils.py          # Shared astronomical calculations
├── phase_calculator.py   # Twilight phase for CSV records
├── twilight_times.py     # Yearly streetlight schedule generator
├── requirements.txt      # Python dependencies
├── scripts/
│   └── run_lapd_analysis.bat
├── data/
│   ├── input/            # Place input CSVs here (gitignored)
│   └── output/           # Results saved here (gitignored)
└── README.md
```

## Phase Calculator Options

```
python phase_calculator.py INPUT OUTPUT --lat COL --lon COL --date COL --time COL

Required:
  INPUT           Input CSV file path
  OUTPUT          Output CSV file path
  --lat           Latitude column name
  --lon           Longitude column name
  --date          Date column name
  --time          Time column name

Optional:
  --chunk-size    Rows to process at once (default: 50000)
```

## How It Works

1. For each record, extracts lat/lon/date/time
2. Determines timezone from coordinates
3. Calculates precise sun elevation using astronomical formulas
4. Categorizes into twilight phase
5. Outputs original data + new columns

## License

MIT
