import streamlit as st
import pandas as pd
import numpy as np
import random
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="India AQI Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Theme Definitions ─────────────────────────────────────────────────────────
THEMES = {
    "🌌 Galaxy": {
        "bg": "linear-gradient(135deg,#0f0a1e,#1e1040)",
        "sidebar_bg": "linear-gradient(180deg,#050010,#0f0a1e)",
        "sidebar_text": "#ddd6fe", "sidebar_btn": "#6d28d9", "sidebar_btn_text": "#ddd6fe",
        "card_border": "#2e1065", "card_accent": "#7c3aed",
        "h1": "#ddd6fe", "h2": "#c4b5fd", "text": "#ede9fe",
        "btn_bg": "#1e1040", "btn_text": "#ddd6fe", "btn_hover": "#6d28d9",
        "select_border": "#6d28d9", "hr": "#2e1065",
        "progress": "linear-gradient(90deg,#6d28d9,#a855f7)", "caption": "#a855f7",
        "aqi_scale": ["#34d399","#818cf8","#c084fc","#f472b6","#f97316","#7c3aed"],
    },
}

def apply_theme(t):
    st.markdown(f"""
<style>
.stApp {{background:{t["bg"]};color:{t["text"]};}}
[data-testid="stSidebar"]{{background:{t["sidebar_bg"]} !important;}}
[data-testid="stSidebar"] *{{color:{t["sidebar_text"]} !important;}}
[data-testid="stSidebar"] .stButton>button{{background:{t["sidebar_btn"]} !important;color:{t["sidebar_btn_text"]} !important;border:none !important;font-weight:700 !important;border-radius:8px !important;}}
[data-testid="stSidebar"] hr{{border-color:{t["sidebar_btn"]} !important;}}
h1{{color:{t["h1"]} !important;}}
h2,h3{{color:{t["h2"]} !important;}}
[data-testid="metric-container"]{{background:rgba(255,255,255,0.08);border:2px solid {t["card_border"]};border-left:5px solid {t["card_accent"]};border-radius:12px;padding:16px 20px !important;box-shadow:0 2px 12px rgba(0,0,0,0.12);}}
[data-testid="metric-container"] label{{color:{t["h2"]} !important;font-weight:600 !important;}}
[data-testid="metric-container"] [data-testid="stMetricValue"]{{color:{t["h1"]} !important;font-weight:800 !important;}}
[data-testid="metric-container"] [data-testid="stMetricDelta"]{{color:{t["card_accent"]} !important;}}
.stButton>button{{background:{t["btn_bg"]} !important;color:{t["btn_text"]} !important;border:none !important;border-radius:8px !important;font-weight:600 !important;}}
.stButton>button:hover{{background:{t["btn_hover"]} !important;}}
[data-baseweb="select"]>div{{border-color:{t["select_border"]} !important;border-radius:8px !important;}}
hr{{border-color:{t["hr"]} !important;}}
[data-testid="stPlotlyChart"]{{border:1.5px solid {t["card_border"]};border-radius:12px;padding:8px;background:rgba(255,255,255,0.05);}}
[data-testid="stProgressBar"]>div>div{{background:{t["progress"]} !important;}}
.stCaption{{color:{t["caption"]} !important;}}
</style>""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
CITIES = [
    {"name": "Delhi",         "lat": 28.61, "lon": 77.20, "state": "Delhi"},
    {"name": "Mumbai",        "lat": 19.07, "lon": 72.87, "state": "Maharashtra"},
    {"name": "Kolkata",       "lat": 22.57, "lon": 88.36, "state": "West Bengal"},
    {"name": "Chennai",       "lat": 13.08, "lon": 80.27, "state": "Tamil Nadu"},
    {"name": "Bangalore",     "lat": 12.97, "lon": 77.59, "state": "Karnataka"},
    {"name": "Hyderabad",     "lat": 17.38, "lon": 78.48, "state": "Telangana"},
    {"name": "Ahmedabad",     "lat": 23.02, "lon": 72.57, "state": "Gujarat"},
    {"name": "Pune",          "lat": 18.52, "lon": 73.85, "state": "Maharashtra"},
    {"name": "Jaipur",        "lat": 26.91, "lon": 75.79, "state": "Rajasthan"},
    {"name": "Lucknow",       "lat": 26.84, "lon": 80.94, "state": "Uttar Pradesh"},
    {"name": "Kanpur",        "lat": 26.44, "lon": 80.33, "state": "Uttar Pradesh"},
    {"name": "Nagpur",        "lat": 21.14, "lon": 79.08, "state": "Maharashtra"},
    {"name": "Patna",         "lat": 25.59, "lon": 85.13, "state": "Bihar"},
    {"name": "Bhopal",        "lat": 23.25, "lon": 77.40, "state": "Madhya Pradesh"},
    {"name": "Surat",         "lat": 21.19, "lon": 72.83, "state": "Gujarat"},
    {"name": "Chandigarh",    "lat": 30.73, "lon": 76.78, "state": "Chandigarh"},
    {"name": "Varanasi",      "lat": 25.31, "lon": 82.97, "state": "Uttar Pradesh"},
    {"name": "Agra",          "lat": 27.17, "lon": 78.01, "state": "Uttar Pradesh"},
    {"name": "Amritsar",      "lat": 31.63, "lon": 74.87, "state": "Punjab"},
    {"name": "Visakhapatnam", "lat": 17.68, "lon": 83.21, "state": "Andhra Pradesh"},
    {"name": "Indore",        "lat": 22.72, "lon": 75.86, "state": "Madhya Pradesh"},
    {"name": "Coimbatore",    "lat": 11.01, "lon": 76.97, "state": "Tamil Nadu"},
    {"name": "Kochi",         "lat":  9.93, "lon": 76.26, "state": "Kerala"},
    {"name": "Guwahati",      "lat": 26.14, "lon": 91.74, "state": "Assam"},
    {"name": "Bhubaneswar",   "lat": 20.29, "lon": 85.82, "state": "Odisha"},
]

POLLUTANTS  = ["PM2.5", "PM10", "NO2", "SO2", "CO", "O3"]
SAFE_LIMITS = {"PM2.5": 60, "PM10": 100, "NO2": 80, "SO2": 80, "CO": 2.0, "O3": 100}
UNITS       = {"PM2.5": "µg/m³", "PM10": "µg/m³", "NO2": "µg/m³",
               "SO2": "µg/m³", "CO": "mg/m³", "O3": "µg/m³"}

AQI_SCALE = [
    (0,   50,  "Good",         "#22c55e"),
    (51,  100, "Satisfactory", "#84cc16"),
    (101, 200, "Moderate",     "#eab308"),
    (201, 300, "Poor",         "#f97316"),
    (301, 400, "Very Poor",    "#ef4444"),
    (401, 500, "Severe",       "#8b5cf6"),
]

# ── Helpers ───────────────────────────────────────────────────────────────────
def get_aqi_info(aqi):
    for lo, hi, label, color in AQI_SCALE:
        if lo <= aqi <= hi:
            return label, color
    return "Severe", "#8b5cf6"

def aqi_emoji(aqi):
    if aqi <= 50:  return "🟢"
    if aqi <= 100: return "🟡"
    if aqi <= 200: return "🟠"
    if aqi <= 300: return "🔴"
    if aqi <= 400: return "🟣"
    return "⚫"

def simulate_pollutants(aqi):
    factor = aqi / 150
    return {p: round(SAFE_LIMITS[p] * factor * random.uniform(0.65, 1.35), 2)
            for p in POLLUTANTS}

def generate_data():
    rows = []
    for c in CITIES:
        aqi = random.randint(25, 490)
        label, color = get_aqi_info(aqi)
        poll = simulate_pollutants(aqi)
        rows.append({
            "City": c["name"], "State": c["state"],
            "Lat": c["lat"],   "Lon": c["lon"],
            "AQI": aqi, "Category": label, "Color": color,
            **poll,
        })
    return pd.DataFrame(rows)

def pollutant_status(val, safe):
    if val <= safe:       return "✅ Safe"
    if val <= safe * 1.5: return "⚠️ Moderate"
    return "🚨 Unsafe"

# ── Session state ─────────────────────────────────────────────────────────────
if "df" not in st.session_state:
    st.session_state.df = generate_data()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🌍 India AQI Monitor")
    st.divider()

    chosen_theme = st.selectbox(
        "🎨 Dashboard Theme",
        list(THEMES.keys()),
        index=10,
        key="theme_choice",
    )
    apply_theme(THEMES[chosen_theme])

    st.divider()

    if st.button("🔄 Refresh Data", use_container_width=True):
        st.session_state.df = generate_data()
        st.rerun()

    st.divider()
    view_mode = st.radio(
        "📊 Select View",
        ["🗺️ Pollution Map",
         "📊 City Comparison",
         "📈 Hourly Trend",
         "🧪 Pollutant Breakdown",
         "🏆 Rankings & Stats",
         "📸 Image Predictor"],
    )

    st.divider()
    st.subheader("🔍 Filters")
    aqi_range = st.slider("AQI Range", 0, 500, (0, 500))
    all_states = sorted(st.session_state.df["State"].unique())
    selected_states = st.multiselect("Filter by State", all_states)

    st.divider()
    st.subheader("📋 AQI Legend")
    for lo, hi, label, color in AQI_SCALE:
        st.markdown(f"{aqi_emoji((lo+hi)//2)} **{lo}–{hi}** — {label}")

df = st.session_state.df

# Dynamic AQI scale colors from theme
_tc = THEMES[st.session_state.get("theme_choice", "🌌 Galaxy")]["aqi_scale"]
AQI_SCALE = [
    (0,   50,  "Good",         _tc[0]),
    (51,  100, "Satisfactory", _tc[1]),
    (101, 200, "Moderate",     _tc[2]),
    (201, 300, "Poor",         _tc[3]),
    (301, 400, "Very Poor",    _tc[4]),
    (401, 500, "Severe",       _tc[5]),
]

# Apply filters
dff = df[(df["AQI"] >= aqi_range[0]) & (df["AQI"] <= aqi_range[1])]
if selected_states:
    dff = dff[dff["State"].isin(selected_states)]

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🌍 India Air Quality Index Dashboard")
st.caption("Simulated AQI sensor data across 25 major Indian cities · Refresh for new readings")
st.divider()

# ── Top Metrics ───────────────────────────────────────────────────────────────
avg_aqi   = int(df["AQI"].mean())
worst     = df.loc[df["AQI"].idxmax()]
best      = df.loc[df["AQI"].idxmin()]
dangerous = int((df["AQI"] > 200).sum())
avg_label, _ = get_aqi_info(avg_aqi)

c1, c2, c3, c4 = st.columns(4)
c1.metric("🌡️ National Avg AQI", avg_aqi,       avg_label)
c2.metric("☣️ Most Polluted",     worst["City"], f"AQI {worst['AQI']}")
c3.metric("🌿 Cleanest City",     best["City"],  f"AQI {best['AQI']}")
c4.metric("⚠️ High Risk Cities",  dangerous,     "AQI > 200")

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# VIEW 1 — POLLUTION MAP
# ═══════════════════════════════════════════════════════════════════════════════
if "Map" in view_mode:
    col_left, col_right = st.columns([3, 1])

    with col_left:
        st.subheader("🗺️ India Pollution Map")
        map_metric = st.selectbox("Show on map bubbles", ["AQI"] + POLLUTANTS, key="map_metric")
        map_style  = st.selectbox("Map theme",
                                  ["carto-darkmatter", "open-street-map", "carto-positron"],
                                  key="map_style")

        dff2 = dff.copy()
        dff2["size_val"] = dff2["AQI"].apply(lambda v: max(8, min(40, v / 10)))
        dff2["label"]    = dff2.apply(
            lambda r: f"{r['City']}\nAQI {r['AQI']} ({r['Category']})\n"
                      f"PM2.5: {r['PM2.5']} | PM10: {r['PM10']}\n"
                      f"NO2: {r['NO2']} | SO2: {r['SO2']} | CO: {r['CO']} | O3: {r['O3']}",
            axis=1,
        )

        fig_map = go.Figure(go.Scattermapbox(
            lat=dff2["Lat"], lon=dff2["Lon"],
            mode="markers+text",
            marker=dict(
                size=dff2["size_val"],
                color=dff2["AQI"],
                colorscale=[
                    [0.00, "#22c55e"], [0.10, "#22c55e"],
                    [0.10, "#84cc16"], [0.20, "#84cc16"],
                    [0.20, "#eab308"], [0.40, "#eab308"],
                    [0.40, "#f97316"], [0.60, "#f97316"],
                    [0.60, "#ef4444"], [0.80, "#ef4444"],
                    [0.80, "#8b5cf6"], [1.00, "#8b5cf6"],
                ],
                cmin=0, cmax=500,
                colorbar=dict(title="AQI", thickness=14, len=0.6),
                opacity=0.85,
            ),
            text=dff2[map_metric].round(0).astype(int).astype(str),
            textfont=dict(size=9, color="white"),
            textposition="middle center",
            hovertext=dff2["label"],
            hoverinfo="text",
        ))
        fig_map.update_layout(
            mapbox=dict(style=map_style, center=dict(lat=22.5, lon=82.0), zoom=3.8),
            margin=dict(l=0, r=0, t=0, b=0),
            height=520,
        )
        st.plotly_chart(fig_map, use_container_width=True)

    with col_right:
        st.subheader("📋 City Rankings")
        ranked = dff.sort_values("AQI", ascending=False)[
            ["City", "AQI", "Category"]
        ].reset_index(drop=True)
        ranked.index += 1
        for _, row in ranked.iterrows():
            em = aqi_emoji(row["AQI"])
            st.write(f"{em} **{row['City']}** — {row['AQI']} ({row['Category']})")

    st.divider()
    st.subheader("📄 Full City Data Table")
    show_df = dff[["City", "State", "AQI", "Category"] + POLLUTANTS].sort_values(
        "AQI", ascending=False
    ).reset_index(drop=True)
    show_df.index += 1
    st.dataframe(
        show_df.style.background_gradient(subset=["AQI"], cmap="RdYlGn_r"),
        use_container_width=True,
        height=320,
    )

# ═══════════════════════════════════════════════════════════════════════════════
# VIEW 2 — CITY COMPARISON
# ═══════════════════════════════════════════════════════════════════════════════
elif "Comparison" in view_mode:
    st.subheader("📊 City AQI Comparison")

    col_a, col_b = st.columns(2)
    with col_a:
        top_n   = st.slider("Number of cities", 5, 25, 15, key="top_n")
    with col_b:
        sort_by = st.selectbox("Sort / colour by", ["AQI"] + POLLUTANTS, key="sort_by")

    sorted_df = dff.sort_values(sort_by, ascending=False).head(top_n)

    fig_bar = go.Figure(go.Bar(
        x=sorted_df["City"],
        y=sorted_df[sort_by],
        marker_color=sorted_df["Color"],
        marker_line_width=0,
        text=sorted_df[sort_by].round(1),
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>" + sort_by + ": %{y}<extra></extra>",
    ))
    unit = UNITS.get(sort_by, "")
    fig_bar.update_layout(
        xaxis=dict(tickangle=-38, title="City"),
        yaxis=dict(title=f"{sort_by} ({unit})" if unit else sort_by),
        height=420,
        margin=dict(l=60, r=20, t=30, b=100),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()
    st.subheader("🥧 AQI Category Distribution")
    cat_order  = ["Good", "Satisfactory", "Moderate", "Poor", "Very Poor", "Severe"]
    cat_colors = [c[3] for c in AQI_SCALE]
    cat_counts = df["Category"].value_counts().reindex(cat_order, fill_value=0)

    fig_pie = go.Figure(go.Pie(
        labels=cat_counts.index,
        values=cat_counts.values,
        marker_colors=cat_colors,
        hole=0.45,
        hovertemplate="<b>%{label}</b><br>Cities: %{value} (%{percent})<extra></extra>",
    ))
    fig_pie.update_layout(height=320, margin=dict(l=0, r=0, t=20, b=0))
    st.plotly_chart(fig_pie, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# VIEW 3 — HOURLY TREND
# ═══════════════════════════════════════════════════════════════════════════════
elif "Trend" in view_mode:
    st.subheader("📈 24-Hour AQI Trend")

    city_options    = df["City"].tolist()
    selected_cities = st.multiselect(
        "Select cities to compare (up to 6)",
        city_options,
        default=["Delhi", "Mumbai", "Bangalore", "Chennai"],
        key="trend_cities",
    )

    if not selected_cities:
        st.info("Please select at least one city above.")
    else:
        hours       = list(range(24))
        hour_labels = [f"{h:02d}:00" for h in hours]
        palette     = ["#3b82f6", "#ef4444", "#22c55e", "#f97316", "#8b5cf6", "#06b6d4"]

        fig_line = go.Figure()
        for i, city in enumerate(selected_cities[:6]):
            base  = int(df.loc[df["City"] == city, "AQI"].values[0])
            trend = [
                max(20, min(500, int(
                    base + 55 * np.sin((h - 6) * np.pi / 12) + random.randint(-25, 25)
                )))
                for h in hours
            ]
            col = palette[i % len(palette)]
            fig_line.add_trace(go.Scatter(
                x=hour_labels, y=trend,
                mode="lines+markers",
                name=city,
                line=dict(color=col, width=2.5,
                          dash=["solid","dash","dot","dashdot","longdash","longdashdot"][i % 6]),
                marker=dict(size=5, color=col),
                hovertemplate=f"<b>{city}</b> %{{x}}: AQI %{{y}}<extra></extra>",
            ))

        for threshold, lbl in [(200, "Poor threshold"), (300, "Very Poor threshold")]:
            fig_line.add_hline(
                y=threshold, line_dash="dot", line_color="#9ca3af", opacity=0.5,
                annotation_text=lbl, annotation_font_size=11,
            )

        fig_line.update_layout(
            xaxis=dict(title="Hour", tickangle=-45),
            yaxis=dict(title="AQI", range=[0, 520]),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            height=430,
            margin=dict(l=60, r=20, t=60, b=80),
        )
        st.plotly_chart(fig_line, use_container_width=True)
        st.info(
            "💡 The trend is simulated using a sine-wave diurnal pattern "
            "(peaks around 6 AM and 6 PM) plus random noise. "
            "Connect a live API for real hourly data."
        )

# ═══════════════════════════════════════════════════════════════════════════════
# VIEW 4 — POLLUTANT BREAKDOWN
# ═══════════════════════════════════════════════════════════════════════════════
elif "Pollutant" in view_mode:
    st.subheader("🧪 Pollutant Breakdown")

    selected_city = st.selectbox("Select a city", df["City"].tolist(), key="poll_city")
    row           = df[df["City"] == selected_city].iloc[0]
    label, color  = get_aqi_info(row["AQI"])

    c1, c2, c3 = st.columns(3)
    c1.metric("🏙️ City",    selected_city, row["State"])
    c2.metric("🌡️ AQI",     row["AQI"],    label)
    c3.metric("📍 Primary", max(POLLUTANTS, key=lambda p: row[p] / SAFE_LIMITS[p]), "highest vs safe")

    st.divider()

    col_bars, col_radar = st.columns(2)

    with col_bars:
        st.subheader("📊 vs Safe Limit")
        for p in POLLUTANTS:
            val    = row[p]
            safe   = SAFE_LIMITS[p]
            pct    = min(val / (safe * 3), 1.0)
            status = pollutant_status(val, safe)
            st.write(f"**{p}** — {val} {UNITS[p]}   {status}   *(safe ≤ {safe})*")
            st.progress(float(pct))   # FIX: cast to float explicitly

 

    with col_radar:
        st.subheader("🕸️ Radar Overview")

    pct_vals = [
        float(min(row[p] / (SAFE_LIMITS[p] * 2) * 100, 100))
        for p in POLLUTANTS
    ]

    theta = POLLUTANTS + [POLLUTANTS[0]]
    r_vals = pct_vals + [pct_vals[0]]

    fig_radar = go.Figure()

    fig_radar.add_trace(go.Scatterpolar(
        r=r_vals,
        theta=theta,
        fill='toself',
        fillcolor='rgba(0,123,255,0.3)',
        line=dict(color='blue', width=2),
        marker=dict(color='blue', size=7)
    ))

    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=False,
        height=340,
        margin=dict(l=40, r=40, t=20, b=20),
    )

    st.plotly_chart(fig_radar, use_container_width=True)

    st.divider()
    st.subheader("🔍 Compare All Cities — Single Pollutant")
    focus_poll = st.selectbox("Choose pollutant", POLLUTANTS, key="focus_poll")
    cmp_df     = df[["City", focus_poll]].sort_values(focus_poll, ascending=True)
    safe_val   = SAFE_LIMITS[focus_poll]

    bar_colors = [
        "#22c55e" if v <= safe_val else
        "#eab308" if v <= safe_val * 1.5 else "#ef4444"
        for v in cmp_df[focus_poll]
    ]
    fig_hbar = go.Figure(go.Bar(
        x=cmp_df[focus_poll], y=cmp_df["City"],
        orientation="h",
        marker_color=bar_colors,
        marker_line_width=0,
        text=cmp_df[focus_poll].astype(str) + f" {UNITS[focus_poll]}",
        textposition="outside",
        hovertemplate="<b>%{y}</b>: %{x}<extra></extra>",
    ))
    fig_hbar.add_vline(
        x=safe_val, line_dash="dash", line_color="#3b82f6",
        annotation_text=f"Safe limit ({safe_val} {UNITS[focus_poll]})",
        annotation_font_size=11,
    )
    fig_hbar.update_layout(
        xaxis=dict(title=UNITS[focus_poll]),
        yaxis=dict(showgrid=False),
        height=560,
        margin=dict(l=120, r=80, t=20, b=40),
    )
    st.plotly_chart(fig_hbar, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# VIEW 5 — RANKINGS & STATS
# ═══════════════════════════════════════════════════════════════════════════════
elif "Rankings" in view_mode:
    st.subheader("🏆 Rankings & Statistics")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🌿 Top 10 Cleanest Cities")
        best10 = df.nsmallest(10, "AQI")[["City", "State", "AQI", "Category"]].reset_index(drop=True)
        best10.index += 1
        for _, r in best10.iterrows():
            em = aqi_emoji(r["AQI"])
            st.write(f"{em} **{r['City']}** ({r['State']}) — AQI {r['AQI']} · {r['Category']}")

    with col2:
        st.subheader("☣️ Top 10 Most Polluted Cities")
        worst10 = df.nlargest(10, "AQI")[["City", "State", "AQI", "Category"]].reset_index(drop=True)
        worst10.index += 1
        for _, r in worst10.iterrows():
            em = aqi_emoji(r["AQI"])
            st.write(f"{em} **{r['City']}** ({r['State']}) — AQI {r['AQI']} · {r['Category']}")

    st.divider()
    st.subheader("📊 AQI Statistics by State")
    state_stats = df.groupby("State")["AQI"].agg(
        Avg="mean", Max="max", Min="min", Cities="count"
    ).round(1).sort_values("Avg", ascending=False).reset_index()

    fig_state = px.bar(
        state_stats, x="State", y="Avg",
        color="Avg",
        color_continuous_scale=[[0, "#22c55e"], [0.4, "#eab308"], [0.7, "#ef4444"], [1, "#8b5cf6"]],
        range_color=[0, 500],
        hover_data={"Max": True, "Min": True, "Cities": True},
        text=state_stats["Avg"].astype(int),
        labels={"Avg": "Average AQI"},
    )
    fig_state.update_layout(
        coloraxis_showscale=False,
        xaxis=dict(tickangle=-35),
        height=380,
        margin=dict(l=60, r=20, t=20, b=100),
    )
    fig_state.update_traces(textposition="outside")
    st.plotly_chart(fig_state, use_container_width=True)

    st.divider()
    st.subheader("🔗 Pollutant Correlation Heatmap")
    corr    = df[["AQI"] + POLLUTANTS].corr().round(2)
    fig_heat = go.Figure(go.Heatmap(
        z=corr.values, x=list(corr.columns), y=list(corr.index),
        colorscale="RdYlGn", zmin=-1, zmax=1,
        text=corr.values.round(2),
        texttemplate="%{text}",
        textfont=dict(size=12),
        hovertemplate="%{x} × %{y}: %{z}<extra></extra>",
    ))
    fig_heat.update_layout(height=340, margin=dict(l=80, r=20, t=20, b=60))
    st.plotly_chart(fig_heat, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# VIEW 6 — IMAGE PREDICTOR  (merged from app.py / app_.py)
# ═══════════════════════════════════════════════════════════════════════════════
elif "Image" in view_mode:
    st.subheader("📸 Image-Based Air Quality Predictor")
    st.write("Upload an image and get a simulated air quality prediction.")

    uploaded_file = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        img = Image.open(uploaded_file)
        st.image(img, caption="Uploaded Image", use_container_width=True)

        if st.button("Predict"):
            pollution = random.randint(1, 100)

            if pollution <= 20:
                status = "🌿 Very Good"
                msg    = "Air is Healthy"
            elif pollution <= 40:
                status = "✅ Good"
                msg    = "Air quality is Healthy"
            elif pollution <= 60:
                status = "😐 Moderate"
                msg    = "Air quality is Average"
            elif pollution <= 80:
                status = "⚠️ Unhealthy"
                msg    = "Air quality is Unhealthy"
            else:
                status = "🚨 Very Unhealthy"
                msg    = "Air quality is Dangerous"

            st.subheader("Prediction Result")
            st.metric("Pollution Percentage", f"{pollution}%")

            # FIX: st.progress() requires float 0.0–1.0
            st.progress(pollution / 100)

            st.subheader("Health Status")
            st.write(status)

            if pollution <= 40:
                st.success(msg)
            elif pollution <= 60:
                st.warning(msg)
            else:
                st.error(msg)

            st.subheader("Pollution Graph")
            chart = pd.DataFrame({"Level": [pollution]}, index=["Current"])
            st.bar_chart(chart)

            st.subheader("Air Quality Scale")
            st.write("""
| Emoji | Level          | Range      |
|-------|----------------|------------|
| 🌿    | Very Good      | 0 – 20%    |
| ✅    | Good           | 21 – 40%   |
| 😐    | Moderate       | 41 – 60%   |
| ⚠️    | Unhealthy      | 61 – 80%   |
| 🚨    | Very Unhealthy | 81 – 100%  |
""")

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "📡 Data is simulated · "
    "For live readings connect to CPCB API or WAQI (aqicn.org/api) · "
    "Built with Streamlit + Plotly"
)
