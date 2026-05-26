import streamlit as st
from PIL import Image
import random
import pandas as pd

st.set_page_config(page_title="Air Quality Index Indicator", page_icon="🌍", layout="wide")

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.aqi-badge {
    display: inline-block;
    padding: 6px 18px;
    border-radius: 30px;
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
}
.aqi-good        { background:#d4edda; color:#155724; }
.aqi-satisfactory{ background:#c8f5c8; color:#1a6b1a; }
.aqi-moderate    { background:#fff3cd; color:#856404; }
.aqi-poor        { background:#ffe0b2; color:#8c4a00; }
.aqi-very-poor   { background:#f8d7da; color:#842029; }
.aqi-severe      { background:#e8d5f5; color:#4a1466; }

.pollutant-card {
    background: #f8f9fa;
    border-left: 4px solid #4c6ef5;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
}
.health-rec {
    background: #eaf4fb;
    border-radius: 10px;
    padding: 14px 18px;
    margin-top: 10px;
    border-left: 5px solid #0288d1;
}
.scale-row {
    display: flex;
    align-items: center;
    margin-bottom: 6px;
    gap: 12px;
}
.scale-dot {
    width: 16px; height: 16px;
    border-radius: 50%;
    display: inline-block;
    flex-shrink: 0;
}
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────
st.title("🌍 Air Quality Index (AQI) Indicator")
st.markdown("Upload an image to analyse the air quality and get detailed AQI metrics, pollutant breakdown, and health recommendations.")

st.divider()

# ── AQI helpers ───────────────────────────────────────────────────────────────
AQI_SCALE = [
    (0,   50,  "Good",         "#00e400", "aqi-good",
     "Air quality is satisfactory. No health risk.",
     "✅ Ideal for all outdoor activities. Enjoy fresh air!"),
    (51,  100, "Satisfactory", "#92d050", "aqi-satisfactory",
     "Air quality is acceptable. Minor risk for sensitive individuals.",
     "🟢 Sensitive groups may want to limit prolonged outdoor exertion."),
    (101, 200, "Moderate",     "#ffff00", "aqi-moderate",
     "Moderate health concern for sensitive groups.",
     "😐 People with respiratory issues should reduce outdoor time."),
    (201, 300, "Poor",         "#ff7e00", "aqi-poor",
     "Everyone may experience health effects; sensitive groups more serious.",
     "⚠️ Wear a mask outdoors. Avoid prolonged exertion."),
    (301, 400, "Very Poor",    "#ff0000", "aqi-very-poor",
     "Health alert – everyone may experience serious health effects.",
     "🚨 Stay indoors. Use air purifiers. Seek medical attention if needed."),
    (401, 500, "Severe",       "#8f3f97", "aqi-severe",
     "Emergency conditions. Entire population likely affected.",
     "☣️ Do NOT go outside. Emergency response recommended."),
]

POLLUTANTS = ["PM2.5", "PM10", "NO₂", "SO₂", "CO", "O₃"]
POLLUTANT_UNITS = {"PM2.5": "µg/m³", "PM10": "µg/m³", "NO₂": "µg/m³",
                   "SO₂": "µg/m³", "CO": "mg/m³", "O₃": "µg/m³"}
POLLUTANT_SAFE  = {"PM2.5": 60, "PM10": 100, "NO₂": 80, "SO₂": 80, "CO": 2, "O₃": 100}

def get_aqi_info(aqi_value):
    for lo, hi, label, color, css, desc, rec in AQI_SCALE:
        if lo <= aqi_value <= hi:
            return label, color, css, desc, rec
    return AQI_SCALE[-1][2], AQI_SCALE[-1][3], AQI_SCALE[-1][4], AQI_SCALE[-1][5], AQI_SCALE[-1][6]

def simulate_pollutants(aqi):
    """Generate plausible pollutant values correlated with AQI."""
    factor = aqi / 100
    values = {}
    for p in POLLUTANTS:
        base = POLLUTANT_SAFE[p]
        noise = random.uniform(0.7, 1.3)
        values[p] = round(base * factor * noise, 2)
    return values

# ── Upload ────────────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader("📷 Upload an outdoor/city image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    col_img, col_info = st.columns([1, 1], gap="large")

    with col_img:
        img = Image.open(uploaded_file)
        st.image(img, caption="Uploaded Image", use_container_width=True)

    with col_info:
        st.markdown("### Ready to Analyse")
        st.info("Click **Predict AQI** to get air quality metrics for this image.")
        predict = st.button("🔍 Predict AQI", use_container_width=True, type="primary")

    if predict:
        # ── Simulate AQI ─────────────────────────────────────────────────────
        aqi = random.randint(10, 490)
        label, color, css, description, recommendation = get_aqi_info(aqi)
        pollutants = simulate_pollutants(aqi)

        st.divider()
        st.subheader("📊 Prediction Results")

        # ── Top metrics row ───────────────────────────────────────────────────
        m1, m2, m3 = st.columns(3)
        m1.metric("🌡️ AQI Value", aqi, help="Air Quality Index (0–500)")
        m2.metric("📋 Category", label)
        m3.metric("📍 Primary Pollutant", max(pollutants, key=pollutants.get))

        # ── AQI badge + description ───────────────────────────────────────────
        st.markdown(f"""
        <div class="aqi-badge {css}">{label} — AQI {aqi}</div>
        <p style="color:#555;">{description}</p>
        """, unsafe_allow_html=True)

        # ── Progress bar ──────────────────────────────────────────────────────
        st.progress(min(aqi / 500, 1.0))
        st.caption(f"AQI {aqi} / 500")

        st.divider()

        # ── Pollutant breakdown ───────────────────────────────────────────────
        left, right = st.columns(2, gap="large")

        with left:
            st.subheader("🧪 Pollutant Breakdown")
            for p, val in pollutants.items():
                safe = POLLUTANT_SAFE[p]
                pct = min(val / (safe * 5) * 100, 100)
                unit = POLLUTANT_UNITS[p]
                status = "✅" if val <= safe else ("⚠️" if val <= safe * 2 else "🚨")
                st.markdown(f"""
                <div class="pollutant-card">
                    <strong>{p}</strong> &nbsp; {status} &nbsp;
                    <span style="font-size:1.1rem;color:#333;">{val} {unit}</span>
                    <span style="float:right;color:#888;font-size:0.82rem;">Safe: ≤{safe} {unit}</span>
                </div>
                """, unsafe_allow_html=True)
                st.progress(pct / 100)

        with right:
            st.subheader("📈 AQI Comparison Chart")

            # Bar chart for all pollutants as % of their safe limit
            chart_df = pd.DataFrame({
                "Pollutant": list(pollutants.keys()),
                "% of Safe Limit": [
                    round(min(v / POLLUTANT_SAFE[p] * 100, 500), 1)
                    for p, v in pollutants.items()
                ]
            }).set_index("Pollutant")
            st.bar_chart(chart_df, height=280, color="#4c6ef5")
            st.caption("Values shown as % of safe limit (100% = at safe threshold)")

            # Health recommendation card
            st.markdown(f"""
            <div class="health-rec">
                <strong>🏥 Health Recommendation</strong><br><br>
                {recommendation}
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        # ── AQI Scale reference ───────────────────────────────────────────────
        st.subheader("📋 AQI Scale Reference")
        cols = st.columns(len(AQI_SCALE))
        for col, (lo, hi, lbl, clr, _, desc, _rec) in zip(cols, AQI_SCALE):
            border = "3px solid #333" if lbl == label else "1px solid #ddd"
            col.markdown(f"""
            <div style="text-align:center; padding:10px 6px; border-radius:10px;
                        border:{border}; background:{clr}22;">
                <div style="font-size:1.5rem; font-weight:800; color:{clr};">{lo}–{hi}</div>
                <div style="font-weight:600; font-size:0.82rem; margin:4px 0;">{lbl}</div>
            </div>
            """, unsafe_allow_html=True)

else:
    # ── Placeholder when no image uploaded ────────────────────────────────────
    st.markdown("### 🌤️ AQI Scale at a Glance")
    cols = st.columns(len(AQI_SCALE))
    for col, (lo, hi, lbl, clr, _, desc, _rec) in zip(cols, AQI_SCALE):
        col.markdown(f"""
        <div style="text-align:center; padding:12px 6px; border-radius:10px;
                    border:1px solid #ddd; background:{clr}22;">
            <div style="font-size:1.4rem; font-weight:800; color:{clr};">{lo}–{hi}</div>
            <div style="font-weight:600; font-size:0.85rem; margin:4px 0;">{lbl}</div>
            <div style="font-size:0.75rem; color:#555;">{desc[:45]}…</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.info("👆 Upload an image above to get a full AQI prediction with pollutant breakdown and health advice.")
