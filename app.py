import streamlit as st
import pandas as pd
import numpy as np
import random
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="India AQI Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }

.main { background: #0a0e1a; }
.block-container { padding: 1.5rem 2rem; }

/* Metric cards */
.metric-card {
    background: linear-gradient(135deg, #111827 0%, #1f2937 100%);
    border: 1px solid #1e3a5f;
    border-radius: 14px;
    padding: 18px 20px;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 14px 14px 0 0;
}
.metric-card.blue::before  { background: linear-gradient(90deg, #3b82f6, #06b6d4); }
.metric-card.red::before   { background: linear-gradient(90deg, #ef4444, #f97316); }
.metric-card.green::before { background: linear-gradient(90deg, #22c55e, #84cc16); }
.metric-card.amber::before { background: linear-gradient(90deg, #f59e0b, #fbbf24); }

.metric-label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: #6b7280;
    margin-bottom: 8px;
}
.metric-value {
    font-size: 28px;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 4px;
}
.metric-sub {
    font-size: 12px;
    color: #6b7280;
}

/* AQI Badge */
.aqi-badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.3px;
}

/* Legend item */
.legend-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 0;
    font-size: 13px;
    color: #9ca3af;
}
.legend-dot {
    width: 12px; height: 12px;
    border-radius: 50%;
    flex-shrink: 0;
}

/* City row */
.city-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 6px;
    border-bottom: 1px solid #1f2937;
    font-size: 13px;
}
.city-row:last-child { border-bottom: none; }

/* Section heading */
.section-title {
    font-size: 13px;
    font-weight: 600;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 14px;
}

/* Info banner */
.info-banner {
    background: linear-gradient(90deg, #0f2744 0%, #0c2438 100%);
    border: 1px solid #1e3a5f;
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 13px;
    color: #93c5fd;
    margin-bottom: 16px;
}

div[data-testid="stSidebar"] { background: #080c17; border-right: 1px solid #1e2433; }
div[data-testid="stSidebar"] * { color: #d1d5db; }
div[data-testid="metric-container"] { background: #111827; border-radius: 10px; border: 1px solid #1f2937; }
</style>
""", unsafe_allow_html=True)

# ── Data ──────────────────────────────────────────────────────────────────────
CITIES = [
    {"name": "Delhi",           "lat": 28.61, "lon": 77.20, "state": "Delhi"},
    {"name": "Mumbai",          "lat": 19.07, "lon": 72.87, "state": "Maharashtra"},
    {"name": "Kolkata",         "lat": 22.57, "lon": 88.36, "state": "West Bengal"},
    {"name": "Chennai",         "lat": 13.08, "lon": 80.27, "state": "Tamil Nadu"},
    {"name": "Bangalore",       "lat": 12.97, "lon": 77.59, "state": "Karnataka"},
    {"name": "Hyderabad",       "lat": 17.38, "lon": 78.48, "state": "Telangana"},
    {"name": "Ahmedabad",       "lat": 23.02, "lon": 72.57, "state": "Gujarat"},
    {"name": "Pune",            "lat": 18.52, "lon": 73.85, "state": "Maharashtra"},
    {"name": "Jaipur",          "lat": 26.91, "lon": 75.79, "state": "Rajasthan"},
    {"name": "Lucknow",         "lat": 26.84, "lon": 80.94, "state": "Uttar Pradesh"},
    {"name": "Kanpur",          "lat": 26.44, "lon": 80.33, "state": "Uttar Pradesh"},
    {"name": "Nagpur",          "lat": 21.14, "lon": 79.08, "state": "Maharashtra"},
    {"name": "Patna",           "lat": 25.59, "lon": 85.13, "state": "Bihar"},
    {"name": "Bhopal",          "lat": 23.25, "lon": 77.40, "state": "Madhya Pradesh"},
    {"name": "Surat",           "lat": 21.19, "lon": 72.83, "state": "Gujarat"},
    {"name": "Chandigarh",      "lat": 30.73, "lon": 76.78, "state": "Chandigarh"},
    {"name": "Varanasi",        "lat": 25.31, "lon": 82.97, "state": "Uttar Pradesh"},
    {"name": "Agra",            "lat": 27.17, "lon": 78.01, "state": "Uttar Pradesh"},
    {"name": "Amritsar",        "lat": 31.63, "lon": 74.87, "state": "Punjab"},
    {"name": "Visakhapatnam",   "lat": 17.68, "lon": 83.21, "state": "Andhra Pradesh"},
    {"name": "Indore",          "lat": 22.72, "lon": 75.86, "state": "Madhya Pradesh"},
    {"name": "Coimbatore",      "lat": 11.01, "lon": 76.97, "state": "Tamil Nadu"},
    {"name": "Kochi",           "lat": 9.93,  "lon": 76.26, "state": "Kerala"},
    {"name": "Guwahati",        "lat": 26.14, "lon": 91.74, "state": "Assam"},
    {"name": "Bhubaneswar",     "lat": 20.29, "lon": 85.82, "state": "Odisha"},
]

POLLUTANTS   = ["PM2.5", "PM10", "NO₂", "SO₂", "CO", "O₃"]
SAFE_LIMITS  = {"PM2.5": 60, "PM10": 100, "NO₂": 80, "SO₂": 80, "CO": 2.0, "O₃": 100}
UNITS        = {"PM2.5": "µg/m³", "PM10": "µg/m³", "NO₂": "µg/m³", "SO₂": "µg/m³", "CO": "mg/m³", "O₃": "µg/m³"}

AQI_SCALE = [
    (0,   50,  "Good",         "#22c55e", "#dcfce7", "#15803d"),
    (51,  100, "Satisfactory", "#84cc16", "#ecfccb", "#4d7c0f"),
    (101, 200, "Moderate",     "#eab308", "#fef9c3", "#854d0e"),
    (201, 300, "Poor",         "#f97316", "#ffedd5", "#9a3412"),
    (301, 400, "Very Poor",    "#ef4444", "#fee2e2", "#991b1b"),
    (401, 500, "Severe",       "#8b5cf6", "#ede9fe", "#5b21b6"),
]

def get_aqi_info(aqi):
    for lo, hi, label, color, bg, tc in AQI_SCALE:
        if lo <= aqi <= hi:
            return label, color, bg, tc
    return AQI_SCALE[-1][2], AQI_SCALE[-1][3], AQI_SCALE[-1][4], AQI_SCALE[-1][5]

def simulate_pollutants(aqi):
    factor = aqi / 150
    return {
        p: round(SAFE_LIMITS[p] * factor * random.uniform(0.65, 1.35), 2)
        for p in POLLUTANTS
    }

# ── Session state / data generation ──────────────────────────────────────────
def generate_city_data():
    rows = []
    for c in CITIES:
        aqi = random.randint(25, 490)
        label, color, bg, tc = get_aqi_info(aqi)
        poll = simulate_pollutants(aqi)
        rows.append({
            "City": c["name"], "State": c["state"],
            "Lat": c["lat"],   "Lon":   c["lon"],
            "AQI": aqi, "Category": label, "Color": color,
            **poll
        })
    return pd.DataFrame(rows)

if "df" not in st.session_state or st.sidebar.button("🔄 Refresh Data"):
    st.session_state.df = generate_city_data()

df = st.session_state.df

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌍 India AQI Monitor")
    st.markdown("---")

    view_mode = st.radio(
        "📊 View Mode",
        ["🗺️ Pollution Map", "📊 City Comparison", "📈 Hourly Trend",
         "🧪 Pollutant Breakdown", "🏆 Rankings & Stats"],
        index=0
    )

    st.markdown("---")
    st.markdown("### 🎛️ Map Settings")
    map_pollutant = st.selectbox(
        "Show on Map",
        ["AQI"] + POLLUTANTS,
        index=0
    )
    map_style = st.selectbox(
        "Map Style",
        ["carto-darkmatter", "open-street-map", "carto-positron"],
        index=0
    )
    marker_size = st.slider("Marker Size", 10, 40, 22)

    st.markdown("---")
    st.markdown("### 🔍 Filter Cities")
    aqi_range = st.slider("AQI Range", 0, 500, (0, 500))
    selected_states = st.multiselect(
        "Filter by State",
        sorted(df["State"].unique()),
        default=[]
    )

    st.markdown("---")
    st.markdown("### ℹ️ AQI Scale")
    for lo, hi, label, color, bg, tc in AQI_SCALE:
        st.markdown(
            f'<div class="legend-item">'
            f'<div class="legend-dot" style="background:{color};"></div>'
            f'<span>{lo}–{hi} · <b>{label}</b></span></div>',
            unsafe_allow_html=True
        )

# ── Filter ────────────────────────────────────────────────────────────────────
dff = df[(df["AQI"] >= aqi_range[0]) & (df["AQI"] <= aqi_range[1])]
if selected_states:
    dff = dff[dff["State"].isin(selected_states)]

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    '<div style="font-size:24px;font-weight:700;color:#f9fafb;margin-bottom:4px;">'
    '🌍 India Air Quality Index Dashboard</div>'
    '<div style="font-size:13px;color:#6b7280;margin-bottom:20px;">'
    'Real-time AQI monitoring · Simulated sensor data · 25 cities</div>',
    unsafe_allow_html=True
)

# ── Metric Row ────────────────────────────────────────────────────────────────
avg_aqi   = int(df["AQI"].mean())
worst     = df.loc[df["AQI"].idxmax()]
best      = df.loc[df["AQI"].idxmin()]
dangerous = int((df["AQI"] > 200).sum())
avg_label, avg_color, _, _ = get_aqi_info(avg_aqi)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""
    <div class="metric-card blue">
        <div class="metric-label">National Avg AQI</div>
        <div class="metric-value" style="color:{avg_color};">{avg_aqi}</div>
        <div class="metric-sub">{avg_label}</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="metric-card red">
        <div class="metric-label">Most Polluted</div>
        <div class="metric-value" style="font-size:20px;color:#ef4444;">{worst['City']}</div>
        <div class="metric-sub">AQI {worst['AQI']} · {worst['Category']}</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div class="metric-card green">
        <div class="metric-label">Cleanest City</div>
        <div class="metric-value" style="font-size:20px;color:#22c55e;">{best['City']}</div>
        <div class="metric-sub">AQI {best['AQI']} · {best['Category']}</div>
    </div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""
    <div class="metric-card amber">
        <div class="metric-label">High Risk Cities</div>
        <div class="metric-value" style="color:#f97316;">{dangerous}</div>
        <div class="metric-sub">AQI &gt; 200 (Poor or worse)</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# VIEW 1 — POLLUTION MAP
# ═══════════════════════════════════════════════════════════════════════════════
if "Map" in view_mode:
    col_val = map_pollutant if map_pollutant != "AQI" else "AQI"

    # Hover text
    dff = dff.copy()
    dff["hover"] = dff.apply(lambda r: (
        f"<b>{r['City']}</b> · {r['State']}<br>"
        f"AQI: <b>{r['AQI']}</b> ({r['Category']})<br>"
        f"PM2.5: {r['PM2.5']} µg/m³<br>"
        f"PM10:  {r['PM10']} µg/m³<br>"
        f"NO₂:   {r['NO₂']} µg/m³<br>"
        f"SO₂:   {r['SO₂']} µg/m³<br>"
        f"CO:    {r['CO']} mg/m³<br>"
        f"O₃:    {r['O₃']} µg/m³"
    ), axis=1)

    fig_map = go.Figure()

    # Background India boundary (approximate)
    fig_map.add_trace(go.Scattermapbox(
        lat=dff["Lat"], lon=dff["Lon"],
        mode="markers+text",
        marker=dict(
            size=dff[col_val].apply(
                lambda v: max(marker_size * 0.5,
                              min(marker_size * 1.5, (v / 500) * marker_size * 2))
            ) if col_val == "AQI" else marker_size,
            color=dff["AQI"],
            colorscale=[
                [0.00, "#22c55e"], [0.10, "#22c55e"],
                [0.10, "#84cc16"], [0.20, "#84cc16"],
                [0.20, "#eab308"], [0.40, "#eab308"],
                [0.40, "#f97316"], [0.60, "#f97316"],
                [0.60, "#ef4444"], [0.80, "#ef4444"],
                [0.80, "#8b5cf6"], [1.00, "#8b5cf6"],
            ],
            cmin=0, cmax=500,
            colorbar=dict(
                title=dict(text="AQI", font=dict(color="#9ca3af")),
                tickfont=dict(color="#9ca3af"),
                bgcolor="#111827",
                bordercolor="#1f2937",
                thickness=14,
                len=0.6,
            ),
            opacity=0.88,
        ),
        text=dff[col_val].round(0).astype(int).astype(str),
        textfont=dict(size=10, color="white"),
        textposition="middle center",
        hovertext=dff["hover"],
        hoverinfo="text",
        name=""
    ))

    fig_map.update_layout(
        mapbox=dict(
            style=map_style,
            center=dict(lat=22.5, lon=82.0),
            zoom=4.0,
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=560,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )

    st.markdown(
        '<div class="info-banner">🔵 Circle size & colour reflect AQI severity. '
        'Hover any city for full pollutant breakdown. '
        'Use the sidebar to change the map theme or what metric is displayed.</div>',
        unsafe_allow_html=True
    )
    st.plotly_chart(fig_map, use_container_width=True)

    # City table below map
    st.markdown('<div class="section-title">City Overview</div>', unsafe_allow_html=True)
    show_df = dff[["City","State","AQI","Category","PM2.5","PM10","NO₂","SO₂","CO","O₃"]]\
                .sort_values("AQI", ascending=False)\
                .reset_index(drop=True)
    show_df.index += 1
    st.dataframe(
        show_df.style.background_gradient(subset=["AQI"], cmap="RdYlGn_r"),
        use_container_width=True, height=300
    )

# ═══════════════════════════════════════════════════════════════════════════════
# VIEW 2 — CITY COMPARISON BAR CHART
# ═══════════════════════════════════════════════════════════════════════════════
elif "Comparison" in view_mode:
    top_n = st.slider("Number of cities to show", 5, 25, 15)
    sort_by = st.selectbox("Sort by", ["AQI"] + POLLUTANTS)

    sorted_df = dff.sort_values(sort_by, ascending=False).head(top_n)

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=sorted_df["City"],
        y=sorted_df[sort_by],
        marker_color=sorted_df["Color"],
        marker_line_width=0,
        text=sorted_df[sort_by].round(1),
        textposition="outside",
        textfont=dict(color="#9ca3af", size=11),
        hovertemplate="<b>%{x}</b><br>" + sort_by + ": %{y}<extra></extra>",
    ))

    unit = UNITS.get(sort_by, "")
    fig_bar.update_layout(
        title=dict(text=f"{sort_by} by City (Top {top_n})", font=dict(color="#e5e7eb", size=14), x=0),
        xaxis=dict(tickfont=dict(color="#9ca3af"), tickangle=-35, showgrid=False, linecolor="#1f2937"),
        yaxis=dict(tickfont=dict(color="#9ca3af"), gridcolor="#1f2937",
                   title=f"{sort_by} ({unit})" if unit else sort_by,
                   title_font=dict(color="#6b7280")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=420, margin=dict(l=60, r=20, t=50, b=80),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # AQI category distribution
    st.markdown('<div class="section-title">Category Distribution</div>', unsafe_allow_html=True)
    cat_counts = df["Category"].value_counts().reindex(
        ["Good", "Satisfactory", "Moderate", "Poor", "Very Poor", "Severe"], fill_value=0
    )
    colors_cat = [c[3] for c in AQI_SCALE]
    fig_pie = go.Figure(go.Pie(
        labels=cat_counts.index,
        values=cat_counts.values,
        marker_colors=colors_cat,
        hole=0.5,
        textfont=dict(color="#fff", size=12),
        hovertemplate="<b>%{label}</b><br>Cities: %{value}<br>%{percent}<extra></extra>",
    ))
    fig_pie.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(font=dict(color="#9ca3af"), bgcolor="rgba(0,0,0,0)"),
        height=320, margin=dict(l=0, r=0, t=20, b=0),
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# VIEW 3 — HOURLY TREND
# ═══════════════════════════════════════════════════════════════════════════════
elif "Trend" in view_mode:
    selected_cities = st.multiselect(
        "Select cities to compare (max 6)",
        df["City"].tolist(),
        default=["Delhi", "Mumbai", "Bangalore", "Chennai"]
    )
    if not selected_cities:
        st.info("Please select at least one city.")
    else:
        hours = list(range(24))
        hour_labels = [f"{h:02d}:00" for h in hours]
        palette = ["#3b82f6","#ef4444","#22c55e","#f97316","#8b5cf6","#06b6d4"]

        fig_line = go.Figure()
        for i, city in enumerate(selected_cities[:6]):
            row = df[df["City"] == city].iloc[0]
            base = row["AQI"]
            # Simulate realistic diurnal pattern (high morning & evening)
            trend = [
                max(20, min(500, int(base + 60 * np.sin((h - 6) * np.pi / 12)
                            + random.randint(-30, 30))))
                for h in hours
            ]
            fig_line.add_trace(go.Scatter(
                x=hour_labels, y=trend,
                mode="lines+markers",
                name=city,
                line=dict(color=palette[i % len(palette)], width=2.5),
                marker=dict(size=5, color=palette[i % len(palette)]),
                fill="tozeroy",
                fillcolor=palette[i % len(palette)].replace("#", "rgba(") + ",0.06)",
                hovertemplate=f"<b>{city}</b><br>%{{x}}: AQI %{{y}}<extra></extra>",
            ))

        # Add threshold lines
        for threshold, label, color in [(200,"Poor threshold","#f97316"),(300,"Very Poor","#ef4444")]:
            fig_line.add_hline(
                y=threshold, line_dash="dot", line_color=color, opacity=0.4,
                annotation_text=label,
                annotation_font=dict(color=color, size=10),
            )

        fig_line.update_layout(
            title=dict(text="24-Hour AQI Trend", font=dict(color="#e5e7eb", size=14), x=0),
            xaxis=dict(tickfont=dict(color="#9ca3af"), showgrid=False, linecolor="#1f2937",
                       tickangle=-45),
            yaxis=dict(tickfont=dict(color="#9ca3af"), gridcolor="#1f2937",
                       title="AQI", title_font=dict(color="#6b7280"), range=[0, 520]),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(font=dict(color="#9ca3af"), bgcolor="rgba(0,0,0,0)",
                        orientation="h", yanchor="bottom", y=1.02),
            height=430, margin=dict(l=60, r=20, t=60, b=80),
        )
        st.plotly_chart(fig_line, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# VIEW 4 — POLLUTANT BREAKDOWN
# ═══════════════════════════════════════════════════════════════════════════════
elif "Pollutant" in view_mode:
    selected_city = st.selectbox("Select a city", df["City"].tolist(), index=0)
    row = df[df["City"] == selected_city].iloc[0]
    label, color, bg, tc = get_aqi_info(row["AQI"])

    st.markdown(f"""
    <div style="background:#111827;border:1px solid #1f2937;border-radius:14px;
                padding:20px 24px;margin-bottom:20px;">
        <div style="font-size:20px;font-weight:700;color:#f9fafb;margin-bottom:6px;">
            {selected_city} <span style="font-size:13px;color:#6b7280;">· {row['State']}</span>
        </div>
        <div style="font-size:38px;font-weight:700;color:{color};line-height:1;">
            AQI {row['AQI']}
        </div>
        <div style="font-size:14px;color:{tc};margin-top:6px;font-weight:600;">{label}</div>
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div class="section-title">Pollutant Levels vs Safe Limit</div>',
                    unsafe_allow_html=True)
        for p in POLLUTANTS:
            val  = row[p]
            safe = SAFE_LIMITS[p]
            pct  = min(val / (safe * 3) * 100, 100)
            bar_color = "#22c55e" if val <= safe else ("#eab308" if val <= safe * 1.5 else "#ef4444")
            status = "✅" if val <= safe else ("⚠️" if val <= safe * 1.5 else "🚨")
            st.markdown(f"""
            <div style="margin-bottom:14px;">
                <div style="display:flex;justify-content:space-between;
                            font-size:13px;color:#9ca3af;margin-bottom:5px;">
                    <span>{status} <b style="color:#e5e7eb;">{p}</b></span>
                    <span style="color:{bar_color};font-weight:600;">
                        {val} {UNITS[p]}
                        <span style="color:#6b7280;font-weight:400;"> / safe ≤{safe}</span>
                    </span>
                </div>
                <div style="height:8px;background:#1f2937;border-radius:4px;overflow:hidden;">
                    <div style="width:{pct:.1f}%;height:100%;
                                background:{bar_color};border-radius:4px;
                                transition:width 0.5s;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="section-title">Radar Overview</div>', unsafe_allow_html=True)
        categories = POLLUTANTS + [POLLUTANTS[0]]
        vals_pct = [
            min(row[p] / (SAFE_LIMITS[p] * 2) * 100, 100) for p in POLLUTANTS
        ] + [min(row[POLLUTANTS[0]] / (SAFE_LIMITS[POLLUTANTS[0]] * 2) * 100, 100)]

        fig_radar = go.Figure(go.Scatterpolar(
            r=vals_pct, theta=categories,
            fill="toself",
            fillcolor=color + "30",
            line=dict(color=color, width=2),
            marker=dict(color=color, size=6),
        ))
        fig_radar.update_layout(
            polar=dict(
                bgcolor="#111827",
                radialaxis=dict(
                    visible=True, range=[0, 100],
                    tickfont=dict(color="#6b7280", size=10),
                    gridcolor="#1f2937", linecolor="#1f2937"
                ),
                angularaxis=dict(
                    tickfont=dict(color="#9ca3af", size=12),
                    gridcolor="#1f2937", linecolor="#1f2937"
                ),
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            height=340, margin=dict(l=40, r=40, t=20, b=20),
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    # Compare across all cities for one pollutant
    st.markdown("---")
    st.markdown('<div class="section-title">Compare Across All Cities</div>',
                unsafe_allow_html=True)
    focus_poll = st.selectbox("Pollutant", POLLUTANTS, index=0)
    cmp_df = df[["City", focus_poll, "AQI"]].sort_values(focus_poll, ascending=True)
    safe_limit = SAFE_LIMITS[focus_poll]

    fig_h = go.Figure(go.Bar(
        x=cmp_df[focus_poll], y=cmp_df["City"],
        orientation="h",
        marker_color=[
            "#22c55e" if v <= safe_limit else
            "#eab308" if v <= safe_limit * 1.5 else "#ef4444"
            for v in cmp_df[focus_poll]
        ],
        marker_line_width=0,
        text=cmp_df[focus_poll].astype(str) + f" {UNITS[focus_poll]}",
        textposition="outside",
        textfont=dict(color="#9ca3af", size=10),
        hovertemplate="<b>%{y}</b><br>" + focus_poll + ": %{x}<extra></extra>",
    ))
    fig_h.add_vline(
        x=safe_limit, line_dash="dash", line_color="#3b82f6",
        annotation_text=f"Safe limit ({safe_limit})",
        annotation_font=dict(color="#3b82f6", size=11),
    )
    fig_h.update_layout(
        xaxis=dict(tickfont=dict(color="#9ca3af"), gridcolor="#1f2937",
                   title=UNITS[focus_poll], title_font=dict(color="#6b7280")),
        yaxis=dict(tickfont=dict(color="#9ca3af"), showgrid=False),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=550, margin=dict(l=110, r=80, t=20, b=40),
    )
    st.plotly_chart(fig_h, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# VIEW 5 — RANKINGS & STATS
# ═══════════════════════════════════════════════════════════════════════════════
elif "Rankings" in view_mode:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-title">🏆 Cleanest Cities</div>', unsafe_allow_html=True)
        best5 = df.nsmallest(10, "AQI")[["City","State","AQI","Category"]]
        for _, r in best5.iterrows():
            _, color, bg, tc = get_aqi_info(r["AQI"])
            st.markdown(f"""
            <div class="city-row">
                <div>
                    <div style="font-size:13px;color:#e5e7eb;font-weight:600;">{r['City']}</div>
                    <div style="font-size:11px;color:#6b7280;">{r['State']}</div>
                </div>
                <span class="aqi-badge" style="background:{bg};color:{tc};">
                    {r['AQI']} · {r['Category']}
                </span>
            </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-title">☣️ Most Polluted Cities</div>', unsafe_allow_html=True)
        worst10 = df.nlargest(10, "AQI")[["City","State","AQI","Category"]]
        for _, r in worst10.iterrows():
            _, color, bg, tc = get_aqi_info(r["AQI"])
            st.markdown(f"""
            <div class="city-row">
                <div>
                    <div style="font-size:13px;color:#e5e7eb;font-weight:600;">{r['City']}</div>
                    <div style="font-size:11px;color:#6b7280;">{r['State']}</div>
                </div>
                <span class="aqi-badge" style="background:{bg};color:{tc};">
                    {r['AQI']} · {r['Category']}
                </span>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="section-title">📊 AQI Statistics by State</div>', unsafe_allow_html=True)
    state_stats = df.groupby("State")["AQI"].agg(
        Avg="mean", Max="max", Min="min", Cities="count"
    ).round(1).sort_values("Avg", ascending=False).reset_index()

    fig_state = px.bar(
        state_stats, x="State", y="Avg",
        error_y=state_stats["Max"] - state_stats["Avg"],
        color="Avg",
        color_continuous_scale=[[0,"#22c55e"],[0.4,"#eab308"],[0.7,"#ef4444"],[1,"#8b5cf6"]],
        range_color=[0, 500],
        hover_data={"Max":True,"Min":True,"Cities":True},
        text=state_stats["Avg"].astype(int),
    )
    fig_state.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(tickfont=dict(color="#9ca3af"), tickangle=-35, showgrid=False),
        yaxis=dict(tickfont=dict(color="#9ca3af"), gridcolor="#1f2937",
                   title="Average AQI", title_font=dict(color="#6b7280")),
        coloraxis_showscale=False,
        height=360, margin=dict(l=60, r=20, t=20, b=100),
    )
    fig_state.update_traces(textposition="outside", textfont=dict(color="#9ca3af", size=10))
    st.plotly_chart(fig_state, use_container_width=True)

    # Correlation heatmap
    st.markdown('<div class="section-title">🔗 Pollutant Correlation Matrix</div>',
                unsafe_allow_html=True)
    corr = df[["AQI"] + POLLUTANTS].corr().round(2)
    fig_heat = go.Figure(go.Heatmap(
        z=corr.values, x=corr.columns, y=corr.index,
        colorscale="RdYlGn", zmin=-1, zmax=1,
        text=corr.values.round(2),
        texttemplate="%{text}",
        textfont=dict(size=12, color="white"),
        hovertemplate="%{x} × %{y}: %{z}<extra></extra>",
    ))
    fig_heat.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(tickfont=dict(color="#9ca3af")),
        yaxis=dict(tickfont=dict(color="#9ca3af")),
        height=340, margin=dict(l=80, r=20, t=20, b=60),
    )
    st.plotly_chart(fig_heat, use_container_width=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<div style="text-align:center;font-size:11px;color:#374151;">'
    'Data is simulated · For real data connect to CPCB API or WAQI (aqicn.org/api) · '
    'Built with Streamlit + Plotly'
    '</div>',
    unsafe_allow_html=True
)
