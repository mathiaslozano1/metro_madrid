import osmnx as ox

ox.settings.log_console = True
ox.settings.use_cache = True

tags = {'route': 'subway'}
gdf = ox.features_from_place("Madrid, Spain", tags)
print(f"Found {len(gdf)} subway routes.")
if not gdf.empty:
    print(gdf[['name', 'ref']].head())
