"""Patch script: replaces the old sidebar block in app.py with the new one
that includes the Google Maps API key field and direccion-based sample CSV."""

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# ── locate marker lines ───────────────────────────────────────────────────────
START_MARKER = "# \u2500\u2500 Sidebar \u2500"
END_MARKER   = "\n\n# \u2500\u2500 Main area"   # the block that comes after

start = content.find(START_MARKER)
end   = content.find(END_MARKER)

if start == -1 or end == -1:
    print(f"ERROR: markers not found  start={start}  end={end}")
    raise SystemExit(1)

NEW_SIDEBAR = '''# \u2500\u2500 Sidebar \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
with st.sidebar:
    st.markdown("### \u2699\ufe0f Configuration")
    st.markdown("---")

    st.markdown("**\ud83d\udd11 Google Maps API Key**")
    gmaps_api_key = st.text_input(
        "API Key",
        type="password",
        placeholder="AIza\u2026",
        label_visibility="collapsed",
        help="Required for geocoding addresses. Enable the Geocoding API in your Google Cloud project.",
    )
    if gmaps_api_key:
        st.markdown(
            '<span style="color:#34d399;font-size:0.78rem;">\u2714 API key entered</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span style="color:#f59e0b;font-size:0.78rem;">\u26a0 Enter your API key to enable geocoding</span>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("**\ud83d\udccd Depot / Starting Point**")
    depot_name = st.text_input("Depot name", value="Depot - Barranquilla")
    col_lat, col_lon = st.columns(2)
    with col_lat:
        depot_lat = st.number_input("Latitude", value=10.9685, format="%.6f", step=0.0001)
    with col_lon:
        depot_lon = st.number_input("Longitude", value=-74.7813, format="%.6f", step=0.0001)

    st.markdown("---")
    st.markdown("**\ud83d\udcc1 Upload Client File**")
    st.markdown(
        \'<span style="font-size:0.78rem;color:#94a3b8;">Columns required: <code>nombre</code>, <code>direccion</code></span>\',
        unsafe_allow_html=True,
    )
    uploaded_file = st.file_uploader(
        "CSV or Excel with columns: nombre, direccion",
        type=["csv", "xlsx", "xls"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    optimize_btn = st.button("\ud83d\ude80 Geocode & Optimize Route", use_container_width=True)

    st.markdown("---")
    st.markdown("""
    <div style="font-size:0.75rem;color:#64748b;line-height:1.6;">
    <b>How it works</b><br>
    1. Enter your Google Maps API key<br>
    2. Upload your client list (nombre + direccion)<br>
    3. Set your depot coordinates<br>
    4. Click Geocode &amp; Optimize Route<br>
    5. View the optimized map &amp; table
    </div>
    """, unsafe_allow_html=True)

    # Sample download - now uses nombre + direccion
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
        "\u2b07\ufe0f Download Sample CSV",
        data=csv_sample,
        file_name="sample_clients.csv",
        mime="text/csv",
        use_container_width=True,
    )'''

patched = content[:start] + NEW_SIDEBAR + content[end:]

with open("app.py", "w", encoding="utf-8") as f:
    f.write(patched)

print("SUCCESS: sidebar patched")
print(f"  Old block was chars {start}..{end}")
print(f"  File now has {len(patched)} chars")
