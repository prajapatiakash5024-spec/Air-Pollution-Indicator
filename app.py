"""
India AQI Dashboard — powered by WAQI (aqicn.org) live data
============================================================
Setup:
  pip install streamlit plotly pandas requests pillow

Run:
  streamlit run india_aqi_dashboard.py

API token:
  Get a free token at https://aqicn.org/data-platform/token
  Then either:
    1. Set env var:  export WAQI_TOKEN="your_token"
    2. Or enter it in the sidebar at runtime.
  The built-in "demo" token works for ~5 cities — use your own for all 25.
"""

import os
import time
import requests
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
from datetime import datetime

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="India AQI Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constants ─────────────────────────────────────────────────────────────────
CITIES = [
    {"name": "Delhi",         "lat": 28.61, "lon": 77.20, "state": "Delhi",            "waqi_id": "delhi"},
    {"name": "Mumbai",        "lat": 19.07, "lon": 72.87, "state": "Maharashtra",      "waqi_id": "mumbai"},
    {"name": "Kolkata",       "lat": 22.57, "lon": 88.36, "state": "West Bengal",      "waqi_id": "kolkata"},
    {"name": "Chennai",       "lat": 13.08, "lon": 80.27, "state": "Tamil Nadu",       "waqi_id": "chennai"},
    {"name": "Bangalore",     "lat": 12.97, "lon": 77.59, "state": "Karnataka",        "waqi_id": "bangalore"},
    {"name": "Hyderabad",     "lat": 17.38, "lon": 78.48, "state": "Telangana",        "waqi_id": "hyderabad"},
    {"name": "Ahmedabad",     "lat": 23.02, "lon": 72.57, "state": "Gujarat",          "waqi_id": "ahmedabad"},
    {"name": "Pune",          "lat": 18.52, "lon": 73.85, "state": "Maharashtra",      "waqi_id": "pune"},
    {"name": "Jaipur",        "lat": 26.91, "lon": 75.79, "state": "Rajasthan",        "waqi_id": "jaipur"},
    {"name": "Lucknow",       "lat": 26.84, "lon": 80.94, "state": "Uttar Pradesh",    "waqi_id": "lucknow"},
    {"name": "Kanpur",        "lat": 26.44, "lon": 80.33, "state": "Uttar Pradesh",    "waqi_id": "kanpur"},
    {"name": "Nagpur",        "lat": 21.14, "lon": 79.08, "state": "Maharashtra",      "waqi_id": "nagpur"},
    {"name": "Patna",         "lat": 25.59, "lon": 85.13, "state": "Bihar",            "waqi_id": "patna"},
    {"name": "Bhopal",        "lat": 23.25, "lon": 77.40, "state": "Madhya Pradesh",   "waqi_id": "bhopal"},
    {"name": "Surat",         "lat": 21.19, "lon": 72.83, "state": "Gujarat",          "waqi_id": "surat"},
    {"name": "Chandigarh",    "lat": 30.73, "lon": 76.78, "state": "Chandigarh",       "waqi_id": "chandigarh"},
    {"name": "Varanasi",      "lat": 25.31, "lon": 82.97, "state": "Uttar Pradesh",    "waqi_id": "varanasi"},
    {"name": "Agra",          "lat": 27.17, "lon": 78.01, "state": "Uttar Pradesh",    "waqi_id": "agra"},
    {"name": "Amritsar",      "lat": 31.63, "lon": 74.87, "state": "Punjab",           "waqi_id": "amritsar"},
    {"name": "Visakhapatnam", "lat": 17.68, "lon": 83.21, "state": "Andhra Pradesh",   "waqi_id": "visakhapatnam"},
    {"name": "Indore",        "lat": 22.72, "lon": 75.86, "state": "Madhya Pradesh",   "waqi_id": "indore"},
    {"name": "Coimbatore",    "lat": 11.01, "lon": 76.97, "state": "Tamil Nadu",       "waqi_id": "coimbatore"},
    {"name": "Kochi",         "lat":  9.93, "lon": 76.26, "state": "Kerala",           "waqi_id": "kochi"},
    {"name": "Guwahati",      "lat": 26.14, "lon": 91.74, "state": "Assam",            "waqi_id": "guwahati"},
    {"name": "Bhubaneswar",   "lat": 20.29, "lon": 85.82, "state": "Odisha",           "waqi_id": "bhubaneswar"},
]

POLLUTANTS  = ["PM2.5", "PM10", "NO2", "SO2", "CO", "O3"]
# Maps WAQI iaqi keys → our column names
WAQI_POLLUTANT_MAP = {
    "pm25": "PM2.5",
    "pm10": "PM10",
    "no2":  "NO2",
    "so2":  "SO2",
    "co":   "CO",
    "o3":   "O3",
}
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

WAQI_BASE = "https://api.waqi.info"

# ── Helpers ───────────────────────────────────────────────────────────────────
def get_aqi_info(aqi: int) -> tuple[str, str]:
    for lo, hi, label, color in AQI_SCALE:
        if lo <= aqi <= hi:
            return label, color
    return "Severe", "#8b5cf6"

def aqi_emoji(aqi: int) -> str:
    if aqi <= 50:  return "🟢"
    if aqi <= 100: return "🟡"
    if aqi <= 200: return "🟠"
    if aqi <= 300: return "🔴"
    if aqi <= 400: return "🟣"
    return "⚫"

def pollutant_status(val: float, safe: float) -> str:
    if val <= safe:         return "✅ Safe"
    if val <= safe * 1.5:  return "⚠️ Moderate"
    return "🚨 Unsafe"

def safe_int(v) -> int:
    """Convert a value to int safely, returning 0 on failure."""
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return 0

# ── WAQI API layer ─────────────────────────────────────────────────────────────
def _fetch_city(waqi_id: str, token: str) -> dict | None:
    """
    Fetch live data for one city from WAQI.
    Returns a normalised dict or None on failure.
    """
    url = f"{WAQI_BASE}/feed/{waqi_id}/?token={token}"
    try:
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        payload = resp.json()
    except Exception:
        return None

    if payload.get("status") != "ok":
        return None

    d = payload["data"]
    iaqi = d.get("iaqi", {})

    # AQI value — WAQI sometimes returns "-" or a non-numeric string
    raw_aqi = d.get("aqi", 0)
    aqi = safe_int(raw_aqi)
    if aqi == 0:
        return None                       # station returned no data

    # Individual pollutants — missing ones stay at 0
    pollutants: dict[str, float] = {}
    for waqi_key, col in WAQI_POLLUTANT_MAP.items():
        raw = iaqi.get(waqi_key, {}).get("v")
        pollutants[col] = round(float(raw), 2) if raw is not None else 0.0

    # Dominant pollutant
    dominant = d.get("dominentpol", "")

    # Observation timestamp
    obs_time = d.get("time", {}).get("s", "")

    return {
        "aqi":        aqi,
        "dominant":   dominant,
        "obs_time":   obs_time,
        **pollutants,
    }


@st.cache_data(ttl=600, show_spinner=False)   # cache for 10 minutes
def fetch_all_cities(token: str) -> pd.DataFrame:
    """
    Fetch live AQI for all 25 cities.
    Falls back gracefully: cities with no data are excluded from the DataFrame
    but a warning is surfaced to the user.
    """
    rows = []
    failed = []

    progress = st.progress(0, text="Fetching live AQI data from WAQI…")

    for i, city in enumerate(CITIES):
        result = _fetch_city(city["waqi_id"], token)
        progress.progress((i + 1) / len(CITIES),
                          text=f"Fetching {city['name']}… ({i+1}/{len(CITIES)})")

        if result is None:
            failed.append(city["name"])
            continue

        aqi = result["aqi"]
        label, color = get_aqi_info(aqi)

        rows.append({
            "City":      city["name"],
            "State":     city["state"],
            "Lat":       city["lat"],
            "Lon":       city["lon"],
            "AQI":       aqi,
            "Category":  label,
            "Color":     color,
            "Dominant":  result["dominant"],
            "ObsTime":   result["obs_time"],
            **{p: result[p] for p in POLLUTANTS},
        })

        # Respect WAQI rate-limit (~10 req/s for free tokens)
        time.sleep(0.12)

    progress.empty()

    if failed:
        st.warning(
            f"⚠️ Could not fetch data for: **{', '.join(failed)}**. "
            "These cities are excluded. Check your token or try again later."
        )

    if not rows:
        st.error(
            "❌ No data returned. Your token may be invalid or rate-limited. "
            "Get a free token at https://aqicn.org/data-platform/token"
        )
        st.stop()

    return pd.DataFrame(rows)


# ── Token resolution ──────────────────────────────────────────────────────────
def resolve_token() -> str:
    """
    Token priority:
      1. st.session_state (user typed it in sidebar)
      2. WAQI_TOKEN environment variable
      3. "demo" fallback
    """
    if st.session_state.get("waqi_token_input"):
        return st.session_state["waqi_token_input"].strip()
    env = os.environ.get("WAQI_TOKEN", "").strip()
    if env:
        return env
    return "demo"


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🌍 India AQI Monitor")
    st.divider()

    # API Token input
    st.subheader("🔑 WAQI API Token")
    st.text_input(
        "Paste your token (or set WAQI_TOKEN env var)",
        key="waqi_token_input",
        type="password",
        placeholder="demo  ·  or your token from aqicn.org",
        help="Get a free token at https://aqicn.org/data-platform/token",
    )
    token = resolve_token()
    if token == "demo":
        st.info(
            "Using **demo** token — limited to ~5 cities. "
            "[Get a free token](https://aqicn.org/data-platform/token) for all 25."
        )
    else:
        st.success("Using your token ✓")

    st.divider()

    if st.button("🔄 Refresh Live Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.divider()

    view_mode = st.radio(
        "📊 Select View",
        [
            "🗺️ Pollution Map",
            "📊 City Comparison",
            "📈 Hourly Trend",
            "🧪 Pollutant Breakdown",
            "🏆 Rankings & Stats",
            "📸 Image Predictor",
        ],
    )

    st.divider()
    st.subheader("🔍 Filters")
    aqi_range = st.slider("AQI Range", 0, 500, (0, 500))
    all_states: list[str] = []   # populated after data loads

    st.divider()
    st.subheader("📋 AQI Legend")
    for lo, hi, label, color in AQI_SCALE:
        st.markdown(f"{aqi_emoji((lo + hi) // 2)} **{lo}–{hi}** — {label}")


# ── Load data ─────────────────────────────────────────────────────────────────
with st.spinner("Loading live AQI data…"):
    df = fetch_all_cities(token)

# State filter needs actual data
all_states = sorted(df["State"].unique().tolist())
with st.sidebar:
    selected_states = st.multiselect("Filter by State", all_states)

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🌍 India Air Quality Index Dashboard")

last_obs = df["ObsTime"].dropna().iloc[0] if "ObsTime" in df.columns and not df["ObsTime"].dropna().empty else "—"
st.caption(
    f"🔴 Live data from WAQI (aqicn.org) · "
    f"Last observation: **{last_obs}** · "
    f"{len(df)} cities loaded · "
    "Refresh sidebar to update"
)
st.divider()

# ── Apply filters ─────────────────────────────────────────────────────────────
dff = df[(df["AQI"] >= aqi_range[0]) & (df["AQI"] <= aqi_range[1])]
if selected_states:
    dff = dff[dff["State"].isin(selected_states)]

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
        map_style  = st.selectbox(
            "Map theme",
            ["carto-darkmatter", "open-street-map", "carto-positron"],
            key="map_style",
        )

        dff2 = dff.copy()
        dff2["size_val"] = dff2["AQI"].apply(lambda v: max(8, min(40, v / 10)))
        dff2["label"] = dff2.apply(
            lambda r: (
                f"{r['City']} ({r['State']})\n"
                f"AQI {r['AQI']} — {r['Category']}\n"
                f"PM2.5: {r['PM2.5']} | PM10: {r['PM10']}\n"
                f"NO2: {r['NO2']} | SO2: {r['SO2']} | CO: {r['CO']} | O3: {r['O3']}\n"
                f"Dominant: {r['Dominant'] or '—'}  |  Obs: {r['ObsTime'] or '—'}"
            ),
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
    show_df = dff[["City", "State", "AQI", "Category", "Dominant", "ObsTime"] + POLLUTANTS]\
        .sort_values("AQI", ascending=False)\
        .reset_index(drop=True)
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
        top_n   = st.slider("Number of cities", 5, len(dff), min(15, len(dff)), key="top_n")
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
# VIEW 3 — HOURLY TREND  (WAQI provides 24 h history in the feed)
# ═══════════════════════════════════════════════════════════════════════════════
elif "Trend" in view_mode:
    st.subheader("📈 24-Hour AQI Trend")
    st.info(
        "ℹ️ WAQI's free feed exposes the **current** AQI only. "
        "The 24-hour lines below are a diurnal simulation seeded from live AQI values. "
        "For real hourly history, upgrade to a WAQI Enterprise token."
    )

    city_options    = df["City"].tolist()
    selected_cities = st.multiselect(
        "Select cities to compare (up to 6)",
        city_options,
        default=city_options[:4],
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
            rng   = np.random.default_rng(hash(city) % (2**32))
            trend = [
                max(20, min(500, int(
                    base + 55 * np.sin((h - 6) * np.pi / 12) + rng.integers(-25, 25)
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


# ═══════════════════════════════════════════════════════════════════════════════
# VIEW 4 — POLLUTANT BREAKDOWN
# ═══════════════════════════════════════════════════════════════════════════════
elif "Pollutant" in view_mode:
    st.subheader("🧪 Pollutant Breakdown")

    selected_city = st.selectbox("Select a city", df["City"].tolist(), key="poll_city")
    row           = df[df["City"] == selected_city].iloc[0]
    label, color  = get_aqi_info(row["AQI"])

    # Find worst pollutant (those with data only)
    available_pollutants = [p for p in POLLUTANTS if row[p] > 0]
    primary_poll = (
        max(available_pollutants, key=lambda p: row[p] / SAFE_LIMITS[p])
        if available_pollutants else "—"
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🏙️ City",        selected_city, row["State"])
    c2.metric("🌡️ AQI",         row["AQI"],    label)
    c3.metric("📍 Primary",     primary_poll,  "highest vs safe limit")
    c4.metric("🕐 Observed",    row.get("ObsTime", "—"), "")

    st.divider()

    col_bars, col_radar = st.columns(2)

    with col_bars:
        st.subheader("📊 vs Safe Limit")
        for p in POLLUTANTS:
            val    = row[p]
            safe   = SAFE_LIMITS[p]
            pct    = min(float(val) / (safe * 3), 1.0)
            status = pollutant_status(val, safe)
            suffix = " *(no data)*" if val == 0 else f"   *(safe ≤ {safe})*"
            st.write(f"**{p}** — {val} {UNITS[p]}   {status}{suffix}")
            st.progress(float(pct))

    with col_radar:
        st.subheader("🕸️ Radar Overview")
        pct_vals = [
            float(min(row[p] / (SAFE_LIMITS[p] * 2) * 100, 100))
            for p in POLLUTANTS
        ]
        theta  = POLLUTANTS + [POLLUTANTS[0]]
        r_vals = pct_vals + [pct_vals[0]]

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=r_vals,
            theta=theta,
            fill="toself",
            fillcolor="rgba(0,123,255,0.3)",
            line=dict(color="blue", width=2),
            marker=dict(color="blue", size=7),
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
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
    # Only include pollutants with actual data
    live_polls = [p for p in POLLUTANTS if df[p].sum() > 0]
    corr     = df[["AQI"] + live_polls].corr().round(2)
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
# VIEW 6 — IMAGE PREDICTOR
# ═══════════════════════════════════════════════════════════════════════════════
elif "Image" in view_mode:
    st.subheader("📸 Image-Based Air Quality Predictor")
    st.write("Upload an outdoor photo and get a simulated visibility-based AQI estimate.")

    uploaded_file = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        img = Image.open(uploaded_file)
        st.image(img, caption="Uploaded Image", use_container_width=True)

        if st.button("Estimate from Image"):
            # Heuristic: use average brightness/saturation as a visibility proxy
            img_rgb  = img.convert("RGB")
            arr      = np.array(img_rgb).astype(float)
            # Desaturated, grey/hazy images have low std across channels
            channel_std = arr.std(axis=(0, 1)).mean()
            brightness  = arr.mean()
            # Low brightness + low saturation → hazy
            haze_score  = max(0.0, 1.0 - (channel_std / 80 + brightness / 400))
            pollution   = int(haze_score * 100)

            if pollution <= 20:
                status, msg = "🌿 Very Good", "Air appears clear and healthy"
            elif pollution <= 40:
                status, msg = "✅ Good",      "Air quality looks healthy"
            elif pollution <= 60:
                status, msg = "😐 Moderate",  "Some haziness detected"
            elif pollution <= 80:
                status, msg = "⚠️ Unhealthy", "Visible haze — air may be unhealthy"
            else:
                status, msg = "🚨 Very Unhealthy", "Heavy haze — air appears dangerous"

            st.subheader("Prediction Result")
            st.metric("Estimated Pollution Score", f"{pollution}%")
            st.progress(pollution / 100)

            st.subheader("Health Status")
            st.write(status)
            if pollution <= 40:
                st.success(msg)
            elif pollution <= 60:
                st.warning(msg)
            else:
                st.error(msg)

            st.subheader("Air Quality Scale")
            st.write("""
| Level          | Score range | Indicator      |
|----------------|-------------|----------------|
| 🌿 Very Good   | 0 – 20%     | Clear skies    |
| ✅ Good        | 21 – 40%    | Slight haze    |
| 😐 Moderate    | 41 – 60%    | Noticeable haze|
| ⚠️ Unhealthy   | 61 – 80%    | Heavy haze     |
| 🚨 Very Unhealthy | 81–100%  | Dense smog     |
""")
            st.caption(
                "⚠️ This is a heuristic estimate based on image brightness/saturation. "
                "For accurate readings use the live WAQI data in other views."
            )


# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "📡 Live data from [WAQI / aqicn.org](https://aqicn.org) · "
    "Data refreshes every 10 minutes · "
    "Built with Streamlit + Plotly"
)
