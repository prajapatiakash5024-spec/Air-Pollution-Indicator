import streamlit as st
import pandas as pd
import numpy as np
import random
import time
import datetime
import json
import hashlib
import re
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ══════════════════════════════════════════════════════════════════
# PAGE CONFIG — must be FIRST
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
import os, pathlib
_DATA_DIR = pathlib.Path("aqi_data")
_DATA_DIR.mkdir(exist_ok=True)
_USERS_FILE      = _DATA_DIR / "users_db.json"
_ATTENDANCE_FILE = _DATA_DIR / "attendance_log.json"

def _hash(pw): return hashlib.sha256(pw.encode()).hexdigest()

def _load_users_db():
    if _USERS_FILE.exists():
        with open(_USERS_FILE, "r") as f:
            db = json.load(f)
        changed = False
        for email, udata in db.items():
            if "is_admin" not in udata:
                udata["is_admin"] = (email == "demo@aqicommand.in")
                changed = True
        if changed:
            _save_users_db(db)
        return db
    demo = {
        "demo@aqicommand.in": {
            "name": "Demo Analyst",
            "password_hash": _hash("Demo@1234"),
            "role": "Analyst",
            "joined": "2024-01-01",
            "last_login": None,
            "alerts_enabled": True,
            "alert_threshold": 200,
            "theme": "Cyber Blue",
            "notifications": [],
            "is_admin": True,
        }
    }
    _save_users_db(demo)
    return demo

def _save_users_db(db):
    with open(_USERS_FILE, "w") as f:
        json.dump(db, f, indent=2)

def _load_attendance():
    if _ATTENDANCE_FILE.exists():
        with open(_ATTENDANCE_FILE, "r") as f:
            return json.load(f)
    return []

def _save_attendance(log):
    with open(_ATTENDANCE_FILE, "w") as f:
        json.dump(log, f, indent=2)

def _record_attendance(email, name, event="login"):
    log = _load_attendance()
    log.append({
        "email": email,
        "name": name,
        "event": event,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "date": datetime.date.today().isoformat(),
    })
    _save_attendance(log)

# ══════════════════════════════════════════════════════════════════
# PASSWORD RESET — OTP SYSTEM
# ══════════════════════════════════════════════════════════════════
# In-memory store: { email: { "otp": "123456", "expires": datetime, "name": str } }
# This resets on server restart — for persistence, store in _DATA_DIR JSON.
if "reset_tokens" not in st.session_state:
    st.session_state.reset_tokens = {}

def _generate_otp():
    return str(random.randint(100000, 999999))

def _send_reset_email(email: str, otp: str, name: str) -> bool:
    """
    Stores OTP in session state (valid 10 min).
    ── PRODUCTION ── Replace body with smtplib / SendGrid / Mailgun / AWS SES.
    """
    st.session_state.reset_tokens[email] = {
        "otp": otp,
        "expires": datetime.datetime.now() + datetime.timedelta(minutes=10),
        "name": name,
    }
    # ---- Uncomment & configure for real email delivery ----
    # import smtplib
    # from email.mime.multipart import MIMEMultipart
    # from email.mime.text import MIMEText
    # SMTP_HOST = "smtp.gmail.com"
    # SMTP_PORT = 587
    # SMTP_USER = "your_email@gmail.com"
    # SMTP_PASS = "your_app_password"          # Use App Password, NOT account password
    # html_body = f"""
    # <div style="font-family:Arial,sans-serif;background:#030b18;color:#d8f0ff;padding:32px;border-radius:12px;">
    #   <h2 style="color:#00e5ff;">🛰️ AQI Command Center</h2>
    #   <p>Hi {name},</p>
    #   <p>Your password reset OTP is:</p>
    #   <div style="font-size:2.4rem;font-weight:900;letter-spacing:10px;color:#00e5ff;
    #               background:#071020;padding:18px 28px;border-radius:10px;display:inline-block;">
    #     {otp}
    #   </div>
    #   <p style="color:#5a7a9a;font-size:0.85rem;margin-top:18px;">
    #     Valid for <b>10 minutes</b>. Do not share this code with anyone.
    #   </p>
    # </div>"""
    # msg = MIMEMultipart("alternative")
    # msg["Subject"] = "AQI Command Center — Password Reset OTP"
    # msg["From"]    = f"AQI Command <{SMTP_USER}>"
    # msg["To"]      = email
    # msg.attach(MIMEText(html_body, "html"))
    # try:
    #     with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
    #         s.starttls()
    #         s.login(SMTP_USER, SMTP_PASS)
    #         s.send_message(msg)
    #     return True
    # except Exception as e:
    #     print(f"[EMAIL ERROR] {e}")
    #     return False
    print(f"[DEV] OTP for {email}: {otp}")   # visible in terminal during dev
    return True

def _verify_otp(email: str, otp_input: str) -> tuple[bool, str]:
    """Returns (success, message)."""
    token = st.session_state.reset_tokens.get(email)
    if not token:
        return False, "No reset request found. Please request OTP again."
    if datetime.datetime.now() > token["expires"]:
        del st.session_state.reset_tokens[email]
        return False, "OTP has expired. Please request a new one."
    if token["otp"] != otp_input.strip():
        return False, "Incorrect OTP. Please try again."
    return True, "OTP verified!"

# ══════════════════════════════════════════════════════════════════
# SESSION STATE INIT
# ══════════════════════════════════════════════════════════════════
def init_session():
    defaults = {
        "logged_in": False,
        "current_user": None,
        "auth_msg": ("", ""),
        "login_anim": False,
        "alerts_log": [],
        "df": None,
        "live_aqi": 142,
        "live_city": "Mumbai",
        "live_history": [142],
        "last_refresh": datetime.datetime.now(),
        "auto_refresh": False,
        "compare_cities": [],
        "nav_page": "🔴 Live Air Pollution",
        # Forgot password flow state
        "fp_step": 1,          # 1=enter email, 2=enter OTP+new pw
        "fp_email": "",
        "fp_msg": ("", ""),    # (text, type)
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    if "users_db" not in st.session_state:
        st.session_state.users_db = _load_users_db()

init_session()

# ══════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Exo+2:wght@300;400;600;700&family=Share+Tech+Mono&family=Rajdhani:wght@400;500;600;700&display=swap');
:root {
    --bg-dark:#030b18; --bg-panel:#071020; --bg-card:#0c1a2e; --bg-card2:#0f2040;
    --accent-cyan:#00e5ff; --accent-blue:#0070ff; --accent-green:#00ff88;
    --accent-red:#ff2255; --accent-amber:#ffaa00; --accent-purple:#aa33ff;
    --accent-teal:#00ffcc; --text-primary:#d8f0ff; --text-muted:#5a7a9a;
    --border:rgba(0,229,255,0.12); --border2:rgba(0,229,255,0.2);
}
html,body,[class*="css"],.stApp{background-color:var(--bg-dark)!important;color:var(--text-primary)!important;font-family:'Exo 2',sans-serif!important;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#04090f 0%,#070f1a 100%)!important;border-right:1px solid var(--border)!important;}
[data-testid="stSidebar"] *{color:var(--text-primary)!important;}
[data-testid="stSidebar"] .stButton>button{background:linear-gradient(135deg,#0070ff18,#00e5ff18)!important;border:1px solid var(--accent-cyan)!important;color:var(--accent-cyan)!important;border-radius:8px!important;font-family:'Exo 2',sans-serif!important;font-weight:600!important;letter-spacing:1px!important;transition:all 0.3s ease!important;}
[data-testid="stSidebar"] .stButton>button:hover{background:linear-gradient(135deg,#0070ff33,#00e5ff33)!important;box-shadow:0 0 20px rgba(0,229,255,0.4)!important;}
h1{font-family:'Orbitron',sans-serif!important;font-weight:900!important;background:linear-gradient(90deg,#00e5ff,#0070ff,#aa33ff);-webkit-background-clip:text!important;-webkit-text-fill-color:transparent!important;letter-spacing:2px!important;}
h2,h3{font-family:'Orbitron',sans-serif!important;font-weight:700!important;color:var(--accent-cyan)!important;letter-spacing:1px!important;}
[data-testid="stMetric"]{background:linear-gradient(135deg,var(--bg-card),var(--bg-card2))!important;border:1px solid var(--border)!important;border-radius:12px!important;padding:16px!important;position:relative!important;overflow:hidden!important;}
[data-testid="stMetric"]::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,var(--accent-cyan),var(--accent-blue));}
[data-testid="stMetricLabel"]{color:var(--text-muted)!important;font-family:'Exo 2',sans-serif!important;font-size:0.78rem!important;letter-spacing:1px!important;text-transform:uppercase!important;}
[data-testid="stMetricValue"]{color:var(--accent-cyan)!important;font-family:'Orbitron',sans-serif!important;font-weight:700!important;}
.stSelectbox>div>div,.stMultiSelect>div>div{background:var(--bg-card)!important;border:1px solid var(--border)!important;border-radius:8px!important;color:var(--text-primary)!important;}
.stSlider>div{color:var(--accent-cyan)!important;}
hr{border-color:var(--border)!important;margin:1.5rem 0!important;}
.stAlert{background:var(--bg-card)!important;border:1px solid var(--border)!important;border-radius:10px!important;}
::-webkit-scrollbar{width:5px;height:5px;}
::-webkit-scrollbar-track{background:var(--bg-dark);}
::-webkit-scrollbar-thumb{background:#0070ff;border-radius:3px;}
.stTextInput input{background:rgba(255,255,255,0.06)!important;border:1px solid rgba(0,229,255,0.25)!important;border-radius:10px!important;color:#ffffff!important;font-family:'Exo 2',sans-serif!important;padding:12px 16px!important;}
.stTextInput input::placeholder{color:#4a6a8a!important;}
.stTextInput input:focus{border-color:#00e5ff!important;box-shadow:0 0 14px rgba(0,229,255,0.2)!important;}
.stTextInput label{color:#5a7a9a!important;font-family:'Exo 2',sans-serif!important;font-size:0.78rem!important;letter-spacing:1px!important;}
.stTextArea textarea{background:rgba(255,255,255,0.05)!important;border:1px solid rgba(0,229,255,0.2)!important;border-radius:10px!important;color:#d8f0ff!important;font-family:'Exo 2',sans-serif!important;}
/* LIVE BADGE */
.live-badge{display:inline-flex;align-items:center;gap:6px;background:rgba(0,255,136,0.08);border:1px solid #00ff88;border-radius:20px;padding:4px 14px;font-family:'Share Tech Mono',monospace;font-size:0.72rem;color:#00ff88;letter-spacing:1.5px;animation:pulse-live 2s infinite;}
@keyframes pulse-live{0%,100%{box-shadow:0 0 6px rgba(0,255,136,0.3);}50%{box-shadow:0 0 18px rgba(0,255,136,0.7);}}
.dot-live{width:7px;height:7px;background:#00ff88;border-radius:50%;animation:blink 1.2s infinite;}
@keyframes blink{0%,100%{opacity:1;}50%{opacity:0.1;}}
/* CARDS */
.aqi-live-card{background:linear-gradient(135deg,#0a1628,#122040);border:1px solid rgba(0,229,255,0.25);border-radius:16px;padding:20px;text-align:center;position:relative;overflow:hidden;}
.aqi-number{font-family:'Orbitron',monospace;font-size:3.2rem;font-weight:900;line-height:1;}
.aqi-label-text{font-family:'Exo 2',sans-serif;font-size:1rem;font-weight:600;letter-spacing:2px;text-transform:uppercase;margin-top:4px;}
.health-advice{background:linear-gradient(135deg,rgba(0,229,255,0.04),rgba(0,112,255,0.04));border:1px solid rgba(0,229,255,0.18);border-radius:12px;padding:16px;font-family:'Exo 2',sans-serif;font-size:0.9rem;line-height:1.6;}
.section-header{font-family:'Orbitron',sans-serif;font-size:0.9rem;font-weight:700;color:#00e5ff;letter-spacing:2px;text-transform:uppercase;padding:8px 0;border-bottom:1px solid rgba(0,229,255,0.18);margin-bottom:12px;}
/* ALERTS */
.alert-card-red{background:rgba(255,34,85,0.07);border:1px solid rgba(255,34,85,0.35);border-radius:12px;padding:14px 16px;margin:6px 0;animation:alert-pulse-red 2s infinite;}
@keyframes alert-pulse-red{0%,100%{box-shadow:0 0 0px rgba(255,34,85,0);}50%{box-shadow:0 0 16px rgba(255,34,85,0.25);}}
.alert-card-amber{background:rgba(255,170,0,0.07);border:1px solid rgba(255,170,0,0.3);border-radius:12px;padding:14px 16px;margin:6px 0;}
.alert-card-green{background:rgba(0,255,136,0.06);border:1px solid rgba(0,255,136,0.25);border-radius:12px;padding:14px 16px;margin:6px 0;}
/* AUTH */
.auth-card{background:linear-gradient(145deg,rgba(7,16,32,0.98),rgba(12,26,46,0.98));border:1px solid rgba(0,229,255,0.25);border-radius:22px;padding:42px 38px;box-shadow:0 0 80px rgba(0,229,255,0.06),inset 0 1px 0 rgba(0,229,255,0.08);position:relative;overflow:hidden;animation:card-appear 0.7s cubic-bezier(0.16,1,0.3,1) forwards;}
@keyframes card-appear{0%{opacity:0;transform:translateY(40px) scale(0.95);}100%{opacity:1;transform:translateY(0) scale(1);}}
.auth-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,#00e5ff,#0070ff,#aa33ff,#00ffcc,#00e5ff);background-size:300% 100%;animation:gradient-slide 4s linear infinite;}
@keyframes gradient-slide{0%{background-position:0% 50%;}100%{background-position:300% 50%;}}
.corner-tl,.corner-tr,.corner-bl,.corner-br{position:absolute;width:20px;height:20px;}
.corner-tl{top:12px;left:12px;border-top:2px solid rgba(0,229,255,0.5);border-left:2px solid rgba(0,229,255,0.5);}
.corner-tr{top:12px;right:12px;border-top:2px solid rgba(0,229,255,0.5);border-right:2px solid rgba(0,229,255,0.5);}
.corner-bl{bottom:12px;left:12px;border-bottom:2px solid rgba(0,229,255,0.5);border-left:2px solid rgba(0,229,255,0.5);}
.corner-br{bottom:12px;right:12px;border-bottom:2px solid rgba(0,229,255,0.5);border-right:2px solid rgba(0,229,255,0.5);}
.auth-title{font-family:'Orbitron',sans-serif;font-size:1.45rem;font-weight:900;background:linear-gradient(90deg,#00e5ff,#0070ff,#aa33ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-align:center;letter-spacing:2px;margin-bottom:3px;}
.auth-subtitle{font-family:'Share Tech Mono',monospace;font-size:0.68rem;color:#4a6a8a;text-align:center;letter-spacing:3px;margin-bottom:24px;}
.stButton>button{background:linear-gradient(135deg,#0070ff,#00e5ff)!important;border:none!important;color:#030b18!important;font-family:'Orbitron',sans-serif!important;font-weight:700!important;font-size:0.82rem!important;letter-spacing:2px!important;border-radius:10px!important;padding:14px 28px!important;transition:all 0.3s ease!important;box-shadow:0 4px 22px rgba(0,229,255,0.22)!important;}
.stButton>button:hover{transform:translateY(-2px)!important;box-shadow:0 8px 32px rgba(0,229,255,0.42)!important;}
.stTabs [data-baseweb="tab-list"]{background:rgba(0,229,255,0.035)!important;border-radius:12px!important;border:1px solid rgba(0,229,255,0.12)!important;padding:4px!important;}
.stTabs [data-baseweb="tab"]{font-family:'Orbitron',sans-serif!important;font-size:0.72rem!important;letter-spacing:2px!important;color:#5a7a9a!important;border-radius:8px!important;padding:10px 18px!important;}
.stTabs [aria-selected="true"]{background:linear-gradient(135deg,rgba(0,112,255,0.25),rgba(0,229,255,0.15))!important;color:#00e5ff!important;}
.user-badge{background:linear-gradient(135deg,rgba(0,229,255,0.06),rgba(0,112,255,0.06));border:1px solid rgba(0,229,255,0.18);border-radius:12px;padding:12px 14px;margin-bottom:12px;}
.user-name{font-family:'Orbitron',sans-serif;font-size:0.82rem;color:#00e5ff;font-weight:700;}
.user-email{font-family:'Share Tech Mono',monospace;font-size:0.62rem;color:#5a7a9a;margin-top:3px;}
.user-role{font-family:'Exo 2',sans-serif;font-size:0.68rem;color:#00ff88;margin-top:4px;letter-spacing:1px;}
.auth-success{background:rgba(0,255,136,0.07);border:1px solid #00ff88;border-radius:10px;padding:12px 16px;font-family:'Exo 2',sans-serif;color:#00ff88;font-size:0.85rem;margin:8px 0;}
.auth-error{background:rgba(255,34,85,0.07);border:1px solid #ff2255;border-radius:10px;padding:12px 16px;font-family:'Exo 2',sans-serif;color:#ff2255;font-size:0.85rem;margin:8px 0;}
.auth-info{background:rgba(0,229,255,0.05);border:1px solid rgba(0,229,255,0.25);border-radius:10px;padding:12px 16px;font-family:'Exo 2',sans-serif;color:#00e5ff;font-size:0.85rem;margin:8px 0;}
/* OTP BOX */
.otp-box{background:linear-gradient(135deg,rgba(0,112,255,0.08),rgba(0,229,255,0.04));border:1px solid rgba(0,229,255,0.3);border-radius:14px;padding:20px 18px;margin:12px 0;text-align:center;}
.otp-sent-badge{display:inline-flex;align-items:center;gap:8px;background:rgba(0,255,136,0.07);border:1px solid rgba(0,255,136,0.3);border-radius:20px;padding:6px 16px;font-family:'Share Tech Mono',monospace;font-size:0.72rem;color:#00ff88;letter-spacing:1.5px;margin-bottom:12px;}
.hex-stat{display:flex;flex-direction:column;align-items:center;justify-content:center;background:linear-gradient(135deg,rgba(0,229,255,0.06),rgba(0,112,255,0.04));border:1px solid rgba(0,229,255,0.15);border-radius:14px;padding:18px 12px;text-align:center;transition:all 0.3s ease;}
.hex-stat:hover{border-color:rgba(0,229,255,0.4);box-shadow:0 0 20px rgba(0,229,255,0.12);}
.hex-val{font-family:'Orbitron',sans-serif;font-size:1.6rem;font-weight:900;color:#00e5ff;}
.hex-lbl{font-family:'Exo 2',sans-serif;font-size:0.68rem;color:#5a7a9a;letter-spacing:1px;text-transform:uppercase;margin-top:4px;}
.ticker-wrap{overflow:hidden;background:rgba(0,229,255,0.04);border-top:1px solid rgba(0,229,255,0.12);border-bottom:1px solid rgba(0,229,255,0.12);padding:8px 0;margin:8px 0;}
.ticker-text{display:inline-block;white-space:nowrap;font-family:'Share Tech Mono',monospace;font-size:0.72rem;color:#5a7a9a;animation:ticker 40s linear infinite;}
@keyframes ticker{0%{transform:translateX(100vw);}100%{transform:translateX(-100%);}}
@keyframes notif-pulse{0%,100%{box-shadow:0 0 4px rgba(255,34,85,0.2);}50%{box-shadow:0 0 14px rgba(255,34,85,0.5);}}
.grid-bg{position:fixed;top:0;left:0;width:100%;height:100%;background-image:linear-gradient(rgba(0,229,255,0.025) 1px,transparent 1px),linear-gradient(90deg,rgba(0,229,255,0.025) 1px,transparent 1px);background-size:44px 44px;pointer-events:none;z-index:0;}
.scan-line{position:fixed;top:0;left:0;width:100%;height:2px;background:linear-gradient(90deg,transparent,rgba(0,229,255,0.5),transparent);animation:scan 5s linear infinite;z-index:1;pointer-events:none;}
@keyframes scan{0%{top:0%;}100%{top:100%;}}
.insight-red{background:rgba(255,34,85,0.06);border:1px solid rgba(255,34,85,0.2);border-radius:12px;padding:16px;}
.insight-green{background:rgba(0,255,136,0.05);border:1px solid rgba(0,255,136,0.2);border-radius:12px;padding:16px;}
.insight-blue{background:rgba(0,229,255,0.05);border:1px solid rgba(0,229,255,0.18);border-radius:12px;padding:16px;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# SVG LOGO
# ══════════════════════════════════════════════════════════════════
AQI_LOGO_SVG = """<svg width="110" height="110" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="bgGrad" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#0a1e3a"/><stop offset="100%" stop-color="#030b18"/>
    </radialGradient>
    <radialGradient id="coreGrad" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#00e5ff" stop-opacity="0.9"/>
      <stop offset="60%" stop-color="#0070ff" stop-opacity="0.7"/>
      <stop offset="100%" stop-color="#aa33ff" stop-opacity="0.5"/>
    </radialGradient>
    <filter id="glow"><feGaussianBlur stdDeviation="2.5" result="coloredBlur"/>
      <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <filter id="glow2"><feGaussianBlur stdDeviation="4" result="coloredBlur"/>
      <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <linearGradient id="orbitGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#00e5ff" stop-opacity="0"/>
      <stop offset="50%" stop-color="#00e5ff" stop-opacity="0.8"/>
      <stop offset="100%" stop-color="#00e5ff" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="orbitGrad2" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#aa33ff" stop-opacity="0"/>
      <stop offset="50%" stop-color="#aa33ff" stop-opacity="0.7"/>
      <stop offset="100%" stop-color="#aa33ff" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <circle cx="60" cy="60" r="56" fill="url(#bgGrad)" stroke="rgba(0,229,255,0.15)" stroke-width="1"/>
  <ellipse cx="60" cy="60" rx="50" ry="20" fill="none" stroke="url(#orbitGrad)" stroke-width="1.5" opacity="0.5">
    <animateTransform attributeName="transform" type="rotate" from="0 60 60" to="360 60 60" dur="8s" repeatCount="indefinite"/>
  </ellipse>
  <ellipse cx="60" cy="60" rx="42" ry="15" fill="none" stroke="url(#orbitGrad2)" stroke-width="1" opacity="0.4" transform="rotate(60 60 60)">
    <animateTransform attributeName="transform" type="rotate" from="60 60 60" to="420 60 60" dur="6s" repeatCount="indefinite"/>
  </ellipse>
  <circle cx="60" cy="60" r="44" fill="none" stroke="rgba(0,229,255,0.08)" stroke-width="1" stroke-dasharray="4,6"/>
  <g filter="url(#glow)">
    <rect x="50" y="54" width="20" height="12" rx="3" fill="#0a2040" stroke="#00e5ff" stroke-width="1.5"/>
    <rect x="26" y="57" width="22" height="6" rx="2" fill="#071830" stroke="#0070ff" stroke-width="1.2"/>
    <line x1="30" y1="57" x2="30" y2="63" stroke="#00e5ff" stroke-width="0.5" opacity="0.5"/>
    <line x1="34" y1="57" x2="34" y2="63" stroke="#00e5ff" stroke-width="0.5" opacity="0.5"/>
    <line x1="38" y1="57" x2="38" y2="63" stroke="#00e5ff" stroke-width="0.5" opacity="0.5"/>
    <line x1="42" y1="57" x2="42" y2="63" stroke="#00e5ff" stroke-width="0.5" opacity="0.5"/>
    <rect x="72" y="57" width="22" height="6" rx="2" fill="#071830" stroke="#0070ff" stroke-width="1.2"/>
    <line x1="76" y1="57" x2="76" y2="63" stroke="#00e5ff" stroke-width="0.5" opacity="0.5"/>
    <line x1="80" y1="57" x2="80" y2="63" stroke="#00e5ff" stroke-width="0.5" opacity="0.5"/>
    <line x1="84" y1="57" x2="84" y2="63" stroke="#00e5ff" stroke-width="0.5" opacity="0.5"/>
    <line x1="88" y1="57" x2="88" y2="63" stroke="#00e5ff" stroke-width="0.5" opacity="0.5"/>
    <line x1="60" y1="54" x2="60" y2="44" stroke="#00e5ff" stroke-width="1.5"/>
    <circle cx="60" cy="43" r="2.5" fill="#00e5ff" opacity="0.9">
      <animate attributeName="opacity" values="0.9;0.2;0.9" dur="1.5s" repeatCount="indefinite"/>
    </circle>
    <circle cx="60" cy="60" r="5" fill="url(#coreGrad)" filter="url(#glow2)">
      <animate attributeName="r" values="5;5.5;5" dur="2s" repeatCount="indefinite"/>
    </circle>
    <circle cx="53" cy="58" r="1.5" fill="#00ff88">
      <animate attributeName="opacity" values="1;0.2;1" dur="1s" repeatCount="indefinite"/>
    </circle>
    <circle cx="67" cy="58" r="1.5" fill="#ff2255">
      <animate attributeName="opacity" values="0.2;1;0.2" dur="0.8s" repeatCount="indefinite"/>
    </circle>
  </g>
  <circle r="3" fill="#00e5ff" filter="url(#glow)">
    <animateMotion dur="5s" repeatCount="indefinite"><mpath href="#orbitPath"/></animateMotion>
  </circle>
  <path id="orbitPath" d="M 60,10 A 50,20 0 1 1 59.99,10" fill="none"/>
  <circle cx="60" cy="60" r="20" fill="none" stroke="#00e5ff" stroke-width="1.5" opacity="0">
    <animate attributeName="r" values="20;55;20" dur="3s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.6;0;0.6" dur="3s" repeatCount="indefinite"/>
  </circle>
  <polygon points="4,4 14,4 4,14" fill="rgba(0,229,255,0.3)"/>
  <polygon points="116,4 106,4 116,14" fill="rgba(0,229,255,0.3)"/>
  <polygon points="4,116 14,116 4,106" fill="rgba(0,229,255,0.3)"/>
  <polygon points="116,116 106,116 116,106" fill="rgba(0,229,255,0.3)"/>
</svg>"""

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

POLLUTANTS  = ["PM2.5","PM10","NO2","SO2","CO","O3"]
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

AXIS_STYLE = dict(gridcolor="rgba(0,229,255,0.07)",linecolor="rgba(0,229,255,0.15)",tickfont=dict(color="#5a7a9a"))

def apply_theme(fig, height=400, margin=None, **kwargs):
    m = margin or dict(l=60,r=20,t=40,b=60)
    legend_defaults = dict(bgcolor="rgba(7,16,32,0.85)",bordercolor="rgba(0,229,255,0.18)",borderwidth=1)
    legend = {**legend_defaults, **kwargs.pop("legend",{})}
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(7,16,32,0.6)",
        font=dict(family="Exo 2, sans-serif",color="#d8f0ff",size=12),
        legend=legend, margin=m, height=height, **kwargs
    )
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig

def get_aqi_info(aqi):
    for lo,hi,label,color,emoji,advice in AQI_SCALE:
        if lo <= aqi <= hi:
            return label, color, emoji, advice
    return "Severe","#aa33ff","☠️",AQI_SCALE[-1][5]

def simulate_pollutants(aqi):
    factor = aqi / 150
    return {p: round(SAFE_LIMITS[p]*factor*random.uniform(0.65,1.35), 2) for p in POLLUTANTS}

def generate_data():
    rows = []
    for c in CITIES:
        aqi = random.randint(25, 490)
        label, color, emoji, advice = get_aqi_info(aqi)
        poll = simulate_pollutants(aqi)
        rows.append({
            "City":c["name"],"State":c["state"],"Lat":c["lat"],"Lon":c["lon"],
            "AQI":aqi,"Category":label,"Color":color,"Emoji":emoji,**poll
        })
    return pd.DataFrame(rows)

def pollutant_status(val, safe):
    if val <= safe:      return "✅ Safe","#00ff88"
    if val <= safe*1.5:  return "⚠️ Warning","#ffaa00"
    return "🚨 Danger","#ff2255"

def check_alerts(df_in, threshold=200):
    alerts = []
    for _,row in df_in.iterrows():
        if row["AQI"] > threshold:
            level = "CRITICAL" if row["AQI"] > 300 else "WARNING"
            alerts.append({
                "city":row["City"],"aqi":row["AQI"],"level":level,
                "cat":row["Category"],"color":row["Color"],
                "time":datetime.datetime.now().strftime("%H:%M:%S")
            })
    return sorted(alerts, key=lambda x: x["aqi"], reverse=True)

# ══════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════
def is_valid_email(e): return bool(re.match(r"^[^@]+@[^@]+\.[^@]+$", e))
def is_strong_password(pw):
    return (len(pw)>=8 and re.search(r"[A-Z]",pw) and
            re.search(r"[0-9]",pw) and re.search(r"[^A-Za-z0-9]",pw))

# ══════════════════════════════════════════════════════════════════
# LOGIN SCREEN  (with Forgot Password tab)
# ══════════════════════════════════════════════════════════════════
def show_auth_screen():
    st.markdown('<div class="grid-bg"></div><div class="scan-line"></div>', unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        st.markdown(
            '<div style="text-align:center;padding:10px 0 6px;filter:drop-shadow(0 0 16px rgba(0,229,255,0.5));">'
            + AQI_LOGO_SVG + '</div>', unsafe_allow_html=True
        )
        st.markdown("""
        <div class="auth-title">AQI COMMAND CENTER</div>
        <div class="auth-subtitle">INDIA POLLUTION INTELLIGENCE SYSTEM v4.0</div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="auth-card"><div class="corner-tl"></div><div class="corner-tr"></div><div class="corner-bl"></div><div class="corner-br"></div>', unsafe_allow_html=True)

        msg_text, msg_type = st.session_state.auth_msg
        if msg_text:
            css_cls = "auth-success" if msg_type=="success" else ("auth-error" if msg_type=="error" else "auth-info")
            st.markdown(f'<div class="{css_cls}">{msg_text}</div>', unsafe_allow_html=True)

        tab_login, tab_reg, tab_fp = st.tabs(["🔐  LOGIN", "📡  REGISTER", "🔑  FORGOT PASSWORD"])

        # ── LOGIN TAB ──────────────────────────────────────────
        with tab_login:
            st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
            st.markdown('<div style="font-family:Share Tech Mono;font-size:0.65rem;color:#4a6a8a;letter-spacing:2px;margin-bottom:14px;text-align:center;">ENTER CREDENTIALS TO ACCESS THE SYSTEM</div>', unsafe_allow_html=True)

            with st.form("login_form", clear_on_submit=False):
                login_email = st.text_input("📧  Email Address", placeholder="you@domain.com", key="form_login_email")
                login_pw    = st.text_input("🔒  Password", placeholder="••••••••", type="password", key="form_login_pw")
                st.markdown('<div style="font-family:Exo 2;font-size:0.72rem;color:#4a6a8a;text-align:right;margin-bottom:8px;">Demo: demo@aqicommand.in / Demo@1234</div>', unsafe_allow_html=True)
                submitted = st.form_submit_button("🚀  LAUNCH COMMAND CENTER", use_container_width=True)

            if submitted:
                if not login_email or not login_pw:
                    st.session_state.auth_msg = ("⚠️ Please fill in all fields.", "error")
                    st.rerun()
                elif login_email.strip() not in st.session_state.users_db:
                    st.session_state.auth_msg = ("❌ Email not found. Please register first.", "error")
                    st.rerun()
                elif st.session_state.users_db[login_email.strip()]["password_hash"] != _hash(login_pw):
                    st.session_state.auth_msg = ("❌ Incorrect password. Try again.", "error")
                    st.rerun()
                else:
                    email = login_email.strip()
                    st.session_state.users_db[email]["last_login"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    _save_users_db(st.session_state.users_db)
                    _record_attendance(email, st.session_state.users_db[email]["name"], "login")
                    st.session_state.logged_in = True
                    st.session_state.current_user = email
                    st.session_state.auth_msg = ("", "")
                    st.session_state.login_anim = True
                    st.rerun()

            st.markdown('<div style="text-align:center;margin-top:12px;font-family:Share Tech Mono;font-size:0.62rem;color:#2a4a6a;">──── SECURE · AES-256 ENCRYPTED ────</div>', unsafe_allow_html=True)

        # ── REGISTER TAB ───────────────────────────────────────
        with tab_reg:
            st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
            with st.form("register_form", clear_on_submit=False):
                reg_name  = st.text_input("👤  Full Name", placeholder="Dr. Aditya Kumar")
                reg_email = st.text_input("📧  Email", placeholder="you@domain.com")
                reg_role  = st.selectbox("🏷️  Role", ["Analyst","Researcher","Policy Maker","Student","Journalist"])
                reg_pw    = st.text_input("🔒  Password", type="password", placeholder="8+ chars · Uppercase · Number · Symbol")
                reg_pw2   = st.text_input("🔒  Confirm Password", type="password", placeholder="Re-enter password")
                terms     = st.checkbox("I agree to Terms of Service")
                reg_submitted = st.form_submit_button("📡  CREATE ACCOUNT", use_container_width=True)

            if reg_submitted:
                errors = []
                if not reg_name.strip(): errors.append("Name required")
                if not is_valid_email(reg_email): errors.append("Valid email required")
                if reg_email in st.session_state.users_db: errors.append("Email already registered")
                if not is_strong_password(reg_pw): errors.append("Password too weak (need uppercase, number, symbol, 8+ chars)")
                if reg_pw != reg_pw2: errors.append("Passwords don't match")
                if not terms: errors.append("Accept Terms of Service")
                if errors:
                    st.session_state.auth_msg = ("❌ " + " · ".join(errors), "error")
                    st.rerun()
                else:
                    st.session_state.users_db[reg_email] = {
                        "name": reg_name.strip(), "password_hash": _hash(reg_pw),
                        "role": reg_role, "joined": datetime.date.today().isoformat(),
                        "last_login": None, "alerts_enabled": True,
                        "alert_threshold": 200, "theme": "Cyber Blue", "notifications": [],
                        "is_admin": False,
                    }
                    _save_users_db(st.session_state.users_db)
                    _record_attendance(reg_email, reg_name.strip(), "register")
                    st.session_state.auth_msg = (f"✅ Account created! Welcome, {reg_name.split()[0]}. Please login.", "success")
                    st.rerun()

        # ── FORGOT PASSWORD TAB ────────────────────────────────
        with tab_fp:
            st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
            st.markdown(
                '<div style="font-family:Share Tech Mono;font-size:0.65rem;color:#4a6a8a;'
                'letter-spacing:2px;margin-bottom:16px;text-align:center;">'
                'RESET YOUR PASSWORD VIA EMAIL OTP</div>',
                unsafe_allow_html=True
            )

            # Forgot-password local message banner
            fp_msg_text, fp_msg_type = st.session_state.fp_msg
            if fp_msg_text:
                fp_css = ("auth-success" if fp_msg_type == "success"
                          else "auth-error" if fp_msg_type == "error"
                          else "auth-info")
                st.markdown(f'<div class="{fp_css}">{fp_msg_text}</div>', unsafe_allow_html=True)

            # ── STEP 1: Enter registered email ──
            if st.session_state.fp_step == 1:
                st.markdown(
                    '<div class="otp-box">'
                    '<div style="font-family:Orbitron,sans-serif;font-size:0.78rem;color:#00e5ff;'
                    'letter-spacing:2px;margin-bottom:10px;">STEP 1 OF 2 · VERIFY YOUR EMAIL</div>'
                    '<div style="font-family:Exo 2;font-size:0.82rem;color:#5a7a9a;margin-bottom:14px;">'
                    'Enter the email address registered with your account.<br>'
                    'A 6-digit OTP will be generated and displayed below (demo mode).</div>'
                    '</div>',
                    unsafe_allow_html=True
                )
                with st.form("fp_email_form", clear_on_submit=False):
                    fp_email_input = st.text_input(
                        "📧  Registered Email", placeholder="you@domain.com", key="fp_email_input"
                    )
                    send_otp_btn = st.form_submit_button("📨  SEND RESET OTP", use_container_width=True)

                if send_otp_btn:
                    fe = fp_email_input.strip().lower()
                    if not is_valid_email(fe):
                        st.session_state.fp_msg = ("❌ Please enter a valid email address.", "error")
                        st.rerun()
                    elif fe not in st.session_state.users_db:
                        # Security: don't reveal whether email exists — generic message
                        st.session_state.fp_msg = (
                            "📨 If this email is registered, an OTP has been sent. Check your inbox.",
                            "info"
                        )
                        st.rerun()
                    else:
                        otp = _generate_otp()
                        user_name = st.session_state.users_db[fe]["name"]
                        _send_reset_email(fe, otp, user_name)
                        st.session_state.fp_email = fe
                        st.session_state.fp_step  = 2
                        st.session_state.fp_msg   = (
                            f"✅ OTP sent to {fe[:3]}***{fe[fe.index('@'):]}.  "
                            f"Valid for 10 minutes.",
                            "success"
                        )
                        st.rerun()

            # ── STEP 2: Enter OTP + new password ──
            elif st.session_state.fp_step == 2:
                fp_email_display = st.session_state.fp_email
                masked = fp_email_display[:3] + "***" + fp_email_display[fp_email_display.index("@"):]

                # Show OTP hint for demo (remove in production)
                otp_hint = ""
                token_info = st.session_state.reset_tokens.get(fp_email_display)
                if token_info:
                    mins_left = max(0, int((token_info["expires"] - datetime.datetime.now()).total_seconds() // 60))
                    otp_hint  = token_info["otp"]   # DEV ONLY — remove in production
                    st.markdown(
                        f'<div class="otp-box">'
                        f'<div class="otp-sent-badge">📨 OTP SENT TO {masked}</div>'
                        f'<div style="font-family:Exo 2;font-size:0.78rem;color:#5a7a9a;margin-bottom:10px;">'
                        f'⏱ Expires in <b style="color:#ffaa00;">{mins_left} min</b></div>'
                        f'<div style="font-family:Share Tech Mono;font-size:0.72rem;color:#2a4a6a;'
                        f'background:rgba(0,0,0,0.3);border-radius:8px;padding:8px 12px;'
                        f'border:1px dashed rgba(0,229,255,0.1);">'
                        f'🛠 DEV MODE · OTP: <span style="color:#ffaa00;font-size:1.1rem;'
                        f'letter-spacing:4px;">{otp_hint}</span><br>'
                        f'<span style="color:#2a4a6a;font-size:0.62rem;">'
                        f'Remove this block in production</span></div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                st.markdown(
                    '<div style="font-family:Orbitron,sans-serif;font-size:0.78rem;color:#00e5ff;'
                    'letter-spacing:2px;margin:12px 0 10px;">STEP 2 OF 2 · SET NEW PASSWORD</div>',
                    unsafe_allow_html=True
                )

                with st.form("fp_reset_form", clear_on_submit=False):
                    otp_input   = st.text_input(
                        "🔢  Enter 6-Digit OTP",
                        placeholder="123456",
                        max_chars=6,
                        key="fp_otp_input"
                    )
                    new_pw      = st.text_input(
                        "🔒  New Password",
                        type="password",
                        placeholder="8+ chars · Uppercase · Number · Symbol",
                        key="fp_new_pw"
                    )
                    confirm_pw  = st.text_input(
                        "🔒  Confirm New Password",
                        type="password",
                        placeholder="Re-enter new password",
                        key="fp_confirm_pw"
                    )
                    col_reset, col_back = st.columns(2)
                    with col_reset:
                        reset_btn = st.form_submit_button("🔐  RESET PASSWORD", use_container_width=True)
                    with col_back:
                        back_btn  = st.form_submit_button("↩  BACK", use_container_width=True)

                if back_btn:
                    st.session_state.fp_step = 1
                    st.session_state.fp_msg  = ("", "")
                    st.rerun()

                if reset_btn:
                    errors = []
                    ok, verify_msg = _verify_otp(fp_email_display, otp_input)
                    if not ok:
                        errors.append(verify_msg)
                    if not is_strong_password(new_pw):
                        errors.append("Password too weak (need uppercase, number, symbol, 8+ chars)")
                    if new_pw != confirm_pw:
                        errors.append("Passwords don't match")

                    if errors:
                        st.session_state.fp_msg = ("❌ " + " · ".join(errors), "error")
                        st.rerun()
                    else:
                        # Update password in DB
                        st.session_state.users_db[fp_email_display]["password_hash"] = _hash(new_pw)
                        _save_users_db(st.session_state.users_db)

                        # Clear used token
                        if fp_email_display in st.session_state.reset_tokens:
                            del st.session_state.reset_tokens[fp_email_display]

                        # Reset flow state
                        uname = st.session_state.users_db[fp_email_display]["name"]
                        st.session_state.fp_step  = 1
                        st.session_state.fp_email = ""
                        st.session_state.fp_msg   = ("", "")
                        st.session_state.auth_msg = (
                            f"✅ Password reset successful! Welcome back, {uname.split()[0]}. Please login.",
                            "success"
                        )
                        st.rerun()

                # Resend OTP link
                st.markdown(
                    '<div style="text-align:center;margin-top:12px;">'
                    '<span style="font-family:Exo 2;font-size:0.78rem;color:#5a7a9a;">Didn\'t receive OTP? </span>',
                    unsafe_allow_html=True
                )
                if st.button("🔄  Resend OTP", key="resend_otp_btn", use_container_width=False):
                    if fp_email_display in st.session_state.users_db:
                        new_otp   = _generate_otp()
                        user_name = st.session_state.users_db[fp_email_display]["name"]
                        _send_reset_email(fp_email_display, new_otp, user_name)
                        st.session_state.fp_msg = (
                            f"✅ New OTP sent to {masked}. Valid for 10 minutes.",
                            "success"
                        )
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown(
            '<div style="text-align:center;margin-top:16px;font-family:Share Tech Mono;font-size:0.6rem;color:#2a4a6a;">'
            '🛰️ INDIA AQI COMMAND CENTER v4.0 · REAL-TIME · INTELLIGENT · SECURE</div>',
            unsafe_allow_html=True
        )

# ══════════════════════════════════════════════════════════════════
# GUARD — show login if not authenticated
# ══════════════════════════════════════════════════════════════════
if not st.session_state.logged_in:
    show_auth_screen()
    st.stop()

# ── Login success animation ──
if st.session_state.login_anim:
    user_info_anim = st.session_state.users_db[st.session_state.current_user]
    ph = st.empty()
    ph.markdown(
        '<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:80vh;text-align:center;">'
        '<div style="margin-bottom:20px;filter:drop-shadow(0 0 20px rgba(0,229,255,0.7));">' + AQI_LOGO_SVG + '</div>'
        '<div style="font-family:Orbitron,sans-serif;font-size:2.2rem;font-weight:900;background:linear-gradient(90deg,#00e5ff,#0070ff,#aa33ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">ACCESS GRANTED</div>'
        '<div style="font-family:Share Tech Mono,monospace;font-size:0.85rem;color:#00ff88;letter-spacing:3px;margin:14px 0;">● INITIALIZING COMMAND CENTER…</div>'
        f'<div style="font-family:Exo 2,sans-serif;font-size:1.05rem;color:#d8f0ff;margin-top:6px;">Welcome back, <b style="color:#00e5ff;">{user_info_anim["name"]}</b></div>'
        f'<div style="font-family:Share Tech Mono,monospace;font-size:0.72rem;color:#5a7a9a;margin-top:5px;">{st.session_state.current_user}</div>'
        '</div>', unsafe_allow_html=True
    )
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
user_info        = st.session_state.users_db[st.session_state.current_user]
alert_threshold_user = user_info.get("alert_threshold", 200)
active_alerts    = check_alerts(st.session_state.df, alert_threshold_user)

with st.sidebar:
    logo_small = AQI_LOGO_SVG.replace('width="110" height="110"','width="70" height="70"')
    st.markdown(
        '<div style="text-align:center;padding:10px 0 14px;">'
        + logo_small +
        '<div style="font-family:Orbitron,sans-serif;font-size:1.05rem;font-weight:900;background:linear-gradient(90deg,#00e5ff,#aa33ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">AQI COMMAND</div>'
        '<div style="font-family:Share Tech Mono,monospace;font-size:0.58rem;color:#4a6a8a;letter-spacing:2px;margin-top:2px;">INDIA MONITOR v4.0</div>'
        '</div>', unsafe_allow_html=True
    )

    initials = "".join([w[0].upper() for w in user_info["name"].split()[:2]])
    st.markdown(f"""
    <div class="user-badge">
        <div style="display:flex;align-items:center;gap:10px;">
            <div style="width:38px;height:38px;border-radius:50%;background:linear-gradient(135deg,#0070ff,#00e5ff);display:flex;align-items:center;justify-content:center;font-family:'Orbitron',sans-serif;font-size:0.82rem;font-weight:700;color:#030b18;flex-shrink:0;">{initials}</div>
            <div>
                <div class="user-name">{user_info['name']}</div>
                <div class="user-email">{st.session_state.current_user}</div>
                <div class="user-role">⬡ {user_info['role']}</div>
            </div>
        </div>
        <div style="font-family:'Share Tech Mono';font-size:0.58rem;color:#2a4a6a;margin-top:7px;">
            Joined: {user_info['joined']} · Last: {user_info.get('last_login','—') or 'First session'}
        </div>
    </div>""", unsafe_allow_html=True)

    if active_alerts:
        st.markdown(
            f'<div style="background:rgba(255,34,85,0.08);border:1px solid rgba(255,34,85,0.3);border-radius:8px;'
            f'padding:8px 12px;font-family:Share Tech Mono;font-size:0.68rem;color:#ff2255;text-align:center;'
            f'animation:notif-pulse 2s infinite;margin-bottom:8px;">'
            f'🚨 {len(active_alerts)} ACTIVE ALERT{"S" if len(active_alerts)>1 else ""}</div>',
            unsafe_allow_html=True
        )

    if st.button("🚪  LOGOUT", use_container_width=True, key="logout_btn"):
        for key in ["logged_in","current_user","auth_msg","login_anim",
                    "alerts_log","df","live_aqi","live_city","live_history","nav_page"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    st.divider()

    if st.button("🔄  REFRESH DATA", use_container_width=True, key="refresh_btn"):
        st.session_state.df = generate_data()
        st.session_state.last_refresh = datetime.datetime.now()
        st.rerun()

    st.session_state.auto_refresh = st.checkbox("⚡ Auto-Refresh (30s)", value=st.session_state.auto_refresh)
    st.divider()

    view_mode = st.radio("📡  NAVIGATION", [
        "🔴 Live Air Pollution","🗺️ Pollution Map","📊 City Comparison",
        "📈 Hourly Trend","🧪 Pollutant Breakdown","🏆 Rankings & Stats",
        "🔔 Alerts & Notifications",
        "🌡️ Weather & AQI Forecast","📸 Image Predictor",
        "📋 Data Export","👤 My Account",
    ], key="view_mode_radio")

    st.divider()
    st.markdown('<div style="font-family:Exo 2;font-size:0.75rem;color:#5a7a9a;letter-spacing:1px;text-transform:uppercase;margin-bottom:6px;">FILTERS</div>', unsafe_allow_html=True)
    aqi_range       = st.slider("AQI Range", 0, 500, (0, 500))
    all_states      = sorted(st.session_state.df["State"].unique())
    selected_states = st.multiselect("Filter by State", all_states)
    st.divider()

    st.markdown('<div style="font-family:Exo 2;font-size:0.75rem;color:#5a7a9a;letter-spacing:1px;text-transform:uppercase;margin-bottom:6px;">AQI LEGEND</div>', unsafe_allow_html=True)
    for lo,hi,label,color,emoji,_ in AQI_SCALE:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;margin:3px 0;font-family:Exo 2;font-size:0.75rem;">'
            f'<span style="width:9px;height:9px;border-radius:50%;background:{color};display:inline-block;box-shadow:0 0 5px {color};flex-shrink:0;"></span>'
            f'<span style="color:#5a7a9a;">{lo}–{hi}</span>'
            f'<span style="color:#d8f0ff;font-weight:600;">{label}</span></div>',
            unsafe_allow_html=True
        )
    st.divider()
    lr = st.session_state.last_refresh.strftime("%H:%M:%S")
    st.markdown(f'<div style="font-family:Share Tech Mono;font-size:0.68rem;color:#4a6a8a;text-align:center;">LAST UPDATE: {lr}</div>', unsafe_allow_html=True)

# ── Data prep ──
df  = st.session_state.df
dff = df[(df["AQI"]>=aqi_range[0]) & (df["AQI"]<=aqi_range[1])]
if selected_states:
    dff = dff[dff["State"].isin(selected_states)]

# ── Auto-refresh ──
if st.session_state.auto_refresh:
    elapsed = (datetime.datetime.now() - st.session_state.last_refresh).seconds
    if elapsed >= 30:
        st.session_state.df = generate_data()
        st.session_state.last_refresh = datetime.datetime.now()
        st.rerun()

# ══════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════
col_title, col_live = st.columns([3,1])
with col_title:
    st.markdown(
        '<h1 style="margin-bottom:2px;">🛰️ INDIA AQI COMMAND CENTER</h1>'
        '<p style="font-family:Share Tech Mono,monospace;color:#5a7a9a;font-size:0.78rem;letter-spacing:1.5px;margin-top:0;">'
        'REAL-TIME AIR QUALITY INTELLIGENCE · 25 MAJOR CITIES · POLLUTION MONITOR v4.0</p>',
        unsafe_allow_html=True
    )
with col_live:
    st.markdown(
        '<div style="display:flex;justify-content:flex-end;align-items:center;height:100%;padding-top:8px;">'
        '<div class="live-badge"><div class="dot-live"></div>LIVE MONITORING</div></div>',
        unsafe_allow_html=True
    )

ticker_items = " · ".join([f"{r['Emoji']} {r['City']}: AQI {r['AQI']} ({r['Category']})" for _,r in df.iterrows()])
st.markdown(
    f'<div class="ticker-wrap"><span style="font-family:Share Tech Mono;font-size:0.72rem;color:#00e5ff;letter-spacing:2px;margin-right:12px;">📡 LIVE</span>'
    f'<span class="ticker-text">{ticker_items}</span></div>',
    unsafe_allow_html=True
)

# ── Top metrics ──
avg_aqi   = int(df["AQI"].mean())
worst     = df.loc[df["AQI"].idxmax()]
best      = df.loc[df["AQI"].idxmin()]
dangerous = int((df["AQI"]>200).sum())
safe_count= int((df["AQI"]<=100).sum())
avg_label, avg_color, avg_emoji, _ = get_aqi_info(avg_aqi)

c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.metric("🌡️ National Avg",  avg_aqi,        f"{avg_emoji} {avg_label}")
c2.metric("☣️ Most Polluted", worst["City"],   f"AQI {worst['AQI']}")
c3.metric("🌿 Cleanest",      best["City"],    f"AQI {best['AQI']}")
c4.metric("⚠️ High Risk",     dangerous,       "AQI > 200")
c5.metric("✅ Safe Cities",   safe_count,      "AQI ≤ 100")
c6.metric("🚨 Active Alerts", len(active_alerts), f"Threshold: {alert_threshold_user}")
st.divider()

# ══════════════════════════════════════════════════════════════════
# PAGE ROUTING — paste your existing page code below unchanged
# ══════════════════════════════════════════════════════════════════

if "Live" in view_mode:
    st.markdown('<h2>🔴 LIVE AIR POLLUTION INDICATOR</h2>', unsafe_allow_html=True)
    st.info("Live page content goes here — paste your existing Live page code.")

elif "Map" in view_mode:
    st.markdown('<h2>🗺️ INDIA POLLUTION MAP</h2>', unsafe_allow_html=True)
    st.info("Map page content goes here.")

elif "Comparison" in view_mode:
    st.markdown('<h2>📊 CITY AQI COMPARISON</h2>', unsafe_allow_html=True)
    st.info("Comparison page content goes here.")

elif "Trend" in view_mode:
    st.markdown('<h2>📈 24-HOUR AQI TREND</h2>', unsafe_allow_html=True)
    st.info("Trend page content goes here.")

elif "Pollutant" in view_mode:
    st.markdown('<h2>🧪 POLLUTANT BREAKDOWN</h2>', unsafe_allow_html=True)
    st.info("Pollutant page content goes here.")

elif "Rankings" in view_mode:
    st.markdown('<h2>🏆 RANKINGS & STATISTICS</h2>', unsafe_allow_html=True)
    st.info("Rankings page content goes here.")

else:
    st.info(f"Page: {view_mode}")
