"""
India Air Quality Index Dashboard
Merged from Tkinter desktop app + Streamlit web dashboard

Run options:
  Streamlit (web):  streamlit run india_aqi_dashboard.py
  Tkinter (desktop): python india_aqi_dashboard.py --desktop

Install deps:
  pip install streamlit plotly pandas pillow
"""

import sys
import math
import time
import threading
import random

# ─────────────────────────────────────────
#  SHARED DATA
# ─────────────────────────────────────────

CITIES_DETAIL = {
    "Mumbai": {
        "aqi": 142, "pm25": 58, "pm10": 92, "o3": 44, "no2": 38,
        "visibility": 6, "humidity": 74, "wind": 18,
        "status": "Unhealthy for Sensitive Groups",
        "advice": "Children & elderly should limit outdoor activity.",
        "state": "Maharashtra", "lat": 19.07, "lon": 72.87,
    },
    "Delhi": {
        "aqi": 287, "pm25": 134, "pm10": 210, "o3": 68, "no2": 92,
        "visibility": 2, "humidity": 55, "wind": 7,
        "status": "Very Unhealthy",
        "advice": "Everyone should avoid prolonged outdoor exertion.",
        "state": "Delhi", "lat": 28.61, "lon": 77.20,
    },
    "Pune": {
        "aqi": 68, "pm25": 22, "pm10": 48, "o3": 31, "no2": 18,
        "visibility": 12, "humidity": 62, "wind": 24,
        "status": "Moderate",
        "advice": "Air quality is acceptable for most people.",
        "state": "Maharashtra", "lat": 18.52, "lon": 73.85,
    },
    "Chennai": {
        "aqi": 95, "pm25": 34, "pm10": 67, "o3": 38, "no2": 28,
        "visibility": 9, "humidity": 82, "wind": 21,
        "status": "Moderate",
        "advice": "Sensitive groups may experience minor symptoms.",
        "state": "Tamil Nadu", "lat": 13.08, "lon": 80.27,
    },
    "Kolkata": {
        "aqi": 198, "pm25": 89, "pm10": 145, "o3": 55, "no2": 61,
        "visibility": 4, "humidity": 68, "wind": 11,
        "status": "Unhealthy",
        "advice": "Everyone may begin to experience health effects.",
        "state": "West Bengal", "lat": 22.57, "lon": 88.36,
    },
    "Bangalore": {
        "aqi": 72, "pm25": 24, "pm10": 52, "o3": 29, "no2": 21,
        "visibility": 11, "humidity": 58, "wind": 22,
        "status": "Moderate",
        "advice": "Air quality is acceptable for most people.",
        "state": "Karnataka", "lat": 12.97, "lon": 77.59,
    },
    "Hyderabad": {
        "aqi": 118, "pm25": 46, "pm10": 78, "o3": 41, "no2": 33,
        "visibility": 8, "humidity": 60, "wind": 19,
        "status": "Unhealthy for Sensitive Groups",
        "advice": "Sensitive individuals should reduce outdoor activity.",
        "state": "Telangana", "lat": 17.38, "lon": 78.48,
    },
    "Ahmedabad": {
        "aqi": 156, "pm25": 65, "pm10": 108, "o3": 48, "no2": 44,
        "visibility": 5, "humidity": 45, "wind": 16,
        "status": "Unhealthy for Sensitive Groups",
        "advice": "Children & elderly should limit outdoor activity.",
        "state": "Gujarat", "lat": 23.02, "lon": 72.57,
    },
    "Jaipur": {
        "aqi": 178, "pm25": 76, "pm10": 128, "o3": 52, "no2": 54,
        "visibility": 5, "humidity": 38, "wind": 14,
        "status": "Unhealthy",
        "advice": "Everyone may experience health effects.",
        "state": "Rajasthan", "lat": 26.91, "lon": 75.79,
    },
    "Lucknow": {
        "aqi": 224, "pm25": 104, "pm10": 168, "o3": 61, "no2": 74,
        "visibility": 3, "humidity": 62, "wind": 9,
        "status": "Very Unhealthy",
        "advice": "Avoid all outdoor physical activity.",
        "state": "Uttar Pradesh", "lat": 26.84, "lon": 80.94,
    },
    "Kanpur": {
        "aqi": 261, "pm25": 121, "pm10": 195, "o3": 66, "no2": 86,
        "visibility": 2, "humidity": 60, "wind": 8,
        "status": "Very Unhealthy",
        "advice": "Health alert: everyone may experience serious effects.",
        "state": "Uttar Pradesh", "lat": 26.44, "lon": 80.33,
    },
    "Patna": {
        "aqi": 253, "pm25": 118, "pm10": 188, "o3": 65, "no2": 83,
        "visibility": 3, "humidity": 66, "wind": 8,
        "status": "Very Unhealthy",
        "advice": "Health alert: everyone may experience serious effects.",
        "state": "Bihar", "lat": 25.59, "lon": 85.13,
    },
    "Bhopal": {
        "aqi": 132, "pm25": 52, "pm10": 86, "o3": 43, "no2": 36,
        "visibility": 7, "humidity": 57, "wind": 17,
        "status": "Unhealthy for Sensitive Groups",
        "advice": "Sensitive groups should reduce outdoor activity.",
        "state": "Madhya Pradesh", "lat": 23.25, "lon": 77.40,
    },
    "Surat": {
        "aqi": 148, "pm25": 61, "pm10": 98, "o3": 46, "no2": 42,
        "visibility": 6, "humidity": 72, "wind": 20,
        "status": "Unhealthy for Sensitive Groups",
        "advice": "Children & elderly should limit outdoor activity.",
        "state": "Gujarat", "lat": 21.19, "lon": 72.83,
    },
    "Chandigarh": {
        "aqi": 88, "pm25": 31, "pm10": 61, "o3": 36, "no2": 24,
        "visibility": 10, "humidity": 54, "wind": 23,
        "status": "Moderate",
        "advice": "Air quality acceptable for most people.",
        "state": "Chandigarh", "lat": 30.73, "lon": 76.78,
    },
    "Varanasi": {
        "aqi": 241, "pm25": 112, "pm10": 178, "o3": 63, "no2": 79,
        "visibility": 3, "humidity": 64, "wind": 8,
        "status": "Very Unhealthy",
        "advice": "Avoid all outdoor physical activity.",
        "state": "Uttar Pradesh", "lat": 25.31, "lon": 82.97,
    },
    "Nagpur": {
        "aqi": 122, "pm25": 49, "pm10": 82, "o3": 42, "no2": 34,
        "visibility": 7, "humidity": 56, "wind": 17,
        "status": "Unhealthy for Sensitive Groups",
        "advice": "Sensitive groups should reduce outdoor activity.",
        "state": "Maharashtra", "lat": 21.14, "lon": 79.08,
    },
    "Indore": {
        "aqi": 109, "pm25": 42, "pm10": 72, "o3": 39, "no2": 30,
        "visibility": 8, "humidity": 55, "wind": 18,
        "status": "Unhealthy for Sensitive Groups",
        "advice": "Sensitive groups should take care.",
        "state": "Madhya Pradesh", "lat": 22.72, "lon": 75.86,
    },
    "Kochi": {
        "aqi": 54, "pm25": 18, "pm10": 38, "o3": 26, "no2": 15,
        "visibility": 14, "humidity": 88, "wind": 28,
        "status": "Moderate",
        "advice": "Air quality is acceptable.",
        "state": "Kerala", "lat": 9.93, "lon": 76.26,
    },
    "Guwahati": {
        "aqi": 82, "pm25": 28, "pm10": 56, "o3": 33, "no2": 22,
        "visibility": 10, "humidity": 78, "wind": 20,
        "status": "Moderate",
        "advice": "Air quality is acceptable for most people.",
        "state": "Assam", "lat": 26.14, "lon": 91.74,
    },
    "Amritsar": {
        "aqi": 188, "pm25": 82, "pm10": 136, "o3": 54, "no2": 58,
        "visibility": 4, "humidity": 52, "wind": 12,
        "status": "Unhealthy",
        "advice": "Everyone may experience health effects.",
        "state": "Punjab", "lat": 31.63, "lon": 74.87,
    },
    "Visakhapatnam": {
        "aqi": 88, "pm25": 30, "pm10": 58, "o3": 34, "no2": 23,
        "visibility": 10, "humidity": 80, "wind": 25,
        "status": "Moderate",
        "advice": "Air quality is acceptable for most people.",
        "state": "Andhra Pradesh", "lat": 17.68, "lon": 83.21,
    },
    "Coimbatore": {
        "aqi": 62, "pm25": 20, "pm10": 44, "o3": 28, "no2": 17,
        "visibility": 13, "humidity": 70, "wind": 26,
        "status": "Moderate",
        "advice": "Air quality is acceptable.",
        "state": "Tamil Nadu", "lat": 11.01, "lon": 76.97,
    },
    "Bhubaneswar": {
        "aqi": 104, "pm25": 40, "pm10": 70, "o3": 38, "no2": 29,
        "visibility": 9, "humidity": 72, "wind": 19,
        "status": "Unhealthy for Sensitive Groups",
        "advice": "Sensitive groups should take precautions.",
        "state": "Odisha", "lat": 20.29, "lon": 85.82,
    },
    "Agra": {
        "aqi": 202, "pm25": 93, "pm10": 152, "o3": 57, "no2": 65,
        "visibility": 4, "humidity": 58, "wind": 10,
        "status": "Very Unhealthy",
        "advice": "Avoid all outdoor physical activity.",
        "state": "Uttar Pradesh", "lat": 27.17, "lon": 78.01,
    },
}

POLLUTANTS  = ["PM2.5", "PM10", "NO2", "O3"]
SAFE_LIMITS = {"PM2.5": 60, "PM10": 100, "NO2": 80, "O3": 100}
UNITS       = {"PM2.5": "µg/m³", "PM10": "µg/m³", "NO2": "µg/m³", "O3": "ppb"}

AQI_SCALE = [
    (0,   50,  "Good",                     "#22c55e"),
    (51,  100, "Moderate",                 "#84cc16"),
    (101, 150, "Unhealthy for Sensitive",  "#f59e0b"),
    (151, 200, "Unhealthy",                "#f97316"),
    (201, 300, "Very Unhealthy",           "#ef4444"),
    (301, 500, "Hazardous",               "#7c3aed"),
]


def aqi_color(aqi):
    for lo, hi, _, col in AQI_SCALE:
        if lo <= aqi <= hi:
            return col
    return "#7c3aed"


def aqi_label(aqi):
    for lo, hi, label, _ in AQI_SCALE:
        if lo <= aqi <= hi:
            return label
    return "Hazardous"


def aqi_emoji(aqi):
    if aqi <= 50:   return "🟢"
    if aqi <= 100:  return "🟡"
    if aqi <= 150:  return "🟠"
    if aqi <= 200:  return "🔴"
    if aqi <= 300:  return "🟣"
    return "⚫"


# ═══════════════════════════════════════
#  STREAMLIT WEB DASHBOARD
# ═══════════════════════════════════════

def run_streamlit():
    import streamlit as st
    import pandas as pd
    import numpy as np
    import plotly.graph_objects as go
    import plotly.express as px
    from PIL import Image

    st.set_page_config(
        page_title="India AQI Dashboard",
        page_icon="🌍",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # ── Theme ──
    st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg,#0f0a1e 0%,#1e1040 100%); color:#ede9fe; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg,#050010 0%,#0f0a1e 100%) !important; }
    [data-testid="stSidebar"] * { color:#ddd6fe !important; }
    [data-testid="stSidebar"] .stButton>button {
        background:#6d28d9 !important; color:#ddd6fe !important;
        border:none !important; font-weight:700 !important; border-radius:8px !important; }
    h1 { color:#ddd6fe !important; }
    h2,h3 { color:#c4b5fd !important; }
    [data-testid="metric-container"] {
        background:rgba(109,40,217,.12); border:2px solid #2e1065;
        border-left:5px solid #7c3aed; border-radius:12px;
        padding:16px 20px !important; box-shadow:0 0 18px rgba(124,58,237,.25); }
    [data-testid="metric-container"] label { color:#c4b5fd !important; font-weight:600 !important; }
    [data-testid="metric-container"] [data-testid="stMetricValue"] { color:#ddd6fe !important; font-weight:800 !important; }
    .stButton>button {
        background:#1e1040 !important; color:#ddd6fe !important;
        border:1px solid #6d28d9 !important; border-radius:8px !important; font-weight:600 !important; }
    .stButton>button:hover { background:#6d28d9 !important; }
    [data-baseweb="select"]>div {
        border-color:#6d28d9 !important; border-radius:8px !important;
        background:#0f0a1e !important; color:#ede9fe !important; }
    [data-testid="stPlotlyChart"] {
        border:1.5px solid #2e1065; border-radius:12px; padding:8px;
        background:rgba(109,40,217,.06); }
    .stCaption { color:#a855f7 !important; }
    </style>
    """, unsafe_allow_html=True)

    # ── Build DataFrame ──
    def build_df():
        rows = []
        for name, d in CITIES_DETAIL.items():
            rows.append({
                "City": name, "State": d["state"],
                "Lat": d["lat"], "Lon": d["lon"],
                "AQI": d["aqi"], "Category": aqi_label(d["aqi"]),
                "Color": aqi_color(d["aqi"]),
                "PM2.5": d["pm25"], "PM10": d["pm10"],
                "NO2": d["no2"], "O3": d["o3"],
                "Visibility": d["visibility"],
                "Humidity": d["humidity"], "Wind": d["wind"],
                "Status": d["status"], "Advice": d["advice"],
            })
        return pd.DataFrame(rows)

    if "df" not in st.session_state:
        st.session_state.df = build_df()

    # ── Sidebar ──
    with st.sidebar:
        st.title("🌍 India AQI Monitor")
        st.divider()
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.session_state.df = build_df()
            st.rerun()
        st.divider()
        view_mode = st.radio("📊 Select View", [
            "🗺️ Pollution Map",
            "📊 City Comparison",
            "📈 Hourly Trend",
            "🔬 Pollutant Detail",
            "🏆 Rankings & Stats",
            "📸 Image Predictor",
        ])
        st.divider()
        st.subheader("🔍 Filters")
        aqi_range = st.slider("AQI Range", 0, 500, (0, 500))
        all_states = sorted(st.session_state.df["State"].unique())
        sel_states = st.multiselect("Filter by State", all_states)
        st.divider()
        st.subheader("📋 AQI Legend")
        for lo, hi, label, _ in AQI_SCALE:
            st.markdown(f"{aqi_emoji((lo+hi)//2)} **{lo}–{hi}** — {label}")

    df  = st.session_state.df
    dff = df[(df["AQI"] >= aqi_range[0]) & (df["AQI"] <= aqi_range[1])]
    if sel_states:
        dff = dff[dff["State"].isin(sel_states)]

    # ── Header & Metrics ──
    st.title("🌍 India Air Quality Index Dashboard")
    st.caption("AQI data across 25 major Indian cities · Refresh for new readings")
    st.divider()

    avg_aqi   = int(df["AQI"].mean())
    worst     = df.loc[df["AQI"].idxmax()]
    best      = df.loc[df["AQI"].idxmin()]
    dangerous = int((df["AQI"] > 200).sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🌡️ National Avg AQI", avg_aqi, aqi_label(avg_aqi))
    c2.metric("☣️ Most Polluted",     worst["City"], f"AQI {worst['AQI']}")
    c3.metric("🌿 Cleanest City",     best["City"],  f"AQI {best['AQI']}")
    c4.metric("⚠️ High Risk Cities",  dangerous,     "AQI > 200")
    st.divider()

    # ══ VIEW 1 — MAP ══
    if "Map" in view_mode:
        col_left, col_right = st.columns([3, 1])
        with col_left:
            st.subheader("🗺️ India Pollution Map")
            map_style = st.selectbox("Map theme",
                ["carto-darkmatter", "open-street-map", "carto-positron"])
            dff2 = dff.copy()
            dff2["size_val"] = dff2["AQI"].apply(lambda v: max(8, min(40, v / 10)))
            dff2["label"] = dff2.apply(
                lambda r: (f"{r['City']}\nAQI {r['AQI']} ({r['Category']})\n"
                           f"PM2.5: {r['PM2.5']} | PM10: {r['PM10']}\n"
                           f"NO2: {r['NO2']} | O3: {r['O3']}"), axis=1)
            fig_map = go.Figure(go.Scattermapbox(
                lat=dff2["Lat"], lon=dff2["Lon"],
                mode="markers+text",
                marker=dict(
                    size=dff2["size_val"],
                    color=dff2["AQI"],
                    colorscale=[[0,"#22c55e"],[0.2,"#84cc16"],
                                [0.4,"#f59e0b"],[0.6,"#f97316"],
                                [0.8,"#ef4444"],[1.0,"#7c3aed"]],
                    cmin=0, cmax=500, opacity=0.85,
                    colorbar=dict(title="AQI", thickness=14, len=0.6),
                ),
                text=dff2["AQI"].astype(str),
                textfont=dict(size=9, color="white"),
                textposition="middle center",
                hovertext=dff2["label"], hoverinfo="text",
            ))
            fig_map.update_layout(
                mapbox=dict(style=map_style,
                            center=dict(lat=22.5, lon=82.0), zoom=3.8),
                margin=dict(l=0, r=0, t=0, b=0), height=520)
            st.plotly_chart(fig_map, use_container_width=True)

        with col_right:
            st.subheader("📋 Rankings")
            ranked = dff.sort_values("AQI", ascending=False)[
                ["City","AQI","Category"]].reset_index(drop=True)
            for _, row in ranked.iterrows():
                st.write(f"{aqi_emoji(row['AQI'])} **{row['City']}** — {row['AQI']}")

        st.divider()
        st.subheader("📄 Full Data Table")
        show_df = dff[["City","State","AQI","Category","PM2.5","PM10","NO2","O3"]]\
            .sort_values("AQI", ascending=False).reset_index(drop=True)
        show_df.index += 1
        st.dataframe(show_df.style.background_gradient(
            subset=["AQI"], cmap="RdYlGn_r"), use_container_width=True, height=320)

    # ══ VIEW 2 — COMPARISON ══
    elif "Comparison" in view_mode:
        st.subheader("📊 City AQI Comparison")
        col_a, col_b = st.columns(2)
        with col_a:
            top_n = st.slider("Number of cities", 5, 25, 15)
        with col_b:
            sort_by = st.selectbox("Sort by", ["AQI", "PM2.5", "PM10", "NO2", "O3"])
        sorted_df = dff.sort_values(sort_by, ascending=False).head(top_n)
        fig_bar = go.Figure(go.Bar(
            x=sorted_df["City"], y=sorted_df[sort_by],
            marker_color=sorted_df["Color"], marker_line_width=0,
            text=sorted_df[sort_by].round(1), textposition="outside",
        ))
        fig_bar.update_layout(xaxis=dict(tickangle=-38), height=420,
                              margin=dict(l=60,r=20,t=30,b=100))
        st.plotly_chart(fig_bar, use_container_width=True)
        st.divider()
        st.subheader("🥧 AQI Category Distribution")
        cat_counts = df["Category"].value_counts()
        fig_pie = go.Figure(go.Pie(
            labels=cat_counts.index, values=cat_counts.values,
            hole=0.45,
        ))
        fig_pie.update_layout(height=320, margin=dict(l=0,r=0,t=20,b=0))
        st.plotly_chart(fig_pie, use_container_width=True)

    # ══ VIEW 3 — HOURLY TREND ══
    elif "Trend" in view_mode:
        st.subheader("📈 24-Hour AQI Trend")
        import numpy as np
        sel_cities = st.multiselect(
            "Select cities (up to 6)", list(CITIES_DETAIL.keys()),
            default=["Delhi", "Mumbai", "Bangalore", "Chennai"])
        if not sel_cities:
            st.info("Select at least one city.")
        else:
            hours  = list(range(24))
            labels = [f"{h:02d}:00" for h in hours]
            palette= ["#818cf8","#a855f7","#34d399","#f472b6","#f97316","#38bdf8"]
            fig = go.Figure()
            for i, city in enumerate(sel_cities[:6]):
                base  = CITIES_DETAIL[city]["aqi"]
                trend = [max(20, min(500, int(
                    base + 55*np.sin((h-6)*np.pi/12) + random.randint(-25,25)
                ))) for h in hours]
                col = palette[i % len(palette)]
                fig.add_trace(go.Scatter(
                    x=labels, y=trend, mode="lines+markers", name=city,
                    line=dict(color=col, width=2.5), marker=dict(size=5),
                ))
            for thresh, lbl in [(200,"Poor threshold"),(300,"Very Poor threshold")]:
                fig.add_hline(y=thresh, line_dash="dot", line_color="#9ca3af",
                              opacity=0.5, annotation_text=lbl)
            fig.update_layout(
                xaxis=dict(tickangle=-45),
                yaxis=dict(title="AQI", range=[0,520]),
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                height=430, margin=dict(l=60,r=20,t=60,b=80))
            st.plotly_chart(fig, use_container_width=True)
            st.info("Trend simulated using sine-wave diurnal pattern + random noise.")

    # ══ VIEW 4 — POLLUTANT DETAIL ══
    elif "Pollutant" in view_mode:
        st.subheader("🔬 Pollutant Breakdown")
        city_sel = st.selectbox("Select a city", list(CITIES_DETAIL.keys()))
        d = CITIES_DETAIL[city_sel]
        c1, c2, c3 = st.columns(3)
        c1.metric("🏙️ City",    city_sel, d["state"])
        c2.metric("🌡️ AQI",     d["aqi"], aqi_label(d["aqi"]))
        c3.metric("📍 Status",  d["status"], "")
        st.divider()

        pmap = {"PM2.5": d["pm25"], "PM10": d["pm10"],
                "NO2": d["no2"], "O3": d["o3"]}

        col_bars, col_radar = st.columns(2)
        with col_bars:
            st.subheader("📊 vs Safe Limit")
            for p, val in pmap.items():
                safe   = SAFE_LIMITS[p]
                pct    = min(val / (safe * 3), 1.0)
                status = ("✅ Safe" if val <= safe else
                          "⚠️ Moderate" if val <= safe * 1.5 else "🚨 Unsafe")
                st.write(f"**{p}** — {val} {UNITS[p]}  {status}  *(safe ≤ {safe})*")
                st.progress(float(pct))

        with col_radar:
            st.subheader("🕸️ Radar Overview")
            pct_vals = [float(min(pmap[p]/(SAFE_LIMITS[p]*2)*100, 100)) for p in POLLUTANTS]
            theta = POLLUTANTS + [POLLUTANTS[0]]
            r_vals = pct_vals + [pct_vals[0]]
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=r_vals, theta=theta, fill="toself",
                fillcolor="rgba(124,58,237,0.25)",
                line=dict(color="#a855f7", width=2),
                marker=dict(color="#818cf8", size=7),
            ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0,100])),
                showlegend=False, height=340,
                margin=dict(l=40,r=40,t=20,b=20))
            st.plotly_chart(fig_radar, use_container_width=True)

        st.divider()
        st.subheader("📋 City advice")
        st.info(d["advice"])

    # ══ VIEW 5 — RANKINGS ══
    elif "Rankings" in view_mode:
        st.subheader("🏆 Rankings & Statistics")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🌿 Top 10 Cleanest")
            best10 = df.nsmallest(10, "AQI")[["City","State","AQI","Category"]]
            for _, r in best10.iterrows():
                st.write(f"{aqi_emoji(r['AQI'])} **{r['City']}** — AQI {r['AQI']} · {r['Category']}")
        with c2:
            st.subheader("☣️ Top 10 Most Polluted")
            worst10 = df.nlargest(10, "AQI")[["City","State","AQI","Category"]]
            for _, r in worst10.iterrows():
                st.write(f"{aqi_emoji(r['AQI'])} **{r['City']}** — AQI {r['AQI']} · {r['Category']}")

        st.divider()
        st.subheader("📊 Avg AQI by State")
        state_stats = df.groupby("State")["AQI"].mean().round(1).sort_values(ascending=False)
        fig_state = px.bar(
            x=state_stats.index, y=state_stats.values,
            labels={"x":"State","y":"Avg AQI"},
            color=state_stats.values,
            color_continuous_scale=[[0,"#22c55e"],[0.5,"#f97316"],[1,"#7c3aed"]],
            range_color=[0,300],
        )
        fig_state.update_layout(
            xaxis=dict(tickangle=-35), height=360,
            margin=dict(l=60,r=20,t=20,b=100), coloraxis_showscale=False)
        st.plotly_chart(fig_state, use_container_width=True)

    # ══ VIEW 6 — IMAGE PREDICTOR ══
    elif "Image" in view_mode:
        st.subheader("📸 Image-Based Air Quality Predictor")
        st.write("Upload an outdoor scene image for a simulated air quality prediction.")
        uploaded = st.file_uploader("Upload Image", type=["jpg","jpeg","png"])
        if uploaded:
            img = Image.open(uploaded)
            st.image(img, caption="Uploaded Image", use_container_width=True)
            if st.button("Predict"):
                pollution = random.randint(1, 100)
                if pollution <= 20:   status, msg = "🌿 Very Good", "Air is Healthy"
                elif pollution <= 40: status, msg = "✅ Good", "Air quality is Healthy"
                elif pollution <= 60: status, msg = "😐 Moderate", "Air quality is Average"
                elif pollution <= 80: status, msg = "⚠️ Unhealthy", "Air quality is Unhealthy"
                else:                 status, msg = "🚨 Very Unhealthy", "Air quality is Dangerous"

                st.subheader("Prediction Result")
                st.metric("Pollution Level", f"{pollution}%")
                st.progress(pollution / 100)
                st.subheader("Health Status")
                st.write(status)
                if pollution <= 40:   st.success(msg)
                elif pollution <= 60: st.warning(msg)
                else:                 st.error(msg)

    st.divider()
    st.caption("📡 Data is static/simulated · For live data connect CPCB or WAQI API · Built with Streamlit + Plotly")


# ═══════════════════════════════════════
#  TKINTER DESKTOP APP
# ═══════════════════════════════════════

def run_tkinter():
    import tkinter as tk

    # Only use cities with full detail for the desktop app
    DESKTOP_CITIES = ["Mumbai", "Delhi", "Pune", "Chennai", "Kolkata",
                      "Bangalore", "Hyderabad", "Chandigarh"]

    def hex_to_rgb(h):
        h = h.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    class AirPollutionApp:
        BG       = "#0d1b2a"
        CARD     = "#112236"
        BORDER   = "#1e3a5f"
        TEXT_PRI = "#e8f4ff"
        TEXT_SEC = "#7aa8cc"
        TEXT_MUT = "#4a7a9b"
        ACCENT   = "#1565c0"

        def __init__(self, root):
            self.root = root
            self.root.title("India Air Pollution Dashboard")
            self.root.geometry("960x680")
            self.root.configure(bg=self.BG)
            self.root.resizable(False, False)
            self.current_city  = "Mumbai"
            self.displayed_aqi = 0
            self.target_aqi    = 0
            self.animating     = False
            self.clock_running = True
            self._build_ui()
            self._load_city("Mumbai")
            self._start_clock()

        def _build_ui(self):
            # ── TOP BAR ──
            top = tk.Frame(self.root, bg=self.BG)
            top.pack(fill="x", padx=24, pady=(18, 0))

            left_top = tk.Frame(top, bg=self.BG)
            left_top.pack(side="left")

            self.lbl_city = tk.Label(left_top, text="Mumbai, Maharashtra",
                bg=self.BG, fg=self.TEXT_PRI, font=("Arial Black", 18, "bold"))
            self.lbl_city.pack(anchor="w")

            tk.Label(left_top, text="Air Quality Monitoring Dashboard",
                bg=self.BG, fg=self.TEXT_MUT, font=("Arial", 10)).pack(anchor="w")

            live_row = tk.Frame(left_top, bg=self.BG)
            live_row.pack(anchor="w", pady=(3, 0))

            self.live_canvas = tk.Canvas(live_row, width=10, height=10,
                bg=self.BG, highlightthickness=0)
            self.live_canvas.pack(side="left", padx=(0, 5))
            self.live_dot = self.live_canvas.create_oval(1,1,9,9, fill="#34d399", outline="")

            self.lbl_clock = tk.Label(live_row, text="",
                bg=self.BG, fg=self.TEXT_MUT, font=("Arial", 9))
            self.lbl_clock.pack(side="left", padx=10)

            # City buttons
            btn_frame = tk.Frame(top, bg=self.BG)
            btn_frame.pack(side="right")
            self.city_btns = {}
            for city in DESKTOP_CITIES:
                d = CITIES_DETAIL[city]
                col = aqi_color(d["aqi"])
                btn = tk.Button(btn_frame, text=city, font=("Arial", 9, "bold"),
                    bg=self.CARD, fg=self.TEXT_SEC,
                    activebackground=self.ACCENT, activeforeground="#e3f2fd",
                    relief="flat", bd=0, padx=10, pady=5, cursor="hand2",
                    command=lambda c=city: self._load_city(c))
                btn.pack(side="left", padx=2)
                self.city_btns[city] = btn

            # ── MAIN CONTENT ──
            content = tk.Frame(self.root, bg=self.BG)
            content.pack(fill="both", expand=True, padx=24, pady=14)

            # Left: AQI ring card
            left = tk.Frame(content, bg=self.CARD,
                highlightbackground=self.BORDER, highlightthickness=1)
            left.pack(side="left", fill="y", ipadx=12, ipady=12, padx=(0, 14))

            tk.Label(left, text="AIR QUALITY INDEX",
                bg=self.CARD, fg=self.TEXT_MUT,
                font=("Arial", 8, "bold")).pack(pady=(10, 6))

            self.ring_canvas = tk.Canvas(left, width=180, height=180,
                bg=self.CARD, highlightthickness=0)
            self.ring_canvas.pack()
            self._draw_ring(0, "#22c55e")

            self.lbl_status = tk.Label(left, text="Loading...",
                bg=self.CARD, fg="#f59e0b",
                font=("Arial", 9, "bold"), wraplength=160, justify="center")
            self.lbl_status.pack(pady=(8, 2))

            self.lbl_advice = tk.Label(left, text="",
                bg=self.CARD, fg=self.TEXT_MUT,
                font=("Arial", 8), wraplength=160, justify="center")
            self.lbl_advice.pack(pady=(0, 10))

            # Right column
            right = tk.Frame(content, bg=self.BG)
            right.pack(side="left", fill="both", expand=True)

            # Pollutant cards grid
            poll_frame = tk.Frame(right, bg=self.BG)
            poll_frame.pack(fill="x", pady=(0, 12))

            self.poll_widgets = {}
            pollutants = [("PM2.5", "µg/m³", "#38bdf8"),
                          ("PM10",  "µg/m³", "#a78bfa"),
                          ("O₃",   "ppb",   "#fb923c"),
                          ("NO₂",  "µg/m³", "#34d399")]

            for i, (name, unit, col) in enumerate(pollutants):
                card = tk.Frame(poll_frame, bg=self.CARD,
                    highlightbackground=self.BORDER, highlightthickness=1)
                card.grid(row=i//2, column=i%2,
                    padx=(0 if i%2==0 else 6, 0),
                    pady=(0, 6 if i < 2 else 0), sticky="nsew")
                poll_frame.columnconfigure(i%2, weight=1)

                tk.Label(card, text=name, bg=self.CARD, fg=self.TEXT_MUT,
                    font=("Arial", 8, "bold")).pack(anchor="w", padx=12, pady=(10, 0))

                val_frame = tk.Frame(card, bg=self.CARD)
                val_frame.pack(anchor="w", padx=12)

                val_lbl = tk.Label(val_frame, text="--", bg=self.CARD, fg=col,
                    font=("Arial Black", 20))
                val_lbl.pack(side="left")

                tk.Label(val_frame, text=unit, bg=self.CARD, fg=self.TEXT_MUT,
                    font=("Arial", 9)).pack(side="left", padx=(4,0), pady=(6,0))

                bar_bg = tk.Canvas(card, height=4, bg="#1a3352", highlightthickness=0)
                bar_bg.pack(fill="x", padx=12, pady=(6, 10))

                self.poll_widgets[name] = {"val": val_lbl, "bar": bar_bg, "col": col}

            # AQI Health Scale
            scale_card = tk.Frame(right, bg=self.CARD,
                highlightbackground=self.BORDER, highlightthickness=1)
            scale_card.pack(fill="x")

            tk.Label(scale_card, text="AQI HEALTH SCALE",
                bg=self.CARD, fg=self.TEXT_MUT,
                font=("Arial", 8, "bold")).pack(anchor="w", padx=12, pady=(10, 4))

            self.scale_canvas = tk.Canvas(scale_card, height=16,
                bg=self.CARD, highlightthickness=0)
            self.scale_canvas.pack(fill="x", padx=12, pady=(0, 4))

            labels_frame = tk.Frame(scale_card, bg=self.CARD)
            labels_frame.pack(fill="x", padx=12, pady=(0, 8))
            for lbl in ["Good", "Moderate", "Sensitive", "Unhealthy", "Hazardous"]:
                tk.Label(labels_frame, text=lbl, bg=self.CARD, fg=self.TEXT_MUT,
                    font=("Arial", 7)).pack(side="left", expand=True)

            # ── BOTTOM ROW ──
            bottom = tk.Frame(self.root, bg=self.BG)
            bottom.pack(fill="x", padx=24, pady=(0, 10))

            self.stat_widgets = {}
            stats = [("Visibility", "km",     "spvis"),
                     ("Humidity",   "%",       "sphum"),
                     ("Wind Speed", "km/h",    "spwind")]

            for i, (label, unit, key) in enumerate(stats):
                card = tk.Frame(bottom, bg=self.CARD,
                    highlightbackground=self.BORDER, highlightthickness=1)
                card.pack(side="left", fill="x", expand=True,
                    padx=(0 if i == 0 else 10, 0))

                tk.Label(card, text=label.upper(), bg=self.CARD, fg=self.TEXT_MUT,
                    font=("Arial", 8, "bold")).pack(anchor="w", padx=12, pady=(10, 0))

                val_lbl = tk.Label(card, text="--", bg=self.CARD, fg="#c9e4ff",
                    font=("Arial Black", 18))
                val_lbl.pack(anchor="w", padx=12)

                tk.Label(card, text=unit, bg=self.CARD, fg=self.TEXT_MUT,
                    font=("Arial", 8)).pack(anchor="w", padx=12, pady=(0, 8))

                spark = tk.Canvas(card, height=28, bg="#1a3352", highlightthickness=0)
                spark.pack(fill="x", padx=12, pady=(0, 10))

                self.stat_widgets[key] = {"val": val_lbl, "spark": spark}

            # Forecast bar
            fc_frame = tk.Frame(self.root, bg=self.BG)
            fc_frame.pack(fill="x", padx=24, pady=(0, 14))

            tk.Label(fc_frame, text="24-HOUR FORECAST",
                bg=self.BG, fg=self.TEXT_MUT, font=("Arial", 8, "bold")).pack(anchor="w")

            self.fc_canvas = tk.Canvas(fc_frame, height=60, bg=self.BG,
                highlightthickness=0)
            self.fc_canvas.pack(fill="x", pady=(6, 0))

        def _load_city(self, city):
            self.current_city = city
            data = CITIES_DETAIL[city]

            for c, btn in self.city_btns.items():
                btn.configure(bg=self.ACCENT if c == city else self.CARD,
                              fg="#e3f2fd" if c == city else self.TEXT_SEC)

            state_map = {c: f"{c}, {CITIES_DETAIL[c]['state']}" for c in DESKTOP_CITIES}
            self.lbl_city.configure(text=state_map.get(city, city))

            col = aqi_color(data["aqi"])
            self.target_aqi = data["aqi"]
            self._animate_aqi(col)

            self.lbl_status.configure(text=data["status"], fg=col)
            self.lbl_advice.configure(text=data["advice"])

            pmap = {"PM2.5": data["pm25"], "PM10": data["pm10"],
                    "O₃": data["o3"], "NO₂": data["no2"]}
            pmx  = {"PM2.5": 150, "PM10": 300, "O₃": 120, "NO₂": 100}

            for name, w in self.poll_widgets.items():
                val = pmap[name]
                w["val"].configure(text=str(val))
                pct = min(1.0, val / pmx[name])
                self._draw_bar(w["bar"], pct, w["col"])

            self._draw_scale(data["aqi"])

            vis = data["visibility"]
            hum = data["humidity"]
            wnd = data["wind"]
            self._update_stat("spvis",  vis, col, [8,7,6,5,vis,vis-1,vis+1,7])
            self._update_stat("sphum",  hum, col, [68,72,70,hum,75,hum-3,hum+2,71])
            self._update_stat("spwind", wnd, col, [12,15,wnd,20,18,wnd-2,wnd+3,16])
            self.stat_widgets["spvis"]["val"].configure(text=str(vis))
            self.stat_widgets["sphum"]["val"].configure(text=str(hum))
            self.stat_widgets["spwind"]["val"].configure(text=str(wnd))

            self._draw_forecast(data["aqi"])

        def _draw_ring(self, aqi, col):
            c = self.ring_canvas
            c.delete("all")
            cx, cy, r = 90, 90, 72
            c.create_arc(cx-r, cy-r, cx+r, cy+r,
                start=0, extent=359.9, outline="#1a3352",
                style="arc", width=12)
            if aqi > 0:
                extent = min(359.9, (aqi / 500) * 359.9)
                c.create_arc(cx-r, cy-r, cx+r, cy+r,
                    start=90, extent=-extent, outline=col,
                    style="arc", width=12)
            ri = 58
            c.create_oval(cx-ri, cy-ri, cx+ri, cy+ri, fill="#0a1929", outline="")
            c.create_text(cx, cy-10, text=str(aqi), fill=col, font=("Arial Black", 28))
            c.create_text(cx, cy+18, text="AQI", fill=self.TEXT_MUT, font=("Arial", 9, "bold"))
            c.create_text(cx, cy+36, text=aqi_label(aqi), fill=col, font=("Arial", 7, "bold"))

        def _animate_aqi(self, col):
            if self.animating:
                return
            self.animating = True
            def step():
                diff = self.target_aqi - self.displayed_aqi
                if abs(diff) <= 2:
                    self.displayed_aqi = self.target_aqi
                    self._draw_ring(self.displayed_aqi, col)
                    self.animating = False
                    return
                self.displayed_aqi += diff // 6 or (1 if diff > 0 else -1)
                self._draw_ring(self.displayed_aqi, col)
                self.root.after(30, step)
            step()

        def _draw_scale(self, aqi):
            c = self.scale_canvas
            c.update_idletasks()
            w = c.winfo_width() or 400
            c.delete("all")
            segs   = ["#22c55e","#84cc16","#eab308","#f97316","#ef4444","#dc2626","#7c3aed"]
            levels = [50, 100, 150, 200, 300, 400, 500]
            sw = (w - 12) / len(segs)
            for i, (sc, lv) in enumerate(zip(segs, levels)):
                x1 = i * sw + 2
                x2 = x1 + sw - 3
                c.create_rectangle(x1, 2, x2, 14, fill=sc, outline="")
                if aqi <= lv and (i == 0 or aqi > levels[i-1]):
                    mx = (x1 + x2) / 2
                    c.create_polygon(mx-5, 16, mx+5, 16, mx, 9, fill="#fff")

        def _draw_bar(self, canvas, pct, col):
            canvas.update_idletasks()
            w = canvas.winfo_width() or 200
            canvas.delete("all")
            canvas.create_rectangle(0, 0, w, 4, fill="#1a3352", outline="")
            canvas.create_rectangle(0, 0, int(w * pct), 4, fill=col, outline="")

        def _update_stat(self, key, value, col, spark_vals):
            w = self.stat_widgets[key]
            self._draw_sparkline(w["spark"], spark_vals, col)

        def _draw_sparkline(self, canvas, vals, col):
            canvas.update_idletasks()
            w  = canvas.winfo_width() or 200
            h  = 28
            canvas.delete("all")
            mx = max(vals) or 1
            bw = (w - 8) / len(vals)
            for i, v in enumerate(vals):
                bh = max(3, int((v / mx) * (h - 4)))
                x1 = 4 + i * bw
                x2 = x1 + bw - 2
                canvas.create_rectangle(x1, h-bh, x2, h, fill=col+"88", outline="")

        def _draw_forecast(self, base_aqi):
            c = self.fc_canvas
            c.update_idletasks()
            w = c.winfo_width() or 860
            c.delete("all")
            hours  = ["Now","3h","6h","9h","12h","15h","18h","21h"]
            deltas = [-10, 5, -5, 18, 30, 12, -6, -18]
            sw = w / len(hours)
            for i, (h, d) in enumerate(zip(hours, deltas)):
                a   = max(0, base_aqi + d)
                col = aqi_color(int(a))
                cx  = int(i * sw + sw / 2)
                c.create_text(cx, 8,  text=h,       fill=self.TEXT_MUT, font=("Arial", 8))
                c.create_oval(cx-6, 20, cx+6, 32,   fill=col, outline="")
                c.create_text(cx, 48, text=str(int(a)), fill=col, font=("Arial", 9, "bold"))

        def _start_clock(self):
            def tick():
                while self.clock_running:
                    now = time.strftime("%I:%M:%S %p IST")
                    try:
                        self.lbl_clock.configure(text=f"● LIVE  {now}")
                        t = time.time() % 1.4
                        g = max(80, min(212, int(255*(0.5+0.5*math.sin(t*math.pi/0.7)))))
                        self.live_canvas.itemconfig(self.live_dot, fill=f"#00{g:02x}6e")
                    except Exception:
                        pass
                    time.sleep(0.5)
            threading.Thread(target=tick, daemon=True).start()

        def on_close(self):
            self.clock_running = False
            self.root.destroy()

    import tkinter as tk
    root = tk.Tk()
    app  = AirPollutionApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


# ═══════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════

if __name__ == "__main__":
    if "--desktop" in sys.argv:
        run_tkinter()
    else:
        # When run via `streamlit run`, __name__ == "__main__" is NOT true
        # but Streamlit imports the module and executes top-level code.
        # So we fall through to the Streamlit section below.
        run_tkinter()

# Streamlit entry — executed when Streamlit imports this file
# (streamlit run india_aqi_dashboard.py)
try:
    import streamlit as st
    # Only run Streamlit UI if we're actually inside a Streamlit session
    if hasattr(st, "session_state") and "--desktop" not in sys.argv:
        run_streamlit()
except (ImportError, Exception):
    pass
