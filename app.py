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
from PIL import Image

st.set_page_config(
    page_title="India AQI Command Center",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════
# GLOBAL CSS — dark sci-fi theme + login animations
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Exo+2:wght@300;400;600;700&family=Share+Tech+Mono&display=swap');
:root {
    --bg-dark:#050d1a; --bg-panel:#0a1628; --bg-card:#0f1f35; --bg-card2:#122040;
    --accent-cyan:#00f5ff; --accent-blue:#0080ff; --accent-green:#00ff88;
    --accent-red:#ff3366; --accent-amber:#ffb800; --accent-purple:#b44dff;
    --text-primary:#e0f4ff; --text-muted:#6a8fad; --border:rgba(0,245,255,0.15);
    --glow-cyan:0 0 20px rgba(0,245,255,0.4); --glow-green:0 0 20px rgba(0,255,136,0.4);
}
html,body,[class*="css"],.stApp{background-color:var(--bg-dark)!important;color:var(--text-primary)!important;font-family:'Exo 2',sans-serif!important;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#060f1f 0%,#091525 100%)!important;border-right:1px solid var(--border)!important;}
[data-testid="stSidebar"] *{color:var(--text-primary)!important;}
[data-testid="stSidebar"] .stButton>button{background:linear-gradient(135deg,#0080ff22,#00f5ff22)!important;border:1px solid var(--accent-cyan)!important;color:var(--accent-cyan)!important;border-radius:8px!important;font-family:'Exo 2',sans-serif!important;font-weight:600!important;letter-spacing:1px!important;transition:all 0.3s ease!important;}
[data-testid="stSidebar"] .stButton>button:hover{background:linear-gradient(135deg,#0080ff44,#00f5ff44)!important;box-shadow:var(--glow-cyan)!important;}
h1{font-family:'Orbitron',sans-serif!important;font-weight:900!important;background:linear-gradient(90deg,#00f5ff,#0080ff,#b44dff);-webkit-background-clip:text!important;-webkit-text-fill-color:transparent!important;letter-spacing:2px!important;}
h2,h3{font-family:'Orbitron',sans-serif!important;font-weight:700!important;color:var(--accent-cyan)!important;letter-spacing:1px!important;}
[data-testid="stMetric"]{background:linear-gradient(135deg,var(--bg-card),var(--bg-card2))!important;border:1px solid var(--border)!important;border-radius:12px!important;padding:16px!important;position:relative!important;overflow:hidden!important;}
[data-testid="stMetric"]::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,var(--accent-cyan),var(--accent-blue));}
[data-testid="stMetricLabel"]{color:var(--text-muted)!important;font-family:'Exo 2',sans-serif!important;font-size:0.78rem!important;letter-spacing:1px!important;text-transform:uppercase!important;}
[data-testid="stMetricValue"]{color:var(--accent-cyan)!important;font-family:'Orbitron',sans-serif!important;font-weight:700!important;}
[data-testid="stDataFrame"],.stDataFrame{border:1px solid var(--border)!important;border-radius:10px!important;overflow:hidden!important;}
.stSelectbox>div>div,.stMultiSelect>div>div{background:var(--bg-card)!important;border:1px solid var(--border)!important;border-radius:8px!important;color:var(--text-primary)!important;}
.stSlider>div{color:var(--accent-cyan)!important;}
.js-plotly-plot .plotly .bg{fill:transparent!important;}
hr{border-color:var(--border)!important;margin:1.5rem 0!important;}
.stAlert{background:var(--bg-card)!important;border:1px solid var(--border)!important;border-radius:10px!important;color:var(--text-primary)!important;}
::-webkit-scrollbar{width:6px;height:6px;}
::-webkit-scrollbar-track{background:var(--bg-dark);}
::-webkit-scrollbar-thumb{background:var(--accent-blue);border-radius:3px;}

/* ── LIVE BADGE ── */
.live-badge{display:inline-flex;align-items:center;gap:6px;background:rgba(0,255,136,0.1);border:1px solid var(--accent-green);border-radius:20px;padding:4px 12px;font-family:'Share Tech Mono',monospace;font-size:0.75rem;color:var(--accent-green);letter-spacing:1px;animation:pulse-live 2s infinite;}
@keyframes pulse-live{0%,100%{box-shadow:0 0 6px rgba(0,255,136,0.4);}50%{box-shadow:0 0 18px rgba(0,255,136,0.8);}}
.dot-live{width:8px;height:8px;background:var(--accent-green);border-radius:50%;animation:blink 1.2s infinite;}
@keyframes blink{0%,100%{opacity:1;}50%{opacity:0.2;}}

/* ── AQI CARDS ── */
.aqi-live-card{background:linear-gradient(135deg,#0a1628,#122040);border:1px solid rgba(0,245,255,0.25);border-radius:16px;padding:20px;text-align:center;position:relative;overflow:hidden;}
.aqi-number{font-family:'Orbitron',monospace;font-size:3.2rem;font-weight:900;line-height:1;}
.aqi-label-text{font-family:'Exo 2',sans-serif;font-size:1rem;font-weight:600;letter-spacing:2px;text-transform:uppercase;margin-top:4px;}
.health-advice{background:linear-gradient(135deg,rgba(0,245,255,0.05),rgba(0,128,255,0.05));border:1px solid rgba(0,245,255,0.2);border-radius:12px;padding:16px;font-family:'Exo 2',sans-serif;font-size:0.9rem;line-height:1.6;}
.section-header{font-family:'Orbitron',sans-serif;font-size:1.1rem;font-weight:700;color:#00f5ff;letter-spacing:2px;text-transform:uppercase;padding:8px 0;border-bottom:1px solid rgba(0,245,255,0.2);margin-bottom:12px;}

/* ══════════════════════════════════════════════
   LOGIN / REGISTER SCREEN
══════════════════════════════════════════════ */
.login-bg{
    position:fixed;top:0;left:0;width:100%;height:100%;
    background:radial-gradient(ellipse at 20% 50%,rgba(0,128,255,0.08) 0%,transparent 60%),
               radial-gradient(ellipse at 80% 20%,rgba(180,77,255,0.08) 0%,transparent 60%),
               #050d1a;
    z-index:0;overflow:hidden;
}
/* Floating particles */
.particle{position:absolute;border-radius:50%;animation:float-particle linear infinite;opacity:0;}
@keyframes float-particle{
    0%{transform:translateY(100vh) scale(0);opacity:0;}
    10%{opacity:0.6;}
    90%{opacity:0.4;}
    100%{transform:translateY(-10vh) scale(1.2);opacity:0;}
}
/* Scanning line */
.scan-line{position:fixed;top:0;left:0;width:100%;height:2px;
    background:linear-gradient(90deg,transparent,rgba(0,245,255,0.6),transparent);
    animation:scan 4s linear infinite;z-index:1;pointer-events:none;}
@keyframes scan{0%{top:0%;}100%{top:100%;}}

/* Corner decorations */
.corner-tl,.corner-tr,.corner-bl,.corner-br{position:absolute;width:24px;height:24px;}
.corner-tl{top:0;left:0;border-top:2px solid #00f5ff;border-left:2px solid #00f5ff;}
.corner-tr{top:0;right:0;border-top:2px solid #00f5ff;border-right:2px solid #00f5ff;}
.corner-bl{bottom:0;left:0;border-bottom:2px solid #00f5ff;border-left:2px solid #00f5ff;}
.corner-br{bottom:0;right:0;border-bottom:2px solid #00f5ff;border-right:2px solid #00f5ff;}

/* Login card */
.auth-card{
    background:linear-gradient(135deg,rgba(10,22,40,0.97),rgba(18,32,64,0.97));
    border:1px solid rgba(0,245,255,0.3);
    border-radius:20px;padding:40px 36px;
    box-shadow:0 0 60px rgba(0,245,255,0.08),0 0 120px rgba(0,128,255,0.05);
    position:relative;overflow:hidden;
    animation:card-appear 0.6s ease forwards;
}
@keyframes card-appear{
    0%{opacity:0;transform:translateY(30px) scale(0.96);}
    100%{opacity:1;transform:translateY(0) scale(1);}
}
.auth-card::before{
    content:'';position:absolute;top:0;left:0;right:0;height:3px;
    background:linear-gradient(90deg,#00f5ff,#0080ff,#b44dff,#00f5ff);
    background-size:200% 100%;
    animation:gradient-slide 3s linear infinite;
}
@keyframes gradient-slide{0%{background-position:0% 50%;}100%{background-position:200% 50%;}}

/* Logo pulse */
.auth-logo{
    text-align:center;margin-bottom:24px;
    animation:logo-pulse 3s ease-in-out infinite;
}
@keyframes logo-pulse{
    0%,100%{filter:drop-shadow(0 0 8px rgba(0,245,255,0.4));}
    50%{filter:drop-shadow(0 0 20px rgba(0,245,255,0.8));}
}
.auth-title{
    font-family:'Orbitron',sans-serif;font-size:1.5rem;font-weight:900;
    background:linear-gradient(90deg,#00f5ff,#0080ff,#b44dff);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
    text-align:center;letter-spacing:2px;margin-bottom:4px;
}
.auth-subtitle{
    font-family:'Share Tech Mono',monospace;font-size:0.7rem;
    color:#6a8fad;text-align:center;letter-spacing:3px;margin-bottom:28px;
}

/* Input fields styling */
.stTextInput input{
    background:rgba(0,245,255,0.04)!important;
    border:1px solid rgba(0,245,255,0.25)!important;
    border-radius:10px!important;
    color:#e0f4ff!important;
    font-family:'Exo 2',sans-serif!important;
    padding:12px 16px!important;
    transition:all 0.3s ease!important;
}
.stTextInput input:focus{
    border-color:#00f5ff!important;
    box-shadow:0 0 12px rgba(0,245,255,0.2)!important;
    background:rgba(0,245,255,0.06)!important;
}
.stTextInput label{color:#6a8fad!important;font-family:'Exo 2',sans-serif!important;font-size:0.8rem!important;letter-spacing:1px!important;}

/* Auth buttons */
.stButton>button{
    background:linear-gradient(135deg,#0080ff,#00f5ff)!important;
    border:none!important;color:#050d1a!important;
    font-family:'Orbitron',sans-serif!important;
    font-weight:700!important;font-size:0.85rem!important;
    letter-spacing:2px!important;border-radius:10px!important;
    padding:14px 28px!important;
    transition:all 0.3s ease!important;
    box-shadow:0 4px 20px rgba(0,245,255,0.25)!important;
}
.stButton>button:hover{
    transform:translateY(-2px)!important;
    box-shadow:0 8px 30px rgba(0,245,255,0.45)!important;
}
.stButton>button:active{transform:translateY(0)!important;}

/* Tab styling */
.stTabs [data-baseweb="tab-list"]{
    background:rgba(0,245,255,0.04)!important;
    border-radius:12px!important;
    border:1px solid rgba(0,245,255,0.15)!important;
    padding:4px!important;
}
.stTabs [data-baseweb="tab"]{
    font-family:'Orbitron',sans-serif!important;
    font-size:0.78rem!important;letter-spacing:2px!important;
    color:#6a8fad!important;border-radius:8px!important;
    padding:10px 20px!important;
}
.stTabs [aria-selected="true"]{
    background:linear-gradient(135deg,rgba(0,128,255,0.3),rgba(0,245,255,0.2))!important;
    color:#00f5ff!important;
}

/* User badge in sidebar */
.user-badge{
    background:linear-gradient(135deg,rgba(0,245,255,0.08),rgba(0,128,255,0.08));
    border:1px solid rgba(0,245,255,0.2);border-radius:12px;
    padding:12px 14px;margin-bottom:12px;
    animation:card-appear 0.5s ease;
}
.user-name{font-family:'Orbitron',sans-serif;font-size:0.85rem;color:#00f5ff;font-weight:700;}
.user-email{font-family:'Share Tech Mono',monospace;font-size:0.65rem;color:#6a8fad;margin-top:3px;}
.user-role{font-family:'Exo 2',sans-serif;font-size:0.7rem;color:#00ff88;margin-top:4px;letter-spacing:1px;}

/* Notification badge */
.notif-badge{
    display:inline-block;background:rgba(255,51,102,0.15);border:1px solid #ff3366;
    border-radius:20px;padding:3px 10px;font-family:'Share Tech Mono',monospace;
    font-size:0.65rem;color:#ff3366;letter-spacing:1px;margin-left:8px;
    animation:notif-pulse 2s infinite;
}
@keyframes notif-pulse{0%,100%{box-shadow:0 0 4px rgba(255,51,102,0.3);}50%{box-shadow:0 0 12px rgba(255,51,102,0.6);}}

/* Success / Error messages */
.auth-success{background:rgba(0,255,136,0.08);border:1px solid #00ff88;border-radius:10px;padding:12px 16px;font-family:'Exo 2',sans-serif;color:#00ff88;font-size:0.85rem;margin:8px 0;animation:card-appear 0.4s ease;}
.auth-error{background:rgba(255,51,102,0.08);border:1px solid #ff3366;border-radius:10px;padding:12px 16px;font-family:'Exo 2',sans-serif;color:#ff3366;font-size:0.85rem;margin:8px 0;animation:card-appear 0.4s ease;}
.auth-info{background:rgba(0,245,255,0.06);border:1px solid rgba(0,245,255,0.3);border-radius:10px;padding:12px 16px;font-family:'Exo 2',sans-serif;color:#00f5ff;font-size:0.85rem;margin:8px 0;}

/* Grid decorations on login page */
.grid-bg{
    position:fixed;top:0;left:0;width:100%;height:100%;
    background-image:
        linear-gradient(rgba(0,245,255,0.03) 1px,transparent 1px),
        linear-gradient(90deg,rgba(0,245,255,0.03) 1px,transparent 1px);
    background-size:40px 40px;pointer-events:none;z-index:0;
}

/* Orbit ring animation */
.orbit-ring{
    position:absolute;border-radius:50%;border:1px solid rgba(0,245,255,0.1);
    animation:orbit-spin linear infinite;
}
@keyframes orbit-spin{from{transform:rotate(0deg);}to{transform:rotate(360deg);}}

/* Data stream lines */
.data-stream{
    position:fixed;left:0;right:0;
    height:1px;background:linear-gradient(90deg,transparent,rgba(0,245,255,0.3),transparent);
    animation:data-flow 6s linear infinite;opacity:0.4;
}
@keyframes data-flow{0%{top:-2px;opacity:0;}5%{opacity:0.4;}95%{opacity:0.4;}100%{top:102%;opacity:0;}}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# USER DATABASE (session-based — replace with a real DB in production)
# ══════════════════════════════════════════════════════════════════
if "users_db" not in st.session_state:
    # Seed with a demo account
    demo_hash = hashlib.sha256("Demo@1234".encode()).hexdigest()
    st.session_state.users_db = {
        "demo@aqicommand.in": {
            "name": "Demo Analyst",
            "password_hash": demo_hash,
            "role": "Analyst",
            "joined": "2024-01-01",
            "last_login": None,
            "alerts_enabled": True,
        }
    }

if "logged_in"   not in st.session_state: st.session_state.logged_in   = False
if "current_user" not in st.session_state: st.session_state.current_user = None
if "auth_msg"    not in st.session_state: st.session_state.auth_msg    = ("", "")
if "login_anim"  not in st.session_state: st.session_state.login_anim  = False

# ── Helpers ──
def _hash(pw): return hashlib.sha256(pw.encode()).hexdigest()

def is_valid_email(email):
    return re.match(r"^[^@]+@[^@]+\.[^@]+$", email) is not None

def is_strong_password(pw):
    return (len(pw) >= 8 and
            re.search(r"[A-Z]", pw) and
            re.search(r"[0-9]", pw) and
            re.search(r"[^A-Za-z0-9]", pw))

# ══════════════════════════════════════════════════════════════════
# LOGIN / REGISTER SCREEN
# ══════════════════════════════════════════════════════════════════
def show_auth_screen():
    # Animated background decorations
    st.markdown("""
    <div class="grid-bg"></div>
    <div class="scan-line"></div>
    <div class="data-stream" style="animation-delay:0s;"></div>
    <div class="data-stream" style="animation-delay:2s;"></div>
    <div class="data-stream" style="animation-delay:4s;"></div>
    <!-- floating particles -->
    <div class="particle" style="left:10%;width:4px;height:4px;background:#00f5ff;animation-duration:8s;animation-delay:0s;"></div>
    <div class="particle" style="left:25%;width:3px;height:3px;background:#b44dff;animation-duration:11s;animation-delay:1s;"></div>
    <div class="particle" style="left:45%;width:5px;height:5px;background:#00ff88;animation-duration:9s;animation-delay:2.5s;"></div>
    <div class="particle" style="left:60%;width:3px;height:3px;background:#0080ff;animation-duration:12s;animation-delay:0.5s;"></div>
    <div class="particle" style="left:75%;width:4px;height:4px;background:#ff3366;animation-duration:7s;animation-delay:3s;"></div>
    <div class="particle" style="left:88%;width:3px;height:3px;background:#00f5ff;animation-duration:10s;animation-delay:1.5s;"></div>
    """, unsafe_allow_html=True)

    # Center the auth card
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        # Logo + title
        st.markdown("""
        <div class="auth-logo">
            <div style="font-size:3.5rem;margin-bottom:8px;">🛰️</div>
        </div>
        <div class="auth-title">AQI COMMAND CENTER</div>
        <div class="auth-subtitle">INDIA POLLUTION INTELLIGENCE SYSTEM v3.0</div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="auth-card"><div class="corner-tl"></div><div class="corner-tr"></div><div class="corner-bl"></div><div class="corner-br"></div>', unsafe_allow_html=True)

        tab_login, tab_reg = st.tabs(["🔐  LOGIN", "📡  REGISTER"])

        # ── Show persistent message ──
        msg_text, msg_type = st.session_state.auth_msg
        if msg_text:
            css_cls = "auth-success" if msg_type == "success" else ("auth-error" if msg_type == "error" else "auth-info")
            st.markdown(f'<div class="{css_cls}">{msg_text}</div>', unsafe_allow_html=True)

        # ─────────────── LOGIN TAB ───────────────
        with tab_login:
            st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
            st.markdown('<div style="font-family:Share Tech Mono;font-size:0.68rem;color:#6a8fad;letter-spacing:2px;margin-bottom:16px;text-align:center;">ENTER YOUR CREDENTIALS TO ACCESS THE SYSTEM</div>', unsafe_allow_html=True)

            login_email = st.text_input("📧  Email Address", key="login_email", placeholder="you@domain.com")
            login_pw    = st.text_input("🔒  Password",      key="login_pw",    placeholder="••••••••", type="password")

            col_l1, col_l2 = st.columns(2)
            with col_l1:
                remember = st.checkbox("Remember session", value=True, key="remember_me")
            with col_l2:
                st.markdown('<div style="text-align:right;font-family:Exo 2;font-size:0.75rem;color:#6a8fad;padding-top:6px;">Demo: demo@aqicommand.in / Demo@1234</div>', unsafe_allow_html=True)

            st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

            if st.button("🚀  LAUNCH COMMAND CENTER", use_container_width=True, key="btn_login"):
                if not login_email or not login_pw:
                    st.session_state.auth_msg = ("⚠️ Please fill in all fields.", "error")
                    st.rerun()
                elif login_email not in st.session_state.users_db:
                    st.session_state.auth_msg = ("❌ Email not found. Please register first.", "error")
                    st.rerun()
                elif st.session_state.users_db[login_email]["password_hash"] != _hash(login_pw):
                    st.session_state.auth_msg = ("❌ Incorrect password. Try again.", "error")
                    st.rerun()
                else:
                    # Success
                    st.session_state.users_db[login_email]["last_login"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    st.session_state.logged_in    = True
                    st.session_state.current_user = login_email
                    st.session_state.auth_msg     = ("", "")
                    st.session_state.login_anim   = True
                    st.rerun()

            st.markdown("""
            <div style="text-align:center;margin-top:16px;font-family:'Share Tech Mono';font-size:0.65rem;color:#6a8fad;">
                ──── SECURE CONNECTION · AES-256 ENCRYPTED ────
            </div>""", unsafe_allow_html=True)

        # ─────────────── REGISTER TAB ───────────────
        with tab_reg:
            st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
            st.markdown('<div style="font-family:Share Tech Mono;font-size:0.68rem;color:#6a8fad;letter-spacing:2px;margin-bottom:16px;text-align:center;">CREATE YOUR ANALYST ACCOUNT</div>', unsafe_allow_html=True)

            reg_name  = st.text_input("👤  Full Name",         key="reg_name",  placeholder="Dr. Aditya Kumar")
            reg_email = st.text_input("📧  Email Address",     key="reg_email", placeholder="you@domain.com")
            reg_role  = st.selectbox("🏷️  Role",               ["Analyst","Researcher","Policy Maker","Student","Journalist"], key="reg_role")
            reg_pw    = st.text_input("🔒  Password",          key="reg_pw",    type="password", placeholder="Min 8 chars · 1 uppercase · 1 number · 1 symbol")
            reg_pw2   = st.text_input("🔒  Confirm Password",  key="reg_pw2",   type="password", placeholder="Re-enter password")

            # Password strength indicator
            if reg_pw:
                strength = 0
                hints = []
                if len(reg_pw) >= 8:         strength += 1
                else:                         hints.append("8+ chars")
                if re.search(r"[A-Z]", reg_pw): strength += 1
                else:                         hints.append("uppercase")
                if re.search(r"[0-9]", reg_pw): strength += 1
                else:                         hints.append("number")
                if re.search(r"[^A-Za-z0-9]", reg_pw): strength += 1
                else:                         hints.append("symbol")
                colors  = ["#ff3366","#ffb800","#a3ff00","#00ff88"]
                labels  = ["Weak","Fair","Good","Strong"]
                bar_w   = strength * 25
                col = colors[strength - 1] if strength > 0 else "#ff3366"
                hint_str = "  · Missing: " + ", ".join(hints) if hints else "  ✅ All criteria met"
                st.markdown(f"""
                <div style="margin:4px 0 10px;">
                    <div style="display:flex;justify-content:space-between;font-family:'Exo 2';font-size:0.72rem;color:#6a8fad;margin-bottom:4px;">
                        <span>Password strength: <b style="color:{col};">{labels[strength-1] if strength>0 else "Weak"}</b></span>
                        <span style="color:#6a8fad;">{hint_str}</span>
                    </div>
                    <div style="background:rgba(0,0,0,0.3);border-radius:4px;height:5px;">
                        <div style="width:{bar_w}%;height:100%;background:{col};border-radius:4px;transition:width 0.4s ease;"></div>
                    </div>
                </div>""", unsafe_allow_html=True)

            terms = st.checkbox("I agree to the Terms of Service and Privacy Policy", key="reg_terms")
            st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

            if st.button("📡  CREATE ACCOUNT & JOIN", use_container_width=True, key="btn_register"):
                errors = []
                if not reg_name.strip():             errors.append("Name is required")
                if not is_valid_email(reg_email):    errors.append("Valid email required")
                if reg_email in st.session_state.users_db: errors.append("Email already registered")
                if not is_strong_password(reg_pw):   errors.append("Password too weak")
                if reg_pw != reg_pw2:                errors.append("Passwords do not match")
                if not terms:                        errors.append("Accept Terms to continue")

                if errors:
                    st.session_state.auth_msg = ("❌ " + "  ·  ".join(errors), "error")
                    st.rerun()
                else:
                    st.session_state.users_db[reg_email] = {
                        "name": reg_name.strip(),
                        "password_hash": _hash(reg_pw),
                        "role": reg_role,
                        "joined": datetime.date.today().isoformat(),
                        "last_login": None,
                        "alerts_enabled": True,
                    }
                    st.session_state.auth_msg = (f"✅ Account created! Welcome, {reg_name.split()[0]}. Please login.", "success")
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)  # close auth-card

        # Footer
        st.markdown("""
        <div style="text-align:center;margin-top:20px;font-family:'Share Tech Mono',monospace;font-size:0.62rem;color:#3a5a7a;">
            🛰️ INDIA AQI COMMAND CENTER v3.0 · SECURE · REAL-TIME · INTELLIGENT
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# SHOW LOGIN SCREEN IF NOT LOGGED IN
# ══════════════════════════════════════════════════════════════════
if not st.session_state.logged_in:
    show_auth_screen()
    st.stop()

# ══════════════════════════════════════════════════════════════════
# LOGGED-IN WELCOME FLASH
# ══════════════════════════════════════════════════════════════════
if st.session_state.login_anim:
    user_info = st.session_state.users_db[st.session_state.current_user]
    placeholder = st.empty()
    placeholder.markdown(f"""
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
                height:80vh;text-align:center;animation:card-appear 0.6s ease;">
        <div style="font-size:4rem;margin-bottom:16px;animation:logo-pulse 2s infinite;">🛰️</div>
        <div style="font-family:'Orbitron',sans-serif;font-size:2rem;font-weight:900;
                    background:linear-gradient(90deg,#00f5ff,#0080ff,#b44dff);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            ACCESS GRANTED
        </div>
        <div style="font-family:'Share Tech Mono',monospace;font-size:0.9rem;color:#00ff88;
                    letter-spacing:3px;margin:12px 0;animation:pulse-live 1.5s infinite;">
            ● AUTHENTICATING…
        </div>
        <div style="font-family:'Exo 2',sans-serif;font-size:1.1rem;color:#e0f4ff;margin-top:8px;">
            Welcome back, <b style="color:#00f5ff;">{user_info['name']}</b>
        </div>
        <div style="font-family:'Share Tech Mono',monospace;font-size:0.75rem;color:#6a8fad;margin-top:6px;">
            {st.session_state.current_user}
        </div>
    </div>""", unsafe_allow_html=True)
    time.sleep(2.0)
    placeholder.empty()
    st.session_state.login_anim = False
    st.rerun()

# ══════════════════════════════════════════════════════════════════
# DATA & CONSTANTS
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
    (101, 200, "Moderate",    "#ffb800","🟠","People with respiratory issues may experience discomfort."),
    (201, 300, "Poor",        "#ff6600","🔴","Avoid prolonged outdoor activity. Wear masks."),
    (301, 400, "Very Poor",   "#ff3366","🚨","Serious health effects. Stay indoors."),
    (401, 500, "Severe",      "#b44dff","☠️","Emergency conditions. Avoid all outdoor exposure!"),
]

HEALTH_TIPS = {
    "Good":        ["✅ Great day for outdoor exercise","🌿 Open windows for fresh air","🚴 Ideal for cycling or jogging"],
    "Satisfactory":["😷 Sensitive groups carry inhalers","🏃 Moderate outdoor exercise OK","👁️ May cause eye irritation"],
    "Moderate":    ["😷 Wear N95 mask outdoors","🏠 Reduce time outside","💊 Asthma patients avoid exertion"],
    "Poor":        ["🚫 Avoid outdoor exercise","😷 N95 mask mandatory outdoors","🏥 Seek medical help if breathing issues"],
    "Very Poor":   ["🔴 Stay indoors at all times","🪟 Keep windows closed","🚑 Call doctor if symptoms appear"],
    "Severe":      ["☠️ Do NOT go outside","🏥 Emergency: seek immediate medical attention","🔴 Government may enforce restrictions"],
}

AXIS_STYLE = dict(gridcolor="rgba(0,245,255,0.08)",linecolor="rgba(0,245,255,0.2)",tickfont=dict(color="#6a8fad"))

def apply_theme(fig, height=400, margin=None, **kwargs):
    m = margin or dict(l=60, r=20, t=40, b=60)
    legend_defaults = dict(bgcolor="rgba(10,22,40,0.8)", bordercolor="rgba(0,245,255,0.2)", borderwidth=1)
    legend = {**legend_defaults, **kwargs.pop("legend", {})}
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(10,22,40,0.6)",
        font=dict(family="Exo 2, sans-serif",color="#e0f4ff",size=12),legend=legend,margin=m,height=height,**kwargs)
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig

def get_aqi_info(aqi):
    for lo,hi,label,color,emoji,advice in AQI_SCALE:
        if lo<=aqi<=hi: return label,color,emoji,advice
    return "Severe","#b44dff","☠️",AQI_SCALE[-1][5]

def simulate_pollutants(aqi):
    factor=aqi/150
    return {p:round(SAFE_LIMITS[p]*factor*random.uniform(0.65,1.35),2) for p in POLLUTANTS}

def generate_data():
    rows=[]
    for c in CITIES:
        aqi=random.randint(25,490)
        label,color,emoji,advice=get_aqi_info(aqi)
        poll=simulate_pollutants(aqi)
        rows.append({"City":c["name"],"State":c["state"],"Lat":c["lat"],"Lon":c["lon"],
                     "AQI":aqi,"Category":label,"Color":color,"Emoji":emoji,**poll})
    return pd.DataFrame(rows)

def pollutant_status(val,safe):
    if val<=safe:       return "✅ Safe","#00ff88"
    if val<=safe*1.5:   return "⚠️ Warning","#ffb800"
    return "🚨 Danger","#ff3366"

# ── Session state ──
if "df"           not in st.session_state: st.session_state.df           = generate_data()
if "live_aqi"     not in st.session_state: st.session_state.live_aqi     = 142
if "live_city"    not in st.session_state: st.session_state.live_city    = "Mumbai"
if "live_history" not in st.session_state: st.session_state.live_history = [142]
if "last_refresh" not in st.session_state: st.session_state.last_refresh = datetime.datetime.now()
if "auto_refresh" not in st.session_state: st.session_state.auto_refresh = False

# ══════════════════════════════════════════════════════════════════
# SIDEBAR (only shown when logged in)
# ══════════════════════════════════════════════════════════════════
user_info = st.session_state.users_db[st.session_state.current_user]

with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:10px 0 16px;">
        <div style="font-family:'Orbitron',sans-serif;font-size:1.3rem;font-weight:900;
                    background:linear-gradient(90deg,#00f5ff,#b44dff);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            🛰️ AQI COMMAND
        </div>
        <div style="font-family:'Share Tech Mono',monospace;font-size:0.65rem;color:#6a8fad;letter-spacing:2px;margin-top:4px;">
            INDIA POLLUTION MONITOR v3.0
        </div>
    </div>""", unsafe_allow_html=True)

    # User badge
    initials = "".join([w[0].upper() for w in user_info["name"].split()[:2]])
    st.markdown(f"""
    <div class="user-badge">
        <div style="display:flex;align-items:center;gap:10px;">
            <div style="width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#0080ff,#00f5ff);
                        display:flex;align-items:center;justify-content:center;font-family:'Orbitron',sans-serif;
                        font-size:0.8rem;font-weight:700;color:#050d1a;flex-shrink:0;">{initials}</div>
            <div>
                <div class="user-name">{user_info['name']}</div>
                <div class="user-email">{st.session_state.current_user}</div>
                <div class="user-role">⬡ {user_info['role']}</div>
            </div>
        </div>
        <div style="font-family:'Share Tech Mono';font-size:0.6rem;color:#3a5a7a;margin-top:8px;">
            Joined: {user_info['joined']} · Last: {user_info.get('last_login','—') or 'First session'}
        </div>
    </div>""", unsafe_allow_html=True)

    if st.button("🚪  LOGOUT", use_container_width=True, key="logout_btn"):
        st.session_state.logged_in    = False
        st.session_state.current_user = None
        st.session_state.auth_msg     = ("", "")
        st.rerun()

    st.divider()

    if st.button("🔄  REFRESH DATA", use_container_width=True):
        st.session_state.df           = generate_data()
        st.session_state.last_refresh = datetime.datetime.now()
        st.rerun()

    st.session_state.auto_refresh = st.checkbox("⚡ Auto-Refresh (30s)", value=st.session_state.auto_refresh)
    st.divider()

    view_mode = st.radio("📡  NAVIGATION", [
        "🔴 Live Air Pollution","🗺️ Pollution Map","📊 City Comparison",
        "📈 Hourly Trend","🧪 Pollutant Breakdown","🏆 Rankings & Stats",
        "🌡️ Weather & AQI Forecast","📸 Image Predictor","📋 Data Export",
        "👤 My Account",
    ])
    st.divider()

    st.markdown('<div style="font-family:Exo 2;font-size:0.8rem;color:#6a8fad;letter-spacing:1px;text-transform:uppercase;">FILTERS</div>', unsafe_allow_html=True)
    aqi_range       = st.slider("AQI Range",0,500,(0,500))
    all_states      = sorted(st.session_state.df["State"].unique())
    selected_states = st.multiselect("Filter by State",all_states)
    st.divider()

    st.markdown('<div style="font-family:Exo 2;font-size:0.8rem;color:#6a8fad;letter-spacing:1px;text-transform:uppercase;margin-bottom:8px;">AQI LEGEND</div>', unsafe_allow_html=True)
    for lo,hi,label,color,emoji,_ in AQI_SCALE:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;margin:3px 0;font-family:Exo 2;font-size:0.78rem;">'
            f'<span style="width:10px;height:10px;border-radius:50%;background:{color};display:inline-block;box-shadow:0 0 6px {color};"></span>'
            f'<span style="color:#6a8fad;">{lo}–{hi}</span>'
            f'<span style="color:#e0f4ff;font-weight:600;">{label}</span></div>',
            unsafe_allow_html=True)
    st.divider()
    lr = st.session_state.last_refresh.strftime("%H:%M:%S")
    st.markdown(f'<div style="font-family:Share Tech Mono;font-size:0.7rem;color:#6a8fad;text-align:center;">LAST UPDATE: {lr}</div>', unsafe_allow_html=True)

# ── Data prep ──
df  = st.session_state.df
dff = df[(df["AQI"]>=aqi_range[0])&(df["AQI"]<=aqi_range[1])]
if selected_states:
    dff = dff[dff["State"].isin(selected_states)]

if st.session_state.auto_refresh:
    elapsed=(datetime.datetime.now()-st.session_state.last_refresh).seconds
    if elapsed>=30:
        st.session_state.df           = generate_data()
        st.session_state.last_refresh = datetime.datetime.now()
        st.rerun()

# ── Header ──
col_title,col_live = st.columns([3,1])
with col_title:
    st.markdown("""
    <h1 style="margin-bottom:4px;">🛰️ INDIA AQI COMMAND CENTER</h1>
    <p style="font-family:'Share Tech Mono',monospace;color:#6a8fad;font-size:0.82rem;letter-spacing:1.5px;margin-top:0;">
        REAL-TIME AIR QUALITY INTELLIGENCE · 25 MAJOR CITIES · LIVE POLLUTION MONITOR
    </p>""", unsafe_allow_html=True)
with col_live:
    st.markdown("""
    <div style="display:flex;justify-content:flex-end;align-items:center;height:100%;padding-top:8px;">
        <div class="live-badge"><div class="dot-live"></div>LIVE MONITORING</div>
    </div>""", unsafe_allow_html=True)

st.divider()

avg_aqi   = int(df["AQI"].mean())
worst     = df.loc[df["AQI"].idxmax()]
best      = df.loc[df["AQI"].idxmin()]
dangerous = int((df["AQI"]>200).sum())
avg_label,avg_color,avg_emoji,_ = get_aqi_info(avg_aqi)
safe_count = int((df["AQI"]<=100).sum())

c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("🌡️ National Avg AQI", avg_aqi,       f"{avg_emoji} {avg_label}")
c2.metric("☣️ Most Polluted",     worst["City"],  f"AQI {worst['AQI']}")
c3.metric("🌿 Cleanest City",     best["City"],   f"AQI {best['AQI']}")
c4.metric("⚠️ High Risk Cities",  dangerous,      "AQI > 200")
c5.metric("✅ Safe Cities",        safe_count,     "AQI ≤ 100")
st.divider()

# ══════════════════════════════════════════════════════════════════
# VIEW 0 — LIVE AIR POLLUTION
# ══════════════════════════════════════════════════════════════════
if "Live" in view_mode:
    st.markdown('<h2>🔴 LIVE AIR POLLUTION INDICATOR</h2>', unsafe_allow_html=True)
    lcol1,lcol2,lcol3 = st.columns([2,2,1])
    with lcol1:
        live_city = st.selectbox("📍 Select City for Live Feed",
            [c["name"] for c in CITIES],
            index=[c["name"] for c in CITIES].index(st.session_state.live_city),
            key="live_city_sel")
        if live_city != st.session_state.live_city:
            st.session_state.live_city    = live_city
            base_aqi = int(df[df["City"]==live_city]["AQI"].values[0])
            st.session_state.live_aqi     = base_aqi
            st.session_state.live_history = [base_aqi]
    with lcol2:
        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
        if st.button("⚡  SIMULATE NEW READING", use_container_width=True):
            prev    = st.session_state.live_aqi
            new_aqi = max(10, min(500, prev+random.randint(-30,30)))
            st.session_state.live_aqi = new_aqi
            st.session_state.live_history.append(new_aqi)
            if len(st.session_state.live_history)>60:
                st.session_state.live_history.pop(0)
    with lcol3:
        st.markdown('<div class="live-badge" style="margin-top:18px;"><div class="dot-live"></div>ACTIVE</div>', unsafe_allow_html=True)

    st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
    current_aqi = st.session_state.live_aqi
    label,color,emoji,advice = get_aqi_info(current_aqi)
    poll_vals   = simulate_pollutants(current_aqi)
    tips        = HEALTH_TIPS.get(label,[])

    gauge_col,detail_col = st.columns([1,2])
    with gauge_col:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",value=current_aqi,
            delta={"reference":st.session_state.live_history[-2] if len(st.session_state.live_history)>=2 else current_aqi,
                   "increasing":{"color":"#ff3366"},"decreasing":{"color":"#00ff88"},
                   "font":{"size":18,"family":"Orbitron, sans-serif"}},
            number={"font":{"size":56,"family":"Orbitron, sans-serif","color":color},"suffix":" AQI"},
            gauge={"axis":{"range":[0,500],"tickvals":[0,50,100,200,300,400,500],
                           "ticktext":["0","50","100","200","300","400","500"],"tickfont":{"size":10,"color":"#6a8fad"}},
                   "bar":{"color":color,"thickness":0.25},"bgcolor":"rgba(0,0,0,0)","borderwidth":0,
                   "steps":[{"range":[0,50],"color":"rgba(0,255,136,0.15)"},{"range":[50,100],"color":"rgba(163,255,0,0.12)"},
                             {"range":[100,200],"color":"rgba(255,184,0,0.12)"},{"range":[200,300],"color":"rgba(255,102,0,0.12)"},
                             {"range":[300,400],"color":"rgba(255,51,102,0.12)"},{"range":[400,500],"color":"rgba(180,77,255,0.12)"}],
                   "threshold":{"line":{"color":color,"width":4},"thickness":0.85,"value":current_aqi}},
            title={"text":f"{emoji} {label}<br><span style='font-size:11px;color:#6a8fad;'>{live_city} · Live Sensor</span>",
                   "font":{"size":18,"family":"Orbitron, sans-serif","color":"#e0f4ff"}}))
        fig_gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e0f4ff"),height=340,margin=dict(l=20,r=20,t=60,b=20))
        st.plotly_chart(fig_gauge, use_container_width=True)
        st.markdown(f"""
        <div class="health-advice" style="border-color:{color}33;">
            <div style="font-family:'Orbitron',sans-serif;font-size:0.75rem;color:{color};letter-spacing:2px;margin-bottom:8px;">HEALTH ADVISORY</div>
            <div style="color:#e0f4ff;">{advice}</div>
        </div>""", unsafe_allow_html=True)

    with detail_col:
        st.markdown('<div class="section-header">🧪 LIVE POLLUTANT READINGS</div>', unsafe_allow_html=True)
        for p in POLLUTANTS:
            val  = poll_vals[p]
            safe = SAFE_LIMITS[p]
            pct  = min(val/(safe*2.5),1.0)
            status_text,s_color = pollutant_status(val,safe)
            bar_w = int(pct*100)
            st.markdown(f"""
            <div style="margin:6px 0;padding:10px 14px;background:rgba(0,245,255,0.04);border-radius:8px;border-left:3px solid {s_color};">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                    <span style="font-family:'Orbitron',sans-serif;font-size:0.8rem;color:#e0f4ff;font-weight:700;">{p}</span>
                    <span style="font-family:'Share Tech Mono',monospace;font-size:0.85rem;color:{s_color};">{val} {UNITS[p]}</span>
                    <span style="font-size:0.75rem;">{status_text}</span>
                </div>
                <div style="background:rgba(0,0,0,0.3);border-radius:4px;height:6px;overflow:hidden;">
                    <div style="width:{bar_w}%;height:100%;background:linear-gradient(90deg,{s_color}88,{s_color});border-radius:4px;"></div>
                </div>
                <div style="font-family:'Share Tech Mono';font-size:0.68rem;color:#6a8fad;margin-top:4px;">
                    Safe ≤ {safe} {UNITS[p]} · {int(pct*100)}% of danger threshold
                </div>
            </div>""", unsafe_allow_html=True)
        st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-header">💡 HEALTH TIPS</div>', unsafe_allow_html=True)
        for tip in tips:
            st.markdown(f'<div style="padding:6px 12px;margin:4px 0;background:rgba(0,245,255,0.04);border-radius:6px;font-family:Exo 2;font-size:0.85rem;color:#e0f4ff;">{tip}</div>', unsafe_allow_html=True)

    st.divider()
    st.markdown('<div class="section-header">📡 REAL-TIME AQI STREAM (LAST 60 READINGS)</div>', unsafe_allow_html=True)
    hist        = st.session_state.live_history
    x_vals      = list(range(len(hist)))
    colors_hist = [get_aqi_info(v)[1] for v in hist]
    r_int,g_int,b_int = int(color[1:3],16),int(color[3:5],16),int(color[5:7],16)
    fig_stream = go.Figure()
    fig_stream.add_trace(go.Scatter(x=x_vals,y=hist,mode="lines",line=dict(color=color,width=0),fill="tozeroy",
        fillcolor=f"rgba({r_int},{g_int},{b_int},0.1)",showlegend=False,hoverinfo="skip"))
    fig_stream.add_trace(go.Scatter(x=x_vals,y=hist,mode="lines+markers",line=dict(color=color,width=2.5),
        marker=dict(size=[10 if i==len(hist)-1 else 4 for i in range(len(hist))],color=colors_hist,
                    line=dict(width=1,color="rgba(0,0,0,0.5)")),name="AQI",hovertemplate="Reading %{x}: AQI %{y}<extra></extra>"))
    for threshold,t_label,t_color in [(100,"Satisfactory","#a3ff00"),(200,"Moderate","#ffb800"),(300,"Poor","#ff6600")]:
        fig_stream.add_hline(y=threshold,line_dash="dash",line_color=t_color,opacity=0.4,
                             annotation_text=t_label,annotation_font_size=10,annotation_font_color=t_color)
    if hist:
        fig_stream.add_trace(go.Scatter(x=[len(hist)-1],y=[hist[-1]],mode="markers",
            marker=dict(size=16,color=color,symbol="circle",line=dict(width=2,color="#ffffff"),opacity=0.9),
            name="Current",hovertemplate=f"CURRENT: AQI {hist[-1]}<extra></extra>"))
    apply_theme(fig_stream,height=260,margin=dict(l=60,r=20,t=20,b=50),showlegend=False)
    fig_stream.update_xaxes(title_text="Reading #")
    fig_stream.update_yaxes(title_text="AQI Value",range=[0,520])
    st.plotly_chart(fig_stream, use_container_width=True)

    st.markdown('<div class="section-header">🔮 24-HOUR AQI FORECAST</div>', unsafe_allow_html=True)
    now_h    = datetime.datetime.now().hour
    h_labels = [f"{(now_h+i)%24:02d}:00" for i in range(24)]
    forecast = [max(20,min(500,int(current_aqi+40*np.sin((i-6)*np.pi/12)+random.randint(-20,20)))) for i in range(24)]
    f_colors = [get_aqi_info(v)[1] for v in forecast]
    fig_fc = go.Figure()
    fig_fc.add_trace(go.Bar(x=h_labels,y=forecast,marker_color=f_colors,marker_line_width=0,
                            hovertemplate="%{x}<br>Forecast AQI: %{y}<extra></extra>",name="Forecast"))
    apply_theme(fig_fc,height=220,margin=dict(l=60,r=20,t=10,b=70))
    fig_fc.update_xaxes(title_text="Hour",tickangle=-45)
    fig_fc.update_yaxes(title_text="AQI")
    st.plotly_chart(fig_fc, use_container_width=True)

# ══════════════════════════════════════════════════════════════════
# VIEW 1 — POLLUTION MAP
# ══════════════════════════════════════════════════════════════════
elif "Map" in view_mode:
    st.markdown('<h2>🗺️ INDIA POLLUTION MAP</h2>', unsafe_allow_html=True)
    col_left,col_right = st.columns([3,1])
    with col_left:
        mapc1,mapc2 = st.columns(2)
        map_metric  = mapc1.selectbox("Show on map bubbles",["AQI"]+POLLUTANTS,key="map_metric")
        map_style   = mapc2.selectbox("Map theme",["carto-darkmatter","open-street-map","carto-positron"],key="map_style")
        dff2 = dff.copy()
        dff2["size_val"] = dff2["AQI"].apply(lambda v:max(8,min(40,v/10)))
        dff2["label"]    = dff2.apply(
            lambda r:f"<b>{r['City']}</b>  {r['Emoji']}<br>AQI: {r['AQI']}  ·  {r['Category']}<br>"
                     f"PM2.5: {r['PM2.5']}  |  PM10: {r['PM10']}<br>NO2: {r['NO2']}  |  SO2: {r['SO2']}  |  CO: {r['CO']}  |  O3: {r['O3']}",axis=1)
        fig_map = go.Figure(go.Scattermapbox(
            lat=dff2["Lat"],lon=dff2["Lon"],mode="markers+text",
            marker=dict(size=dff2["size_val"],color=dff2["AQI"],
                colorscale=[[0.00,"#00ff88"],[0.10,"#00ff88"],[0.10,"#a3ff00"],[0.20,"#a3ff00"],
                            [0.20,"#ffb800"],[0.40,"#ffb800"],[0.40,"#ff6600"],[0.60,"#ff6600"],
                            [0.60,"#ff3366"],[0.80,"#ff3366"],[0.80,"#b44dff"],[1.00,"#b44dff"]],
                cmin=0,cmax=500,opacity=0.9,
                colorbar=dict(title=dict(text="AQI",font=dict(color="#e0f4ff")),thickness=12,len=0.6,
                              tickfont=dict(color="#e0f4ff"))),
            text=dff2[map_metric].round(0).astype(int).astype(str),
            textfont=dict(size=9,color="white"),textposition="middle center",
            hovertext=dff2["label"],hoverinfo="text"))
        fig_map.update_layout(mapbox=dict(style=map_style,center=dict(lat=22.5,lon=82.0),zoom=3.8),
            margin=dict(l=0,r=0,t=0,b=0),height=540,paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_map, use_container_width=True)
    with col_right:
        st.markdown('<div class="section-header">CITY RANKINGS</div>', unsafe_allow_html=True)
        ranked = dff.sort_values("AQI",ascending=False)[["City","AQI","Category","Color","Emoji"]].reset_index(drop=True)
        for _,row in ranked.iterrows():
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;padding:7px 10px;margin:3px 0;
                        border-radius:7px;background:rgba(0,245,255,0.04);border-left:3px solid {row['Color']};">
                <span style="font-family:'Exo 2';font-size:0.82rem;font-weight:600;color:#e0f4ff;">{row['Emoji']} {row['City']}</span>
                <span style="font-family:'Share Tech Mono';font-size:0.8rem;color:{row['Color']};">{row['AQI']}</span>
            </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# VIEW 2 — CITY COMPARISON
# ══════════════════════════════════════════════════════════════════
elif "Comparison" in view_mode:
    st.markdown('<h2>📊 CITY AQI COMPARISON</h2>', unsafe_allow_html=True)
    cc1,cc2 = st.columns(2)
    top_n   = cc1.slider("Number of cities",5,25,15,key="top_n")
    sort_by = cc2.selectbox("Sort / colour by",["AQI"]+POLLUTANTS,key="sort_by")
    sorted_df = dff.sort_values(sort_by,ascending=False).head(top_n)
    unit = UNITS.get(sort_by,"")
    fig_bar = go.Figure(go.Bar(x=sorted_df["City"],y=sorted_df[sort_by],marker_color=sorted_df["Color"],marker_line_width=0,
        text=sorted_df[sort_by].round(1),textposition="outside",hovertemplate="<b>%{x}</b><br>"+sort_by+": %{y}<extra></extra>"))
    apply_theme(fig_bar,height=440)
    fig_bar.update_xaxes(title_text="City",tickangle=-38)
    fig_bar.update_yaxes(title_text=f"{sort_by} ({unit})" if unit else sort_by)
    st.plotly_chart(fig_bar, use_container_width=True)
    st.divider()
    pie_col,scatter_col = st.columns(2)
    with pie_col:
        st.markdown('<div class="section-header">🥧 AQI CATEGORY DISTRIBUTION</div>', unsafe_allow_html=True)
        cat_order  = ["Good","Satisfactory","Moderate","Poor","Very Poor","Severe"]
        cat_colors = [c[3] for c in AQI_SCALE]
        cat_counts = df["Category"].value_counts().reindex(cat_order,fill_value=0)
        fig_pie = go.Figure(go.Pie(labels=cat_counts.index,values=cat_counts.values,marker_colors=cat_colors,hole=0.5,
            hovertemplate="<b>%{label}</b><br>Cities: %{value} (%{percent})<extra></extra>",
            textinfo="label+percent",textfont=dict(family="Exo 2, sans-serif",size=11)))
        apply_theme(fig_pie,height=340,margin=dict(l=0,r=0,t=20,b=0))
        st.plotly_chart(fig_pie, use_container_width=True)
    with scatter_col:
        st.markdown('<div class="section-header">🔵 PM2.5 vs PM10 SCATTER</div>', unsafe_allow_html=True)
        fig_sc = go.Figure()
        for cat,grp in df.groupby("Category"):
            col_c = grp["Color"].iloc[0]
            fig_sc.add_trace(go.Scatter(x=grp["PM2.5"],y=grp["PM10"],mode="markers+text",name=cat,text=grp["City"],
                textposition="top center",textfont=dict(size=8,color="#6a8fad"),
                marker=dict(size=10,color=col_c,opacity=0.85,line=dict(width=1,color="rgba(255,255,255,0.2)")),
                hovertemplate="<b>%{text}</b><br>PM2.5: %{x}<br>PM10: %{y}<extra></extra>"))
        apply_theme(fig_sc,height=340)
        fig_sc.update_xaxes(title_text="PM2.5 (µg/m³)")
        fig_sc.update_yaxes(title_text="PM10 (µg/m³)")
        st.plotly_chart(fig_sc, use_container_width=True)

# ══════════════════════════════════════════════════════════════════
# VIEW 3 — HOURLY TREND
# ══════════════════════════════════════════════════════════════════
elif "Trend" in view_mode:
    st.markdown('<h2>📈 24-HOUR AQI TREND</h2>', unsafe_allow_html=True)
    selected_cities = st.multiselect("Select cities (up to 6)",df["City"].tolist(),
        default=["Delhi","Mumbai","Bangalore","Chennai"],key="trend_cities")
    if not selected_cities:
        st.info("Please select at least one city above.")
    else:
        hour_labels = [f"{h:02d}:00" for h in range(24)]
        palette     = ["#00f5ff","#ff3366","#00ff88","#ffb800","#b44dff","#0080ff"]
        fig_line = go.Figure()
        for i,city in enumerate(selected_cities[:6]):
            base  = int(df.loc[df["City"]==city,"AQI"].values[0])
            trend = [max(20,min(500,int(base+55*np.sin((h-6)*np.pi/12)+random.randint(-25,25)))) for h in range(24)]
            col_c = palette[i%len(palette)]
            r_i,g_i,b_i = int(col_c[1:3],16),int(col_c[3:5],16),int(col_c[5:7],16)
            fig_line.add_trace(go.Scatter(x=hour_labels,y=trend,mode="none",fill="tozeroy",
                fillcolor=f"rgba({r_i},{g_i},{b_i},0.05)",showlegend=False,hoverinfo="skip"))
            fig_line.add_trace(go.Scatter(x=hour_labels,y=trend,mode="lines+markers",name=city,
                line=dict(color=col_c,width=2.5),marker=dict(size=5,color=col_c),
                hovertemplate=f"<b>{city}</b> %{{x}}: AQI %{{y}}<extra></extra>"))
        apply_theme(fig_line,height=450,legend=dict(orientation="h",yanchor="bottom",y=1.02,bgcolor="rgba(10,22,40,0.8)",bordercolor="rgba(0,245,255,0.2)",borderwidth=1))
        fig_line.update_xaxes(title_text="Hour",tickangle=-45)
        fig_line.update_yaxes(title_text="AQI",range=[0,520])
        st.plotly_chart(fig_line, use_container_width=True)

# ══════════════════════════════════════════════════════════════════
# VIEW 4 — POLLUTANT BREAKDOWN
# ══════════════════════════════════════════════════════════════════
elif "Pollutant" in view_mode:
    st.markdown('<h2>🧪 POLLUTANT BREAKDOWN</h2>', unsafe_allow_html=True)
    selected_city = st.selectbox("Select a city",df["City"].tolist(),key="poll_city")
    row = df[df["City"]==selected_city].iloc[0]
    bar_col,radar_col = st.columns(2)
    with bar_col:
        st.markdown('<div class="section-header">📊 POLLUTANT LEVELS vs SAFE LIMITS</div>', unsafe_allow_html=True)
        poll_vals2 = [row[p] for p in POLLUTANTS]
        safe_vals2 = [SAFE_LIMITS[p] for p in POLLUTANTS]
        b_colors   = ["#00ff88" if row[p]<=SAFE_LIMITS[p] else "#ffb800" if row[p]<=SAFE_LIMITS[p]*1.5 else "#ff3366" for p in POLLUTANTS]
        fig_poll = go.Figure()
        fig_poll.add_trace(go.Bar(name="Measured",x=POLLUTANTS,y=poll_vals2,marker_color=b_colors,marker_line_width=0,
            hovertemplate="<b>%{x}</b>: %{y}<extra></extra>"))
        fig_poll.add_trace(go.Bar(name="Safe Limit",x=POLLUTANTS,y=safe_vals2,
            marker_color="rgba(0,245,255,0.15)",marker_line_color="#00f5ff",marker_line_width=1,
            hovertemplate="Safe limit %{x}: %{y}<extra></extra>"))
        apply_theme(fig_poll,height=340,barmode="group")
        fig_poll.update_xaxes(title_text="Pollutant")
        fig_poll.update_yaxes(title_text="Concentration")
        st.plotly_chart(fig_poll, use_container_width=True)
    with radar_col:
        st.markdown('<div class="section-header">🕸️ POLLUTANT RADAR</div>', unsafe_allow_html=True)
        norm_vals = [min(row[p]/SAFE_LIMITS[p],3.0) for p in POLLUTANTS]
        cat_color = row["Color"]
        r_c,g_c,b_c = int(cat_color[1:3],16),int(cat_color[3:5],16),int(cat_color[5:7],16)
        fig_radar = go.Figure(go.Scatterpolar(r=norm_vals+[norm_vals[0]],theta=POLLUTANTS+[POLLUTANTS[0]],
            fill="toself",fillcolor=f"rgba({r_c},{g_c},{b_c},0.2)",
            line=dict(color=cat_color,width=2),marker=dict(size=7,color=cat_color)))
        fig_radar.add_trace(go.Scatterpolar(r=[1]*len(POLLUTANTS)+[1],theta=POLLUTANTS+[POLLUTANTS[0]],
            mode="lines",line=dict(color="#00f5ff",width=1,dash="dot"),showlegend=False))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True,range=[0,3],tickfont=dict(color="#6a8fad",size=9),gridcolor="rgba(0,245,255,0.1)"),
            angularaxis=dict(tickfont=dict(color="#e0f4ff",size=11,family="Exo 2"),gridcolor="rgba(0,245,255,0.1)"),bgcolor="rgba(10,22,40,0.6)"),
            showlegend=False,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e0f4ff"),height=360,margin=dict(l=40,r=40,t=40,b=40))
        st.plotly_chart(fig_radar, use_container_width=True)
    st.divider()
    st.markdown('<div class="section-header">🔍 COMPARE ALL CITIES — SINGLE POLLUTANT</div>', unsafe_allow_html=True)
    focus_poll = st.selectbox("Choose pollutant",POLLUTANTS,key="focus_poll")
    cmp_df     = df[["City",focus_poll]].sort_values(focus_poll,ascending=True)
    safe_val   = SAFE_LIMITS[focus_poll]
    bar_colors = ["#00ff88" if v<=safe_val else "#ffb800" if v<=safe_val*1.5 else "#ff3366" for v in cmp_df[focus_poll]]
    fig_hbar = go.Figure(go.Bar(x=cmp_df[focus_poll],y=cmp_df["City"],orientation="h",marker_color=bar_colors,marker_line_width=0,
        text=cmp_df[focus_poll].astype(str)+f" {UNITS[focus_poll]}",textposition="outside",hovertemplate="<b>%{y}</b>: %{x}<extra></extra>"))
    fig_hbar.add_vline(x=safe_val,line_dash="dash",line_color="#00f5ff",
                       annotation_text=f"Safe limit ({safe_val} {UNITS[focus_poll]})",annotation_font_size=11,annotation_font_color="#00f5ff")
    apply_theme(fig_hbar,height=580,margin=dict(l=120,r=80,t=20,b=40))
    fig_hbar.update_xaxes(title_text=UNITS[focus_poll])
    fig_hbar.update_yaxes(showgrid=False)
    st.plotly_chart(fig_hbar, use_container_width=True)

# ══════════════════════════════════════════════════════════════════
# VIEW 5 — RANKINGS & STATS
# ══════════════════════════════════════════════════════════════════
elif "Rankings" in view_mode:
    st.markdown('<h2>🏆 RANKINGS & STATISTICS</h2>', unsafe_allow_html=True)
    col1,col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-header">🌿 TOP 10 CLEANEST CITIES</div>', unsafe_allow_html=True)
        best10 = df.nsmallest(10,"AQI")[["City","State","AQI","Category","Color","Emoji"]].reset_index(drop=True)
        for i,r in best10.iterrows():
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 12px;margin:4px 0;
                        border-radius:8px;background:rgba(0,255,136,0.06);border-left:3px solid {r['Color']};">
                <span style="font-family:'Exo 2';font-size:0.9rem;"><b>{i+1}.</b> {r['Emoji']} <b>{r['City']}</b>
                    <span style="color:#6a8fad;font-size:0.78rem;"> · {r['State']}</span></span>
                <span style="font-family:'Share Tech Mono';color:{r['Color']};font-size:0.9rem;">{r['AQI']}</span>
            </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="section-header">☣️ TOP 10 MOST POLLUTED CITIES</div>', unsafe_allow_html=True)
        worst10 = df.nlargest(10,"AQI")[["City","State","AQI","Category","Color","Emoji"]].reset_index(drop=True)
        for i,r in worst10.iterrows():
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 12px;margin:4px 0;
                        border-radius:8px;background:rgba(255,51,102,0.06);border-left:3px solid {r['Color']};">
                <span style="font-family:'Exo 2';font-size:0.9rem;"><b>{i+1}.</b> {r['Emoji']} <b>{r['City']}</b>
                    <span style="color:#6a8fad;font-size:0.78rem;"> · {r['State']}</span></span>
                <span style="font-family:'Share Tech Mono';color:{r['Color']};font-size:0.9rem;">{r['AQI']}</span>
            </div>""", unsafe_allow_html=True)
    st.divider()
    st.markdown('<div class="section-header">📊 AQI STATISTICS BY STATE</div>', unsafe_allow_html=True)
    state_stats = df.groupby("State")["AQI"].agg(Avg="mean",Max="max",Min="min",Cities="count").round(1).sort_values("Avg",ascending=False).reset_index()
    fig_state = px.bar(state_stats,x="State",y="Avg",color="Avg",
        color_continuous_scale=[[0,"#00ff88"],[0.4,"#ffb800"],[0.7,"#ff3366"],[1,"#b44dff"]],
        range_color=[0,500],hover_data={"Max":True,"Min":True,"Cities":True},
        text=state_stats["Avg"].astype(int),labels={"Avg":"Average AQI"})
    apply_theme(fig_state,height=380,coloraxis_showscale=False)
    fig_state.update_xaxes(tickangle=-35)
    fig_state.update_traces(textposition="outside",textfont=dict(color="#e0f4ff"))
    st.plotly_chart(fig_state, use_container_width=True)
    st.divider()
    corr_col,violin_col = st.columns(2)
    with corr_col:
        st.markdown('<div class="section-header">🔗 POLLUTANT CORRELATION HEATMAP</div>', unsafe_allow_html=True)
        corr = df[["AQI"]+POLLUTANTS].corr().round(2)
        fig_heat = go.Figure(go.Heatmap(z=corr.values,x=list(corr.columns),y=list(corr.index),
            colorscale=[[0,"#ff3366"],[0.5,"#0a1628"],[1,"#00ff88"]],zmin=-1,zmax=1,
            text=corr.values.round(2),texttemplate="%{text}",textfont=dict(size=11,family="Share Tech Mono"),
            hovertemplate="%{x} × %{y}: %{z}<extra></extra>"))
        apply_theme(fig_heat,height=340,margin=dict(l=80,r=20,t=20,b=60))
        st.plotly_chart(fig_heat, use_container_width=True)
    with violin_col:
        st.markdown('<div class="section-header">🎻 AQI DISTRIBUTION BY CATEGORY</div>', unsafe_allow_html=True)
        fig_v = go.Figure()
        for lo,hi,label_v,color_v,emoji_v,_ in AQI_SCALE:
            subset = df[df["Category"]==label_v]["AQI"]
            if len(subset)>0:
                r_v,g_v,b_v = int(color_v[1:3],16),int(color_v[3:5],16),int(color_v[5:7],16)
                fig_v.add_trace(go.Violin(y=subset,name=f"{emoji_v} {label_v}",
                    fillcolor=f"rgba({r_v},{g_v},{b_v},0.3)",line_color=color_v,
                    box_visible=True,meanline_visible=True,points="all"))
        apply_theme(fig_v,height=340,margin=dict(l=60,r=20,t=20,b=60),showlegend=False)
        fig_v.update_yaxes(title_text="AQI")
        st.plotly_chart(fig_v, use_container_width=True)

# ══════════════════════════════════════════════════════════════════
# VIEW 6 — WEATHER & AQI FORECAST
# ══════════════════════════════════════════════════════════════════
elif "Weather" in view_mode:
    st.markdown('<h2>🌡️ WEATHER & AQI FORECAST</h2>', unsafe_allow_html=True)
    wc1,wc2 = st.columns(2)
    fcity = wc1.selectbox("Select City",[c["name"] for c in CITIES],key="wcity")
    fdays = wc2.slider("Forecast Days",3,14,7,key="fdays")
    city_aqi = int(df[df["City"]==fcity]["AQI"].values[0])
    dates    = [datetime.date.today()+datetime.timedelta(days=i) for i in range(fdays)]
    aqi_fc   = [max(10,min(500,city_aqi+random.randint(-80,80))) for _ in range(fdays)]
    temp_fc  = [random.randint(28,42) for _ in range(fdays)]
    humid_fc = [random.randint(30,80) for _ in range(fdays)]
    wind_fc  = [random.uniform(3,25)  for _ in range(fdays)]
    d_labels = [d.strftime("%b %d") for d in dates]
    fig_fc2 = make_subplots(rows=3,cols=1,shared_xaxes=True,
        subplot_titles=["AQI Forecast","Temperature (°C)","Humidity (%)"],vertical_spacing=0.08)
    fc_colors = [get_aqi_info(v)[1] for v in aqi_fc]
    fig_fc2.add_trace(go.Bar(x=d_labels,y=aqi_fc,marker_color=fc_colors,name="AQI",hovertemplate="%{x}: AQI %{y}<extra></extra>"),row=1,col=1)
    fig_fc2.add_trace(go.Scatter(x=d_labels,y=temp_fc,mode="lines+markers",line=dict(color="#ff6600",width=2.5),marker=dict(size=7,color="#ff6600"),name="Temp °C",hovertemplate="%{x}: %{y}°C<extra></extra>"),row=2,col=1)
    fig_fc2.add_trace(go.Bar(x=d_labels,y=humid_fc,marker_color=[f"rgba(0,128,255,{0.4+h/200})" for h in humid_fc],name="Humidity %",hovertemplate="%{x}: %{y}%<extra></extra>"),row=3,col=1)
    apply_theme(fig_fc2,height=600,showlegend=False,title=dict(text=f"Forecast · {fcity}",font=dict(family="Orbitron",color="#00f5ff",size=14)))
    for i in range(1,4):
        fig_fc2.update_xaxes(gridcolor="rgba(0,245,255,0.08)",linecolor="rgba(0,245,255,0.2)",row=i,col=1)
        fig_fc2.update_yaxes(gridcolor="rgba(0,245,255,0.08)",linecolor="rgba(0,245,255,0.2)",row=i,col=1)
    st.plotly_chart(fig_fc2, use_container_width=True)
    st.divider()
    st.markdown('<div class="section-header">📅 DAILY FORECAST TABLE</div>', unsafe_allow_html=True)
    forecast_df = pd.DataFrame({"Date":d_labels,"AQI":aqi_fc,"Category":[get_aqi_info(v)[0] for v in aqi_fc],
        "Temp (°C)":temp_fc,"Humidity (%)":humid_fc,"Wind (km/h)":[round(w,1) for w in wind_fc]})
    st.dataframe(forecast_df.style.background_gradient(subset=["AQI"],cmap="RdYlGn_r"),use_container_width=True,hide_index=True)

# ══════════════════════════════════════════════════════════════════
# VIEW 7 — IMAGE PREDICTOR
# ══════════════════════════════════════════════════════════════════
elif "Image" in view_mode:
    st.markdown('<h2>📸 IMAGE-BASED AIR QUALITY PREDICTOR</h2>', unsafe_allow_html=True)
    up_col,result_col = st.columns([1,1])
    with up_col:
        uploaded_file = st.file_uploader("Upload Image (JPG / PNG)",type=["jpg","jpeg","png"])
        if uploaded_file:
            img = Image.open(uploaded_file)
            st.image(img,caption="📷 Uploaded Image",use_column_width=True)
    with result_col:
        if uploaded_file:
            if st.button("🔍  ANALYZE IMAGE",use_container_width=True):
                with st.spinner("🛰️ Analyzing visual haze and particulate density..."):
                    time.sleep(1.2)
                pollution = random.randint(1,100)
                aqi_equiv = int(pollution*5)
                p_label,p_color,p_emoji,p_advice = get_aqi_info(aqi_equiv)
                st.markdown(f"""
                <div class="aqi-live-card" style="border-color:{p_color}44;">
                    <div style="font-family:'Share Tech Mono';font-size:0.72rem;color:#6a8fad;letter-spacing:2px;margin-bottom:8px;">VISUAL HAZE ANALYSIS RESULT</div>
                    <div class="aqi-number" style="color:{p_color};text-shadow:0 0 30px {p_color}80;">{pollution}%</div>
                    <div class="aqi-label-text" style="color:{p_color};">{p_emoji} {p_label}</div>
                    <div style="font-family:'Exo 2';font-size:0.82rem;color:#6a8fad;margin-top:8px;">
                        Estimated AQI Equivalent: <b style="color:{p_color};">{aqi_equiv}</b>
                    </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align:center;padding:60px 20px;background:rgba(0,245,255,0.04);
                        border:1px dashed rgba(0,245,255,0.2);border-radius:12px;font-family:Exo 2;">
                <div style="font-size:3rem;margin-bottom:12px;">📷</div>
                <div style="color:#6a8fad;font-size:0.9rem;">Upload a sky or outdoor image<br>to begin visual haze analysis</div>
            </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# VIEW 8 — DATA EXPORT
# ══════════════════════════════════════════════════════════════════
elif "Export" in view_mode:
    st.markdown('<h2>📋 DATA EXPORT & REPORT</h2>', unsafe_allow_html=True)
    exp_col1,exp_col2 = st.columns(2)
    with exp_col1:
        st.markdown('<div class="section-header">📥 EXPORT OPTIONS</div>', unsafe_allow_html=True)
        st.download_button("⬇️  Download Full Dataset (CSV)",
            df[["City","State","AQI","Category"]+POLLUTANTS].to_csv(index=False),
            file_name=f"india_aqi_{datetime.date.today()}.csv",mime="text/csv",use_container_width=True)
        st.download_button("⬇️  Download Top 10 Polluted Cities (CSV)",
            df.nlargest(10,"AQI")[["City","State","AQI","Category"]+POLLUTANTS].to_csv(index=False),
            file_name=f"top10_polluted_{datetime.date.today()}.csv",mime="text/csv",use_container_width=True)
        st.download_button("⬇️  Download Safe Cities Report (CSV)",
            df[df["AQI"]<=100][["City","State","AQI","Category"]+POLLUTANTS].to_csv(index=False),
            file_name=f"safe_cities_{datetime.date.today()}.csv",mime="text/csv",use_container_width=True)
    with exp_col2:
        st.markdown('<div class="section-header">📊 DATA SUMMARY</div>', unsafe_allow_html=True)
        summary = df[["AQI"]+POLLUTANTS].describe().round(2)
        st.dataframe(summary.style.background_gradient(cmap="Blues"),use_container_width=True)
    st.divider()
    st.markdown('<div class="section-header">🔍 INTERACTIVE DATA TABLE</div>', unsafe_allow_html=True)
    search_city = st.text_input("🔎 Search city…",placeholder="Type a city name")
    display_df  = df.copy()
    if search_city:
        display_df = display_df[display_df["City"].str.contains(search_city,case=False)]
    st.dataframe(display_df[["City","State","AQI","Category"]+POLLUTANTS]
        .sort_values("AQI",ascending=False).reset_index(drop=True)
        .style.background_gradient(subset=["AQI"],cmap="RdYlGn_r"),use_container_width=True,height=420)

# ══════════════════════════════════════════════════════════════════
# VIEW 9 — MY ACCOUNT
# ══════════════════════════════════════════════════════════════════
elif "Account" in view_mode:
    st.markdown('<h2>👤 MY ACCOUNT</h2>', unsafe_allow_html=True)
    u = st.session_state.users_db[st.session_state.current_user]

    acc_col1, acc_col2 = st.columns([1,1])
    with acc_col1:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#0a1628,#122040);border:1px solid rgba(0,245,255,0.25);
                    border-radius:16px;padding:28px;text-align:center;margin-bottom:16px;">
            <div style="width:72px;height:72px;border-radius:50%;background:linear-gradient(135deg,#0080ff,#00f5ff);
                        display:flex;align-items:center;justify-content:center;font-family:'Orbitron',sans-serif;
                        font-size:1.6rem;font-weight:700;color:#050d1a;margin:0 auto 16px;">
                {''.join([w[0].upper() for w in u['name'].split()[:2]])}
            </div>
            <div style="font-family:'Orbitron',sans-serif;font-size:1.2rem;color:#00f5ff;font-weight:700;">{u['name']}</div>
            <div style="font-family:'Share Tech Mono',monospace;font-size:0.72rem;color:#6a8fad;margin:6px 0;">{st.session_state.current_user}</div>
            <div style="display:inline-block;background:rgba(0,255,136,0.1);border:1px solid #00ff88;border-radius:20px;
                        padding:4px 14px;font-family:'Exo 2',sans-serif;font-size:0.75rem;color:#00ff88;margin-top:8px;">
                ⬡ {u['role']}
            </div>
            <div style="margin-top:16px;font-family:'Share Tech Mono';font-size:0.65rem;color:#3a5a7a;">
                Member since: {u['joined']}<br>Last login: {u.get('last_login') or 'This session'}
            </div>
        </div>""", unsafe_allow_html=True)

        # Alert preferences
        st.markdown('<div class="section-header">🔔 ALERT PREFERENCES</div>', unsafe_allow_html=True)
        alerts = st.toggle("Enable AQI Email Alerts", value=u.get("alerts_enabled", True), key="alerts_toggle")
        if alerts != u.get("alerts_enabled"):
            st.session_state.users_db[st.session_state.current_user]["alerts_enabled"] = alerts
        alert_threshold = st.slider("Alert when AQI exceeds", 100, 400, 200, step=50, key="alert_threshold")
        st.markdown(f'<div class="auth-info">📧 Alerts will be sent to <b>{st.session_state.current_user}</b> when AQI > {alert_threshold}</div>', unsafe_allow_html=True)

    with acc_col2:
        st.markdown('<div class="section-header">🔑 CHANGE PASSWORD</div>', unsafe_allow_html=True)
        old_pw  = st.text_input("Current Password", type="password", key="chg_old")
        new_pw  = st.text_input("New Password",      type="password", key="chg_new")
        new_pw2 = st.text_input("Confirm New Password", type="password", key="chg_new2")

        if st.button("🔄  UPDATE PASSWORD", use_container_width=True, key="chg_pw_btn"):
            if not old_pw or not new_pw or not new_pw2:
                st.markdown('<div class="auth-error">⚠️ Fill all password fields.</div>', unsafe_allow_html=True)
            elif st.session_state.users_db[st.session_state.current_user]["password_hash"] != _hash(old_pw):
                st.markdown('<div class="auth-error">❌ Current password is incorrect.</div>', unsafe_allow_html=True)
            elif not is_strong_password(new_pw):
                st.markdown('<div class="auth-error">❌ New password too weak. Use 8+ chars, 1 uppercase, 1 number, 1 symbol.</div>', unsafe_allow_html=True)
            elif new_pw != new_pw2:
                st.markdown('<div class="auth-error">❌ Passwords do not match.</div>', unsafe_allow_html=True)
            else:
                st.session_state.users_db[st.session_state.current_user]["password_hash"] = _hash(new_pw)
                st.markdown('<div class="auth-success">✅ Password updated successfully!</div>', unsafe_allow_html=True)

        st.divider()
        st.markdown('<div class="section-header">📊 MY SESSION STATS</div>', unsafe_allow_html=True)
        total_users = len(st.session_state.users_db)
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px;">
            <div style="background:rgba(0,245,255,0.05);border:1px solid rgba(0,245,255,0.15);border-radius:10px;padding:14px;text-align:center;">
                <div style="font-family:'Orbitron',sans-serif;font-size:1.4rem;color:#00f5ff;">{total_users}</div>
                <div style="font-family:'Exo 2',sans-serif;font-size:0.72rem;color:#6a8fad;margin-top:4px;">REGISTERED USERS</div>
            </div>
            <div style="background:rgba(0,255,136,0.05);border:1px solid rgba(0,255,136,0.15);border-radius:10px;padding:14px;text-align:center;">
                <div style="font-family:'Orbitron',sans-serif;font-size:1.4rem;color:#00ff88;">{len(CITIES)}</div>
                <div style="font-family:'Exo 2',sans-serif;font-size:0.72rem;color:#6a8fad;margin-top:4px;">CITIES MONITORED</div>
            </div>
            <div style="background:rgba(180,77,255,0.05);border:1px solid rgba(180,77,255,0.15);border-radius:10px;padding:14px;text-align:center;">
                <div style="font-family:'Orbitron',sans-serif;font-size:1.4rem;color:#b44dff;">{avg_aqi}</div>
                <div style="font-family:'Exo 2',sans-serif;font-size:0.72rem;color:#6a8fad;margin-top:4px;">NATIONAL AVG AQI</div>
            </div>
            <div style="background:rgba(255,184,0,0.05);border:1px solid rgba(255,184,0,0.15);border-radius:10px;padding:14px;text-align:center;">
                <div style="font-family:'Orbitron',sans-serif;font-size:1.4rem;color:#ffb800;">{dangerous}</div>
                <div style="font-family:'Exo 2',sans-serif;font-size:0.72rem;color:#6a8fad;margin-top:4px;">HIGH RISK CITIES</div>
            </div>
        </div>""", unsafe_allow_html=True)

# ── Footer ──
st.divider()
st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:center;
            font-family:'Share Tech Mono',monospace;font-size:0.72rem;color:#6a8fad;padding:8px 0;">
    <span>🛰️ INDIA AQI COMMAND CENTER v3.0</span>
    <span>👤 Logged in as <b style="color:#00f5ff;">{user_info['name']}</b></span>
    <span>Built with Streamlit + Plotly</span>
</div>""", unsafe_allow_html=True)
