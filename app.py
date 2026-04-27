import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import math
import io
import requests
import time

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Optimizador de Rutas · Logística",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Dark gradient background */
.stApp {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    min-height: 100vh;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.04);
    border-right: 1px solid rgba(255,255,255,0.08);
    backdrop-filter: blur(20px);
}
[data-testid="stSidebar"] * {
    color: #e0e0f0 !important;
}

/* Main content text */
.stApp * { color: #e0e0f0; }

/* Hero title */
.hero-title {
    background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 2.6rem;
    font-weight: 700;
    line-height: 1.15;
    margin-bottom: 0.25rem;
}
.hero-sub {
    color: #94a3b8;
    font-size: 1rem;
    margin-bottom: 1.5rem;
}

/* Metric cards */
.metric-card {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 1.2rem 1.5rem;
    text-align: center;
    backdrop-filter: blur(10px);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.metric-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 32px rgba(0,0,0,0.4);
}
.metric-value {
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(90deg, #a78bfa, #60a5fa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.metric-label {
    font-size: 0.78rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.15rem;
}

/* Section headers */
.section-header {
    font-size: 1.1rem;
    font-weight: 600;
    color: #c4b5fd;
    border-left: 3px solid #a78bfa;
    padding-left: 0.75rem;
    margin: 1.5rem 0 0.75rem;
}

/* Route table */
.route-table-wrapper {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    overflow: hidden;
}

/* Glassmorphism panel */
.glass-panel {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 1.25rem;
    backdrop-filter: blur(10px);
}

/* Streamlit overrides */
.stFileUploader > div > div {
    background: rgba(167,139,250,0.1);
    border: 2px dashed rgba(167,139,250,0.5);
    border-radius: 14px;
    transition: border-color 0.2s;
}
.stFileUploader > div > div:hover {
    border-color: #a78bfa;
}

div[data-testid="stNumberInput"] input,
div[data-testid="stTextInput"] input {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 10px !important;
    color: #e0e0f0 !important;
    -webkit-user-select: text !important;
    user-select: text !important;
    pointer-events: auto !important;
    cursor: text !important;
}

.stButton > button {
    background: linear-gradient(135deg, #7c3aed, #2563eb);
    color: white !important;
    border: none;
    border-radius: 12px;
    padding: 0.6rem 1.5rem;
    font-weight: 600;
    font-size: 0.95rem;
    width: 100%;
    transition: opacity 0.2s, transform 0.15s;
    box-shadow: 0 4px 20px rgba(124,58,237,0.4);
}
.stButton > button:hover {
    opacity: 0.9;
    transform: translateY(-1px);
}

.stAlert {
    border-radius: 12px;
}

/* Divider */
hr { border-color: rgba(255,255,255,0.08); }

/* Dataframe */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
}
</style>
""", unsafe_allow_html=True)


# ── Google Maps Geocoding ─────────────────────────────────────────────────────
GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
GOOGLE_MAPS_API_KEY = "AIzaSyAVy23EyHZUgunjQS01iTyschLGJidOoao"


def geocode_address(address: str, api_key: str):
    """
    Geocode a single address string via Google Maps Geocoding API.
    Returns (lat, lng, formatted_address) or (None, None, error_message).
    """
    try:
        resp = requests.get(
            GEOCODE_URL,
            params={"address": address, "key": api_key},
            timeout=10,
        )
        data = resp.json()
        status = data.get("status", "UNKNOWN")
        if status == "OK":
            loc = data["results"][0]["geometry"]["location"]
            fmt = data["results"][0]["formatted_address"]
            return float(loc["lat"]), float(loc["lng"]), fmt
        else:
            return None, None, f"API status: {status}"
    except Exception as exc:
        return None, None, str(exc)


def geocode_dataframe(df: pd.DataFrame, api_key: str, progress_bar, status_text) -> pd.DataFrame:
    """
    Geocode all rows in df (columns: nombre, direccion).
    Returns df with added columns: latitud, longitud, direccion_formateada, geocode_ok.
    """
    lats, lngs, fmts, oks = [], [], [], []
    total = len(df)
    for i, row in enumerate(df.itertuples(index=False), start=1):
        status_text.markdown(
            f'<span style="color:#94a3b8;font-size:0.82rem;">'
            f'Geocodificando {i}/{total}: <b>{row.nombre}</b> &mdash; {row.direccion}</span>',
            unsafe_allow_html=True,
        )
        lat, lng, fmt = geocode_address(row.direccion, api_key)
        lats.append(lat)
        lngs.append(lng)
        fmts.append(fmt if lat is not None else f"FAILED: {fmt}")
        oks.append(lat is not None)
        progress_bar.progress(i / total)
        if i < total:
            time.sleep(0.05)   # stay well under 50 QPS free-tier limit
    df = df.copy()
    df["latitud"] = lats
    df["longitud"] = lngs
    df["direccion_formateada"] = fmts
    df["geocode_ok"] = oks
    return df


# ── OR-Tools TSP solver ────────────────────────────────────────────────────────
def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in kilometres."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def build_distance_matrix(locations):
    """locations: list of (lat, lon) tuples. Returns km matrix scaled to int."""
    n = len(locations)
    matrix = []
    for i in range(n):
        row = []
        for j in range(n):
            if i == j:
                row.append(0)
            else:
                d = haversine_km(locations[i][0], locations[i][1],
                                 locations[j][0], locations[j][1])
                row.append(int(d * 1000))   # metres as int for OR-Tools
        matrix.append(row)
    return matrix


def solve_tsp(locations):
    """
    Solve TSP using OR-Tools.
    Returns (ordered_indices, total_distance_km).
    """
    from ortools.constraint_solver import pywrapcp, routing_enums_pb2

    distance_matrix = build_distance_matrix(locations)
    n = len(locations)

    manager = pywrapcp.RoutingIndexManager(n, 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_idx, to_idx):
        i = manager.IndexToNode(from_idx)
        j = manager.IndexToNode(to_idx)
        return distance_matrix[i][j]

    transit_cb_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_cb_index)

    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_params.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_params.time_limit.seconds = 10

    solution = routing.SolveWithParameters(search_params)

    if not solution:
        return None, None

    # Extract route
    route = []
    index = routing.Start(0)
    while not routing.IsEnd(index):
        route.append(manager.IndexToNode(index))
        index = solution.Value(routing.NextVar(index))
    route.append(manager.IndexToNode(index))   # back to depot

    # Calculate total distance
    total_m = solution.ObjectiveValue()
    total_km = total_m / 1000.0

    return route, total_km


# ── Map builder ───────────────────────────────────────────────────────────────
STOP_COLORS = [
    "#f59e0b", "#10b981", "#3b82f6", "#8b5cf6", "#ef4444",
    "#06b6d4", "#ec4899", "#84cc16", "#f97316", "#6366f1",
]


def build_map(df_all, route_indices):
    """
    df_all: DataFrame with columns nombre, latitud, longitud, direccion_formateada.
            Index 0 is always the depot.
    route_indices: ordered list of node indices (starts and ends at 0).
    """
    # Center map
    center_lat = df_all["latitud"].mean()
    center_lon = df_all["longitud"].mean()

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=11,
        tiles="CartoDB dark_matter",
    )

    # Draw route polyline
    coords = [(df_all.iloc[i]["latitud"], df_all.iloc[i]["longitud"]) for i in route_indices]
    folium.PolyLine(
        coords,
        color="#a78bfa",
        weight=3.5,
        opacity=0.85,
        dash_array=None,
    ).add_to(m)

    # Add stop markers
    stop_num = 0
    for order, node_idx in enumerate(route_indices):
        if order == len(route_indices) - 1:
            # Return to depot - don't add duplicate marker
            break

        row = df_all.iloc[node_idx]
        is_depot = (node_idx == 0)
        addr = row.get("direccion_formateada", row["nombre"])

        if is_depot:
            color = "#34d399"
            tooltip_text = f"<b>DEPÓSITO</b><br>{row['nombre']}"
        else:
            stop_num += 1
            color = STOP_COLORS[(stop_num - 1) % len(STOP_COLORS)]
            tooltip_text = f"<b>Parada {stop_num}</b><br>{row['nombre']}<br><i>{addr}</i>"

        folium.CircleMarker(
            location=[row["latitud"], row["longitud"]],
            radius=14 if is_depot else 11,
            color="white",
            weight=2,
            fill=True,
            fill_color=color,
            fill_opacity=0.92,
            tooltip=folium.Tooltip(tooltip_text, sticky=True),
        ).add_to(m)

        # Stop number label
        label_html = "D" if is_depot else str(stop_num)

        folium.Marker(
            location=[row["latitud"], row["longitud"]],
            icon=folium.DivIcon(
                html=f'<div style="font-family:Inter,sans-serif;font-size:11px;'
                     f'font-weight:700;color:white;text-align:center;'
                     f'line-height:22px;">{label_html}</div>',
                icon_size=(22, 22),
                icon_anchor=(11, 11),
            ),
        ).add_to(m)

    return m


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Configuración")
    st.markdown("---")
    st.markdown("**Depósito / Punto de Partida**")
    depot_name = st.text_input(
        "Nombre del depósito",
        value="Depósito - Barranquilla",
        key="depot_name",
        placeholder="ej. Bodega Norte",
    )
    depot_address = st.text_input(
        "Dirección del depósito",
        value="Carrera 53 #68-50, Barranquilla, Colombia",
        key="depot_address",
        placeholder="ej. Carrera 53 #68-50, Barranquilla",
        help="Dirección completa del punto de partida. Será geocodificada automáticamente.",
    )

    st.markdown("---")
    st.markdown("**Subir Archivo de Clientes**")
    st.markdown(
        '<span style="font-size:0.78rem;color:#94a3b8;">Columnas requeridas: <code>nombre</code>, <code>direccion</code></span>',
        unsafe_allow_html=True,
    )
    uploaded_file = st.file_uploader(
        "CSV o Excel con columnas: nombre, direccion",
        type=["csv", "xlsx", "xls"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    optimize_btn = st.button("Geocodificar y Optimizar Ruta", use_container_width=True)

    st.markdown("---")
    st.markdown("""
    <div style="font-size:0.75rem;color:#64748b;line-height:1.6;">
    <b>Cómo funciona</b><br>
    1. Sube la lista de clientes (nombre + direccion)<br>
    2. Configura las coordenadas del depósito<br>
    3. Haz clic en Geocodificar y Optimizar Ruta<br>
    4. Ve el mapa y la tabla optimizados
    </div>
    """, unsafe_allow_html=True)

    # Sample download - uses nombre + direccion
    sample_df = pd.DataFrame({
        "nombre": ["Cliente A", "Cliente B", "Cliente C", "Cliente D", "Cliente E"],
        "direccion": [
            "Calle 72 #57-43, Barranquilla, Colombia",
            "Carrera 46 #76-20, Barranquilla, Colombia",
            "Calle 84 #46-112, Barranquilla, Colombia",
            "Avenida El Dorado #68B-31, Bogota, Colombia",
            "Carrera 7 #32-29, Bogota, Colombia",
        ],
    })
    csv_sample = sample_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Descargar CSV de Ejemplo",
        data=csv_sample,
        file_name="clientes_ejemplo.csv",
        mime="text/csv",
        use_container_width=True,
    )


# ── Main area ─────────────────────────────────────────────────────────────────
st.markdown('<p class="hero-title">Optimizador de Rutas Logísticas</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-sub">Sube una lista de clientes con direcciones &mdash; la aplicación las geocodifica vía '
    'Google Maps, resuelve el TSP con OR-Tools y visualiza la ruta óptima en un mapa interactivo.</p>',
    unsafe_allow_html=True,
)

# ── State ─────────────────────────────────────────────────────────────────────
if "result" not in st.session_state:
    st.session_state.result = None

# ── Run optimization ──────────────────────────────────────────────────────────
if optimize_btn:
    if not depot_address.strip():
        st.error("Por favor ingresa una dirección de depósito en la barra lateral.")
    elif uploaded_file is None:
        st.error("Por favor sube un archivo de clientes primero.")
    else:
        try:
            # ── 1. Read file ──────────────────────────────────────────────────
            if uploaded_file.name.endswith(".csv"):
                df_clients = pd.read_csv(uploaded_file)
            else:
                df_clients = pd.read_excel(uploaded_file)

            df_clients.columns = df_clients.columns.str.strip().str.lower()

            required = {"nombre", "direccion"}
            if not required.issubset(set(df_clients.columns)):
                st.error(
                    f"El archivo debe contener las columnas: {', '.join(sorted(required))}. "
                    f"Encontradas: {', '.join(df_clients.columns)}"
                )
                st.stop()

            df_clients = df_clients[["nombre", "direccion"]].dropna(subset=["direccion"])
            df_clients["nombre"] = df_clients["nombre"].fillna("(sin nombre)")
            df_clients = df_clients.reset_index(drop=True)

            if len(df_clients) < 1:
                st.error("No se encontraron filas válidas en el archivo.")
                st.stop()

            # ── 2. Geocode depot address ──────────────────────────────────────
            with st.spinner("Geocodificando dirección del depósito..."):
                depot_lat, depot_lon, depot_fmt = geocode_address(depot_address.strip(), GOOGLE_MAPS_API_KEY)
            if depot_lat is None:
                st.error(
                    f"No se pudo geocodificar la dirección del depósito: {depot_fmt}. "
                    "Revisa la dirección y tu clave de API."
                )
                st.stop()

            # ── 3. Geocode client addresses ───────────────────────────────────
            st.markdown('<p class="section-header">Geocodificando Direcciones de Clientes</p>', unsafe_allow_html=True)
            geo_progress = st.progress(0)
            geo_status = st.empty()

            df_geocoded = geocode_dataframe(df_clients, GOOGLE_MAPS_API_KEY, geo_progress, geo_status)
            geo_status.empty()

            failed = df_geocoded[~df_geocoded["geocode_ok"]]
            succeeded = df_geocoded[df_geocoded["geocode_ok"]].reset_index(drop=True)

            # Show geocoding summary expander
            fail_count = len(failed)
            ok_count = len(succeeded)
            expander_label = (
                f"{ok_count} geocodificados exitosamente  |  "
                f"{'ADVERTENCIA: ' + str(fail_count) + ' fallaron' if fail_count else '0 fallaron'}"
            )
            with st.expander(expander_label, expanded=(fail_count > 0)):
                display_cols = ["nombre", "direccion", "direccion_formateada"]
                st.dataframe(
                    df_geocoded[display_cols].rename(columns={
                        "nombre": "Cliente",
                        "direccion": "Dirección Ingresada",
                        "direccion_formateada": "Dirección Geocodificada",
                    }),
                    use_container_width=True,
                    hide_index=True,
                )
                if fail_count:
                    st.warning(
                        f"{fail_count} dirección(es) no pudieron ser geocodificadas y serán omitidas: "
                        + ", ".join(failed["nombre"].tolist())
                    )

            if ok_count < 1:
                st.error("Ninguna dirección pudo ser geocodificada. Revisa tu clave de API y las direcciones.")
                st.stop()

            # ── 4. Build full dataframe: depot first ──────────────────────────
            depot_row = pd.DataFrame([{
                "nombre": depot_name,
                "direccion": depot_address.strip(),
                "latitud": depot_lat,
                "longitud": depot_lon,
                "direccion_formateada": depot_fmt,
                "geocode_ok": True,
            }])
            df_all = pd.concat([depot_row, succeeded], ignore_index=True)

            locations = list(zip(df_all["latitud"], df_all["longitud"]))

            # ── 4. Solve TSP ──────────────────────────────────────────────────
            with st.spinner("Resolviendo el TSP con OR-Tools... esto puede tomar unos segundos."):
                route, total_km = solve_tsp(locations)

            if route is None:
                st.error("OR-Tools no pudo encontrar una solución. Intenta con más/diferentes datos.")
                st.stop()

            # ── 5. Build route table ──────────────────────────────────────────
            route_rows = []
            stop_num = 0
            for order, node_idx in enumerate(route):
                is_depot = (node_idx == 0)
                if is_depot and order == len(route) - 1:
                    client_label = "Regreso al Depósito"
                    stop_label = "Depósito (Regreso)"
                    addr_label = depot_name
                elif is_depot:
                    client_label = depot_name
                    stop_label = "Depósito (Inicio)"
                    addr_label = depot_name
                else:
                    stop_num += 1
                    client_label = df_all.iloc[node_idx]["nombre"]
                    stop_label = f"Parada {stop_num}"
                    addr_label = df_all.iloc[node_idx]["direccion_formateada"]

                if order < len(route) - 1:
                    ni = route[order]
                    nj = route[order + 1]
                    leg_km = haversine_km(
                        df_all.iloc[ni]["latitud"], df_all.iloc[ni]["longitud"],
                        df_all.iloc[nj]["latitud"], df_all.iloc[nj]["longitud"],
                    )
                    leg_str = f"{leg_km:.2f}"
                else:
                    leg_str = "-"

                route_rows.append({
                    "Orden": stop_label,
                    "Cliente": client_label,
                    "Dirección": addr_label,
                    "Tramo (km)": leg_str,
                })

            route_df = pd.DataFrame(route_rows)

            # ── 6. Build map ──────────────────────────────────────────────────
            fmap = build_map(df_all, route)

            st.session_state.result = {
                "route": route,
                "total_km": total_km,
                "route_df": route_df,
                "fmap": fmap,
                "n_clients": ok_count,
                "n_failed": fail_count,
            }

        except Exception as e:
            st.error(f"Error: {e}")
            import traceback
            st.code(traceback.format_exc())

# ── Show results ──────────────────────────────────────────────────────────────
if st.session_state.result:
    res = st.session_state.result

    st.markdown("---")

    # Metric cards
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{res['n_clients']}</div>
            <div class="metric-label">Clientes geocodificados</div>
        </div>""", unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{res['total_km']:.1f} km</div>
            <div class="metric-label">Distancia total de la ruta</div>
        </div>""", unsafe_allow_html=True)
    with m3:
        stops = len(res["route"]) - 1   # exclude return leg
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{stops}</div>
            <div class="metric-label">Total de paradas (inc. depósito)</div>
        </div>""", unsafe_allow_html=True)
    with m4:
        skipped = res.get("n_failed", 0)
        val_color = "#ef4444" if skipped else "#34d399"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="background:linear-gradient(90deg,{val_color},{val_color});
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">
                {skipped}
            </div>
            <div class="metric-label">Direcciones omitidas</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Map + Table side by side
    col_map, col_table = st.columns([3, 2], gap="large")

    with col_map:
        st.markdown('<p class="section-header">Mapa de la Ruta Optimizada</p>', unsafe_allow_html=True)
        st_folium(res["fmap"], width=None, height=520, returned_objects=[])

    with col_table:
        st.markdown('<p class="section-header">Secuencia de Paradas</p>', unsafe_allow_html=True)
        st.dataframe(
            res["route_df"],
            use_container_width=True,
            hide_index=True,
            height=490,
        )

    # Download route table
    st.markdown("---")
    csv_out = res["route_df"].to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Descargar CSV de Ruta Optimizada",
        data=csv_out,
        file_name="ruta_optimizada.csv",
        mime="text/csv",
    )

else:
    # Empty state
    st.markdown("""
    <div style="text-align:center;padding:4rem 2rem;opacity:0.5;">
        <div style="font-size:5rem;">🗺️</div>
        <div style="font-size:1.1rem;margin-top:1rem;color:#94a3b8;">
            Sube un archivo de clientes, configura la dirección del depósito, y haz clic en
            <b>Geocodificar y Optimizar Ruta</b> para comenzar.
        </div>
    </div>
    """, unsafe_allow_html=True)
