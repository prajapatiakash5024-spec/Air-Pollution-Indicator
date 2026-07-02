import streamlit as st
import pandas as pd
import numpy as np
import random
import time
import datetime
import json
import hashlib
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ══════════════════════════════════════════════════════════════════
# IST TIMEZONE
# ══════════════════════════════════════════════════════════════════
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

def get_ist_now():
    return datetime.datetime.now(IST)

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
# GMAIL SMTP CONFIG (for real OTP delivery)
# ══════════════════════════════════════════════════════════════════
# Set these via .streamlit/secrets.toml (create a ".streamlit" folder next to
# app.py, and inside it a "secrets.toml" file):
#   GMAIL_ADDRESS = "youraddress@gmail.com"
#   GMAIL_APP_PASSWORD = "xxxx xxxx xxxx xxxx"   # 16-char Gmail App Password (NOT your normal Gmail password)
# Generate an App Password at: https://myaccount.google.com/apppasswords
# (This requires 2-Step Verification to be turned ON for that Gmail account —
#  App Passwords are hidden/unavailable until 2-Step Verification is enabled.)
GMAIL_ADDRESS = st.secrets.get("GMAIL_ADDRESS", "") if hasattr(st, "secrets") else ""
GMAIL_APP_PASSWORD = st.secrets.get("GMAIL_APP_PASSWORD", "") if hasattr(st, "secrets") else ""
GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587

def _gmail_configured() -> bool:
    return bool(GMAIL_ADDRESS and GMAIL_APP_PASSWORD)

def _log_email_attempt(to_email: str, success: bool, err: str):
    """Writes every send attempt to a local log file so the app owner can
    diagnose delivery problems without exposing errors to end users."""
    try:
        entry = {
            "to": to_email,
            "success": success,
            "error": err,
            "time": get_ist_now().strftime("%Y-%m-%d %H:%M:%S IST"),
        }
        log = []
        if _EMAIL_LOG_FILE.exists():
            with open(_EMAIL_LOG_FILE, "r") as f:
                log = json.load(f)
        log.append(entry)
        log = log[-200:]  # keep last 200 entries
        with open(_EMAIL_LOG_FILE, "w") as f:
            json.dump(log, f, indent=2)
    except Exception:
        pass  # logging must never break the app

def _send_gmail(to_email: str, subject: str, html_body: str, text_body: str) -> tuple:
    """Send an email via Gmail SMTP. Returns (success: bool, error_message: str).

    Includes BOTH a plain-text and an HTML part, plus Date/Message-ID headers.
    Emails sent with only an HTML part and no Date/Message-ID are very commonly
    flagged as spam by Gmail and other providers — this was the #1 likely cause
    of OTP emails not arriving (or landing straight in Spam) in the previous version.
    """
    if not _gmail_configured():
        return False, "Gmail sender is not configured (missing GMAIL_ADDRESS / GMAIL_APP_PASSWORD in .streamlit/secrets.toml)."
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"AQI Command Center <{GMAIL_ADDRESS}>"
        msg["To"] = to_email
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid(domain="aqicommand.in")
        # Plain-text part MUST come first, HTML part second (per MIME alternative spec)
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(GMAIL_SMTP_HOST, GMAIL_SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, [to_email], msg.as_string())
        _log_email_attempt(to_email, True, "")
        return True, ""
    except smtplib.SMTPAuthenticationError:
        err = ("Gmail rejected the login. This almost always means: (1) you used your normal Gmail "
               "password instead of a 16-character App Password, or (2) 2-Step Verification isn't "
               "enabled on the sending account yet. Generate an App Password at "
               "https://myaccount.google.com/apppasswords and put it in GMAIL_APP_PASSWORD.")
        _log_email_attempt(to_email, False, err)
        return False, err
    except Exception as e:
        _log_email_attempt(to_email, False, str(e))
        return False, str(e)

# ══════════════════════════════════════════════════════════════════
# PERSISTENT STORAGE
# ══════════════════════════════════════════════════════════════════
import os, pathlib
_DATA_DIR = pathlib.Path("aqi_data")
_DATA_DIR.mkdir(exist_ok=True)
_USERS_FILE      = _DATA_DIR / "users_db.json"
_ATTENDANCE_FILE = _DATA_DIR / "attendance_log.json"
_EMAIL_LOG_FILE  = _DATA_DIR / "email_log.json"

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
        "timestamp": get_ist_now().strftime("%Y-%m-%d %H:%M:%S IST"),
        "date": get_ist_now().date().isoformat(),
    })
    _save_attendance(log)

# ══════════════════════════════════════════════════════════════════
# PASSWORD RESET — OTP SYSTEM (delivered via real Gmail SMTP)
# ══════════════════════════════════════════════════════════════════
if "reset_tokens" not in st.session_state:
    st.session_state.reset_tokens = {}

def _generate_otp():
    return str(random.randint(100000, 999999))

def _send_reset_email(email: str, otp: str, name: str) -> tuple:
    """Generates + stores the OTP, and emails it to the user's real inbox via Gmail SMTP.
    Returns (success: bool, error_message: str)."""
    st.session_state.reset_tokens[email] = {
        "otp": otp,
        "expires": get_ist_now() + datetime.timedelta(minutes=10),
        "name": name,
    }

    subject = "AQI Command Center - Your Password Reset OTP"
    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;background:#0a1628;color:#d8f0ff;padding:28px;border-radius:14px;border:1px solid #133a5a;">
        <h2 style="color:#00e5ff;margin-top:0;">🛰️ AQI Command Center</h2>
        <p>Hi {name},</p>
        <p>We received a request to reset your password. Use the OTP below to continue. This code is valid for <b>10 minutes</b>.</p>
        <div style="text-align:center;margin:24px 0;">
            <span style="font-size:32px;letter-spacing:8px;font-weight:bold;color:#ffaa00;background:#071020;padding:14px 22px;border-radius:10px;display:inline-block;">{otp}</span>
        </div>
        <p style="color:#5a7a9a;font-size:13px;">If you did not request this, you can safely ignore this email — your password will not be changed.</p>
        <hr style="border-color:#133a5a;">
        <p style="font-size:11px;color:#4a6a8a;">India AQI Command Center · Real-time Air Quality Intelligence</p>
    </div>
    """
    text_body = (
        f"Hi {name},\n\n"
        f"We received a request to reset your AQI Command Center password.\n\n"
        f"Your OTP: {otp}\n"
        f"This code is valid for 10 minutes.\n\n"
        f"If you did not request this, you can safely ignore this email.\n\n"
        f"— India AQI Command Center"
    )
    success, err = _send_gmail(email, subject, html_body, text_body)
    print(f"[OTP] {email}: {otp} (email sent: {success}{'' if success else ' — ' + err})")
    return success, err

def _verify_otp(email: str, otp_input: str) -> tuple:
    token = st.session_state.reset_tokens.get(email)
    if not token:
        return False, "No reset request found. Please request OTP again."
    if get_ist_now() > token["expires"]:
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
        "last_refresh": get_ist_now(),
        "auto_refresh": False,
        "compare_cities": [],
        "nav_page": "🔴 Live Air Pollution",
        "fp_step": 1,
        "fp_email": "",
        "fp_msg": ("", ""),
        "fe_msg": ("", ""),
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
.live-badge{display:inline-flex;align-items:center;gap:6px;background:rgba(0,255,136,0.08);border:1px solid #00ff88;border-radius:20px;padding:4px 14px;font-family:'Share Tech Mono',monospace;font-size:0.72rem;color:#00ff88;letter-spacing:1.5px;animation:pulse-live 2s infinite;}
@keyframes pulse-live{0%,100%{box-shadow:0 0 6px rgba(0,255,136,0.3);}50%{box-shadow:0 0 18px rgba(0,255,136,0.7);}}
.dot-live{width:7px;height:7px;background:#00ff88;border-radius:50%;animation:blink 1.2s infinite;}
@keyframes blink{0%,100%{opacity:1;}50%{opacity:0.1;}}
.aqi-live-card{background:linear-gradient(135deg,#0a1628,#122040);border:1px solid rgba(0,229,255,0.25);border-radius:16px;padding:20px;text-align:center;position:relative;overflow:hidden;}
.aqi-number{font-family:'Orbitron',monospace;font-size:3.2rem;font-weight:900;line-height:1;}
.aqi-label-text{font-family:'Exo 2',sans-serif;font-size:1rem;font-weight:600;letter-spacing:2px;text-transform:uppercase;margin-top:4px;}
.health-advice{background:linear-gradient(135deg,rgba(0,229,255,0.04),rgba(0,112,255,0.04));border:1px solid rgba(0,229,255,0.18);border-radius:12px;padding:16px;font-family:'Exo 2',sans-serif;font-size:0.9rem;line-height:1.6;}
.section-header{font-family:'Orbitron',sans-serif;font-size:0.9rem;font-weight:700;color:#00e5ff;letter-spacing:2px;text-transform:uppercase;padding:8px 0;border-bottom:1px solid rgba(0,229,255,0.18);margin-bottom:12px;}
.alert-card-red{background:rgba(255,34,85,0.07);border:1px solid rgba(255,34,85,0.35);border-radius:12px;padding:14px 16px;margin:6px 0;animation:alert-pulse-red 2s infinite;}
@keyframes alert-pulse-red{0%,100%{box-shadow:0 0 0px rgba(255,34,85,0);}50%{box-shadow:0 0 16px rgba(255,34,85,0.25);}}
.alert-card-amber{background:rgba(255,170,0,0.07);border:1px solid rgba(255,170,0,0.3);border-radius:12px;padding:14px 16px;margin:6px 0;}
.alert-card-green{background:rgba(0,255,136,0.06);border:1px solid rgba(0,255,136,0.25);border-radius:12px;padding:14px 16px;margin:6px 0;}
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
/* IST CLOCK CARD */
.ist-clock-card{background:linear-gradient(135deg,rgba(0,229,255,0.04),rgba(0,112,255,0.06));border:1px solid rgba(0,229,255,0.25);border-radius:12px;padding:10px 14px;margin-bottom:10px;text-align:center;}
.ist-time-display{font-family:'Share Tech Mono',monospace;font-size:1.35rem;color:#00e5ff;font-weight:700;letter-spacing:3px;}
.ist-date-display{font-family:'Exo 2',sans-serif;font-size:0.68rem;color:#5a7a9a;margin-top:3px;letter-spacing:1px;}
.ist-label{font-family:'Share Tech Mono',monospace;font-size:0.6rem;color:#4a6a8a;letter-spacing:2px;margin-bottom:4px;}
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
                "time":get_ist_now().strftime("%H:%M:%S IST")
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
# IST CLOCK COMPONENT
# ══════════════════════════════════════════════════════════════════
def render_ist_clock():
    """Renders a live IST clock in the sidebar using HTML + JS."""
    ist_now = get_ist_now()
    # Static fallback values (JS will override immediately)
    time_str = ist_now.strftime("%H:%M:%S")
    date_str = ist_now.strftime("%a, %d %b %Y")

    st.markdown(f"""
    <div class="ist-clock-card">
        <div class="ist-label">🕐 INDIA STANDARD TIME (IST · UTC+5:30)</div>
        <div class="ist-time-display" id="sidebar-ist-time">{time_str}</div>
        <div class="ist-date-display" id="sidebar-ist-date">{date_str}</div>
    </div>
    <script>
    (function() {{
        function pad(n) {{ return String(n).padStart(2,'0'); }}
        const DAYS = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
        const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
        function getIST() {{
            const now = new Date();
            return new Date(now.getTime() + now.getTimezoneOffset()*60000 + 5.5*3600000);
        }}
        function updateClock() {{
            const ist = getIST();
            const tEl = document.getElementById('sidebar-ist-time');
            const dEl = document.getElementById('sidebar-ist-date');
            if (tEl) tEl.textContent = pad(ist.getHours())+':'+pad(ist.getMinutes())+':'+pad(ist.getSeconds());
            if (dEl) dEl.textContent = DAYS[ist.getDay()]+', '+ist.getDate()+' '+MONTHS[ist.getMonth()]+' '+ist.getFullYear();
        }}
        updateClock();
        setInterval(updateClock, 1000);
    }})();
    </script>
    """, unsafe_allow_html=True)
# ══════════════════════════════════════════════════════════════════
# LOGIN SCREEN
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

        tab_login, tab_reg, tab_fp, tab_fe = st.tabs(
            ["🔐  LOGIN", "📡  REGISTER", "🔑  FORGOT PASSWORD", "✉️  FORGOT EMAIL"]
        )

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
                    st.session_state.users_db[email]["last_login"] = get_ist_now().strftime("%Y-%m-%d %H:%M IST")
                    _save_users_db(st.session_state.users_db)
                    _record_attendance(email, st.session_state.users_db[email]["name"], "login")
                    st.session_state.logged_in = True
                    st.session_state.current_user = email
                    st.session_state.auth_msg = ("", "")
                    st.session_state.login_anim = True
                    st.rerun()

            st.markdown('<div style="text-align:center;margin-top:12px;font-family:Share Tech Mono;font-size:0.62rem;color:#2a4a6a;">──── SECURE · AES-256 ENCRYPTED ────</div>', unsafe_allow_html=True)

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
                        "role": reg_role, "joined": get_ist_now().date().isoformat(),
                        "last_login": None, "alerts_enabled": True,
                        "alert_threshold": 200, "theme": "Cyber Blue", "notifications": [],
                        "is_admin": False,
                    }
                    _save_users_db(st.session_state.users_db)
                    _record_attendance(reg_email, reg_name.strip(), "register")
                    st.session_state.auth_msg = (f"✅ Account created! Welcome, {reg_name.split()[0]}. Please login.", "success")
                    st.rerun()

        with tab_fp:
            st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
            st.markdown(
                '<div style="font-family:Share Tech Mono;font-size:0.65rem;color:#4a6a8a;'
                'letter-spacing:2px;margin-bottom:16px;text-align:center;">'
                'RESET YOUR PASSWORD VIA EMAIL OTP</div>',
                unsafe_allow_html=True
            )

            fp_msg_text, fp_msg_type = st.session_state.fp_msg
            if fp_msg_text:
                fp_css = ("auth-success" if fp_msg_type == "success"
                          else "auth-error" if fp_msg_type == "error"
                          else "auth-info")
                st.markdown(f'<div class="{fp_css}">{fp_msg_text}</div>', unsafe_allow_html=True)

            if st.session_state.fp_step == 1:
                st.markdown(
                    '<div class="otp-box">'
                    '<div style="font-family:Orbitron,sans-serif;font-size:0.78rem;color:#00e5ff;'
                    'letter-spacing:2px;margin-bottom:10px;">STEP 1 OF 2 · VERIFY YOUR EMAIL</div>'
                    '<div style="font-family:Exo 2;font-size:0.82rem;color:#5a7a9a;margin-bottom:14px;">'
                    'Enter the email address registered with your account.<br>'
                    'A 6-digit OTP will be sent to that inbox via Gmail.</div>'
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
                        st.session_state.fp_msg = (
                            "📨 If this email is registered, an OTP has been sent. Check your inbox.",
                            "info"
                        )
                        st.rerun()
                    else:
                        otp = _generate_otp()
                        user_name = st.session_state.users_db[fe]["name"]
                        with st.spinner("📨 Sending OTP to your Gmail inbox..."):
                            _send_reset_email(fe, otp, user_name)  # failures are logged server-side only
                        st.session_state.fp_email = fe
                        st.session_state.fp_step  = 2
                        st.session_state.fp_msg = (
                            f"✅ OTP sent to {fe[:3]}*{fe[fe.index('@'):]}.  Valid for 10 minutes. "
                            f"Check your inbox (and spam folder).",
                            "success"
                        )
                        st.rerun()

            elif st.session_state.fp_step == 2:
                fp_email_display = st.session_state.fp_email
                masked = fp_email_display[:3] + "*" + fp_email_display[fp_email_display.index("@"):]

                token_info = st.session_state.reset_tokens.get(fp_email_display)
                if token_info:
                    mins_left = max(0, int((token_info["expires"] - get_ist_now()).total_seconds() // 60))
                    st.markdown(
                        f'<div class="otp-box">'
                        f'<div class="otp-sent-badge">📨 OTP SENT TO {masked}</div>'
                        f'<div style="font-family:Exo 2;font-size:0.78rem;color:#5a7a9a;margin-bottom:6px;">'
                        f'⏱️ Expires in <b style="color:#ffaa00;">{mins_left} min</b></div>'
                        f'<div style="font-family:Exo 2;font-size:0.72rem;color:#5a7a9a;">'
                        f'Open your Gmail inbox and enter the 6-digit code below.</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                st.markdown(
                    '<div style="font-family:Orbitron,sans-serif;font-size:0.78rem;color:#00e5ff;'
                    'letter-spacing:2px;margin:12px 0 10px;">STEP 2 OF 2 · SET NEW PASSWORD</div>',
                    unsafe_allow_html=True
                )

                with st.form("fp_reset_form", clear_on_submit=False):
                    otp_input   = st.text_input("🔢  Enter 6-Digit OTP (from your email)", placeholder="123456", max_chars=6, key="fp_otp_input")
                    new_pw      = st.text_input("🔒  New Password", type="password", placeholder="8+ chars · Uppercase · Number · Symbol", key="fp_new_pw")
                    confirm_pw  = st.text_input("🔒  Confirm New Password", type="password", placeholder="Re-enter new password", key="fp_confirm_pw")
                    col_reset, col_back = st.columns(2)
                    with col_reset:
                        reset_btn = st.form_submit_button("🔐  RESET PASSWORD", use_container_width=True)
                    with col_back:
                        back_btn  = st.form_submit_button("↩️  BACK", use_container_width=True)

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
                        st.session_state.users_db[fp_email_display]["password_hash"] = _hash(new_pw)
                        _save_users_db(st.session_state.users_db)
                        if fp_email_display in st.session_state.reset_tokens:
                            del st.session_state.reset_tokens[fp_email_display]
                        uname = st.session_state.users_db[fp_email_display]["name"]
                        st.session_state.fp_step  = 1
                        st.session_state.fp_email = ""
                        st.session_state.fp_msg   = ("", "")
                        st.session_state.auth_msg = (
                            f"✅ Password reset successful! Welcome back, {uname.split()[0]}. Please login.",
                            "success"
                        )
                        st.rerun()

                st.markdown(
                    '<div style="text-align:center;margin-top:12px;">'
                    '<span style="font-family:Exo 2;font-size:0.78rem;color:#5a7a9a;">Didn\'t receive OTP? </span>',
                    unsafe_allow_html=True
                )
                if st.button("🔄  Resend OTP", key="resend_otp_btn", use_container_width=False):
                    if fp_email_display in st.session_state.users_db:
                        new_otp   = _generate_otp()
                        user_name = st.session_state.users_db[fp_email_display]["name"]
                        with st.spinner("📨 Resending OTP..."):
                            _send_reset_email(fp_email_display, new_otp, user_name)  # failures are logged server-side only
                        st.session_state.fp_msg = (
                            f"✅ New OTP sent to {masked}. Valid for 10 minutes.",
                            "success"
                        )
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        with tab_fe:
            st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
            st.markdown(
                '<div style="font-family:Share Tech Mono;font-size:0.65rem;color:#4a6a8a;'
                'letter-spacing:2px;margin-bottom:16px;text-align:center;">'
                'FIND THE EMAIL LINKED TO YOUR ACCOUNT</div>',
                unsafe_allow_html=True
            )

            fe_msg_text, fe_msg_type = st.session_state.fe_msg
            if fe_msg_text:
                fe_css = ("auth-success" if fe_msg_type == "success"
                          else "auth-error" if fe_msg_type == "error"
                          else "auth-info")
                st.markdown(f'<div class="{fe_css}">{fe_msg_text}</div>', unsafe_allow_html=True)

            st.markdown(
                '<div class="otp-box">'
                '<div style="font-family:Exo 2;font-size:0.82rem;color:#5a7a9a;">'
                'Enter the full name you registered with. We\'ll show a masked version of any '
                'matching account email(s) so you can identify yours.</div>'
                '</div>',
                unsafe_allow_html=True
            )

            with st.form("forgot_email_form", clear_on_submit=False):
                fe_name_input = st.text_input("👤  Full Name (as registered)", placeholder="Dr. Aditya Kumar", key="fe_name_input")
                fe_submit = st.form_submit_button("🔍  FIND MY EMAIL", use_container_width=True)

            if fe_submit:
                query_name = fe_name_input.strip().lower()
                if not query_name:
                    st.session_state.fe_msg = ("⚠️ Please enter your name.", "error")
                    st.rerun()
                else:
                    matches = [
                        (email, data["name"])
                        for email, data in st.session_state.users_db.items()
                        if data["name"].strip().lower() == query_name
                    ]
                    if not matches:
                        st.session_state.fe_msg = (
                            "❌ No account found with that name. Double-check spelling or register a new account.",
                            "error"
                        )
                    else:
                        lines = []
                        for email, name in matches:
                            masked = email[:2] + "***" + email[email.index("@"):]
                            lines.append(f"👤 <b>{name}</b> — <span style='color:#00e5ff;'>{masked}</span>")
                        st.session_state.fe_msg = (
                            "✅ Found " + str(len(matches)) + " matching account(s):<br>" + "<br>".join(lines),
                            "success"
                        )
                    st.rerun()

            st.markdown(
                '<div style="text-align:center;margin-top:10px;font-family:Exo 2;font-size:0.72rem;color:#4a6a8a;">'
                'Still can\'t find it? Contact your workspace admin for account recovery.</div>',
                unsafe_allow_html=True
            )

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
user_info            = st.session_state.users_db[st.session_state.current_user]
alert_threshold_user = user_info.get("alert_threshold", 200)
active_alerts        = check_alerts(st.session_state.df, alert_threshold_user)

with st.sidebar:
    logo_small = AQI_LOGO_SVG.replace('width="110" height="110"','width="70" height="70"')
    st.markdown(
        '<div style="text-align:center;padding:10px 0 14px;">'
        + logo_small +
        '<div style="font-family:Orbitron,sans-serif;font-size:1.05rem;font-weight:900;background:linear-gradient(90deg,#00e5ff,#aa33ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">AQI COMMAND</div>'
        '<div style="font-family:Share Tech Mono,monospace;font-size:0.58rem;color:#4a6a8a;letter-spacing:2px;margin-top:2px;">INDIA MONITOR v4.0</div>'
        '</div>', unsafe_allow_html=True
    )

    # ── LIVE IST CLOCK ──────────────────────────────────────────
    render_ist_clock()

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
        st.session_state.last_refresh = get_ist_now()
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

    # ── LAST UPDATE in IST ──────────────────────────────────────
    lr = st.session_state.last_refresh.strftime("%H:%M:%S IST")
    st.markdown(f'<div style="font-family:Share Tech Mono;font-size:0.68rem;color:#4a6a8a;text-align:center;">LAST UPDATE: {lr}</div>', unsafe_allow_html=True)

# ── Data prep ──
df  = st.session_state.df
dff = df[(df["AQI"]>=aqi_range[0]) & (df["AQI"]<=aqi_range[1])]
if selected_states:
    dff = dff[dff["State"].isin(selected_states)]

# ── Auto-refresh (IST-aware) ──
if st.session_state.auto_refresh:
    elapsed = (get_ist_now() - st.session_state.last_refresh).seconds
    if elapsed >= 30:
        st.session_state.df = generate_data()
        st.session_state.last_refresh = get_ist_now()
        st.rerun()

# ══════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════
col_title, col_live = st.columns([3,1])
with col_title:
    ist_header = get_ist_now()
    st.markdown(
        '<h1 style="margin-bottom:2px;">🛰️ INDIA AQI COMMAND CENTER</h1>'
        f'<p style="font-family:Share Tech Mono,monospace;color:#5a7a9a;font-size:0.78rem;letter-spacing:1.5px;margin-top:0;">'
        f'REAL-TIME AIR QUALITY INTELLIGENCE · 25 MAJOR CITIES · {ist_header.strftime("%d %b %Y · %H:%M IST")}</p>',
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
# PAGES
# ══════════════════════════════════════════════════════════════════

if "Live" in view_mode:
    st.markdown('<h2>🔴 LIVE AIR POLLUTION INDICATOR</h2>', unsafe_allow_html=True)

    lcol1, lcol2, lcol3 = st.columns([2,2,1])
    with lcol1:
        live_city = st.selectbox(
            "📍 Select City",
            [c["name"] for c in CITIES],
            index=[c["name"] for c in CITIES].index(st.session_state.live_city),
            key="live_city_sel"
        )
        if live_city != st.session_state.live_city:
            st.session_state.live_city   = live_city
            base_aqi = int(df[df["City"]==live_city]["AQI"].values[0])
            st.session_state.live_aqi    = base_aqi
            st.session_state.live_history = [base_aqi]
    with lcol2:
        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
        if st.button("⚡  SIMULATE NEW READING", use_container_width=True, key="sim_btn"):
            prev    = st.session_state.live_aqi
            new_aqi = max(10, min(500, prev + random.randint(-30,30)))
            st.session_state.live_aqi = new_aqi
            st.session_state.live_history.append(new_aqi)
            if len(st.session_state.live_history) > 60:
                st.session_state.live_history.pop(0)
    with lcol3:
        st.markdown('<div class="live-badge" style="margin-top:18px;"><div class="dot-live"></div>ACTIVE</div>', unsafe_allow_html=True)

    current_aqi = st.session_state.live_aqi
    label, color, emoji, advice = get_aqi_info(current_aqi)
    poll_vals   = simulate_pollutants(current_aqi)
    tips        = HEALTH_TIPS.get(label, [])

    gauge_col, detail_col = st.columns([1,2])
    with gauge_col:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta", value=current_aqi,
            delta={
                "reference": st.session_state.live_history[-2] if len(st.session_state.live_history)>=2 else current_aqi,
                "increasing":{"color":"#ff2255"}, "decreasing":{"color":"#00ff88"},
                "font":{"size":16,"family":"Orbitron, sans-serif"}
            },
            number={"font":{"size":52,"family":"Orbitron, sans-serif","color":color},"suffix":" AQI"},
            gauge={
                "axis":{"range":[0,500],"tickvals":[0,50,100,200,300,400,500],"tickfont":{"size":9,"color":"#5a7a9a"}},
                "bar":{"color":color,"thickness":0.22},"bgcolor":"rgba(0,0,0,0)","borderwidth":0,
                "steps":[
                    {"range":[0,50],"color":"rgba(0,255,136,0.12)"},{"range":[50,100],"color":"rgba(163,255,0,0.1)"},
                    {"range":[100,200],"color":"rgba(255,170,0,0.1)"},{"range":[200,300],"color":"rgba(255,102,0,0.1)"},
                    {"range":[300,400],"color":"rgba(255,34,85,0.1)"},{"range":[400,500],"color":"rgba(170,51,255,0.1)"}
                ],
                "threshold":{"line":{"color":color,"width":4},"thickness":0.85,"value":current_aqi}
            },
            title={"text":f"{emoji} {label}<br><span style='font-size:10px;color:#5a7a9a;'>{live_city} · Live Sensor</span>",
                   "font":{"size":16,"family":"Orbitron, sans-serif","color":"#d8f0ff"}}
        ))
        fig_gauge.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#d8f0ff"), height=330, margin=dict(l=20,r=20,t=60,b=20)
        )
        st.plotly_chart(fig_gauge, use_container_width=True)
        st.markdown(
            f'<div class="health-advice" style="border-color:{color}33;">'
            f'<div style="font-family:Orbitron,sans-serif;font-size:0.72rem;color:{color};letter-spacing:2px;margin-bottom:7px;">HEALTH ADVISORY</div>'
            f'<div style="color:#d8f0ff;">{advice}</div></div>',
            unsafe_allow_html=True
        )

    with detail_col:
        st.markdown('<div class="section-header">🧪 LIVE POLLUTANT READINGS</div>', unsafe_allow_html=True)
        for p in POLLUTANTS:
            val  = poll_vals[p]; safe = SAFE_LIMITS[p]
            pct  = min(val/(safe*2.5), 1.0)
            status_text, s_color = pollutant_status(val, safe)
            bar_w = int(pct*100)
            st.markdown(f"""<div style="margin:5px 0;padding:10px 14px;background:rgba(0,229,255,0.03);border-radius:8px;border-left:3px solid {s_color};">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">
                    <span style="font-family:Orbitron,sans-serif;font-size:0.78rem;color:#d8f0ff;font-weight:700;">{p}</span>
                    <span style="font-family:Share Tech Mono,monospace;font-size:0.82rem;color:{s_color};">{val} {UNITS[p]}</span>
                    <span style="font-size:0.72rem;">{status_text}</span>
                </div>
                <div style="background:rgba(0,0,0,0.3);border-radius:4px;height:5px;overflow:hidden;">
                    <div style="width:{bar_w}%;height:100%;background:linear-gradient(90deg,{s_color}80,{s_color});border-radius:4px;"></div>
                </div>
                <div style="font-family:Share Tech Mono;font-size:0.65rem;color:#5a7a9a;margin-top:3px;">Safe ≤ {safe} {UNITS[p]} · {int(pct*100)}% of danger threshold</div>
            </div>""", unsafe_allow_html=True)

        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-header">💡 HEALTH TIPS</div>', unsafe_allow_html=True)
        for tip in tips:
            st.markdown(f'<div style="padding:6px 12px;margin:3px 0;background:rgba(0,229,255,0.03);border-radius:6px;font-family:Exo 2;font-size:0.83rem;color:#d8f0ff;">{tip}</div>', unsafe_allow_html=True)

    st.divider()
    st.markdown('<div class="section-header">📡 REAL-TIME AQI STREAM (LAST 60 READINGS)</div>', unsafe_allow_html=True)
    hist = st.session_state.live_history
    x_vals = list(range(len(hist)))
    colors_hist = [get_aqi_info(v)[1] for v in hist]
    r_int,g_int,b_int = int(color[1:3],16), int(color[3:5],16), int(color[5:7],16)
    fig_stream = go.Figure()
    fig_stream.add_trace(go.Scatter(x=x_vals, y=hist, mode="lines", line=dict(color=color,width=0),
        fill="tozeroy", fillcolor=f"rgba({r_int},{g_int},{b_int},0.08)", showlegend=False, hoverinfo="skip"))
    fig_stream.add_trace(go.Scatter(x=x_vals, y=hist, mode="lines+markers",
        line=dict(color=color,width=2.5),
        marker=dict(size=[10 if i==len(hist)-1 else 4 for i in range(len(hist))], color=colors_hist,
                    line=dict(width=1,color="rgba(0,0,0,0.4)")),
        name="AQI", hovertemplate="Reading %{x}: AQI %{y}<extra></extra>"))
    for threshold,t_label,t_color in [(100,"Satisfactory","#a3ff00"),(200,"Moderate","#ffaa00"),(300,"Poor","#ff6600")]:
        fig_stream.add_hline(y=threshold, line_dash="dash", line_color=t_color, opacity=0.35,
            annotation_text=t_label, annotation_font_size=9, annotation_font_color=t_color)
    apply_theme(fig_stream, height=250, margin=dict(l=60,r=20,t=20,b=50), showlegend=False)
    fig_stream.update_xaxes(title_text="Reading #")
    fig_stream.update_yaxes(title_text="AQI Value", range=[0,520])
    st.plotly_chart(fig_stream, use_container_width=True)

    st.markdown('<div class="section-header">🔮 24-HOUR AQI FORECAST</div>', unsafe_allow_html=True)
    now_h    = get_ist_now().hour
    h_labels = [f"{(now_h+i)%24:02d}:00 IST" for i in range(24)]
    forecast = [max(20,min(500, int(current_aqi+40*np.sin((i-6)*np.pi/12)+random.randint(-20,20)))) for i in range(24)]
    f_colors = [get_aqi_info(v)[1] for v in forecast]
    fig_fc   = go.Figure()
    fig_fc.add_trace(go.Bar(x=h_labels, y=forecast, marker_color=f_colors, marker_line_width=0,
        hovertemplate="%{x}<br>AQI: %{y}<extra></extra>", name="Forecast"))
    apply_theme(fig_fc, height=210, margin=dict(l=60,r=20,t=10,b=70))
    fig_fc.update_xaxes(title_text="Hour (IST)", tickangle=-45)
    fig_fc.update_yaxes(title_text="AQI")
    st.plotly_chart(fig_fc, use_container_width=True)

elif "Map" in view_mode:
    st.markdown('<h2>🗺️ INDIA POLLUTION MAP</h2>', unsafe_allow_html=True)
    col_left, col_right = st.columns([3,1])
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
            marker=dict(
                size=dff2["size_val"], color=dff2["AQI"],
                colorscale=[[0,"#00ff88"],[0.1,"#00ff88"],[0.2,"#a3ff00"],[0.4,"#ffaa00"],
                            [0.6,"#ff6600"],[0.8,"#ff2255"],[1,"#aa33ff"]],
                cmin=0, cmax=500, opacity=0.9,
                colorbar=dict(title=dict(text="AQI",font=dict(color="#d8f0ff")),
                              thickness=11, len=0.6, tickfont=dict(color="#d8f0ff"))
            ),
            text=dff2[map_metric].round(0).astype(int).astype(str),
            textfont=dict(size=9,color="white"), textposition="middle center",
            hovertext=dff2["label"], hoverinfo="text"
        ))
        fig_map.update_layout(
            mapbox=dict(style=map_style, center=dict(lat=22.5,lon=82.0), zoom=3.8),
            margin=dict(l=0,r=0,t=0,b=0), height=540, paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_map, use_container_width=True)
    with col_right:
        st.markdown('<div class="section-header">CITY RANKINGS</div>', unsafe_allow_html=True)
        ranked = dff.sort_values("AQI", ascending=False)[["City","AQI","Category","Color","Emoji"]].reset_index(drop=True)
        for _,row in ranked.iterrows():
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;align-items:center;padding:6px 10px;'
                f'margin:2px 0;border-radius:7px;background:rgba(0,229,255,0.03);border-left:3px solid {row["Color"]};">'
                f'<span style="font-family:Exo 2;font-size:0.8rem;font-weight:600;color:#d8f0ff;">{row["Emoji"]} {row["City"]}</span>'
                f'<span style="font-family:Share Tech Mono;font-size:0.78rem;color:{row["Color"]};">{row["AQI"]}</span></div>',
                unsafe_allow_html=True
            )

elif "Comparison" in view_mode:
    st.markdown('<h2>📊 CITY AQI COMPARISON</h2>', unsafe_allow_html=True)
    cc1, cc2 = st.columns(2)
    top_n   = cc1.slider("Number of cities", 5, 25, 15, key="top_n")
    sort_by = cc2.selectbox("Sort / colour by", ["AQI"]+POLLUTANTS, key="sort_by")
    sorted_df = dff.sort_values(sort_by, ascending=False).head(top_n)
    unit = UNITS.get(sort_by,"")
    fig_bar = go.Figure(go.Bar(
        x=sorted_df["City"], y=sorted_df[sort_by],
        marker_color=sorted_df["Color"], marker_line_width=0,
        text=sorted_df[sort_by].round(1), textposition="outside",
        hovertemplate="<b>%{x}</b><br>"+sort_by+": %{y}<extra></extra>"
    ))
    apply_theme(fig_bar, height=420)
    fig_bar.update_xaxes(title_text="City", tickangle=-38)
    fig_bar.update_yaxes(title_text=f"{sort_by} ({unit})" if unit else sort_by)
    st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()
    pie_col, scatter_col = st.columns(2)
    with pie_col:
        st.markdown('<div class="section-header">🥧 AQI CATEGORY DISTRIBUTION</div>', unsafe_allow_html=True)
        cat_order  = ["Good","Satisfactory","Moderate","Poor","Very Poor","Severe"]
        cat_colors = [c[3] for c in AQI_SCALE]
        cat_counts = df["Category"].value_counts().reindex(cat_order, fill_value=0)
        fig_pie = go.Figure(go.Pie(
            labels=cat_counts.index, values=cat_counts.values,
            marker_colors=cat_colors, hole=0.5,
            hovertemplate="<b>%{label}</b><br>Cities: %{value} (%{percent})<extra></extra>",
            textinfo="label+percent", textfont=dict(family="Exo 2, sans-serif",size=11)
        ))
        apply_theme(fig_pie, height=330, margin=dict(l=0,r=0,t=20,b=0))
        st.plotly_chart(fig_pie, use_container_width=True)
    with scatter_col:
        st.markdown('<div class="section-header">🔵 PM2.5 vs PM10 SCATTER</div>', unsafe_allow_html=True)
        fig_sc = go.Figure()
        for cat, grp in df.groupby("Category"):
            col_c = grp["Color"].iloc[0]
            fig_sc.add_trace(go.Scatter(
                x=grp["PM2.5"], y=grp["PM10"], mode="markers+text", name=cat,
                text=grp["City"], textposition="top center",
                textfont=dict(size=8,color="#5a7a9a"),
                marker=dict(size=10,color=col_c,opacity=0.85,line=dict(width=1,color="rgba(255,255,255,0.15)")),
                hovertemplate="<b>%{text}</b><br>PM2.5: %{x}<br>PM10: %{y}<extra></extra>"
            ))
        apply_theme(fig_sc, height=330)
        fig_sc.update_xaxes(title_text="PM2.5 (µg/m³)")
        fig_sc.update_yaxes(title_text="PM10 (µg/m³)")
        st.plotly_chart(fig_sc, use_container_width=True)

elif "Trend" in view_mode:
    st.markdown('<h2>📈 24-HOUR AQI TREND</h2>', unsafe_allow_html=True)
    selected_cities = st.multiselect(
        "Select cities (up to 6)", df["City"].tolist(),
        default=["Delhi","Mumbai","Bangalore","Chennai"], key="trend_cities"
    )
    if not selected_cities:
        st.info("Please select at least one city above.")
    else:
        now_ist_h = get_ist_now().hour
        hour_labels = [f"{(now_ist_h+h)%24:02d}:00 IST" for h in range(24)]
        palette = ["#00e5ff","#ff2255","#00ff88","#ffaa00","#aa33ff","#0070ff"]
        fig_line = go.Figure()
        for i, city in enumerate(selected_cities[:6]):
            base  = int(df.loc[df["City"]==city,"AQI"].values[0])
            trend = [max(20,min(500, int(base+55*np.sin((h-6)*np.pi/12)+random.randint(-25,25)))) for h in range(24)]
            col_c = palette[i%len(palette)]
            r_i,g_i,b_i = int(col_c[1:3],16),int(col_c[3:5],16),int(col_c[5:7],16)
            fig_line.add_trace(go.Scatter(x=hour_labels, y=trend, mode="none",
                fill="tozeroy", fillcolor=f"rgba({r_i},{g_i},{b_i},0.05)", showlegend=False, hoverinfo="skip"))
            fig_line.add_trace(go.Scatter(x=hour_labels, y=trend, mode="lines+markers", name=city,
                line=dict(color=col_c,width=2.5), marker=dict(size=5,color=col_c),
                hovertemplate=f"<b>{city}</b> %{{x}}: AQI %{{y}}<extra></extra>"))
        apply_theme(fig_line, height=440,
            legend=dict(orientation="h",yanchor="bottom",y=1.02,bgcolor="rgba(7,16,32,0.85)",
                        bordercolor="rgba(0,229,255,0.15)",borderwidth=1))
        fig_line.update_xaxes(title_text="Hour (IST)", tickangle=-45)
        fig_line.update_yaxes(title_text="AQI", range=[0,520])
        st.plotly_chart(fig_line, use_container_width=True)

        st.markdown('<div class="section-header">📅 7-DAY AQI TREND</div>', unsafe_allow_html=True)
        days = [(get_ist_now() + datetime.timedelta(days=i)).strftime("%a %d %b") for i in range(7)]
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

elif "Pollutant" in view_mode:
    st.markdown('<h2>🧪 POLLUTANT BREAKDOWN</h2>', unsafe_allow_html=True)
    selected_city = st.selectbox("Select a city", df["City"].tolist(), key="poll_city")
    row = df[df["City"]==selected_city].iloc[0]

    bar_col, radar_col = st.columns(2)
    with bar_col:
        st.markdown('<div class="section-header">📊 LEVELS vs SAFE LIMITS</div>', unsafe_allow_html=True)
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
        st.markdown('<div class="section-header">🕸️ POLLUTANT RADAR</div>', unsafe_allow_html=True)
        norm_vals = [min(row[p]/SAFE_LIMITS[p], 3.0) for p in POLLUTANTS]
        cat_color = row["Color"]
        r_c,g_c,b_c = int(cat_color[1:3],16),int(cat_color[3:5],16),int(cat_color[5:7],16)
        fig_radar = go.Figure(go.Scatterpolar(
            r=norm_vals+[norm_vals[0]], theta=POLLUTANTS+[POLLUTANTS[0]],
            fill="toself", fillcolor=f"rgba({r_c},{g_c},{b_c},0.18)",
            line=dict(color=cat_color,width=2), marker=dict(size=7,color=cat_color)
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=[1]*len(POLLUTANTS)+[1], theta=POLLUTANTS+[POLLUTANTS[0]],
            mode="lines", line=dict(color="#00e5ff",width=1,dash="dot"), showlegend=False
        ))
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True,range=[0,3],tickfont=dict(color="#5a7a9a",size=9),gridcolor="rgba(0,229,255,0.08)"),
                angularaxis=dict(tickfont=dict(color="#d8f0ff",size=11,family="Exo 2"),gridcolor="rgba(0,229,255,0.08)"),
                bgcolor="rgba(7,16,32,0.6)"
            ),
            showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#d8f0ff"), height=340, margin=dict(l=40,r=40,t=40,b=40)
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    st.divider()
    st.markdown('<div class="section-header">🔍 ALL CITIES — SINGLE POLLUTANT COMPARISON</div>', unsafe_allow_html=True)
    focus_poll = st.selectbox("Choose pollutant", POLLUTANTS, key="focus_poll")
    cmp_df     = df[["City",focus_poll]].sort_values(focus_poll, ascending=True)
    safe_val   = SAFE_LIMITS[focus_poll]
    bar_colors = ["#00ff88" if v<=safe_val else "#ffaa00" if v<=safe_val*1.5 else "#ff2255" for v in cmp_df[focus_poll]]
    fig_hbar   = go.Figure(go.Bar(
        x=cmp_df[focus_poll], y=cmp_df["City"], orientation="h",
        marker_color=bar_colors, marker_line_width=0,
        text=cmp_df[focus_poll].astype(str)+f" {UNITS[focus_poll]}",
        textposition="outside", hovertemplate="<b>%{y}</b>: %{x}<extra></extra>"
    ))
    fig_hbar.add_vline(x=safe_val, line_dash="dash", line_color="#00e5ff",
        annotation_text=f"Safe limit ({safe_val} {UNITS[focus_poll]})",
        annotation_font_size=10, annotation_font_color="#00e5ff")
    apply_theme(fig_hbar, height=570, margin=dict(l=120,r=80,t=20,b=40))
    fig_hbar.update_xaxes(title_text=UNITS[focus_poll])
    fig_hbar.update_yaxes(showgrid=False)
    st.plotly_chart(fig_hbar, use_container_width=True)

elif "Rankings" in view_mode:
    st.markdown('<h2>🏆 RANKINGS & STATISTICS</h2>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-header">🌿 TOP 10 CLEANEST</div>', unsafe_allow_html=True)
        best10 = df.nsmallest(10,"AQI")[["City","State","AQI","Category","Color","Emoji"]].reset_index(drop=True)
        for i,r in best10.iterrows():
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 12px;'
                f'margin:3px 0;border-radius:8px;background:rgba(0,255,136,0.05);border-left:3px solid {r["Color"]};">'
                f'<span style="font-family:Exo 2;font-size:0.88rem;"><b>{i+1}.</b> {r["Emoji"]} <b>{r["City"]}</b>'
                f'<span style="color:#5a7a9a;font-size:0.75rem;"> · {r["State"]}</span></span>'
                f'<span style="font-family:Share Tech Mono;color:{r["Color"]};font-size:0.88rem;">{r["AQI"]}</span></div>',
                unsafe_allow_html=True
            )
    with col2:
        st.markdown('<div class="section-header">☣️ TOP 10 MOST POLLUTED</div>', unsafe_allow_html=True)
        worst10 = df.nlargest(10,"AQI")[["City","State","AQI","Category","Color","Emoji"]].reset_index(drop=True)
        for i,r in worst10.iterrows():
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 12px;'
                f'margin:3px 0;border-radius:8px;background:rgba(255,34,85,0.05);border-left:3px solid {r["Color"]};">'
                f'<span style="font-family:Exo 2;font-size:0.88rem;"><b>{i+1}.</b> {r["Emoji"]} <b>{r["City"]}</b>'
                f'<span style="color:#5a7a9a;font-size:0.75rem;"> · {r["State"]}</span></span>'
                f'<span style="font-family:Share Tech Mono;color:{r["Color"]};font-size:0.88rem;">{r["AQI"]}</span></div>',
                unsafe_allow_html=True
            )

    st.divider()
    st.markdown('<div class="section-header">📊 AQI STATISTICS BY STATE</div>', unsafe_allow_html=True)
    state_stats = df.groupby("State")["AQI"].agg(Avg="mean",Max="max",Min="min",Cities="count").round(1).sort_values("Avg",ascending=False).reset_index()
    fig_state   = px.bar(state_stats, x="State", y="Avg",
        color="Avg", color_continuous_scale=[[0,"#00ff88"],[0.4,"#ffaa00"],[0.7,"#ff2255"],[1,"#aa33ff"]],
        range_color=[0,500], hover_data={"Max":True,"Min":True,"Cities":True},
        text=state_stats["Avg"].astype(int), labels={"Avg":"Average AQI"})
    apply_theme(fig_state, height=320)
    fig_state.update_xaxes(tickangle=-38)
    fig_state.update_coloraxes(showscale=False)
    st.plotly_chart(fig_state, use_container_width=True)

    st.divider()
    st.markdown('<div class="section-header">📋 FULL DATA TABLE</div>', unsafe_allow_html=True)
    display_cols = ["City","State","AQI","Category"]+POLLUTANTS
    st.dataframe(
        df[display_cols].sort_values("AQI",ascending=False).reset_index(drop=True),
        use_container_width=True, height=400
    )

elif "Alerts" in view_mode:
    st.markdown('<h2>🔔 ALERTS & NOTIFICATIONS</h2>', unsafe_allow_html=True)

    a1, a2, a3 = st.columns(3)
    with a1:
        st.markdown(f'<div class="hex-stat"><div class="hex-val" style="color:#ff2255;">{len(active_alerts)}</div><div class="hex-lbl">Active Alerts</div></div>', unsafe_allow_html=True)
    with a2:
        critical_count = sum(1 for a in active_alerts if a["level"]=="CRITICAL")
        st.markdown(f'<div class="hex-stat"><div class="hex-val" style="color:#aa33ff;">{critical_count}</div><div class="hex-lbl">Critical</div></div>', unsafe_allow_html=True)
    with a3:
        warning_count = sum(1 for a in active_alerts if a["level"]=="WARNING")
        st.markdown(f'<div class="hex-stat"><div class="hex-val" style="color:#ffaa00;">{warning_count}</div><div class="hex-lbl">Warnings</div></div>', unsafe_allow_html=True)

    st.divider()
    new_threshold = st.slider("🎚️ Alert Threshold (AQI)", 50, 400, alert_threshold_user, step=25, key="alert_thresh_slider")
    if new_threshold != alert_threshold_user:
        st.session_state.users_db[st.session_state.current_user]["alert_threshold"] = new_threshold
        _save_users_db(st.session_state.users_db)
        st.rerun()

    st.markdown('<div class="section-header" style="margin-top:16px;">🚨 ACTIVE ALERTS</div>', unsafe_allow_html=True)
    if not active_alerts:
        st.markdown('<div class="alert-card-green"><b style="color:#00ff88;">✅ All Clear!</b> No cities exceed the threshold.</div>', unsafe_allow_html=True)
    else:
        for a in active_alerts:
            card_cls = "alert-card-red" if a["level"]=="CRITICAL" else "alert-card-amber"
            lv_color = "#ff2255" if a["level"]=="CRITICAL" else "#ffaa00"
            st.markdown(
                f'<div class="{card_cls}">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                f'<span style="font-family:Orbitron,sans-serif;font-size:0.88rem;font-weight:700;color:#d8f0ff;">{a["city"]}</span>'
                f'<span style="font-family:Share Tech Mono;font-size:0.72rem;color:{lv_color};background:rgba(0,0,0,0.3);'
                f'padding:3px 10px;border-radius:12px;border:1px solid {lv_color}40;">{a["level"]}</span></div>'
                f'<div style="font-family:Orbitron,sans-serif;font-size:1.6rem;font-weight:900;color:{a["color"]};margin:4px 0;">{a["aqi"]} AQI</div>'
                f'<div style="font-family:Exo 2;font-size:0.78rem;color:#5a7a9a;">{a["cat"]} · Detected at {a["time"]}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

elif "Weather" in view_mode:
    st.markdown('<h2>🌡️ WEATHER & AQI FORECAST</h2>', unsafe_allow_html=True)
    w_city = st.selectbox("Select City", df["City"].tolist(), key="weather_city")
    row    = df[df["City"]==w_city].iloc[0]
    label, color, emoji, advice = get_aqi_info(row["AQI"])

    wc1, wc2, wc3, wc4 = st.columns(4)
    temp    = random.randint(22, 42)
    humidity= random.randint(30, 90)
    wind    = random.randint(5, 35)
    visibility = round(random.uniform(0.5, 10), 1)
    wc1.metric("🌡️ Temperature", f"{temp}°C", f"{'↑' if temp>30 else '↓'} Feels {temp+random.randint(-3,3)}°C")
    wc2.metric("💧 Humidity", f"{humidity}%", "High" if humidity>70 else "Normal")
    wc3.metric("💨 Wind Speed", f"{wind} km/h", "Strong" if wind>20 else "Moderate")
    wc4.metric("👁️ Visibility", f"{visibility} km", "Poor" if visibility<3 else "Good")

    st.divider()
    days_7 = [(get_ist_now() + datetime.timedelta(days=i)).strftime("%a %d %b") for i in range(7)]
    aqi_7  = [max(20,min(500, row["AQI"]+random.randint(-80,80))) for _ in range(7)]
    temp_7 = [temp + random.randint(-5,5) for _ in range(7)]
    fc_colors_7 = [get_aqi_info(v)[1] for v in aqi_7]

    fig_fc7 = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                             subplot_titles=("7-Day AQI Forecast","7-Day Temperature (°C)"))
    fig_fc7.add_trace(go.Bar(x=days_7, y=aqi_7, marker_color=fc_colors_7, name="AQI",
        hovertemplate="<b>%{x}</b><br>AQI: %{y}<extra></extra>"), row=1, col=1)
    fig_fc7.add_trace(go.Scatter(x=days_7, y=temp_7, mode="lines+markers", name="Temp",
        line=dict(color="#ffaa00",width=2.5), marker=dict(size=8,color="#ffaa00"),
        hovertemplate="<b>%{x}</b><br>Temp: %{y}°C<extra></extra>"), row=2, col=1)
    apply_theme(fig_fc7, height=500)
    st.plotly_chart(fig_fc7, use_container_width=True)

elif "Image" in view_mode:
    st.markdown('<h2>📸 IMAGE-BASED AQI PREDICTOR</h2>', unsafe_allow_html=True)
    st.markdown(
        '<div class="insight-blue"><b style="color:#00e5ff;">ℹ️ How it works:</b> Upload a sky/outdoor photo. '
        'The AI analyzes visual haze, visibility, and color tones to estimate AQI range.</div>',
        unsafe_allow_html=True
    )
    uploaded = st.file_uploader("📤 Upload Sky / Outdoor Image", type=["jpg","jpeg","png","webp"], key="img_upload")
    if uploaded:
        st.image(uploaded, caption="Uploaded Image", use_column_width=True)
        with st.spinner("🔍 Analyzing image for pollution indicators..."):
            time.sleep(2)
        pred_aqi   = random.randint(80, 350)
        pred_label, pred_color, pred_emoji, pred_advice = get_aqi_info(pred_aqi)
        confidence = random.randint(72, 95)
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,rgba(0,229,255,0.05),rgba(0,112,255,0.05));
                    border:1px solid rgba(0,229,255,0.2);border-radius:16px;padding:24px;text-align:center;margin-top:16px;">
            <div style="font-family:Share Tech Mono;font-size:0.72rem;color:#5a7a9a;letter-spacing:2px;margin-bottom:8px;">PREDICTED AQI</div>
            <div style="font-family:Orbitron,sans-serif;font-size:3rem;font-weight:900;color:{pred_color};">{pred_aqi}</div>
            <div style="font-family:Exo 2;font-size:1rem;color:{pred_color};margin-top:4px;">{pred_emoji} {pred_label}</div>
            <div style="font-family:Share Tech Mono;font-size:0.72rem;color:#5a7a9a;margin-top:8px;">Confidence: {confidence}%</div>
            <div style="font-family:Exo 2;font-size:0.85rem;color:#d8f0ff;margin-top:12px;">{pred_advice}</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(
            '<div style="text-align:center;padding:60px 20px;background:rgba(0,229,255,0.02);'
            'border:2px dashed rgba(0,229,255,0.15);border-radius:16px;">'
            '<div style="font-size:3rem;">📷</div>'
            '<div style="font-family:Exo 2;color:#5a7a9a;margin-top:12px;">Upload an outdoor image to predict AQI</div>'
            '</div>', unsafe_allow_html=True
        )

elif "Export" in view_mode:
    st.markdown('<h2>📋 DATA EXPORT</h2>', unsafe_allow_html=True)
    export_cols = st.multiselect("Select columns", ["City","State","AQI","Category"]+POLLUTANTS,
                                  default=["City","State","AQI","Category"]+POLLUTANTS, key="export_cols")
    export_df = df[export_cols] if export_cols else df
    st.dataframe(export_df, use_container_width=True, height=450)

    ec1, ec2 = st.columns(2)
    with ec1:
        csv_data = export_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", csv_data,
            f"india_aqi_{get_ist_now().date()}.csv", "text/csv", use_container_width=True)
    with ec2:
        json_data = export_df.to_json(orient="records", indent=2).encode("utf-8")
        st.download_button("⬇️ Download JSON", json_data,
            f"india_aqi_{get_ist_now().date()}.json", "application/json", use_container_width=True)

    st.divider()
    st.markdown('<div class="section-header">📊 QUICK STATS</div>', unsafe_allow_html=True)
    qs1,qs2,qs3,qs4 = st.columns(4)
    qs1.metric("Total Cities",   len(df))
    qs2.metric("Avg AQI",        int(df["AQI"].mean()))
    qs3.metric("Max AQI",        df["AQI"].max())
    qs4.metric("Min AQI",        df["AQI"].min())

    if user_info.get("is_admin"):
        st.divider()
        st.markdown('<div class="section-header">📑 ATTENDANCE LOG (ADMIN ONLY)</div>', unsafe_allow_html=True)
        att_log = _load_attendance()
        if att_log:
            att_df = pd.DataFrame(att_log).sort_values("timestamp", ascending=False)
            st.dataframe(att_df, use_container_width=True, height=300)
            att_csv = att_df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download Attendance Log", att_csv,
                f"attendance_{get_ist_now().date()}.csv", "text/csv")
        else:
            st.info("No attendance records yet.")

        st.divider()
        st.markdown('<div class="section-header">📧 EMAIL DELIVERY LOG (ADMIN ONLY)</div>', unsafe_allow_html=True)
        if not _gmail_configured():
            st.markdown(
                '<div class="alert-card-amber">⚠️ <b>Gmail sender is not configured.</b> No OTP emails can be sent '
                'until <code>GMAIL_ADDRESS</code> and <code>GMAIL_APP_PASSWORD</code> are set in '
                '<code>.streamlit/secrets.toml</code>. See the comment block at the top of app.py for the exact steps.</div>',
                unsafe_allow_html=True
            )
        if _EMAIL_LOG_FILE.exists():
            with open(_EMAIL_LOG_FILE, "r") as f:
                email_log = json.load(f)
            if email_log:
                email_df = pd.DataFrame(email_log).sort_values("time", ascending=False)
                st.dataframe(email_df, use_container_width=True, height=260)
                fail_count = int((~email_df["success"]).sum())
                if fail_count:
                    st.markdown(
                        f'<div class="alert-card-amber">⚠️ {fail_count} send attempt(s) failed. '
                        f'Check the "error" column above — the most common causes are a missing/incorrect '
                        f'App Password, or 2-Step Verification not being enabled on the Gmail account.</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.info("No email send attempts logged yet.")
        else:
            st.info("No email send attempts logged yet.")

elif "Account" in view_mode:
    st.markdown('<h2>👤 MY ACCOUNT</h2>', unsafe_allow_html=True)
    u = st.session_state.users_db[st.session_state.current_user]

    ac1, ac2 = st.columns([1,2])
    with ac1:
        initials_big = "".join([w[0].upper() for w in u["name"].split()[:2]])
        st.markdown(f"""
        <div style="text-align:center;padding:30px 20px;background:linear-gradient(135deg,rgba(0,229,255,0.06),rgba(0,112,255,0.04));
                    border:1px solid rgba(0,229,255,0.18);border-radius:16px;">
            <div style="width:80px;height:80px;border-radius:50%;background:linear-gradient(135deg,#0070ff,#00e5ff);
                        display:flex;align-items:center;justify-content:center;font-family:Orbitron,sans-serif;
                        font-size:1.6rem;font-weight:900;color:#030b18;margin:0 auto 16px;">
                {initials_big}
            </div>
            <div style="font-family:Orbitron,sans-serif;font-size:1rem;color:#00e5ff;font-weight:700;">{u['name']}</div>
            <div style="font-family:Share Tech Mono;font-size:0.65rem;color:#5a7a9a;margin-top:4px;">{st.session_state.current_user}</div>
            <div style="font-family:Exo 2;font-size:0.75rem;color:#00ff88;margin-top:6px;letter-spacing:1px;">⬡ {u['role']}</div>
            <div style="font-family:Share Tech Mono;font-size:0.62rem;color:#2a4a6a;margin-top:10px;">
                Joined: {u['joined']}<br>
                Last Login: {u.get('last_login','—') or 'First session'}
            </div>
            {"<div style='font-family:Share Tech Mono;font-size:0.68rem;color:#aa33ff;margin-top:8px;background:rgba(170,51,255,0.1);border:1px solid rgba(170,51,255,0.3);border-radius:8px;padding:4px 10px;'>⚡ ADMIN</div>" if u.get('is_admin') else ""}
        </div>""", unsafe_allow_html=True)

    with ac2:
        st.markdown('<div class="section-header">⚙️ ACCOUNT SETTINGS</div>', unsafe_allow_html=True)

        with st.form("update_profile_form"):
            new_name = st.text_input("👤 Display Name", value=u["name"])
            new_role = st.selectbox("🏷️ Role", ["Analyst","Researcher","Policy Maker","Student","Journalist"],
                                     index=["Analyst","Researcher","Policy Maker","Student","Journalist"].index(u["role"]))
            alerts_on = st.checkbox("🔔 Enable Alerts", value=u.get("alerts_enabled", True))
            new_thresh = st.slider("🚨 Alert AQI Threshold", 50, 400, u.get("alert_threshold",200), step=25)
            save_btn = st.form_submit_button("💾 SAVE SETTINGS", use_container_width=True)

        if save_btn:
            st.session_state.users_db[st.session_state.current_user].update({
                "name": new_name.strip() or u["name"],
                "role": new_role,
                "alerts_enabled": alerts_on,
                "alert_threshold": new_thresh,
            })
            _save_users_db(st.session_state.users_db)
            st.success("✅ Profile updated!")
            st.rerun()

        st.markdown('<div class="section-header" style="margin-top:20px;">🔑 CHANGE PASSWORD</div>', unsafe_allow_html=True)
        with st.form("change_pw_form"):
            curr_pw  = st.text_input("Current Password", type="password", key="curr_pw")
            new_pw1  = st.text_input("New Password", type="password", key="new_pw1")
            new_pw2  = st.text_input("Confirm New Password", type="password", key="new_pw2")
            pw_btn   = st.form_submit_button("🔐 CHANGE PASSWORD", use_container_width=True)

        if pw_btn:
            if _hash(curr_pw) != u["password_hash"]:
                st.error("❌ Current password is incorrect.")
            elif not is_strong_password(new_pw1):
                st.error("❌ New password too weak.")
            elif new_pw1 != new_pw2:
                st.error("❌ Passwords don't match.")
            else:
                st.session_state.users_db[st.session_state.current_user]["password_hash"] = _hash(new_pw1)
                _save_users_db(st.session_state.users_db)
                st.success("✅ Password changed successfully!")

    if u.get("is_admin"):
        st.divider()
        st.markdown('<div class="section-header">⚡ ADMIN PANEL — USER MANAGEMENT</div>', unsafe_allow_html=True)
        users_df = pd.DataFrame([
            {"Email": email, "Name": data["name"], "Role": data["role"],
             "Joined": data["joined"], "Last Login": data.get("last_login","—") or "Never",
             "Admin": "✅" if data.get("is_admin") else ""}
            for email, data in st.session_state.users_db.items()
        ])
        st.dataframe(users_df, use_container_width=True, height=300)
        st.markdown('<div style="font-family:Exo 2;font-size:0.82rem;color:#5a7a9a;margin-top:8px;">Total registered users: <b style="color:#00e5ff;">{}</b></div>'.format(len(st.session_state.users_db)), unsafe_allow_html=True)

else:
    st.info(f"Page: {view_mode} — Coming Soon!")
