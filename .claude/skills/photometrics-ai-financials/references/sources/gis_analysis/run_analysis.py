import os, json, warnings
os.environ['PROJ_DATA'] = r'C:\Program Files\QGIS 3.40.8\share\proj'
os.environ['GDAL_DATA'] = r'C:\Program Files\QGIS 3.40.8\apps\gdal\share\gdal'
warnings.filterwarnings('ignore')

import geopandas as gpd
import pandas as pd
import urllib.request, ssl

base = r'C:\Users\aisaa\Projects\photometrics-ai-toolkit\skills\photometrics-ai-financials\references\sources\gis_analysis'
ctx = ssl.create_default_context()

# Load utility territories and fix geometries
utils = gpd.read_file(os.path.join(base, 'ca_iou_pou_territories.geojson'))
utils['geometry'] = utils.geometry.make_valid()

# Remove non-retail overlay entities that cause double-counting
# These are wholesale/pooling/water entities whose polygons overlap actual retail electric territories
non_retail = [
    'Power and Water Resource Pooling Authority',  # wholesale pooling, overlaps PG&E
    'Metropolitan Water District of So. Cal',       # water district, overlaps LADWP
    'Eastside Power Authority',                     # joint powers authority, overlaps PG&E
]
print(f'Removing {len(non_retail)} non-retail overlay entities...')
utils_clean = utils[~utils['Utility'].isin(non_retail)].copy()
print(f'Utilities: {len(utils)} -> {len(utils_clean)}')
print(f'Removed: {", ".join(non_retail)}')

# Load census tracts
tracts = gpd.read_file(os.path.join(base, 'ca_census_tracts_2023.geojson'))

# Population 2023
with open(os.path.join(base, 'ca_tract_population_2023.json')) as f:
    pop2023_raw = json.load(f)
pop2023 = {}
for row in pop2023_raw[1:]:
    pop = int(row[0]) if row[0] else 0
    geoid = f'{row[2]}{row[3]}{row[4]}'
    pop2023[geoid] = pop
tracts['pop2023'] = tracts['GEOID'].map(pop2023).fillna(0).astype(int)

# County-level population for 2013 and 2023 (counties dont change boundaries)
print('Fetching county-level population (2013 ACS and 2023 ACS)...')
county_pop = {}
for year in [2013, 2023]:
    url = f'https://api.census.gov/data/{year}/acs/acs5?get=B01003_001E,NAME&for=county:*&in=state:06'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
        data = json.load(resp)
    county_pop[year] = {}
    for row in data[1:]:
        pop = int(row[0]) if row[0] else 0
        county_fips = row[3]
        county_pop[year][county_fips] = pop
    total = sum(county_pop[year].values())
    print(f'  {year}: {len(county_pop[year])} counties, total: {total:,}')

# Estimate 2013 tract pop by deflating 2023 pop using county growth factor
tracts['county_fips'] = tracts['GEOID'].str[2:5]
tracts['county_pop_2013'] = tracts['county_fips'].map(county_pop[2013]).fillna(0)
tracts['county_pop_2023'] = tracts['county_fips'].map(county_pop[2023]).fillna(0)
tracts['county_growth'] = tracts['county_pop_2023'] / tracts['county_pop_2013'].replace(0, 1)
tracts['pop2013_est'] = (tracts['pop2023'] / tracts['county_growth']).round().astype(int)

print(f'Estimated 2013 CA total from county-deflated tracts: {tracts["pop2013_est"].sum():,}')
print(f'Actual 2013 ACS county total: {sum(county_pop[2013].values()):,}')

# Spatial join with cleaned utilities (centroid-based)
tracts_c = tracts.copy()
tracts_c['geometry'] = tracts_c.geometry.centroid
joined = gpd.sjoin(tracts_c, utils_clean[['Utility', 'Type', 'geometry']], how='left', predicate='within')

dupes = joined.groupby('GEOID').size()
multi = (dupes > 1).sum()
print(f'\nDuplicate tracts after removing PWRPA: {multi}')
if multi > 0:
    dupe_geoids = dupes[dupes > 1].index
    for geoid in list(dupe_geoids)[:5]:
        utilities = joined[joined['GEOID'] == geoid]['Utility'].tolist()
        print(f'  {geoid}: {utilities}')
    joined = joined.drop_duplicates(subset='GEOID', keep='first')

# Final results
ious = ['Pacific Gas & Electric Company', 'Southern California Edison', 'San Diego Gas & Electric']

print('\n' + '=' * 90)
print('CALIFORNIA STREETLIGHT ESTIMATION: POPULATION BY UTILITY TERRITORY')
print('=' * 90)
print(f'\n{"Utility":<45} {"Pop 2013est":>12} {"Pop 2023":>12} {"Growth":>8}')
print('-' * 82)

results = []
for name in ious:
    mask = joined['Utility'] == name
    p13 = joined.loc[mask, 'pop2013_est'].sum()
    p23 = joined.loc[mask, 'pop2023'].sum()
    gf = p23 / p13 if p13 > 0 else 0
    print(f'{name:<45} {p13:>12,} {p23:>12,} {gf:>7.4f}x')
    results.append({'utility': name, 'pop2013': p13, 'pop2023': p23, 'growth': gf})

iou_mask = joined['Utility'].isin(ious)
p13_iou = joined.loc[iou_mask, 'pop2013_est'].sum()
p23_iou = joined.loc[iou_mask, 'pop2023'].sum()
print(f'{"IOU TOTAL":<45} {p13_iou:>12,} {p23_iou:>12,} {p23_iou / p13_iou:.4f}x')

non_iou_mask = ~iou_mask & joined['Utility'].notna()
p13_non = joined.loc[non_iou_mask, 'pop2013_est'].sum()
p23_non = joined.loc[non_iou_mask, 'pop2023'].sum()
print(f'{"NON-IOU TOTAL":<45} {p13_non:>12,} {p23_non:>12,} {p23_non / p13_non:.4f}x')

p13_all = joined['pop2013_est'].sum()
p23_all = joined['pop2023'].sum()
print(f'{"CA TOTAL":<45} {p13_all:>12,} {p23_all:>12,} {p23_all / p13_all:.4f}x')

unmatched = joined['Utility'].isna()
print(f'\nUnmatched: {unmatched.sum()} tracts, {joined.loc[unmatched, "pop2023"].sum():,} people')

# Apply to AB 719 streetlight counts
print('\n' + '=' * 90)
print('STREETLIGHT ESTIMATES (AB 719 baseline x population growth)')
print('=' * 90)
ab719 = {
    'Pacific Gas & Electric Company': 729585,
    'Southern California Edison': 768669,
    'San Diego Gas & Electric': 147450
}
print(f'\n{"Utility":<45} {"2013 CPUC":>10} {"Growth":>8} {"Est. 2023":>10}')
print('-' * 78)
total_2013 = 0
total_2023 = 0
for r in results:
    base_lights = ab719[r['utility']]
    est_lights = round(base_lights * r['growth'])
    total_2013 += base_lights
    total_2023 += est_lights
    print(f'{r["utility"]:<45} {base_lights:>10,} {r["growth"]:>7.4f}x {est_lights:>10,}')
print(f'{"IOU TOTAL":<45} {total_2013:>10,} {"":>8} {total_2023:>10,}')

# Non-IOU estimate using IOU lights-per-capita ratio
iou_lpc_2023 = total_2023 / p23_iou
print(f'\nIOU lights-per-capita (2023): {iou_lpc_2023:.5f} ({1 / iou_lpc_2023:.1f} people per light)')
non_iou_est = round(p23_non * iou_lpc_2023)
unmatched_est = round(joined.loc[unmatched, 'pop2023'].sum() * iou_lpc_2023)
print(f'Non-IOU estimated lights (same ratio): {non_iou_est:,}')
print(f'Unmatched area estimated lights: {unmatched_est:,}')
ca_total = total_2023 + non_iou_est + unmatched_est
print(f'\nCALIFORNIA TOTAL ESTIMATE: {ca_total:,}')

# Top non-IOU utilities
print('\nTOP NON-IOU UTILITIES BY POPULATION:')
non_iou_df = joined[non_iou_mask].groupby('Utility').agg(
    pop2023=('pop2023', 'sum'),
    pop2013_est=('pop2013_est', 'sum')
).sort_values('pop2023', ascending=False)
non_iou_df['growth'] = non_iou_df['pop2023'] / non_iou_df['pop2013_est']
non_iou_df['est_lights'] = (non_iou_df['pop2023'] * iou_lpc_2023).round().astype(int)
for name, row in non_iou_df.head(15).iterrows():
    print(f'  {name:<45} pop={row["pop2023"]:>10,}  est_lights={row["est_lights"]:>8,}')

# Save results
results_out = {
    'methodology': 'AB 719 CPUC baseline (2013) x territory-specific population growth (county-deflated ACS 2013->2023)',
    'data_sources': {
        'utility_territories': 'CEC ElectricLoadServingEntities_IOU_POU (ArcGIS FeatureServer)',
        'census_tracts': 'Census TIGERweb ACS2023 tract boundaries (9,129 tracts)',
        'population_2013': 'ACS 2013 5-year (county level, applied proportionally to 2023 tracts)',
        'population_2023': 'ACS 2023 5-year (tract level)',
        'streetlight_baseline': 'AB 719 Bill Analysis (April 2013), data provided by CPUC'
    },
    'notes': [
        'Non-retail overlays removed: PWRPA (wholesale), Metropolitan Water District (water), Eastside Power Authority (JPA)',
        '2013 tract population estimated by deflating 2023 tract pop using county-level growth factors',
        'Non-IOU streetlights estimated using IOU lights-per-capita ratio (assumption: similar density)',
        '94 tracts (254K people) unmatched to any utility territory'
    ],
    'ious': [],
    'iou_total_lights_2013': total_2013,
    'iou_total_lights_2023_est': total_2023,
    'non_iou_pop_2023': int(p23_non),
    'non_iou_lights_est': non_iou_est,
    'unmatched_pop_2023': int(joined.loc[unmatched, 'pop2023'].sum()),
    'unmatched_lights_est': unmatched_est,
    'iou_lights_per_capita': round(iou_lpc_2023, 5),
    'ca_total_estimate': ca_total
}
for r in results:
    results_out['ious'].append({
        'utility': r['utility'],
        'pop_2013_est': int(r['pop2013']),
        'pop_2023': int(r['pop2023']),
        'growth_factor': round(r['growth'], 5),
        'lights_2013_cpuc': ab719[r['utility']],
        'lights_2023_est': round(ab719[r['utility']] * r['growth'])
    })

outpath = os.path.join(base, 'streetlight_estimation_results.json')
with open(outpath, 'w') as f:
    json.dump(results_out, f, indent=2)
print(f'\nResults saved to {outpath}')
