import streamlit as st
import folium
from streamlit_folium import st_folium
import googlemaps
from shapely.geometry import Polygon, Point
import pyproj
from shapely.ops import transform
import os

# Configuración inicial de la página
st.set_page_config(
    page_title="Kitchen Partner | Cobertura Delivery",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS NATIVOS
st.markdown("""
    <style>
        .block-container { padding-top: 1.2rem; padding-bottom: 0rem; padding-left: 1.5rem; padding-right: 1.5rem; }
        
        /* Encabezado Superior Limpio */
        .kp-header-clean {
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 2px solid rgba(255, 107, 74, 0.3);
            padding-bottom: 12px;
            margin-bottom: 20px;
        }

        .kp-title-text {
            font-size: 1.6rem;
            font-weight: 800;
            letter-spacing: -0.5px;
            margin: 0;
            padding: 0;
            color: var(--text-color) !important;
        }

        .kp-subtitle-text {
            font-size: 0.85rem;
            color: #FF6B4A !important;
            font-weight: 700;
            letter-spacing: 0.8px;
            text-transform: uppercase;
            margin-top: 2px;
        }

        .kp-badge-pill {
            background-color: #FF6B4A;
            color: #FFFFFF !important;
            padding: 6px 16px;
            border-radius: 16px;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        /* Tarjeta Contenedora Neutra Blanca para asegurar visibilidad de la K Azul */
        .sidebar-logo-card {
            background-color: #FFFFFF !important;
            border-radius: 12px;
            padding: 12px;
            text-align: center;
            margin-bottom: 15px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        }

        .sidebar-logo-card img {
            width: 85px;
            height: auto;
            display: inline-block;
        }

        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, 
        [data-testid="stSidebar"] h3, [data-testid="stSidebar"] label {
            color: var(--text-color) !important;
        }
    </style>
""", unsafe_allow_html=True)

# 🔑 LECTURA DE API KEY DE GOOGLE MAPS
if "GOOGLE_MAPS_API_KEY" in st.secrets:
    GOOGLE_MAPS_API_KEY = st.secrets["GOOGLE_MAPS_API_KEY"]
else:
    GOOGLE_MAPS_API_KEY = "AIzaSyC81y07cCifkIrHEm-GR0RUpfBd9XnPJ38"

try:
    gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
except Exception:
    gmaps = None

# --- BARRA LATERAL CON TARJETA DE CONTRASTE PREDETERMINADA ---
with st.sidebar:
    st.markdown('<div class="sidebar-logo-card">', unsafe_allow_html=True)
    if os.path.exists("logo_k_dark.png"):
        st.image("logo_k_dark.png")
    elif os.path.exists("logo.png"):
        st.image("logo.png")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### 🎯 Panel KP 360™")
    st.caption("Evaluación de Coberturas Multi-Plataforma")
    st.markdown("---")
    
    ciudad_seleccionada = st.selectbox(
        "📍 Selecciona la Ciudad:",
        ["Mexicali", "Tijuana", "Ensenada", "Otras Ciudades"]
    )

# --- ENCABEZADO SUPERIOR LIMPIO ---
st.markdown(f"""
    <div class="kp-header-clean">
        <div>
            <h1 class="kp-title-text">KITCHEN PARTNER 360™</h1>
            <div class="kp-subtitle-text">Análisis y Mapeo Estratégico de Cobertura Delivery</div>
        </div>
        <div class="kp-badge-pill">
            COBERTURA {ciudad_seleccionada.upper()}
        </div>
    </div>
""", unsafe_allow_html=True)

# Configuración y Polígonos por Ciudad
CONFIG_CIUDADES = {
    "Mexicali": {
        "coords": (32.6245, -115.4522),
        "poligono": Polygon([
            (-115.5800, 32.6630), (-115.4850, 32.6645), (-115.3500, 32.6700),
            (-115.3200, 32.6300), (-115.3100, 32.5700), (-115.3500, 32.5300),
            (-115.4500, 32.5300), (-115.5500, 32.5500), (-115.5850, 32.6100),
            (-115.5800, 32.6630)
        ]),
        "defaults": [
            (32.6508, -115.4522, "Victoria 52, Residencias, Mexicali"),
            (32.6535, -115.4045, "Plaza San Pedro, Mexicali")
        ]
    },
    "Tijuana": {
        "coords": (32.5149, -117.0382),
        "poligono": Polygon([
            (-117.1200, 32.5400), (-116.9000, 32.5400),
            (-116.9000, 32.4000), (-117.1200, 32.4000)
        ]),
        "defaults": [
            (32.5149, -117.0382, "Zona Río, Tijuana"),
            (32.5000, -116.9700, "Plaza Río Tijuana")
        ]
    },
    "Ensenada": {
        "coords": (31.8667, -116.5964),
        "poligono": Polygon([
            (-116.6500, 31.9100), (-116.5200, 31.9100),
            (-116.5200, 31.8000), (-116.6500, 31.8000)
        ]),
        "defaults": [
            (31.8667, -116.5964, "Centro, Ensenada"),
            (31.8500, -116.6000, "Macroplaza Ensenada")
        ]
    },
    "Otras Ciudades": {
        "coords": (23.6345, -102.5528),
        "poligono": None,
        "defaults": [
            (19.4326, -99.1332, "Centro Histórico, CDMX"),
            (20.6736, -103.3440, "Guadalajara, Jalisco")
        ]
    }
}

cfg_activa = CONFIG_CIUDADES[ciudad_seleccionada]
POLIGONO_URBANO = cfg_activa["poligono"]

@st.cache_data(show_spinner=False)
def obtener_sugerencias_google(texto_busqueda, lat_c, lon_c):
    if not gmaps or not texto_busqueda or len(texto_busqueda.strip()) < 2:
        return []
    q = texto_busqueda.strip()
    try:
        predictions = gmaps.places_autocomplete(
            input_text=q,
            components={"country": "mx"},
            location=(lat_c, lon_c),
            radius=25000,
            language="es"
        )
        return [{"label": p['description'], "place_id": p['place_id']} for p in predictions]
    except Exception:
        return []

@st.cache_data(show_spinner=False)
def obtener_coords_por_place_id(place_id):
    if not gmaps:
        return None
    try:
        place_details = gmaps.place(place_id=place_id, fields=['geometry', 'formatted_address'])
        result = place_details.get('result', {})
        lat = result['geometry']['location']['lat']
        lon = result['geometry']['location']['lng']
        addr = result.get('formatted_address', '')
        return lat, lon, addr
    except Exception:
        return None

def recortar_con_manzana_urbana(lat, lon, radio_km):
    proj_wgs84 = pyproj.CRS('EPSG:4326')
    proj_utm = pyproj.CRS('EPSG:32611')
    to_utm = pyproj.Transformer.from_crs(proj_wgs84, proj_utm, always_xy=True).transform
    to_wgs84 = pyproj.Transformer.from_crs(proj_utm, proj_wgs84, always_xy=True).transform
    
    p_utm = transform(to_utm, Point(lon, lat))
    r_m = radio_km * 1000
    
    box_utm = Polygon([
        (p_utm.x - r_m, p_utm.y - r_m),
        (p_utm.x + r_m, p_utm.y - r_m),
        (p_utm.x + r_m, p_utm.y + r_m),
        (p_utm.x - r_m, p_utm.y + r_m)
    ])
    
    box_wgs = transform(to_wgs84, box_utm)
    if POLIGONO_URBANO:
        return box_wgs.intersection(POLIGONO_URBANO)
    return box_wgs

# CONTROLES SIDEBAR
st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Filtro de Plataformas")
apps_seleccionadas = st.sidebar.multiselect(
    "Selecciona la(s) plataforma(s) a comparar:",
    ["Uber Eats", "Rappi", "DiDi Food"],
    default=["Uber Eats", "Rappi", "DiDi Food"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("🏬 Sucursales Restaurante")
num_sucursales = st.sidebar.number_input("Número de sucursales a evaluar", 1, 5, 2)

sucursales = []

for i in range(num_sucursales):
    st.sidebar.markdown(f"**📍 Sucursal {i+1}**")
    def_lat, def_lon, def_name = cfg_activa["defaults"][i % len(cfg_activa["defaults"])]
    key_prefix = f"{ciudad_seleccionada}_suc_{i}"
    
    if f"{key_prefix}_lat" not in st.session_state:
        st.session_state[f"{key_prefix}_lat"] = def_lat
    if f"{key_prefix}_lon" not in st.session_state:
        st.session_state[f"{key_prefix}_lon"] = def_lon
    if f"{key_prefix}_addr" not in st.session_state:
        st.session_state[f"{key_prefix}_addr"] = def_name

    busqueda = st.sidebar.text_input(
        f"Buscar dirección (Suc. {i+1}):", 
        value="", 
        placeholder="Ej: Plaza, Calle, Colonia...",
        key=f"search_{key_prefix}"
    )

    sugerencias = obtener_sugerencias_google(busqueda, cfg_activa["coords"][0], cfg_activa["coords"][1])

    if sugerencias:
        opciones_dict = {s['label']: s['place_id'] for s in sugerencias}
        opcion_elegida = st.sidebar.selectbox(
            "👇 Selecciona la opción exacta:",
            options=list(opciones_dict.keys()),
            key=f"select_{key_prefix}"
        )
        
        place_id_sel = opciones_dict[opcion_elegida]
        res = obtener_coords_por_place_id(place_id_sel)
        if res:
            st.session_state[f"{key_prefix}_lat"] = res[0]
            st.session_state[f"{key_prefix}_lon"] = res[1]
            st.session_state[f"{key_prefix}_addr"] = res[2]
            st.sidebar.caption(f"✅ Ubicación: {res[2][:45]}...")
    elif busqueda.strip() != "":
        st.sidebar.info("Buscando en Google Maps...")

    sucursales.append({
        "nombre": f"Sucursal {i+1}",
        "lat": st.session_state[f"{key_prefix}_lat"],
        "lon": st.session_state[f"{key_prefix}_lon"],
        "direccion": st.session_state[f"{key_prefix}_addr"]
    })

st.sidebar.markdown("---")
st.sidebar.subheader("📐 Radios Operativos (km)")
radio_didi = st.sidebar.slider("DiDi Food (km)", 0.5, 8.0, 2.5, 0.5)
radio_rappi = st.sidebar.slider("Rappi (km)", 0.5, 10.0, 3.5, 0.5)
radio_uber = st.sidebar.slider("Uber Eats (km)", 0.5, 12.0, 5.0, 0.5)

# RENDERING MAPA
avg_lat = sum(s["lat"] for s in sucursales) / len(sucursales)
avg_lon = sum(s["lon"] for s in sucursales) / len(sucursales)
dynamic_map_id = f"{ciudad_seleccionada}_" + "_".join([f"{s['lat']:.5f}_{s['lon']:.5f}" for s in sucursales])

m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12, tiles="OpenStreetMap")

show_uber = "Uber Eats" in apps_seleccionadas
show_rappi = "Rappi" in apps_seleccionadas
show_didi = "DiDi Food" in apps_seleccionadas
varias_apps = len(apps_seleccionadas) > 1
fill_opacity_val = 0.05 if varias_apps else 0.22
weight_val = 2.5 if varias_apps else 2.0

name_uber_tot = "<span style='color:#06C167; font-weight:bold;'>🟢 Uber Eats</span> - Cobertura Ciudad"
name_rappi_tot = "<span style='color:#FF441F; font-weight:bold;'>🔴 Rappi</span> - Cobertura Ciudad"
name_didi_tot = "<span style='color:#FF8800; font-weight:bold;'>🟠 DiDi Food</span> - Cobertura Ciudad"

name_uber_suc = "<span style='color:#06C167; font-weight:bold;'>🛵 Uber Eats</span> - Polígonos Sucursal"
name_rappi_suc = "<span style='color:#FF441F; font-weight:bold;'>🔴 Rappi</span> - Polígonos Sucursal"
name_didi_suc = "<span style='color:#FF8800; font-weight:bold;'>🛵 DiDi Food</span> - Polígonos Sucursal"
name_puntos = "<span style='color:#0D2845; font-weight:bold;'>🏬 Sucursales KP</span>"

if POLIGONO_URBANO:
    if show_uber:
        layer_u_tot = folium.FeatureGroup(name=name_uber_tot, show=True).add_to(m)
        folium.GeoJson(POLIGONO_URBANO, style_function=lambda x: {'fillColor': 'transparent', 'color': '#06C167', 'weight': 2, 'dashArray': '6, 6'}).add_to(layer_u_tot)
    if show_rappi:
        layer_r_tot = folium.FeatureGroup(name=name_rappi_tot, show=True).add_to(m)
        folium.GeoJson(POLIGONO_URBANO, style_function=lambda x: {'fillColor': 'transparent', 'color': '#FF441F', 'weight': 2, 'dashArray': '6, 6'}).add_to(layer_r_tot)
    if show_didi:
        layer_d_tot = folium.FeatureGroup(name=name_didi_tot, show=True).add_to(m)
        folium.GeoJson(POLIGONO_URBANO, style_function=lambda x: {'fillColor': 'transparent', 'color': '#FF8800', 'weight': 2, 'dashArray': '6, 6'}).add_to(layer_d_tot)

layer_u_suc = folium.FeatureGroup(name=name_uber_suc, show=show_uber).add_to(m)
layer_r_suc = folium.FeatureGroup(name=name_rappi_suc, show=show_rappi).add_to(m)
layer_d_suc = folium.FeatureGroup(name=name_didi_suc, show=show_didi).add_to(m)
layer_puntos = folium.FeatureGroup(name=name_puntos).add_to(m)

colores_icono = ["red", "blue", "purple", "orange", "darkgreen"]

for i, suc in enumerate(sucursales):
    lat, lon = suc["lat"], suc["lon"]
    color_m = colores_icono[i % len(colores_icono)]

    if show_uber:
        poly_u = recortar_con_manzana_urbana(lat, lon, radio_uber)
        folium.GeoJson(poly_u, style_function=lambda x: {'fillColor': '#06C167', 'color': '#048A49', 'weight': weight_val, 'fillOpacity': fill_opacity_val}).add_to(layer_u_suc)

    if show_rappi:
        poly_r = recortar_con_manzana_urbana(lat, lon, radio_rappi)
        folium.GeoJson(poly_r, style_function=lambda x: {'fillColor': '#FF441F', 'color': '#B3260A', 'weight': weight_val, 'fillOpacity': fill_opacity_val}).add_to(layer_r_suc)

    if show_didi:
        poly_d = recortar_con_manzana_urbana(lat, lon, radio_didi)
        folium.GeoJson(poly_d, style_function=lambda x: {'fillColor': '#FF8800', 'color': '#B35F00', 'weight': weight_val, 'fillOpacity': fill_opacity_val}).add_to(layer_d_suc)

    folium.Marker(
        [lat, lon],
        popup=f"<b>{suc['nombre']}</b><br>{suc['direccion']}",
        tooltip=suc["nombre"],
        icon=folium.Icon(color=color_m, icon="store", prefix="fa")
    ).add_to(layer_puntos)

folium.LayerControl(collapsed=False).add_to(m)

st_folium(m, use_container_width=True, height=750, key=f"render_map_{dynamic_map_id}", returned_objects=[])
