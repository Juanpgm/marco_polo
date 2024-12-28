import os
import geopandas as gpd
import streamlit as st
import folium
import webbrowser
from pyproj import Transformer
from shapely.ops import transform

# Crear el mapa
mapa = folium.Map(
    location=[3.4370432046046138, -76.51330883443352],
    zoom_start=12,
    tiles='cartodbpositron',
    
)

def convert_to_epsg_4326(gdf):
    """
    Convert a GeoDataFrame to EPSG:4326.
    
    Parameters:
    gdf (GeoDataFrame): The GeoDataFrame to convert.
    
    Returns:
    GeoDataFrame: The converted GeoDataFrame.
    """
    gdf = gdf.to_crs(epsg=4326)
    return gdf


# Cargar el archivo shapefile
shapefile_path = 'src\SINIESTROS MORTALES CALI 2024\SINIESTROS_MORTALES_2024.shp'  # Reemplazar por el archivo correcto
df = gpd.read_file(shapefile_path)

# Obtener el nombre del archivo sin la extensión
file_name = os.path.splitext(os.path.basename(shapefile_path))[0]

# Convertir la geometría a WGS84
df = convert_to_epsg_4326(df)

# Crear el mapa
mapa = folium.Map(location=[3.4370432046046138, -76.51330883443352], zoom_start=12)

# Iterar sobre la columna "geometry" y agregar cada objeto al mapa
for geom in df['geometry']:
    geo_json = folium.GeoJson(data=geom)
    mapa.add_child(geo_json)

# Guardar el mapa en un archivo HTML
html_file = f'{file_name}.html'
mapa.save(html_file)

# Abrir en el navegador Automáticamente
webbrowser.open(html_file)

#print(df)