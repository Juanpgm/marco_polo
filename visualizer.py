import os
import geopandas as gpd
import streamlit as st
import folium
from streamlit_folium import st_folium
from pyproj import Transformer
from shapely.ops import transform
import zipfile
import shutil
from folium.plugins import Fullscreen, MeasureControl, Draw
from folium import LayerControl
import requests
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Map
from shapely.wkb import loads as wkb_loads
from geoalchemy2.elements import WKBElement

app = FastAPI()

@app.get("/visualize_map/")
def visualize_map(name: str, db: Session = Depends(get_db)):
    try:
        maps = db.query(Map).filter(Map.name == name).all()
        if not maps:
            raise HTTPException(status_code=404, detail="Map not found")

        # Crear un mapa de folium
        m = folium.Map(location=[0, 0], zoom_start=2)

        for map_item in maps:
            geom = wkb_loads(bytes(map_item.geom.data)) if isinstance(map_item.geom, WKBElement) else None
            if geom:
                properties = map_item.properties if map_item.properties else {}
                folium.GeoJson(
                    data=geom.__geo_interface__,
                    name=map_item.name,
                    tooltip=folium.GeoJsonTooltip(fields=list(properties.keys()))
                ).add_to(m)

        return m._repr_html_()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

st.set_page_config(layout="wide")  # Configurar la página para usar todo el ancho disponible

st.title("Visualizador de Datos GIS")

# Definir la función props_view antes de usarla
@st.dialog("Propiedades")
def props_view():
    st.write("Propiedades de la capa seleccionada")
    st.write("Aquí se mostrarán las propiedades de la capa seleccionada.")

# Definir una función para obtener los nombres de las capas y almacenarla en caché
@st.cache_data
def get_unique_map_names():
    response = requests.get("http://localhost:8000/maps/names")
    if response.status_code == 200:
        return response.json()
    else:
        return []
    
def get_maps_by_name(name):
    response = requests.get(f"http://localhost:8000/maps/?name={name}")
    if response.status_code == 200:
        return response.json()
    else:
        return f"Error: {response.status_code}"

def add_geojson_layers_to_map(layer_name, mapa, loaded_layers):
    if layer_name in loaded_layers:
        return  # No hacer nada si la capa ya está cargada

    geojson_data = get_maps_by_name(layer_name)
    if isinstance(geojson_data, str) and geojson_data.startswith("Error"):
        st.error(f"Error al obtener los datos de la capa: {layer_name}")
    else:
        valid_features = []
        all_fields = set()
        for feature in geojson_data:
            if 'geom' in feature and feature['geom'] is not None:
                geometry = feature['geom']
                properties = feature['properties'] if 'properties' in feature else {}
                valid_features.append({
                    'type': 'Feature',
                    'geometry': geometry,
                    'properties': properties
                })
                all_fields.update(properties.keys())
        if not valid_features:
            st.error(f"No hay geometrías válidas en la capa {layer_name}")
        else:
            for feature in valid_features:
                geometry = feature['geometry']
                if geometry['type'] == 'Point':
                    folium.CircleMarker(
                        location=[geometry['coordinates'][1], geometry['coordinates'][0]],
                        radius=5,
                        color='blue',
                        fill=True,
                        fill_color='blue'
                    ).add_to(mapa)
                else:
                    folium.GeoJson(
                        feature,
                        style_function=lambda x: {
                            'color': 'blue',
                            'weight': 2
                        }
                    ).add_to(mapa)
            loaded_layers.add(layer_name)  # Marcar la capa como cargada

# Obtener los nombres de las capas
map_names = get_unique_map_names()

# Mostrar los nombres de las capas en el st.sidebar con checkboxes
st.sidebar.title("Capas")
selected_layers = []
loaded_layers = set()  # Conjunto para rastrear capas cargadas

for name in map_names:
    cols = st.sidebar.columns([4, 1])
    if cols[0].checkbox(name):
        selected_layers.append(name)
    with cols[1]:
        if "props_view" not in st.session_state:
            if st.button("⚙️", key=f"options_{name}", type="tertiary"):
                props_view()
        else:
            props_view()

# Crear el mapa con el tile de "Stadia.AlidadeSmoothDark"
mapa = folium.Map(location=[3.4370432046046138, -76.51330883443352], zoom_start=12)

# Iterar sobre cada capa seleccionada
for layer in selected_layers:
    add_geojson_layers_to_map(layer, mapa, loaded_layers)

# Añadir otras capas de tiles con atribuciones
folium.TileLayer('CartoDB.Positron', attr='&copy; <a href="https://carto.com/">CARTO</a>').add_to(mapa)
folium.TileLayer('CartoDB.DarkMatter', attr='&copy; <a href="https://carto.com/">CARTO</a>').add_to(mapa)
folium.TileLayer('OpenStreetMap', attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors').add_to(mapa)
# Añadir "Stadia.AlidadeSmoothDark" como TileLayer principal
folium.TileLayer('Stadia.AlidadeSmoothDark', name='Stadia.AlidadeSmoothDark').add_to(mapa)

# Añadir el botón de pantalla completa
Fullscreen().add_to(mapa)

# Añadir el control de medición en la esquina superior derecha
measure_control = MeasureControl(
    position='topright',
    primary_length_unit='meters',
    secondary_length_unit='kilometers',
    primary_area_unit='sqmeters',
    secondary_area_unit='sqkilometers'
)
mapa.add_child(measure_control)

# Añadir el control de dibujo
draw_control = Draw()
mapa.add_child(draw_control)

# Añadir el TreeLayerControl justo debajo del control de medición
layer_control = LayerControl(position='topright')
mapa.add_child(layer_control)

# Mostrar el mapa en Streamlit con tamaño ajustado al canvas
st_folium(mapa, width='100%', height=500)