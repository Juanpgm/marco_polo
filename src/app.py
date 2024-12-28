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

st.set_page_config(layout="wide")  # Configurar la página para usar todo el ancho disponible

st.title("Cargue de mapa GeoDB Privada")

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

# Cargar el archivo comprimido
uploaded_file = st.file_uploader("Cargar archivo comprimido del Shapefile", type=["zip"])

if uploaded_file is not None:
    # Crear un directorio temporal para guardar los archivos descomprimidos
    temp_dir = "temp_shapefile"
    os.makedirs(temp_dir, exist_ok=True)

    # Guardar el archivo subido en el sistema de archivos temporal de Streamlit
    with open(os.path.join(temp_dir, "uploaded.zip"), "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Descomprimir el archivo
    with zipfile.ZipFile(os.path.join(temp_dir, "uploaded.zip"), 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    # Leer el archivo shapefile
    shp_path = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if f.endswith('.shp')][0]
    df = gpd.read_file(shp_path)

    # Convertir la geometría a WGS84
    df = convert_to_epsg_4326(df)

    # Crear un menú lateral con checkboxes para seleccionar columnas
    st.sidebar.title("Seleccionar columnas para mostrar en el popup")
    selected_columns = []
    for col in df.columns:
        if st.sidebar.checkbox(col, value=(col != 'geometry')):
            selected_columns.append(col)

    # Crear el mapa con el tile de "Stadia.AlidadeSmoothDark"
    mapa = folium.Map(location=[3.4370432046046138, -76.51330883443352], zoom_start=12)

    

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

    # Iterar sobre la columna "geometry" y agregar cada objeto al mapa con un marcador
    for geom, row in zip(df['geometry'], df.iterrows()):
        index, data = row
        info = "<ul style='text-align: left;'>"
        for col in selected_columns:
            value = data[col]
            # Asegurarse de que el valor sea serializable a JSON
            if isinstance(value, (int, float, str, bool)) or value is None:
                info += f"<li><strong>{col}:</strong> {value}</li>"
            else:
                info += f"<li><strong>{col}:</strong> {str(value)}</li>"
        info += "</ul>"
        
        if geom.geom_type == 'Polygon':
            folium.Polygon(
                locations=[(point[1], point[0]) for point in geom.exterior.coords],
                color='blue',
                weight=2,
                fill=True,
                fill_color='blue',
                fill_opacity=0.6,
                popup=folium.Popup(info, max_width=300)
            ).add_to(mapa)
        elif geom.geom_type == 'LineString':
            folium.Polygon(
                locations=[(point[1], point[0]) for point in geom.coords],
                color='blue',
                weight=2,
                fill=True,
                fill_color='blue',
                fill_opacity=0.6,
                popup=folium.Popup(info, max_width=300)
            ).add_to(mapa)
        elif geom.geom_type == 'Point':
            folium.CircleMarker(
                location=[geom.y, geom.x],
                radius=5,
                color='blue',
                fill=True,
                fill_color='blue',
                fill_opacity=0.6,
                popup=folium.Popup(info, max_width=300)
            ).add_to(mapa)
        elif geom.geom_type == 'MultiPoint':
            for point in geom.geoms:
                folium.CircleMarker(
                    location=[point.y, point.x],
                    radius=5,
                    color='blue',
                    fill=True,
                    fill_color='blue',
                    fill_opacity=0.6,
                    popup=folium.Popup(info, max_width=300)
                ).add_to(mapa)

    # Crear una fila con un botón "Añadir a base de datos"
    if st.button("Añadir a base de datos", key="add_to_db"):
        # Guardar el archivo GeoJSON en el directorio /src
        output_path = os.path.join("src", "output.geojson")
        df.to_file(output_path, driver="GeoJSON")
        st.write(f"Datos añadidos a la base de datos y guardados en {output_path}")

    # Mostrar el mapa en Streamlit con tamaño ajustado al canvas
    st_folium(mapa, width='100%', height=600)

    # Crear una copia de df y eliminar la columna "geometry"
    df_copy = df.copy()
    if 'geometry' in df_copy.columns:
        df_copy = df_copy.drop(columns=['geometry'])

    # Botón para mostrar/ocultar la tabla
    if st.button("Mostrar/Ocultar Tabla de Atributos"):
        if 'show_table' not in st.session_state:
            st.session_state.show_table = True
        else:
            st.session_state.show_table = not st.session_state.show_table

    # Mostrar la tabla con los datos de df_copy si el estado es True
    if st.session_state.get('show_table', False):
        st.title("Tabla de Atributos")
        st.dataframe(df_copy, height=600)

    # Eliminar la carpeta temporal
    shutil.rmtree(temp_dir)
else:
    st.write("Por favor, carga un archivo comprimido del Shapefile para visualizar el mapa.")