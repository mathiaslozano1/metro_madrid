import osmnx as ox

try:
    print("Testing osmnx...")
    ox.settings.log_console = True
    ox.settings.use_cache = True
    
    # We want subway stations in Madrid
    tags = {'station': 'subway'}
    gdf_stations = ox.features_from_place("Madrid, Spain", tags)
    print(f"Found {len(gdf_stations)} subway stations.")
    
    # Just printing a few
    if not gdf_stations.empty:
        print(gdf_stations[['name']].head())
except Exception as e:
    print(f"Error: {e}")
