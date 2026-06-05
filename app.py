import streamlit as st
import pandas as pd
import numpy as np
import random
import time
import datetime
import json
import hashlib
import re
import os
import pathlib
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ══════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="India AQI Command Center",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════
# PERSISTENT STORAGE
# ══════════════════════════════════════════════════════════════════
_DATA_DIR        = pathlib.Path("aqi_data")
_DATA_DIR.mkdir(exist_ok=True)
_USERS_FILE      = _DATA_DIR / "users_db.json"
_ATTENDANCE_FILE = _DATA_DIR / "attendance_log.json"

def _hash(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def _load_users_db():
    if _USERS_FILE.exists():
        with open(_USERS_FILE) as f:
            return json.load(f)
    demo = {"demo@aqicommand.in": {
        "name": "Demo Analyst", "password_hash": _hash("Demo@1234"),
        "role": "Analyst", "joined": "2024-01-01",
        "last_login": None, "alerts_enabled": True,
        "alert_threshold": 200, "theme": "Cyber Blue", "notifications": []
    }}
    _save_users_db(demo)
    return demo

def _save_users_db(db):
    with open(_USERS_FILE, "w") as f:
        json.dump(db, f, indent=2)

def _load_attendance():
    if _ATTENDANCE_FILE.exists():
        with open(_ATTENDANCE_FILE) as f:
            return json.load(f)
    return []

def _save_attendance(log):
    with open(_ATTENDANCE_FILE, "w") as f:
        json.dump(log, f, indent=2)

def _record_attendance(email, name, event="login"):
    log = _load_attendance()
    log.append({
        "email": email, "name": name, "event": event,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "date": datetime.date.today().isoformat(),
    })
    _save_attendance(log)

# ══════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════
def init_session():
    defaults = {
        "logged_in": False, "current_user": None,
        "auth_msg": ("", ""), "login_anim": False,
        "alerts_log": [], "df": None,
        "live_aqi": 142, "live_city": "Mumbai",
        "live_history": [142],
        "last_refresh": datetime.datetime.now(),
        "auto_refresh": False, "compare_cities": [],
        "nav_page": "🔴 Live Air Pollution",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    if "users_db" not in st.session_state:
        st.session_state.users_db = _load_users_db()

init_session()

# ══════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════
def is_valid_email(e):
    return bool(re.match(r"^[^@]+@[^@]+\.[^@]+$", e))

def is_strong_password(pw):
    return (len(pw) >= 8 and re.search(r"[A-Z]", pw)
            and re.search(r"[0-9]", pw) and re.search(r"[^A-Za-z0-9]", pw))

# ══════════════════════════════════════════════════════════════════
# CONSTANTS & DATA
# ══════════════════════════════════════════════════════════════════
CITIES = [
    {"name":"Delhi","lat":28.61,"lon":77.20,"state":"Delhi"},
    {"name":"Mumbai","lat":19.07,"lon":72.87,"state":"Maharashtra"},
    {"name":"Kolkata","lat":22.57,"lon":88.36,"state":"West Bengal"},
    {"name":"Chennai","lat":13.08,"lon":80.27,"state":"Tamil Nadu"},
    {"name":"Bangalore","lat":12.97,"lon":77.59,"state":"Karnataka"},
    {"name":"Hyderabad","lat":17.38,"lon":78.48,"state":"Telangana"},
    {"name":"Ahmedabad","lat":23.02,"lon":72.57,"state":"Gujarat"},
    {"name":"Pune","lat":18.52,"lon":73.85,"state":"Maharashtra"},
    {"name":"Jaipur","lat":26.91,"lon":75.79,"state":"Rajasthan"},
    {"name":"Lucknow","lat":26.84,"lon":80.94,"state":"Uttar Pradesh"},
    {"name":"Kanpur","lat":26.44,"lon":80.33,"state":"Uttar Pradesh"},
    {"name":"Nagpur","lat":21.14,"lon":79.08,"state":"Maharashtra"},
    {"name":"Patna","lat":25.59,"lon":85.13,"state":"Bihar"},
    {"name":"Bhopal","lat":23.25,"lon":77.40,"state":"Madhya Pradesh"},
    {"name":"Surat","lat":21.19,"lon":72.83,"state":"Gujarat"},
    {"name":"Chandigarh","lat":30.73,"lon":76.78,"state":"Chandigarh"},
    {"name":"Varanasi","lat":25.31,"lon":82.97,"state":"Uttar Pradesh"},
    {"name":"Agra","lat":27.17,"lon":78.01,"state":"Uttar Pradesh"},
    {"name":"Amritsar","lat":31.63,"lon":74.87,"state":"Punjab"},
    {"name":"Visakhapatnam","lat":17.68,"lon":83.21,"state":"Andhra Pradesh"},
    {"name":"Indore","lat":22.72,"lon":75.86,"state":"Madhya Pradesh"},
    {"name":"Coimbatore","lat":11.01,"lon":76.97,"state":"Tamil Nadu"},
    {"name":"Kochi","lat":9.93,"lon":76.26,"state":"Kerala"},
    {"name":"Guwahati","lat":26.14,"lon":91.74,"state":"Assam"},
    {"name":"Bhubaneswar","lat":20.29,"lon":85.82,"state":"Odisha"},
]

POLLUTANTS  = ["PM2.5", "PM10", "NO2", "SO2", "CO", "O3"]
SAFE_LIMITS = {"PM2.5":60,"PM10":100,"NO2":80,"SO2":80,"CO":2.0,"O3":100}
UNITS       = {"PM2.5":"µg/m³","PM10":"µg/m³","NO2":"µg/m³","SO2":"µg/m³","CO":"mg/m³","O3":"µg/m³"}

AQI_SCALE = [
    (0,   50,  "Good",        "#00ff88","💚","Air quality is excellent. No health risk."),
    (51,  100, "Satisfactory","#a3ff00","🟡","Sensitive individuals should take mild precautions."),
    (101, 200, "Moderate",    "#ffaa00","🟠","People with respiratory issues may experience discomfort."),
    (201, 300, "Poor",        "#ff6600","🔴","Avoid prolonged outdoor activity. Wear masks."),
    (301, 400, "Very Poor",   "#ff2255","🚨","Serious health effects. Stay indoors."),
    (401, 500, "Severe",      "#aa33ff","☠️","Emergency conditions. Avoid all outdoor exposure!"),
]

HEALTH_TIPS = {
    "Good":        ["✅ Great day for outdoor exercise","🌿 Open windows for fresh air","🚴 Ideal for cycling or jogging"],
    "Satisfactory":["😷 Sensitive groups carry inhalers","🏃 Moderate outdoor exercise OK","👁️ May cause mild eye irritation"],
    "Moderate":    ["😷 Wear N95 mask outdoors","🏠 Reduce time outside","💊 Asthma patients avoid exertion"],
    "Poor":        ["🚫 Avoid outdoor exercise","😷 N95 mask mandatory outdoors","🏥 Seek medical help if breathing issues"],
    "Very Poor":   ["🔴 Stay indoors at all times","🪟 Keep windows closed","🚑 Call doctor if symptoms appear"],
    "Severe":      ["☠️ Do NOT go outside","🏥 Emergency: seek immediate medical attention","🔴 Government may enforce restrictions"],
}

AXIS_STYLE = dict(gridcolor="rgba(0,229,255,0.07)", linecolor="rgba(0,229,255,0.15)",
                  tickfont=dict(color="#5a7a9a"))

def apply_theme(fig, height=400, margin=None, **kwargs):
    m = margin or dict(l=60, r=20, t=40, b=60)
    legend = {**dict(bgcolor="rgba(7,16,32,0.85)", bordercolor="rgba(0,229,255,0.18)",
                     borderwidth=1), **kwargs.pop("legend", {})}
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(7,16,32,0.6)",
        font=dict(family="Exo 2, sans-serif", color="#d8f0ff", size=12),
        legend=legend, margin=m, height=height, **kwargs)
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig

def get_aqi_info(aqi):
    for lo, hi, label, color, emoji, advice in AQI_SCALE:
        if lo <= aqi <= hi:
            return label, color, emoji, advice
    return "Severe", "#aa33ff", "☠️", AQI_SCALE[-1][5]

def simulate_pollutants(aqi):
    factor = aqi / 150
    return {p: round(SAFE_LIMITS[p] * factor * random.uniform(0.65, 1.35), 2) for p in POLLUTANTS}

def generate_data():
    rows = []
    for c in CITIES:
        aqi = random.randint(25, 490)
        label, color, emoji, advice = get_aqi_info(aqi)
        poll = simulate_pollutants(aqi)
        rows.append({"City":c["name"],"State":c["state"],"Lat":c["lat"],"Lon":c["lon"],
                     "AQI":aqi,"Category":label,"Color":color,"Emoji":emoji,**poll})
    return pd.DataFrame(rows)

def pollutant_status(val, safe):
    if val <= safe:       return "✅ Safe", "#00ff88"
    if val <= safe * 1.5: return "⚠️ Warning", "#ffaa00"
    return "🚨 Danger", "#ff2255"

def check_alerts(df_in, threshold=200):
    alerts = []
    for _, row in df_in.iterrows():
        if row["AQI"] > threshold:
            level = "CRITICAL" if row["AQI"] > 300 else "WARNING"
            alerts.append({"city":row["City"],"aqi":row["AQI"],"level":level,
                           "cat":row["Category"],"color":row["Color"],
                           "time":datetime.datetime.now().strftime("%H:%M:%S")})
    return sorted(alerts, key=lambda x: x["aqi"], reverse=True)

# ══════════════════════════════════════════════════════════════════
# LOGIN SCREEN
# ══════════════════════════════════════════════════════════════════
def show_auth_screen():
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        st.title("🛰️ AQI COMMAND CENTER")
        st.caption("INDIA POLLUTION INTELLIGENCE SYSTEM v4.0")
        st.divider()

        msg_text, msg_type = st.session_state.auth_msg
        if msg_text:
            if msg_type == "success":
                st.success(msg_text)
            elif msg_type == "error":
                st.error(msg_text)
            else:
                st.info(msg_text)

        tab_login, tab_reg = st.tabs(["🔐  LOGIN", "📡  REGISTER"])

        with tab_login:
            st.caption("ENTER CREDENTIALS TO ACCESS THE SYSTEM")
            with st.form("login_form", clear_on_submit=False):
                login_email = st.text_input("📧 Email Address", placeholder="you@domain.com", key="form_login_email")
                login_pw    = st.text_input("🔒 Password", placeholder="••••••••", type="password", key="form_login_pw")
                st.caption("Demo: demo@aqicommand.in / Demo@1234")
                submitted   = st.form_submit_button("🚀  LAUNCH COMMAND CENTER", use_container_width=True)
            if submitted:
                if not login_email or not login_pw:
                    st.session_state.auth_msg = ("⚠️ Please fill in all fields.", "error"); st.rerun()
                elif login_email.strip() not in st.session_state.users_db:
                    st.session_state.auth_msg = ("❌ Email not found. Please register first.", "error"); st.rerun()
                elif st.session_state.users_db[login_email.strip()]["password_hash"] != _hash(login_pw):
                    st.session_state.auth_msg = ("❌ Incorrect password. Try again.", "error"); st.rerun()
                else:
                    email = login_email.strip()
                    st.session_state.users_db[email]["last_login"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    _save_users_db(st.session_state.users_db)
                    _record_attendance(email, st.session_state.users_db[email]["name"], "login")
                    st.session_state.logged_in    = True
                    st.session_state.current_user = email
                    st.session_state.auth_msg     = ("", "")
                    st.session_state.login_anim   = True
                    st.rerun()
            st.caption("──── SECURE · AES-256 ENCRYPTED ────")

        with tab_reg:
            with st.form("register_form", clear_on_submit=False):
                reg_name  = st.text_input("👤 Full Name", placeholder="Dr. Aditya Kumar")
                reg_email = st.text_input("📧 Email", placeholder="you@domain.com")
                reg_role  = st.selectbox("🏷️ Role", ["Analyst","Researcher","Policy Maker","Student","Journalist"])
                reg_pw    = st.text_input("🔒 Password", type="password", placeholder="8+ chars · Uppercase · Number · Symbol")
                reg_pw2   = st.text_input("🔒 Confirm Password", type="password", placeholder="Re-enter password")
                terms     = st.checkbox("I agree to Terms of Service")
                reg_submitted = st.form_submit_button("📡  CREATE ACCOUNT", use_container_width=True)
            if reg_submitted:
                errors = []
                if not reg_name.strip():                                       errors.append("Name required")
                if not is_valid_email(reg_email):                              errors.append("Valid email required")
                if reg_email in st.session_state.users_db:                     errors.append("Email already registered")
                if not is_strong_password(reg_pw):                             errors.append("Password too weak (uppercase + number + symbol + 8+ chars)")
                if reg_pw != reg_pw2:                                          errors.append("Passwords don't match")
                if not terms:                                                  errors.append("Accept Terms of Service")
                if errors:
                    st.session_state.auth_msg = ("❌ " + " · ".join(errors), "error"); st.rerun()
                else:
                    st.session_state.users_db[reg_email] = {
                        "name": reg_name.strip(), "password_hash": _hash(reg_pw),
                        "role": reg_role, "joined": datetime.date.today().isoformat(),
                        "last_login": None, "alerts_enabled": True,
                        "alert_threshold": 200, "theme": "Cyber Blue", "notifications": []
                    }
                    _save_users_db(st.session_state.users_db)
                    _record_attendance(reg_email, reg_name.strip(), "register")
                    st.session_state.auth_msg = (f"✅ Account created! Welcome, {reg_name.split()[0]}. Please login.", "success")
                    st.rerun()

        st.caption("🛰️ INDIA AQI COMMAND CENTER v4.0 · REAL-TIME · INTELLIGENT · SECURE")

# ══════════════════════════════════════════════════════════════════
# AUTH GUARD
# ══════════════════════════════════════════════════════════════════
if not st.session_state.logged_in:
    show_auth_screen()
    st.stop()

# Login animation
if st.session_state.login_anim:
    user_info_anim = st.session_state.users_db[st.session_state.current_user]
    ph = st.empty()
    with ph.container():
        st.success(f"✅ ACCESS GRANTED — Welcome, {user_info_anim['name']}!")
        st.info("🛰️ Initializing Command Center…")
    time.sleep(2)
    ph.empty()
    st.session_state.login_anim = False
    st.rerun()

# ══════════════════════════════════════════════════════════════════
# GENERATE DATA (once per session)
# ══════════════════════════════════════════════════════════════════
if st.session_state.df is None:
    st.session_state.df = generate_data()

# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════
user_info            = st.session_state.users_db[st.session_state.current_user]
alert_threshold_user = user_info.get("alert_threshold", 200)
active_alerts        = check_alerts(st.session_state.df, alert_threshold_user)

with st.sidebar:
    st.title("🛰️ AQI COMMAND")
    st.caption("INDIA MONITOR v4.0")
    st.divider()

    initials = "".join([w[0].upper() for w in user_info["name"].split()[:2]])
    st.subheader(f"{initials} — {user_info['name']}")
    st.caption(st.session_state.current_user)
    st.caption(f"⬡ {user_info['role']}  |  Joined: {user_info['joined']}")
    st.caption(f"Last login: {user_info.get('last_login') or 'First session'}")
    st.divider()

    if active_alerts:
        st.error(f"🚨 {len(active_alerts)} ACTIVE ALERT{'S' if len(active_alerts)>1 else ''}")

    if st.button("🚪  LOGOUT", use_container_width=True, key="logout_btn"):
        for key in ["logged_in","current_user","auth_msg","login_anim",
                    "alerts_log","df","live_aqi","live_city","live_history","nav_page"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    st.divider()

    if st.button("🔄  REFRESH DATA", use_container_width=True, key="refresh_btn"):
        st.session_state.df           = generate_data()
        st.session_state.last_refresh = datetime.datetime.now()
        st.rerun()

    st.session_state.auto_refresh = st.checkbox("⚡ Auto-Refresh (30s)", value=st.session_state.auto_refresh)
    st.divider()

    view_mode = st.radio("📡  NAVIGATION", [
        "🔴 Live Air Pollution","🗺️ Pollution Map","📊 City Comparison",
        "📈 Hourly Trend","🧪 Pollutant Breakdown","🏆 Rankings & Stats",
        "🔔 Alerts & Notifications","🌡️ Weather & AQI Forecast",
        "📸 Image Predictor","📋 Data Export","👤 My Account",
    ], key="view_mode_radio")

    st.divider()
    st.caption("FILTERS")
    aqi_range       = st.slider("AQI Range", 0, 500, (0, 500))
    all_states      = sorted(st.session_state.df["State"].unique())
    selected_states = st.multiselect("Filter by State", all_states)
    st.divider()

    st.caption("AQI LEGEND")
    for lo, hi, label, color, emoji, _ in AQI_SCALE:
        st.caption(f"{emoji} {lo}–{hi}  {label}")

    st.divider()
    lr = st.session_state.last_refresh.strftime("%H:%M:%S")
    st.caption(f"LAST UPDATE: {lr}")

# ══════════════════════════════════════════════════════════════════
# DATA PREP
# ══════════════════════════════════════════════════════════════════
df  = st.session_state.df
dff = df[(df["AQI"] >= aqi_range[0]) & (df["AQI"] <= aqi_range[1])]
if selected_states:
    dff = dff[dff["State"].isin(selected_states)]

if st.session_state.auto_refresh:
    elapsed = (datetime.datetime.now() - st.session_state.last_refresh).seconds
    if elapsed >= 30:
        st.session_state.df           = generate_data()
        st.session_state.last_refresh = datetime.datetime.now()
        st.rerun()

# ══════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════
col_title, col_live = st.columns([3, 1])
with col_title:
    st.title("🛰️ INDIA AQI COMMAND CENTER")
    st.caption("REAL-TIME AIR QUALITY INTELLIGENCE · 25 MAJOR CITIES · POLLUTION MONITOR v4.0")
with col_live:
    st.success("🟢 LIVE MONITORING")

ticker_items = "  ·  ".join([f"{r['Emoji']} {r['City']}: AQI {r['AQI']} ({r['Category']})" for _, r in df.iterrows()])
st.info(f"📡 LIVE  {ticker_items}")

avg_aqi   = int(df["AQI"].mean())
worst     = df.loc[df["AQI"].idxmax()]
best      = df.loc[df["AQI"].idxmin()]
dangerous = int((df["AQI"] > 200).sum())
safe_count= int((df["AQI"] <= 100).sum())
avg_label, avg_color, avg_emoji, _ = get_aqi_info(avg_aqi)

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("🌡️ National Avg",   avg_aqi,        f"{avg_emoji} {avg_label}")
c2.metric("☣️ Most Polluted",  worst["City"],   f"AQI {worst['AQI']}")
c3.metric("🌿 Cleanest",       best["City"],    f"AQI {best['AQI']}")
c4.metric("⚠️ High Risk",      dangerous,       "AQI > 200")
c5.metric("✅ Safe Cities",    safe_count,      "AQI ≤ 100")
c6.metric("🚨 Active Alerts",  len(active_alerts), f"Threshold: {alert_threshold_user}")
st.divider()

# ══════════════════════════════════════════════════════════════════
# PAGE: LIVE
# ══════════════════════════════════════════════════════════════════
if "Live" in view_mode:
    st.header("🔴 LIVE AIR POLLUTION INDICATOR")

    lcol1, lcol2, lcol3 = st.columns([2, 2, 1])
    with lcol1:
        live_city = st.selectbox(
            "📍 Select City", [c["name"] for c in CITIES],
            index=[c["name"] for c in CITIES].index(st.session_state.live_city),
            key="live_city_sel")
        if live_city != st.session_state.live_city:
            st.session_state.live_city    = live_city
            base_aqi = int(df[df["City"] == live_city]["AQI"].values[0])
            st.session_state.live_aqi     = base_aqi
            st.session_state.live_history = [base_aqi]
    with lcol2:
        if st.button("⚡  SIMULATE NEW READING", use_container_width=True, key="sim_btn"):
            prev    = st.session_state.live_aqi
            new_aqi = max(10, min(500, prev + random.randint(-30, 30)))
            st.session_state.live_aqi = new_aqi
            st.session_state.live_history.append(new_aqi)
            if len(st.session_state.live_history) > 60:
                st.session_state.live_history.pop(0)
    with lcol3:
        st.success("🟢 ACTIVE")

    current_aqi = st.session_state.live_aqi
    label, color, emoji, advice = get_aqi_info(current_aqi)
    poll_vals   = simulate_pollutants(current_aqi)
    tips        = HEALTH_TIPS.get(label, [])

    gauge_col, detail_col = st.columns([1, 2])
    with gauge_col:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta", value=current_aqi,
            delta={"reference": st.session_state.live_history[-2] if len(st.session_state.live_history) >= 2 else current_aqi,
                   "increasing":{"color":"#ff2255"},"decreasing":{"color":"#00ff88"},
                   "font":{"size":16,"family":"Orbitron, sans-serif"}},
            number={"font":{"size":52,"family":"Orbitron, sans-serif","color":color},"suffix":" AQI"},
            gauge={"axis":{"range":[0,500],"tickvals":[0,50,100,200,300,400,500],"tickfont":{"size":9,"color":"#5a7a9a"}},
                   "bar":{"color":color,"thickness":0.22},"bgcolor":"rgba(0,0,0,0)","borderwidth":0,
                   "steps":[{"range":[0,50],"color":"rgba(0,255,136,0.12)"},{"range":[50,100],"color":"rgba(163,255,0,0.1)"},
                             {"range":[100,200],"color":"rgba(255,170,0,0.1)"},{"range":[200,300],"color":"rgba(255,102,0,0.1)"},
                             {"range":[300,400],"color":"rgba(255,34,85,0.1)"},{"range":[400,500],"color":"rgba(170,51,255,0.1)"}],
                   "threshold":{"line":{"color":color,"width":4},"thickness":0.85,"value":current_aqi}},
            title={"text":f"{emoji} {label}<br><span style='font-size:10px;color:#5a7a9a;'>{live_city} · Live Sensor</span>",
                   "font":{"size":16,"family":"Orbitron, sans-serif","color":"#d8f0ff"}}))
        fig_gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                font=dict(color="#d8f0ff"), height=330, margin=dict(l=20,r=20,t=60,b=20))
        st.plotly_chart(fig_gauge, use_container_width=True)
        st.info(f"**HEALTH ADVISORY**\n\n{advice}")

    with detail_col:
        st.subheader("🧪 LIVE POLLUTANT READINGS")
        for p in POLLUTANTS:
            val  = poll_vals[p]; safe = SAFE_LIMITS[p]
            pct  = min(val / (safe * 2.5), 1.0)
            status_text, _ = pollutant_status(val, safe)
            pcol1, pcol2, pcol3 = st.columns([2, 2, 1])
            pcol1.write(f"**{p}**")
            pcol2.write(f"{val} {UNITS[p]}")
            pcol3.write(status_text)
            st.progress(pct)

        st.divider()
        st.subheader("💡 HEALTH TIPS")
        for tip in tips:
            st.write(tip)

    st.divider()
    st.subheader("📡 REAL-TIME AQI STREAM (LAST 60 READINGS)")
    hist   = st.session_state.live_history
    x_vals = list(range(len(hist)))
    colors_hist = [get_aqi_info(v)[1] for v in hist]
    r_int, g_int, b_int = int(color[1:3],16), int(color[3:5],16), int(color[5:7],16)
    fig_stream = go.Figure()
    fig_stream.add_trace(go.Scatter(x=x_vals, y=hist, mode="lines", line=dict(color=color,width=0),
        fill="tozeroy", fillcolor=f"rgba({r_int},{g_int},{b_int},0.08)", showlegend=False, hoverinfo="skip"))
    fig_stream.add_trace(go.Scatter(x=x_vals, y=hist, mode="lines+markers",
        line=dict(color=color,width=2.5),
        marker=dict(size=[10 if i==len(hist)-1 else 4 for i in range(len(hist))],
                    color=colors_hist, line=dict(width=1,color="rgba(0,0,0,0.4)")),
        name="AQI", hovertemplate="Reading %{x}: AQI %{y}<extra></extra>"))
    for threshold, t_label, t_color in [(100,"Satisfactory","#a3ff00"),(200,"Moderate","#ffaa00"),(300,"Poor","#ff6600")]:
        fig_stream.add_hline(y=threshold, line_dash="dash", line_color=t_color, opacity=0.35,
            annotation_text=t_label, annotation_font_size=9, annotation_font_color=t_color)
    apply_theme(fig_stream, height=250, margin=dict(l=60,r=20,t=20,b=50), showlegend=False)
    fig_stream.update_xaxes(title_text="Reading #")
    fig_stream.update_yaxes(title_text="AQI Value", range=[0,520])
    st.plotly_chart(fig_stream, use_container_width=True)

    st.subheader("🔮 24-HOUR AQI FORECAST")
    now_h    = datetime.datetime.now().hour
    h_labels = [f"{(now_h+i)%24:02d}:00" for i in range(24)]
    forecast = [max(20,min(500,int(current_aqi+40*np.sin((i-6)*np.pi/12)+random.randint(-20,20)))) for i in range(24)]
    f_colors = [get_aqi_info(v)[1] for v in forecast]
    fig_fc   = go.Figure()
    fig_fc.add_trace(go.Bar(x=h_labels, y=forecast, marker_color=f_colors, marker_line_width=0,
        hovertemplate="%{x}<br>AQI: %{y}<extra></extra>", name="Forecast"))
    apply_theme(fig_fc, height=210, margin=dict(l=60,r=20,t=10,b=70))
    fig_fc.update_xaxes(title_text="Hour", tickangle=-45)
    fig_fc.update_yaxes(title_text="AQI")
    st.plotly_chart(fig_fc, use_container_width=True)

# ══════════════════════════════════════════════════════════════════
# PAGE: MAP
# ══════════════════════════════════════════════════════════════════
elif "Map" in view_mode:
    st.header("🗺️ INDIA POLLUTION MAP")
    col_left, col_right = st.columns([3, 1])
    with col_left:
        mapc1, mapc2 = st.columns(2)
        map_metric = mapc1.selectbox("Bubble value", ["AQI"]+POLLUTANTS, key="map_metric")
        map_style  = mapc2.selectbox("Map theme", ["carto-darkmatter","open-street-map","carto-positron"], key="map_style")
        dff2 = dff.copy()
        dff2["size_val"] = dff2["AQI"].apply(lambda v: max(8, min(40, v/10)))
        dff2["label"] = dff2.apply(lambda r:
            f"<b>{r['City']}</b>  {r['Emoji']}<br>AQI: {r['AQI']}  ·  {r['Category']}<br>"
            f"PM2.5: {r['PM2.5']}  |  PM10: {r['PM10']}<br>"
            f"NO2: {r['NO2']}  |  SO2: {r['SO2']}  |  CO: {r['CO']}  |  O3: {r['O3']}", axis=1)
        fig_map = go.Figure(go.Scattermapbox(
            lat=dff2["Lat"], lon=dff2["Lon"], mode="markers+text",
            marker=dict(size=dff2["size_val"], color=dff2["AQI"],
                colorscale=[[0,"#00ff88"],[0.1,"#00ff88"],[0.2,"#a3ff00"],[0.4,"#ffaa00"],
                            [0.6,"#ff6600"],[0.8,"#ff2255"],[1,"#aa33ff"]],
                cmin=0, cmax=500, opacity=0.9,
                colorbar=dict(title=dict(text="AQI",font=dict(color="#d8f0ff")),
                              thickness=11, len=0.6, tickfont=dict(color="#d8f0ff"))),
            text=dff2[map_metric].round(0).astype(int).astype(str),
            textfont=dict(size=9,color="white"), textposition="middle center",
            hovertext=dff2["label"], hoverinfo="text"))
        fig_map.update_layout(
            mapbox=dict(style=map_style, center=dict(lat=22.5,lon=82.0), zoom=3.8),
            margin=dict(l=0,r=0,t=0,b=0), height=540, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_map, use_container_width=True)
    with col_right:
        st.subheader("CITY RANKINGS")
        ranked = dff.sort_values("AQI", ascending=False)[["City","AQI","Category","Emoji"]].reset_index(drop=True)
        for _, row in ranked.iterrows():
            st.write(f"{row['Emoji']} **{row['City']}** — {row['AQI']} ({row['Category']})")

# ══════════════════════════════════════════════════════════════════
# PAGE: COMPARISON
# ══════════════════════════════════════════════════════════════════
elif "Comparison" in view_mode:
    st.header("📊 CITY AQI COMPARISON")
    cc1, cc2 = st.columns(2)
    top_n   = cc1.slider("Number of cities", 5, 25, 15, key="top_n")
    sort_by = cc2.selectbox("Sort / colour by", ["AQI"]+POLLUTANTS, key="sort_by")
    sorted_df = dff.sort_values(sort_by, ascending=False).head(top_n)
    unit = UNITS.get(sort_by, "")
    fig_bar = go.Figure(go.Bar(
        x=sorted_df["City"], y=sorted_df[sort_by],
        marker_color=sorted_df["Color"], marker_line_width=0,
        text=sorted_df[sort_by].round(1), textposition="outside",
        hovertemplate="<b>%{x}</b><br>"+sort_by+": %{y}<extra></extra>"))
    apply_theme(fig_bar, height=420)
    fig_bar.update_xaxes(title_text="City", tickangle=-38)
    fig_bar.update_yaxes(title_text=f"{sort_by} ({unit})" if unit else sort_by)
    st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()
    pie_col, scatter_col = st.columns(2)
    with pie_col:
        st.subheader("🥧 AQI CATEGORY DISTRIBUTION")
        cat_order  = ["Good","Satisfactory","Moderate","Poor","Very Poor","Severe"]
        cat_colors = [c[3] for c in AQI_SCALE]
        cat_counts = df["Category"].value_counts().reindex(cat_order, fill_value=0)
        fig_pie = go.Figure(go.Pie(
            labels=cat_counts.index, values=cat_counts.values,
            marker_colors=cat_colors, hole=0.5,
            hovertemplate="<b>%{label}</b><br>Cities: %{value} (%{percent})<extra></extra>",
            textinfo="label+percent", textfont=dict(family="Exo 2, sans-serif",size=11)))
        apply_theme(fig_pie, height=330, margin=dict(l=0,r=0,t=20,b=0))
        st.plotly_chart(fig_pie, use_container_width=True)
    with scatter_col:
        st.subheader("🔵 PM2.5 vs PM10 SCATTER")
        fig_sc = go.Figure()
        for cat, grp in df.groupby("Category"):
            col_c = grp["Color"].iloc[0]
            fig_sc.add_trace(go.Scatter(
                x=grp["PM2.5"], y=grp["PM10"], mode="markers+text", name=cat,
                text=grp["City"], textposition="top center",
                textfont=dict(size=8,color="#5a7a9a"),
                marker=dict(size=10,color=col_c,opacity=0.85,line=dict(width=1,color="rgba(255,255,255,0.15)")),
                hovertemplate="<b>%{text}</b><br>PM2.5: %{x}<br>PM10: %{y}<extra></extra>"))
        apply_theme(fig_sc, height=330)
        fig_sc.update_xaxes(title_text="PM2.5 (µg/m³)")
        fig_sc.update_yaxes(title_text="PM10 (µg/m³)")
        st.plotly_chart(fig_sc, use_container_width=True)

# ══════════════════════════════════════════════════════════════════
# PAGE: TREND
# ══════════════════════════════════════════════════════════════════
elif "Trend" in view_mode:
    st.header("📈 24-HOUR AQI TREND")
    selected_cities = st.multiselect(
        "Select cities (up to 6)", df["City"].tolist(),
        default=["Delhi","Mumbai","Bangalore","Chennai"], key="trend_cities")
    if not selected_cities:
        st.info("Please select at least one city above.")
    else:
        hour_labels = [f"{h:02d}:00" for h in range(24)]
        palette = ["#00e5ff","#ff2255","#00ff88","#ffaa00","#aa33ff","#0070ff"]
        fig_line = go.Figure()
        for i, city in enumerate(selected_cities[:6]):
            base  = int(df.loc[df["City"]==city,"AQI"].values[0])
            trend = [max(20,min(500,int(base+55*np.sin((h-6)*np.pi/12)+random.randint(-25,25)))) for h in range(24)]
            col_c = palette[i%len(palette)]
            r_i,g_i,b_i = int(col_c[1:3],16),int(col_c[3:5],16),int(col_c[5:7],16)
            fig_line.add_trace(go.Scatter(x=hour_labels, y=trend, mode="none",
                fill="tozeroy", fillcolor=f"rgba({r_i},{g_i},{b_i},0.05)", showlegend=False, hoverinfo="skip"))
            fig_line.add_trace(go.Scatter(x=hour_labels, y=trend, mode="lines+markers", name=city,
                line=dict(color=col_c,width=2.5), marker=dict(size=5,color=col_c),
                hovertemplate=f"<b>{city}</b> %{{x}}: AQI %{{y}}<extra></extra>"))
        apply_theme(fig_line, height=440,
            legend=dict(orientation="h",yanchor="bottom",y=1.02,
                        bgcolor="rgba(7,16,32,0.85)",bordercolor="rgba(0,229,255,0.15)",borderwidth=1))
        fig_line.update_xaxes(title_text="Hour", tickangle=-45)
        fig_line.update_yaxes(title_text="AQI", range=[0,520])
        st.plotly_chart(fig_line, use_container_width=True)

        st.subheader("📅 7-DAY AQI TREND")
        days = [f"Day {i+1}" for i in range(7)]
        fig_week = go.Figure()
        for i, city in enumerate(selected_cities[:6]):
            base   = int(df.loc[df["City"]==city,"AQI"].values[0])
            weekly = [max(20,min(500, base+random.randint(-60,60))) for _ in range(7)]
            col_c  = palette[i%len(palette)]
            fig_week.add_trace(go.Scatter(x=days, y=weekly, mode="lines+markers", name=city,
                line=dict(color=col_c,width=2), marker=dict(size=8,color=col_c,symbol="diamond"),
                hovertemplate=f"<b>{city}</b> %{{x}}: AQI %{{y}}<extra></extra>"))
        apply_theme(fig_week, height=300, legend=dict(orientation="h",yanchor="bottom",y=1.02))
        fig_week.update_yaxes(title_text="AQI")
        st.plotly_chart(fig_week, use_container_width=True)

# ══════════════════════════════════════════════════════════════════
# PAGE: POLLUTANT BREAKDOWN
# ══════════════════════════════════════════════════════════════════
elif "Pollutant" in view_mode:
    st.header("🧪 POLLUTANT BREAKDOWN")
    selected_city = st.selectbox("Select a city", df["City"].tolist(), key="poll_city")
    row = df[df["City"]==selected_city].iloc[0]

    bar_col, radar_col = st.columns(2)
    with bar_col:
        st.subheader("📊 LEVELS vs SAFE LIMITS")
        poll_vals2 = [row[p] for p in POLLUTANTS]
        safe_vals2 = [SAFE_LIMITS[p] for p in POLLUTANTS]
        b_colors   = ["#00ff88" if row[p]<=SAFE_LIMITS[p] else "#ffaa00" if row[p]<=SAFE_LIMITS[p]*1.5 else "#ff2255" for p in POLLUTANTS]
        fig_poll   = go.Figure()
        fig_poll.add_trace(go.Bar(name="Measured", x=POLLUTANTS, y=poll_vals2,
            marker_color=b_colors, marker_line_width=0, hovertemplate="<b>%{x}</b>: %{y}<extra></extra>"))
        fig_poll.add_trace(go.Bar(name="Safe Limit", x=POLLUTANTS, y=safe_vals2,
            marker_color="rgba(0,229,255,0.12)", marker_line_color="#00e5ff", marker_line_width=1,
            hovertemplate="Safe limit %{x}: %{y}<extra></extra>"))
        apply_theme(fig_poll, height=330, barmode="group")
        st.plotly_chart(fig_poll, use_container_width=True)

    with radar_col:
        st.subheader("🕸️ POLLUTANT RADAR")
        norm_vals = [min(row[p]/SAFE_LIMITS[p], 3.0) for p in POLLUTANTS]
        cat_color = row["Color"]
        r_c,g_c,b_c = int(cat_color[1:3],16),int(cat_color[3:5],16),int(cat_color[5:7],16)
        fig_radar = go.Figure(go.Scatterpolar(
            r=norm_vals+[norm_vals[0]], theta=POLLUTANTS+[POLLUTANTS[0]],
            fill="toself", fillcolor=f"rgba({r_c},{g_c},{b_c},0.18)",
            line=dict(color=cat_color,width=2), marker=dict(size=7,color=cat_color)))
        fig_radar.add_trace(go.Scatterpolar(
            r=[1]*len(POLLUTANTS)+[1], theta=POLLUTANTS+[POLLUTANTS[0]],
            mode="lines", line=dict(color="#00e5ff",width=1,dash="dot"), showlegend=False))
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True,range=[0,3],tickfont=dict(color="#5a7a9a",size=9),
                                gridcolor="rgba(0,229,255,0.08)"),
                angularaxis=dict(tickfont=dict(color="#d8f0ff",size=11,family="Exo 2"),
                                 gridcolor="rgba(0,229,255,0.08)"),
                bgcolor="rgba(7,16,32,0.6)"),
            showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#d8f0ff"), height=340, margin=dict(l=40,r=40,t=40,b=40))
        st.plotly_chart(fig_radar, use_container_width=True)

    st.divider()
    st.subheader("🔍 ALL CITIES — SINGLE POLLUTANT COMPARISON")
    focus_poll = st.selectbox("Choose pollutant", POLLUTANTS, key="focus_poll")
    cmp_df     = df[["City",focus_poll]].sort_values(focus_poll, ascending=True)
    safe_val   = SAFE_LIMITS[focus_poll]
    bar_colors = ["#00ff88" if v<=safe_val else "#ffaa00" if v<=safe_val*1.5 else "#ff2255" for v in cmp_df[focus_poll]]
    fig_hbar   = go.Figure(go.Bar(
        x=cmp_df[focus_poll], y=cmp_df["City"], orientation="h",
        marker_color=bar_colors, marker_line_width=0,
        text=cmp_df[focus_poll].astype(str)+f" {UNITS[focus_poll]}",
        textposition="outside", hovertemplate="<b>%{y}</b>: %{x}<extra></extra>"))
    fig_hbar.add_vline(x=safe_val, line_dash="dash", line_color="#00e5ff",
        annotation_text=f"Safe limit ({safe_val} {UNITS[focus_poll]})",
        annotation_font_size=10, annotation_font_color="#00e5ff")
    apply_theme(fig_hbar, height=570, margin=dict(l=120,r=80,t=20,b=40))
    fig_hbar.update_xaxes(title_text=UNITS[focus_poll])
    fig_hbar.update_yaxes(showgrid=False)
    st.plotly_chart(fig_hbar, use_container_width=True)

# ══════════════════════════════════════════════════════════════════
# PAGE: RANKINGS
# ══════════════════════════════════════════════════════════════════
elif "Rankings" in view_mode:
    st.header("🏆 RANKINGS & STATISTICS")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🌿 TOP 10 CLEANEST")
        best10 = df.nsmallest(10,"AQI")[["City","State","AQI","Category","Emoji"]].reset_index(drop=True)
        for i, r in best10.iterrows():
            st.write(f"**{i+1}.** {r['Emoji']} **{r['City']}** · {r['State']} — AQI {r['AQI']} ({r['Category']})")
    with col2:
        st.subheader("☣️ TOP 10 MOST POLLUTED")
        worst10 = df.nlargest(10,"AQI")[["City","State","AQI","Category","Emoji"]].reset_index(drop=True)
        for i, r in worst10.iterrows():
            st.write(f"**{i+1}.** {r['Emoji']} **{r['City']}** · {r['State']} — AQI {r['AQI']} ({r['Category']})")

    st.divider()
    st.subheader("📊 AQI STATISTICS BY STATE")
    state_stats = df.groupby("State")["AQI"].agg(Avg="mean",Max="max",Min="min",Cities="count").round(1)\
                    .sort_values("Avg",ascending=False).reset_index()
    fig_state = px.bar(state_stats, x="State", y="Avg",
        color="Avg", color_continuous_scale=[[0,"#00ff88"],[0.4,"#ffaa00"],[0.7,"#ff2255"],[1,"#aa33ff"]],
        range_color=[0,500], hover_data={"Max":True,"Min":True,"Cities":True},
        text=state_stats["Avg"].astype(int), labels={"Avg":"Average AQI"})
    apply_theme(fig_state, height=370, coloraxis_showscale=False)
    fig_state.update_xaxes(tickangle=-35)
    fig_state.update_traces(textposition="outside", textfont=dict(color="#d8f0ff"))
    st.plotly_chart(fig_state, use_container_width=True)

    st.divider()
    corr_col, violin_col = st.columns(2)
    with corr_col:
        st.subheader("🔗 CORRELATION HEATMAP")
        corr = df[["AQI"]+POLLUTANTS].corr().round(2)
        fig_heat = go.Figure(go.Heatmap(
            z=corr.values, x=list(corr.columns), y=list(corr.index),
            colorscale=[[0,"#ff2255"],[0.5,"#0a1628"],[1,"#00ff88"]],
            zmin=-1, zmax=1, text=corr.values.round(2),
            texttemplate="%{text}", textfont=dict(size=11,family="Share Tech Mono"),
            hovertemplate="%{x} × %{y}: %{z}<extra></extra>"))
        apply_theme(fig_heat, height=330, margin=dict(l=80,r=20,t=20,b=60))
        st.plotly_chart(fig_heat, use_container_width=True)
    with violin_col:
        st.subheader("🎻 AQI DISTRIBUTION")
        fig_v = go.Figure()
        for lo, hi, label_v, color_v, emoji_v, _ in AQI_SCALE:
            subset = df[df["Category"]==label_v]["AQI"]
            if len(subset) > 0:
                r_v,g_v,b_v = int(color_v[1:3],16),int(color_v[3:5],16),int(color_v[5:7],16)
                fig_v.add_trace(go.Violin(y=subset, name=f"{emoji_v} {label_v}",
                    fillcolor=f"rgba({r_v},{g_v},{b_v},0.25)", line_color=color_v,
                    box_visible=True, meanline_visible=True, points="all"))
        apply_theme(fig_v, height=330, margin=dict(l=60,r=20,t=20,b=60), showlegend=False)
        fig_v.update_yaxes(title_text="AQI")
        st.plotly_chart(fig_v, use_container_width=True)

# ══════════════════════════════════════════════════════════════════
# PAGE: ALERTS
# ══════════════════════════════════════════════════════════════════
elif "Alerts" in view_mode:
    st.header("🔔 ALERTS & NOTIFICATIONS")
    al_col1, al_col2 = st.columns([2, 1])
    with al_col1:
        st.subheader(f"🚨 ACTIVE ALERTS ({len(active_alerts)} cities above AQI {alert_threshold_user})")
        if not active_alerts:
            st.success("✅ No alerts active. All cities within your threshold.")
        for alert in active_alerts[:15]:
            icon = "🚨" if alert["level"] == "CRITICAL" else "⚠️"
            if alert["level"] == "CRITICAL":
                st.error(f"{icon} **{alert['city']}** — AQI {alert['aqi']} ({alert['cat']})  |  {alert['time']}")
            else:
                st.warning(f"{icon} **{alert['city']}** — AQI {alert['aqi']} ({alert['cat']})  |  {alert['time']}")
    with al_col2:
        st.subheader("⚙️ ALERT SETTINGS")
        new_threshold = st.slider("Alert Threshold AQI", 50, 400, alert_threshold_user, step=25, key="new_alert_threshold")
        if new_threshold != alert_threshold_user:
            st.session_state.users_db[st.session_state.current_user]["alert_threshold"] = new_threshold
        alerts_on = st.toggle("Enable Alerts", value=user_info.get("alerts_enabled",True), key="alerts_enabled_toggle")
        if alerts_on != user_info.get("alerts_enabled"):
            st.session_state.users_db[st.session_state.current_user]["alerts_enabled"] = alerts_on
        st.checkbox("Email Notifications", value=True,  key="notif_email")
        st.checkbox("Browser Push",        value=False, key="notif_browser")
        st.info(f"📧 Alerts to **{st.session_state.current_user}** when AQI > {new_threshold}")
        critical_count = sum(1 for a in active_alerts if a["level"] == "CRITICAL")
        warning_count  = sum(1 for a in active_alerts if a["level"] == "WARNING")
        mc1, mc2 = st.columns(2)
        mc1.metric("🚨 Critical", critical_count)
        mc2.metric("⚠️ Warning",  warning_count)

    st.divider()
    fig_hist = go.Figure(go.Histogram(x=df["AQI"], nbinsx=25,
        marker_color="#00e5ff", marker_line_color="rgba(0,229,255,0.5)",
        marker_line_width=1, opacity=0.7, hovertemplate="AQI Range: %{x}<br>Cities: %{y}<extra></extra>"))
    fig_hist.add_vline(x=new_threshold, line_dash="dash", line_color="#ff2255",
        annotation_text=f"Alert Threshold ({new_threshold})",
        annotation_font_color="#ff2255", annotation_font_size=11)
    apply_theme(fig_hist, height=260)
    fig_hist.update_xaxes(title_text="AQI Value")
    fig_hist.update_yaxes(title_text="Number of Cities")
    st.plotly_chart(fig_hist, use_container_width=True)

# ══════════════════════════════════════════════════════════════════
# PAGE: WEATHER
# ══════════════════════════════════════════════════════════════════
elif "Weather" in view_mode:
    st.header("🌡️ WEATHER & AQI FORECAST")
    wc1, wc2 = st.columns(2)
    fcity = wc1.selectbox("Select City", [c["name"] for c in CITIES], key="wcity")
    fdays = wc2.slider("Forecast Days", 3, 14, 7, key="fdays")
    city_aqi = int(df[df["City"]==fcity]["AQI"].values[0])
    dates    = [datetime.date.today() + datetime.timedelta(days=i) for i in range(fdays)]
    aqi_fc   = [max(10,min(500, city_aqi+random.randint(-80,80))) for _ in range(fdays)]
    temp_fc  = [random.randint(28,42) for _ in range(fdays)]
    humid_fc = [random.randint(30,80) for _ in range(fdays)]
    wind_fc  = [random.uniform(3,25)  for _ in range(fdays)]
    d_labels = [d.strftime("%b %d") for d in dates]
    fig_fc2  = make_subplots(rows=3, cols=1, shared_xaxes=True,
        subplot_titles=["AQI Forecast","Temperature (°C)","Humidity (%)"], vertical_spacing=0.08)
    fc_colors = [get_aqi_info(v)[1] for v in aqi_fc]
    fig_fc2.add_trace(go.Bar(x=d_labels, y=aqi_fc, marker_color=fc_colors, name="AQI",
        hovertemplate="%{x}: AQI %{y}<extra></extra>"), row=1, col=1)
    fig_fc2.add_trace(go.Scatter(x=d_labels, y=temp_fc, mode="lines+markers",
        line=dict(color="#ff6600",width=2.5), marker=dict(size=7,color="#ff6600"), name="Temp °C"), row=2, col=1)
    fig_fc2.add_trace(go.Bar(x=d_labels, y=humid_fc,
        marker_color=[f"rgba(0,112,255,{0.35+h/200})" for h in humid_fc], name="Humidity %"), row=3, col=1)
    apply_theme(fig_fc2, height=580, showlegend=False,
        title=dict(text=f"Forecast · {fcity}", font=dict(family="Orbitron",color="#00e5ff",size=13)))
    for i in range(1, 4):
        fig_fc2.update_xaxes(gridcolor="rgba(0,229,255,0.06)",linecolor="rgba(0,229,255,0.12)", row=i, col=1)
        fig_fc2.update_yaxes(gridcolor="rgba(0,229,255,0.06)",linecolor="rgba(0,229,255,0.12)", row=i, col=1)
    st.plotly_chart(fig_fc2, use_container_width=True)
    st.divider()
    forecast_df = pd.DataFrame({
        "Date": d_labels, "AQI": aqi_fc,
        "Category": [get_aqi_info(v)[0] for v in aqi_fc],
        "Temp (°C)": temp_fc, "Humidity (%)": humid_fc,
        "Wind (km/h)": [round(w,1) for w in wind_fc]
    })
    st.dataframe(forecast_df.style.background_gradient(subset=["AQI"], cmap="RdYlGn_r"),
        use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════
# PAGE: IMAGE PREDICTOR
# ══════════════════════════════════════════════════════════════════
elif "Image" in view_mode:
    try:
        from PIL import Image as PILImage
        pil_available = True
    except ImportError:
        pil_available = False

    st.header("📸 IMAGE-BASED AIR QUALITY PREDICTOR")
    up_col, result_col = st.columns([1, 1])
    with up_col:
        uploaded_file = st.file_uploader("Upload sky/outdoor image (JPG / PNG)", type=["jpg","jpeg","png"])
        if uploaded_file and pil_available:
            img = PILImage.open(uploaded_file)
            st.image(img, caption="📷 Uploaded Image", use_container_width=True)
        elif uploaded_file and not pil_available:
            st.image(uploaded_file, caption="📷 Uploaded Image", use_container_width=True)
    with result_col:
        if uploaded_file:
            if st.button("🔍  ANALYZE IMAGE", use_container_width=True, key="analyze_img"):
                with st.spinner("🛰️ Analyzing visual haze and particulate density…"):
                    time.sleep(1.5)
                pollution = random.randint(1, 100)
                aqi_equiv = int(pollution * 5)
                p_label, p_color, p_emoji, p_advice = get_aqi_info(aqi_equiv)
                st.metric("🌫️ Haze Index", f"{pollution}%", f"Est. AQI {aqi_equiv}")
                st.info(f"**{p_emoji} {p_label}**\n\n{p_advice}")
                st.divider()
                st.subheader("🔬 VISUAL BREAKDOWN")
                metrics = {
                    "Haze Index":          random.randint(20, 90),
                    "Visibility Score":    random.randint(10, 95),
                    "Particulate Density": random.randint(15, 85),
                    "Sky Clarity":         random.randint(5,  80),
                }
                for k, v in metrics.items():
                    st.write(f"**{k}** — {v}%")
                    st.progress(v / 100)
        else:
            st.info("📷 Upload a sky or outdoor image to begin visual haze analysis.")

# ══════════════════════════════════════════════════════════════════
# PAGE: DATA EXPORT
# ══════════════════════════════════════════════════════════════════
elif "Export" in view_mode:
    st.header("📋 DATA EXPORT & REPORT")
    exp_col1, exp_col2 = st.columns(2)
    with exp_col1:
        st.subheader("📥 EXPORT OPTIONS")
        st.download_button("⬇️  Full Dataset (CSV)",
            df[["City","State","AQI","Category"]+POLLUTANTS].to_csv(index=False),
            file_name=f"india_aqi_{datetime.date.today()}.csv", mime="text/csv", use_container_width=True)
        st.download_button("⬇️  Top 10 Polluted (CSV)",
            df.nlargest(10,"AQI")[["City","State","AQI","Category"]+POLLUTANTS].to_csv(index=False),
            file_name=f"top10_polluted_{datetime.date.today()}.csv", mime="text/csv", use_container_width=True)
        st.download_button("⬇️  Safe Cities (CSV)",
            df[df["AQI"]<=100][["City","State","AQI","Category"]+POLLUTANTS].to_csv(index=False),
            file_name=f"safe_cities_{datetime.date.today()}.csv", mime="text/csv", use_container_width=True)
        json_data = df[["City","State","AQI","Category"]+POLLUTANTS].to_json(orient="records", indent=2)
        st.download_button("⬇️  Full Dataset (JSON)", json_data,
            file_name=f"india_aqi_{datetime.date.today()}.json", mime="application/json", use_container_width=True)
    with exp_col2:
        st.subheader("📊 DATA SUMMARY")
        summary = df[["AQI"]+POLLUTANTS].describe().round(2)
        st.dataframe(summary.style.background_gradient(cmap="Blues"), use_container_width=True)

    st.divider()
    sc1, sc2 = st.columns(2)
    search_city = sc1.text_input("🔎 Search city…", placeholder="Type a city name", key="search_city_export")
    cat_filter  = sc2.multiselect("Filter by Category",
        ["Good","Satisfactory","Moderate","Poor","Very Poor","Severe"], key="cat_filter_export")
    display_df  = df.copy()
    if search_city: display_df = display_df[display_df["City"].str.contains(search_city, case=False)]
    if cat_filter:  display_df = display_df[display_df["Category"].isin(cat_filter)]
    st.dataframe(
        display_df[["City","State","AQI","Category"]+POLLUTANTS]
        .sort_values("AQI", ascending=False).reset_index(drop=True)
        .style.background_gradient(subset=["AQI"], cmap="RdYlGn_r"),
        use_container_width=True, height=420)

# ══════════════════════════════════════════════════════════════════
# PAGE: MY ACCOUNT
# ══════════════════════════════════════════════════════════════════
elif "Account" in view_mode:
    st.header("👤 MY ACCOUNT")
    u = st.session_state.users_db[st.session_state.current_user]
    acc_col1, acc_col2 = st.columns([1, 1])
    with acc_col1:
        initials_acc = "".join([w[0].upper() for w in u["name"].split()[:2]])
        st.subheader(f"{initials_acc} — {u['name']}")
        st.caption(st.session_state.current_user)
        st.caption(f"⬡ {u['role']}")
        st.caption(f"Member since: {u['joined']}  |  Last login: {u.get('last_login') or 'This session'}")
        st.divider()
        alerts_t = st.toggle("Enable AQI Alerts", value=u.get("alerts_enabled",True), key="alerts_toggle")
        if alerts_t != u.get("alerts_enabled"):
            st.session_state.users_db[st.session_state.current_user]["alerts_enabled"] = alerts_t
        alert_threshold = st.slider("Alert when AQI exceeds", 100, 400,
                                    u.get("alert_threshold",200), step=50, key="alert_threshold_acc")
        if alert_threshold != u.get("alert_threshold"):
            st.session_state.users_db[st.session_state.current_user]["alert_threshold"] = alert_threshold
        st.info(f"📧 Alerts to **{st.session_state.current_user}** when AQI > {alert_threshold}")

    with acc_col2:
        st.subheader("🔑 CHANGE PASSWORD")
        with st.form("change_pw_form"):
            old_pw  = st.text_input("Current Password",     type="password", key="chg_old")
            new_pw  = st.text_input("New Password",          type="password", key="chg_new")
            new_pw2 = st.text_input("Confirm New Password",  type="password", key="chg_new2")
            pw_submitted = st.form_submit_button("🔄  UPDATE PASSWORD", use_container_width=True)
        if pw_submitted:
            if not old_pw or not new_pw or not new_pw2:
                st.error("⚠️ Fill all password fields.")
            elif st.session_state.users_db[st.session_state.current_user]["password_hash"] != _hash(old_pw):
                st.error("❌ Current password is incorrect.")
            elif not is_strong_password(new_pw):
                st.error("❌ Password too weak (uppercase + number + symbol required).")
            elif new_pw != new_pw2:
                st.error("❌ Passwords do not match.")
            else:
                st.session_state.users_db[st.session_state.current_user]["password_hash"] = _hash(new_pw)
                _save_users_db(st.session_state.users_db)
                st.success("✅ Password updated successfully!")

        st.divider()
        st.subheader("📊 SESSION STATS")
        total_users = len(st.session_state.users_db)
        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("Registered Users",  total_users)
        sc2.metric("Cities Monitored",  len(CITIES))
        sc3.metric("National Avg AQI",  avg_aqi)
        sc4.metric("High Risk Cities",  dangerous)

    # ATTENDANCE LOG
    st.divider()
    st.header("📋 ATTENDANCE LOG")
    att_log = _load_attendance()
    if att_log:
        att_df = pd.DataFrame(att_log)
        att_df = att_df.sort_values("timestamp", ascending=False).reset_index(drop=True)
        att_df.columns = [c.upper() for c in att_df.columns]

        ac1, ac2, ac3, ac4 = st.columns(4)
        total_logins = int((att_df["EVENT"] == "login").sum())
        total_regs   = int((att_df["EVENT"] == "register").sum())
        unique_users = att_df["EMAIL"].nunique()
        today_logins = int((att_df[att_df["EVENT"]=="login"]["DATE"] == datetime.date.today().isoformat()).sum())
        ac1.metric("Total Logins",   total_logins)
        ac2.metric("Registrations",  total_regs)
        ac3.metric("Unique Users",   unique_users)
        ac4.metric("Logins Today",   today_logins)

        st.dataframe(att_df[["TIMESTAMP","NAME","EMAIL","EVENT","DATE"]],
                     use_container_width=True, height=320)
        st.download_button("⬇️  Download Attendance CSV", att_df.to_csv(index=False),
            file_name=f"attendance_{datetime.date.today()}.csv", mime="text/csv", use_container_width=True)
    else:
        st.info("No attendance records yet. Records are created on each login and registration.")

# ══════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════
st.divider()
fc1, fc2, fc3 = st.columns(3)
fc1.caption("🛰️ INDIA AQI COMMAND CENTER v4.0")
fc2.caption(f"👤 Logged in as **{user_info['name']}**")
fc3.caption("Built with Streamlit · Plotly · Python")
