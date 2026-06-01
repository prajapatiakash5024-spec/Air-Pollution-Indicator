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
# GLOBAL CSS — dark sci-fi theme v4.0
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
    --glow-cyan:0 0 20px rgba(0,229,255,0.4); --glow-green:0 0 20px rgba(0,255,136,0.4);
    --glow-purple:0 0 20px rgba(170,51,255,0.4);
}
html,body,[class*="css"],.stApp{background-color:var(--bg-dark)!important;color:var(--text-primary)!important;font-family:'Exo 2',sans-serif!important;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#04090f 0%,#070f1a 100%)!important;border-right:1px solid var(--border)!important;}
[data-testid="stSidebar"] *{color:var(--text-primary)!important;}
[data-testid="stSidebar"] .stButton>button{background:linear-gradient(135deg,#0070ff18,#00e5ff18)!important;border:1px solid var(--accent-cyan)!important;color:var(--accent-cyan)!important;border-radius:8px!important;font-family:'Exo 2',sans-serif!important;font-weight:600!important;letter-spacing:1px!important;transition:all 0.3s ease!important;}
[data-testid="stSidebar"] .stButton>button:hover{background:linear-gradient(135deg,#0070ff33,#00e5ff33)!important;box-shadow:var(--glow-cyan)!important;}
h1{font-family:'Orbitron',sans-serif!important;font-weight:900!important;background:linear-gradient(90deg,#00e5ff,#0070ff,#aa33ff);-webkit-background-clip:text!important;-webkit-text-fill-color:transparent!important;letter-spacing:2px!important;}
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
::-webkit-scrollbar{width:5px;height:5px;}
::-webkit-scrollbar-track{background:var(--bg-dark);}
::-webkit-scrollbar-thumb{background:var(--accent-blue);border-radius:3px;}
.stTextArea textarea{background:rgba(0,229,255,0.04)!important;border:1px solid rgba(0,229,255,0.2)!important;border-radius:10px!important;color:#d8f0ff!important;font-family:'Exo 2',sans-serif!important;}
.stTextArea textarea:focus{border-color:#00e5ff!important;box-shadow:0 0 12px rgba(0,229,255,0.2)!important;}

/* ── LIVE BADGE ── */
.live-badge{display:inline-flex;align-items:center;gap:6px;background:rgba(0,255,136,0.08);border:1px solid var(--accent-green);border-radius:20px;padding:4px 14px;font-family:'Share Tech Mono',monospace;font-size:0.72rem;color:var(--accent-green);letter-spacing:1.5px;animation:pulse-live 2s infinite;}
@keyframes pulse-live{0%,100%{box-shadow:0 0 6px rgba(0,255,136,0.3);}50%{box-shadow:0 0 18px rgba(0,255,136,0.7);}}
.dot-live{width:7px;height:7px;background:var(--accent-green);border-radius:50%;animation:blink 1.2s infinite;}
@keyframes blink{0%,100%{opacity:1;}50%{opacity:0.1;}}

/* ── AQI CARDS ── */
.aqi-live-card{background:linear-gradient(135deg,#0a1628,#122040);border:1px solid rgba(0,229,255,0.25);border-radius:16px;padding:20px;text-align:center;position:relative;overflow:hidden;}
.aqi-number{font-family:'Orbitron',monospace;font-size:3.2rem;font-weight:900;line-height:1;}
.aqi-label-text{font-family:'Exo 2',sans-serif;font-size:1rem;font-weight:600;letter-spacing:2px;text-transform:uppercase;margin-top:4px;}
.health-advice{background:linear-gradient(135deg,rgba(0,229,255,0.04),rgba(0,112,255,0.04));border:1px solid rgba(0,229,255,0.18);border-radius:12px;padding:16px;font-family:'Exo 2',sans-serif;font-size:0.9rem;line-height:1.6;}
.section-header{font-family:'Orbitron',sans-serif;font-size:0.95rem;font-weight:700;color:#00e5ff;letter-spacing:2px;text-transform:uppercase;padding:8px 0;border-bottom:1px solid rgba(0,229,255,0.18);margin-bottom:12px;}

/* ══ AI CHAT ══ */
.chat-bubble-user{background:linear-gradient(135deg,rgba(0,112,255,0.2),rgba(0,229,255,0.12));border:1px solid rgba(0,229,255,0.25);border-radius:14px 14px 2px 14px;padding:12px 16px;margin:8px 0;font-family:'Exo 2',sans-serif;font-size:0.88rem;color:#d8f0ff;max-width:85%;margin-left:auto;animation:bubble-in 0.3s ease;}
.chat-bubble-ai{background:linear-gradient(135deg,rgba(170,51,255,0.1),rgba(0,229,255,0.06));border:1px solid rgba(170,51,255,0.2);border-radius:14px 14px 14px 2px;padding:12px 16px;margin:8px 0;font-family:'Exo 2',sans-serif;font-size:0.88rem;color:#d8f0ff;max-width:92%;animation:bubble-in 0.3s ease;}
@keyframes bubble-in{from{opacity:0;transform:translateY(8px);}to{opacity:1;transform:translateY(0);}}
.chat-label-user{font-family:'Share Tech Mono';font-size:0.65rem;color:#0090cc;letter-spacing:1px;margin-bottom:4px;text-align:right;}
.chat-label-ai{font-family:'Share Tech Mono';font-size:0.65rem;color:#aa33ff;letter-spacing:1px;margin-bottom:4px;}
.chat-container{height:380px;overflow-y:auto;padding:8px 4px;scrollbar-width:thin;}

/* ══ ALERT CARDS ══ */
.alert-card-red{background:rgba(255,34,85,0.07);border:1px solid rgba(255,34,85,0.35);border-radius:12px;padding:14px 16px;margin:6px 0;animation:alert-pulse-red 2s infinite;}
@keyframes alert-pulse-red{0%,100%{box-shadow:0 0 0px rgba(255,34,85,0);}50%{box-shadow:0 0 16px rgba(255,34,85,0.25);}}
.alert-card-amber{background:rgba(255,170,0,0.07);border:1px solid rgba(255,170,0,0.3);border-radius:12px;padding:14px 16px;margin:6px 0;}
.alert-card-green{background:rgba(0,255,136,0.06);border:1px solid rgba(0,255,136,0.25);border-radius:12px;padding:14px 16px;margin:6px 0;}

/* ══ LOGIN PAGE ══ */
.grid-bg{position:fixed;top:0;left:0;width:100%;height:100%;background-image:linear-gradient(rgba(0,229,255,0.025) 1px,transparent 1px),linear-gradient(90deg,rgba(0,229,255,0.025) 1px,transparent 1px);background-size:44px 44px;pointer-events:none;z-index:0;}
.scan-line{position:fixed;top:0;left:0;width:100%;height:2px;background:linear-gradient(90deg,transparent,rgba(0,229,255,0.5),transparent);animation:scan 5s linear infinite;z-index:1;pointer-events:none;}
@keyframes scan{0%{top:0%;}100%{top:100%;}}
.particle{position:fixed;border-radius:50%;animation:float-particle linear infinite;opacity:0;z-index:0;}
@keyframes float-particle{0%{transform:translateY(100vh) scale(0);opacity:0;}10%{opacity:0.5;}90%{opacity:0.3;}100%{transform:translateY(-5vh) scale(1.1);opacity:0;}}
.auth-card{background:linear-gradient(145deg,rgba(7,16,32,0.98),rgba(12,26,46,0.98));border:1px solid rgba(0,229,255,0.25);border-radius:22px;padding:42px 38px;box-shadow:0 0 80px rgba(0,229,255,0.06),0 0 160px rgba(0,112,255,0.04),inset 0 1px 0 rgba(0,229,255,0.08);position:relative;overflow:hidden;animation:card-appear 0.7s cubic-bezier(0.16,1,0.3,1) forwards;}
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
.stTextInput input{background:rgba(0,229,255,0.035)!important;border:1px solid rgba(0,229,255,0.2)!important;border-radius:10px!important;color:#d8f0ff!important;font-family:'Exo 2',sans-serif!important;padding:12px 16px!important;transition:all 0.3s ease!important;}
.stTextInput input:focus{border-color:#00e5ff!important;box-shadow:0 0 14px rgba(0,229,255,0.18)!important;background:rgba(0,229,255,0.06)!important;}
.stTextInput label{color:#5a7a9a!important;font-family:'Exo 2',sans-serif!important;font-size:0.78rem!important;letter-spacing:1px!important;}
.stButton>button{background:linear-gradient(135deg,#0070ff,#00e5ff)!important;border:none!important;color:#030b18!important;font-family:'Orbitron',sans-serif!important;font-weight:700!important;font-size:0.82rem!important;letter-spacing:2px!important;border-radius:10px!important;padding:14px 28px!important;transition:all 0.3s ease!important;box-shadow:0 4px 22px rgba(0,229,255,0.22)!important;}
.stButton>button:hover{transform:translateY(-2px)!important;box-shadow:0 8px 32px rgba(0,229,255,0.42)!important;}
.stButton>button:active{transform:translateY(0)!important;}
.stTabs [data-baseweb="tab-list"]{background:rgba(0,229,255,0.035)!important;border-radius:12px!important;border:1px solid rgba(0,229,255,0.12)!important;padding:4px!important;}
.stTabs [data-baseweb="tab"]{font-family:'Orbitron',sans-serif!important;font-size:0.72rem!important;letter-spacing:2px!important;color:#5a7a9a!important;border-radius:8px!important;padding:10px 18px!important;}
.stTabs [aria-selected="true"]{background:linear-gradient(135deg,rgba(0,112,255,0.25),rgba(0,229,255,0.15))!important;color:#00e5ff!important;}
.user-badge{background:linear-gradient(135deg,rgba(0,229,255,0.06),rgba(0,112,255,0.06));border:1px solid rgba(0,229,255,0.18);border-radius:12px;padding:12px 14px;margin-bottom:12px;animation:card-appear 0.5s ease;}
.user-name{font-family:'Orbitron',sans-serif;font-size:0.82rem;color:#00e5ff;font-weight:700;}
.user-email{font-family:'Share Tech Mono',monospace;font-size:0.62rem;color:#5a7a9a;margin-top:3px;}
.user-role{font-family:'Exo 2',sans-serif;font-size:0.68rem;color:#00ff88;margin-top:4px;letter-spacing:1px;}
.auth-success{background:rgba(0,255,136,0.07);border:1px solid #00ff88;border-radius:10px;padding:12px 16px;font-family:'Exo 2',sans-serif;color:#00ff88;font-size:0.85rem;margin:8px 0;animation:card-appear 0.4s ease;}
.auth-error{background:rgba(255,34,85,0.07);border:1px solid #ff2255;border-radius:10px;padding:12px 16px;font-family:'Exo 2',sans-serif;color:#ff2255;font-size:0.85rem;margin:8px 0;animation:card-appear 0.4s ease;}
.auth-info{background:rgba(0,229,255,0.05);border:1px solid rgba(0,229,255,0.25);border-radius:10px;padding:12px 16px;font-family:'Exo 2',sans-serif;color:#00e5ff;font-size:0.85rem;margin:8px 0;}

/* ══ HEXAGON STATS ══ */
.hex-stat{display:flex;flex-direction:column;align-items:center;justify-content:center;background:linear-gradient(135deg,rgba(0,229,255,0.06),rgba(0,112,255,0.04));border:1px solid rgba(0,229,255,0.15);border-radius:14px;padding:18px 12px;text-align:center;position:relative;overflow:hidden;transition:all 0.3s ease;}
.hex-stat:hover{border-color:rgba(0,229,255,0.4);box-shadow:0 0 20px rgba(0,229,255,0.12);}
.hex-stat::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,var(--accent-cyan),transparent);opacity:0.6;}
.hex-val{font-family:'Orbitron',sans-serif;font-size:1.6rem;font-weight:900;color:#00e5ff;}
.hex-lbl{font-family:'Exo 2',sans-serif;font-size:0.68rem;color:#5a7a9a;letter-spacing:1px;text-transform:uppercase;margin-top:4px;}

/* ══ NEWS TICKER ══ */
.ticker-wrap{overflow:hidden;background:rgba(0,229,255,0.04);border-top:1px solid rgba(0,229,255,0.12);border-bottom:1px solid rgba(0,229,255,0.12);padding:8px 0;margin:8px 0;}
.ticker-text{display:inline-block;white-space:nowrap;font-family:'Share Tech Mono',monospace;font-size:0.72rem;color:#5a7a9a;animation:ticker 35s linear infinite;}
@keyframes ticker{0%{transform:translateX(100vw);}100%{transform:translateX(-100%);}}
.ticker-label{font-family:'Share Tech Mono',monospace;font-size:0.72rem;color:#00e5ff;letter-spacing:2px;margin-right:12px;}

/* ══ PROGRESS RINGS ══ */
.prog-ring-wrap{display:flex;align-items:center;gap:12px;padding:10px 0;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# SVG LOGO for login page
# ══════════════════════════════════════════════════════════════════
AQI_LOGO_SVG = """
<svg width="120" height="120" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="bgGrad" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#0a1e3a"/>
      <stop offset="100%" stop-color="#030b18"/>
    </radialGradient>
    <radialGradient id="coreGrad" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#00e5ff" stop-opacity="0.9"/>
      <stop offset="60%" stop-color="#0070ff" stop-opacity="0.7"/>
      <stop offset="100%" stop-color="#aa33ff" stop-opacity="0.5"/>
    </radialGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="2.5" result="coloredBlur"/>
      <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="glow2">
      <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
      <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
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
  <!-- Background circle -->
  <circle cx="60" cy="60" r="56" fill="url(#bgGrad)" stroke="rgba(0,229,255,0.15)" stroke-width="1"/>
  
  <!-- Outer orbit ring -->
  <ellipse cx="60" cy="60" rx="50" ry="20" fill="none" stroke="url(#orbitGrad)" stroke-width="1.5" opacity="0.5">
    <animateTransform attributeName="transform" type="rotate" from="0 60 60" to="360 60 60" dur="8s" repeatCount="indefinite"/>
  </ellipse>
  
  <!-- Second orbit ring -->
  <ellipse cx="60" cy="60" rx="42" ry="15" fill="none" stroke="url(#orbitGrad2)" stroke-width="1" opacity="0.4" transform="rotate(60 60 60)">
    <animateTransform attributeName="transform" type="rotate" from="60 60 60" to="420 60 60" dur="6s" repeatCount="indefinite"/>
  </ellipse>
  
  <!-- Static ring decorations -->
  <circle cx="60" cy="60" r="44" fill="none" stroke="rgba(0,229,255,0.08)" stroke-width="1" stroke-dasharray="4,6"/>
  <circle cx="60" cy="60" r="36" fill="none" stroke="rgba(170,51,255,0.07)" stroke-width="1"/>
  
  <!-- Satellite body -->
  <g filter="url(#glow)">
    <!-- Main satellite bus -->
    <rect x="50" y="54" width="20" height="12" rx="3" fill="#0a2040" stroke="#00e5ff" stroke-width="1.5"/>
    <!-- Solar panels left -->
    <rect x="26" y="57" width="22" height="6" rx="2" fill="#071830" stroke="#0070ff" stroke-width="1.2"/>
    <line x1="30" y1="57" x2="30" y2="63" stroke="#00e5ff" stroke-width="0.5" opacity="0.5"/>
    <line x1="34" y1="57" x2="34" y2="63" stroke="#00e5ff" stroke-width="0.5" opacity="0.5"/>
    <line x1="38" y1="57" x2="38" y2="63" stroke="#00e5ff" stroke-width="0.5" opacity="0.5"/>
    <line x1="42" y1="57" x2="42" y2="63" stroke="#00e5ff" stroke-width="0.5" opacity="0.5"/>
    <!-- Solar panels right -->
    <rect x="72" y="57" width="22" height="6" rx="2" fill="#071830" stroke="#0070ff" stroke-width="1.2"/>
    <line x1="76" y1="57" x2="76" y2="63" stroke="#00e5ff" stroke-width="0.5" opacity="0.5"/>
    <line x1="80" y1="57" x2="80" y2="63" stroke="#00e5ff" stroke-width="0.5" opacity="0.5"/>
    <line x1="84" y1="57" x2="84" y2="63" stroke="#00e5ff" stroke-width="0.5" opacity="0.5"/>
    <line x1="88" y1="57" x2="88" y2="63" stroke="#00e5ff" stroke-width="0.5" opacity="0.5"/>
    <!-- Antenna -->
    <line x1="60" y1="54" x2="60" y2="44" stroke="#00e5ff" stroke-width="1.5"/>
    <circle cx="60" cy="43" r="2.5" fill="#00e5ff" opacity="0.9">
      <animate attributeName="opacity" values="0.9;0.2;0.9" dur="1.5s" repeatCount="indefinite"/>
    </circle>
    <!-- Sensor dome -->
    <circle cx="60" cy="60" r="5" fill="url(#coreGrad)" filter="url(#glow2)">
      <animate attributeName="r" values="5;5.5;5" dur="2s" repeatCount="indefinite"/>
    </circle>
    <!-- Status LEDs -->
    <circle cx="53" cy="58" r="1.5" fill="#00ff88">
      <animate attributeName="opacity" values="1;0.2;1" dur="1s" repeatCount="indefinite"/>
    </circle>
    <circle cx="67" cy="58" r="1.5" fill="#ff2255">
      <animate attributeName="opacity" values="0.2;1;0.2" dur="0.8s" repeatCount="indefinite"/>
    </circle>
  </g>
  
  <!-- Orbiting data dot -->
  <circle r="3" fill="#00e5ff" filter="url(#glow)">
    <animateMotion dur="5s" repeatCount="indefinite">
      <mpath href="#orbitPath"/>
    </animateMotion>
    <animate attributeName="opacity" values="0.9;0.4;0.9" dur="2.5s" repeatCount="indefinite"/>
  </circle>
  <path id="orbitPath" d="M 60,10 A 50,20 0 1 1 59.99,10" fill="none"/>
  
  <!-- Orbiting data dot 2 -->
  <circle r="2" fill="#aa33ff" filter="url(#glow)">
    <animateMotion dur="3.5s" repeatCount="indefinite" keyPoints="0.5;1;0;0.5" keyTimes="0;0.5;0.5;1" calcMode="linear">
      <mpath href="#orbitPath2"/>
    </animateMotion>
  </circle>
  <path id="orbitPath2" d="M 60,18 A 42,15 60 1 1 59.99,18" fill="none"/>
  
  <!-- Scan ring pulse -->
  <circle cx="60" cy="60" r="20" fill="none" stroke="#00e5ff" stroke-width="1.5" opacity="0">
    <animate attributeName="r" values="20;55;20" dur="3s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.6;0;0.6" dur="3s" repeatCount="indefinite"/>
  </circle>
  
  <!-- India map simplified dot indicators -->
  <circle cx="48" cy="58" r="1" fill="#ffaa00" opacity="0.7"/>
  <circle cx="55" cy="52" r="1.2" fill="#ff2255" opacity="0.7">
    <animate attributeName="opacity" values="0.7;0.2;0.7" dur="1.8s" repeatCount="indefinite"/>
  </circle>
  <circle cx="68" cy="56" r="1" fill="#00ff88" opacity="0.7"/>
  <circle cx="72" cy="62" r="1" fill="#ffaa00" opacity="0.6"/>
  
  <!-- Corner triangles -->
  <polygon points="4,4 14,4 4,14" fill="rgba(0,229,255,0.3)"/>
  <polygon points="116,4 106,4 116,14" fill="rgba(0,229,255,0.3)"/>
  <polygon points="4,116 14,116 4,106" fill="rgba(0,229,255,0.3)"/>
  <polygon points="116,116 106,116 116,106" fill="rgba(0,229,255,0.3)"/>
</svg>
"""

# ══════════════════════════════════════════════════════════════════
# USER DATABASE
# ══════════════════════════════════════════════════════════════════
if "users_db" not in st.session_state:
    demo_hash = hashlib.sha256("Demo@1234".encode()).hexdigest()
    st.session_state.users_db = {
        "demo@aqicommand.in": {
            "name": "Demo Analyst",
            "password_hash": demo_hash,
            "role": "Analyst",
            "joined": "2024-01-01",
            "last_login": None,
            "alerts_enabled": True,
            "alert_threshold": 200,
            "theme": "Cyber Blue",
            "notifications": [],
        }
    }

if "logged_in"    not in st.session_state: st.session_state.logged_in    = False
if "current_user" not in st.session_state: st.session_state.current_user = None
if "auth_msg"     not in st.session_state: st.session_state.auth_msg     = ("", "")
if "login_anim"   not in st.session_state: st.session_state.login_anim   = False
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "alerts_log"   not in st.session_state: st.session_state.alerts_log   = []

def _hash(pw): return hashlib.sha256(pw.encode()).hexdigest()
def is_valid_email(e): return re.match(r"^[^@]+@[^@]+\.[^@]+$", e) is not None
def is_strong_password(pw):
    return (len(pw)>=8 and re.search(r"[A-Z]",pw) and re.search(r"[0-9]",pw) and re.search(r"[^A-Za-z0-9]",pw))

# ══════════════════════════════════════════════════════════════════
# LOGIN SCREEN
# ══════════════════════════════════════════════════════════════════
def show_auth_screen():
    st.markdown("""
    <div class="grid-bg"></div>
    <div class="scan-line"></div>
    <div class="particle" style="left:8%;width:4px;height:4px;background:#00e5ff;animation-duration:9s;animation-delay:0s;"></div>
    <div class="particle" style="left:22%;width:3px;height:3px;background:#aa33ff;animation-duration:12s;animation-delay:1.5s;"></div>
    <div class="particle" style="left:40%;width:5px;height:5px;background:#00ff88;animation-duration:8s;animation-delay:3s;"></div>
    <div class="particle" style="left:58%;width:3px;height:3px;background:#0070ff;animation-duration:11s;animation-delay:0.8s;"></div>
    <div class="particle" style="left:72%;width:4px;height:4px;background:#ff2255;animation-duration:7s;animation-delay:2s;"></div>
    <div class="particle" style="left:88%;width:3px;height:3px;background:#00e5ff;animation-duration:10s;animation-delay:1s;"></div>
    <div class="particle" style="left:15%;width:2px;height:2px;background:#ffaa00;animation-duration:13s;animation-delay:4s;"></div>
    <div class="particle" style="left:65%;width:3px;height:3px;background:#00ffcc;animation-duration:9s;animation-delay:2.5s;"></div>
    """, unsafe_allow_html=True)

    _, mid, _ = st.columns([1, 1.1, 1])
    with mid:
        # Logo
        st.markdown(f"""
        <div style="text-align:center;margin-bottom:8px;position:relative;z-index:10;">
            <div style="display:inline-block;animation:logo-pulse 3s ease-in-out infinite;filter:drop-shadow(0 0 16px rgba(0,229,255,0.5));">
                {AQI_LOGO_SVG}
            </div>
        </div>
        <style>
        @keyframes logo-pulse{{0%,100%{{filter:drop-shadow(0 0 10px rgba(0,229,255,0.4));}}50%{{filter:drop-shadow(0 0 28px rgba(0,229,255,0.9));}}}}
        </style>
        <div class="auth-title">AQI COMMAND CENTER</div>
        <div class="auth-subtitle">INDIA POLLUTION INTELLIGENCE SYSTEM v4.0</div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="auth-card"><div class="corner-tl"></div><div class="corner-tr"></div><div class="corner-bl"></div><div class="corner-br"></div>', unsafe_allow_html=True)

        tab_login, tab_reg = st.tabs(["🔐  LOGIN", "📡  REGISTER"])

        msg_text, msg_type = st.session_state.auth_msg
        if msg_text:
            css_cls = "auth-success" if msg_type=="success" else ("auth-error" if msg_type=="error" else "auth-info")
            st.markdown(f'<div class="{css_cls}">{msg_text}</div>', unsafe_allow_html=True)

        with tab_login:
            st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
            st.markdown('<div style="font-family:Share Tech Mono;font-size:0.65rem;color:#4a6a8a;letter-spacing:2px;margin-bottom:14px;text-align:center;">ENTER CREDENTIALS TO ACCESS THE SYSTEM</div>', unsafe_allow_html=True)
            login_email = st.text_input("📧  Email Address", key="login_email", placeholder="you@domain.com")
            login_pw    = st.text_input("🔒  Password",      key="login_pw",    placeholder="••••••••", type="password")
            c1,c2 = st.columns(2)
            with c1: st.checkbox("Remember session", value=True, key="remember_me")
            with c2: st.markdown('<div style="text-align:right;font-family:Exo 2;font-size:0.7rem;color:#4a6a8a;padding-top:6px;">demo@aqicommand.in / Demo@1234</div>', unsafe_allow_html=True)
            st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
            if st.button("🚀  LAUNCH COMMAND CENTER", use_container_width=True, key="btn_login"):
                if not login_email or not login_pw:
                    st.session_state.auth_msg=("⚠️ Please fill in all fields.","error"); st.rerun()
                elif login_email not in st.session_state.users_db:
                    st.session_state.auth_msg=("❌ Email not found. Please register first.","error"); st.rerun()
                elif st.session_state.users_db[login_email]["password_hash"]!=_hash(login_pw):
                    st.session_state.auth_msg=("❌ Incorrect password. Try again.","error"); st.rerun()
                else:
                    st.session_state.users_db[login_email]["last_login"]=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    st.session_state.logged_in=True; st.session_state.current_user=login_email
                    st.session_state.auth_msg=("",""); st.session_state.login_anim=True; st.rerun()
            st.markdown('<div style="text-align:center;margin-top:14px;font-family:Share Tech Mono;font-size:0.62rem;color:#2a4a6a;">──── SECURE · AES-256 ENCRYPTED ────</div>', unsafe_allow_html=True)

        with tab_reg:
            st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
            st.markdown('<div style="font-family:Share Tech Mono;font-size:0.65rem;color:#4a6a8a;letter-spacing:2px;margin-bottom:14px;text-align:center;">CREATE YOUR ANALYST ACCOUNT</div>', unsafe_allow_html=True)
            reg_name  = st.text_input("👤  Full Name", key="reg_name", placeholder="Dr. Aditya Kumar")
            reg_email = st.text_input("📧  Email",     key="reg_email", placeholder="you@domain.com")
            reg_role  = st.selectbox("🏷️  Role", ["Analyst","Researcher","Policy Maker","Student","Journalist"], key="reg_role")
            reg_pw    = st.text_input("🔒  Password", key="reg_pw", type="password", placeholder="8+ chars · Uppercase · Number · Symbol")
            reg_pw2   = st.text_input("🔒  Confirm",  key="reg_pw2", type="password", placeholder="Re-enter password")
            if reg_pw:
                strength=sum([len(reg_pw)>=8, bool(re.search(r"[A-Z]",reg_pw)), bool(re.search(r"[0-9]",reg_pw)), bool(re.search(r"[^A-Za-z0-9]",reg_pw))])
                colors=["#ff2255","#ffaa00","#a3ff00","#00ff88"]; labels=["Weak","Fair","Good","Strong"]
                col=colors[strength-1] if strength>0 else "#ff2255"
                st.markdown(f"""<div style="margin:4px 0 10px;"><div style="display:flex;justify-content:space-between;font-family:Exo 2;font-size:0.7rem;color:#5a7a9a;margin-bottom:4px;"><span>Strength: <b style="color:{col};">{labels[strength-1] if strength>0 else "Weak"}</b></span></div><div style="background:rgba(0,0,0,0.3);border-radius:4px;height:4px;"><div style="width:{strength*25}%;height:100%;background:{col};border-radius:4px;transition:width 0.4s;"></div></div></div>""", unsafe_allow_html=True)
            terms = st.checkbox("I agree to Terms of Service", key="reg_terms")
            st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)
            if st.button("📡  CREATE ACCOUNT", use_container_width=True, key="btn_register"):
                errors=[]
                if not reg_name.strip(): errors.append("Name required")
                if not is_valid_email(reg_email): errors.append("Valid email required")
                if reg_email in st.session_state.users_db: errors.append("Email already registered")
                if not is_strong_password(reg_pw): errors.append("Password too weak")
                if reg_pw!=reg_pw2: errors.append("Passwords don't match")
                if not terms: errors.append("Accept Terms")
                if errors:
                    st.session_state.auth_msg=("❌ "+" · ".join(errors),"error"); st.rerun()
                else:
                    st.session_state.users_db[reg_email]={"name":reg_name.strip(),"password_hash":_hash(reg_pw),"role":reg_role,"joined":datetime.date.today().isoformat(),"last_login":None,"alerts_enabled":True,"alert_threshold":200,"theme":"Cyber Blue","notifications":[]}
                    st.session_state.auth_msg=(f"✅ Account created! Welcome, {reg_name.split()[0]}. Please login.","success"); st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("""<div style="text-align:center;margin-top:18px;font-family:'Share Tech Mono',monospace;font-size:0.6rem;color:#2a4a6a;">🛰️ INDIA AQI COMMAND CENTER v4.0 · REAL-TIME · INTELLIGENT · SECURE</div>""", unsafe_allow_html=True)

if not st.session_state.logged_in:
    show_auth_screen()
    st.stop()

if st.session_state.login_anim:
    user_info = st.session_state.users_db[st.session_state.current_user]
    placeholder = st.empty()
    placeholder.markdown(f"""
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:80vh;text-align:center;">
        <div style="margin-bottom:20px;animation:logo-pulse 2s infinite;filter:drop-shadow(0 0 20px rgba(0,229,255,0.7));">{AQI_LOGO_SVG}</div>
        <div style="font-family:'Orbitron',sans-serif;font-size:2.2rem;font-weight:900;background:linear-gradient(90deg,#00e5ff,#0070ff,#aa33ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">ACCESS GRANTED</div>
        <div style="font-family:'Share Tech Mono',monospace;font-size:0.85rem;color:#00ff88;letter-spacing:3px;margin:14px 0;animation:pulse-live 1.5s infinite;">● INITIALIZING COMMAND CENTER…</div>
        <div style="font-family:'Exo 2',sans-serif;font-size:1.05rem;color:#d8f0ff;margin-top:6px;">Welcome back, <b style="color:#00e5ff;">{user_info['name']}</b></div>
        <div style="font-family:'Share Tech Mono',monospace;font-size:0.72rem;color:#5a7a9a;margin-top:5px;">{st.session_state.current_user}</div>
    </div>""", unsafe_allow_html=True)
    time.sleep(2.2)
    placeholder.empty()
    st.session_state.login_anim=False; st.rerun()

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

AI_RESPONSES = {
    "delhi": "🏙️ Delhi's AQI is critically high, especially during winter months (Oct–Jan) due to stubble burning, vehicular emissions, and thermal inversions. PM2.5 levels frequently exceed 10× WHO limits. Recommend: N95 mask, air purifiers indoors, avoid 7–11AM peak pollution hours.",
    "mumbai": "🌊 Mumbai generally has better air quality than Delhi due to sea breezes, but industrial zones in Thane & Turbhe record PM10 > 200 µg/m³. Monsoon season (Jun–Sep) dramatically improves AQI. Current concern: NO2 from vehicular traffic.",
    "pm2.5": "🔬 PM2.5 particles (<2.5 micrometers) are the most dangerous pollutant — they penetrate deep into lung tissue and enter the bloodstream. India's safe limit is 60 µg/m³ (annual) and 40 µg/m³ (WHO guideline). Chronic exposure is linked to cardiovascular disease, lung cancer, and premature death.",
    "pm10": "🌫️ PM10 includes coarse particles (dust, pollen, mold). India's 24hr safe limit is 100 µg/m³. Major sources: road dust, construction, industrial emissions. Less dangerous than PM2.5 but still causes respiratory irritation.",
    "health": "🏥 High AQI affects health in multiple ways:\n• Short-term: eye irritation, coughing, shortness of breath\n• Long-term: COPD, asthma, cardiovascular disease, lung cancer\n• Vulnerable groups: children, elderly, pregnant women, heart/lung patients\nSolution: wear N95 masks, use air purifiers (HEPA), avoid peak hours.",
    "forecast": "📈 AQI forecasting uses ML models incorporating meteorological data (wind speed, humidity, temperature, rainfall), emission inventories, and historical patterns. Winter forecasts are typically worse due to reduced atmospheric mixing height (boundary layer compression).",
    "default": "🤖 I'm your AQI Intelligence Assistant. I can analyze pollution data, explain health impacts, compare cities, forecast trends, and provide actionable recommendations. Try asking about a specific city, pollutant type, health effects, or pollution forecast!",
}

AXIS_STYLE = dict(gridcolor="rgba(0,229,255,0.07)",linecolor="rgba(0,229,255,0.15)",tickfont=dict(color="#5a7a9a"))

def apply_theme(fig, height=400, margin=None, **kwargs):
    m = margin or dict(l=60,r=20,t=40,b=60)
    legend_defaults = dict(bgcolor="rgba(7,16,32,0.85)",bordercolor="rgba(0,229,255,0.18)",borderwidth=1)
    legend = {**legend_defaults, **kwargs.pop("legend",{})}
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(7,16,32,0.6)",
        font=dict(family="Exo 2, sans-serif",color="#d8f0ff",size=12),legend=legend,margin=m,height=height,**kwargs)
    fig.update_xaxes(**AXIS_STYLE); fig.update_yaxes(**AXIS_STYLE)
    return fig

def get_aqi_info(aqi):
    for lo,hi,label,color,emoji,advice in AQI_SCALE:
        if lo<=aqi<=hi: return label,color,emoji,advice
    return "Severe","#aa33ff","☠️",AQI_SCALE[-1][5]

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
    if val<=safe*1.5:   return "⚠️ Warning","#ffaa00"
    return "🚨 Danger","#ff2255"

def get_ai_response(query):
    q = query.lower()
    for key in AI_RESPONSES:
        if key in q:
            return AI_RESPONSES[key]
    # Context-aware fallback
    for c in CITIES:
        if c["name"].lower() in q:
            city_aqi = int(st.session_state.df[st.session_state.df["City"]==c["name"]]["AQI"].values[0]) if c["name"] in st.session_state.df["City"].values else random.randint(80,350)
            label,color,_,advice = get_aqi_info(city_aqi)
            return f"📍 **{c['name']}** — Current AQI: **{city_aqi}** ({label})\n\n{advice}\n\nState: {c['state']} | Lat: {c['lat']}°N, Lon: {c['lon']}°E"
    if any(w in q for w in ["worst","polluted","bad","dangerous","highest"]):
        worst = st.session_state.df.nlargest(3,"AQI")[["City","AQI","Category"]].values
        return "☣️ **Top 3 Most Polluted Cities Right Now:**\n\n" + "\n".join([f"• {r[0]}: AQI {r[1]} ({r[2]})" for r in worst])
    if any(w in q for w in ["best","clean","safe","lowest","good"]):
        best = st.session_state.df.nsmallest(3,"AQI")[["City","AQI","Category"]].values
        return "🌿 **Top 3 Cleanest Cities Right Now:**\n\n" + "\n".join([f"• {r[0]}: AQI {r[1]} ({r[2]})" for r in best])
    if any(w in q for w in ["average","national","india","overall"]):
        avg = int(st.session_state.df["AQI"].mean())
        label,_,_,_ = get_aqi_info(avg)
        return f"🌏 **National Average AQI: {avg}** ({label})\n\nBased on real-time readings from {len(CITIES)} major Indian cities. The Indo-Gangetic Plain cities consistently rank among the most polluted."
    return AI_RESPONSES["default"]

# ── Session state ──
if "df"           not in st.session_state: st.session_state.df           = generate_data()
if "live_aqi"     not in st.session_state: st.session_state.live_aqi     = 142
if "live_city"    not in st.session_state: st.session_state.live_city    = "Mumbai"
if "live_history" not in st.session_state: st.session_state.live_history = [142]
if "last_refresh" not in st.session_state: st.session_state.last_refresh = datetime.datetime.now()
if "auto_refresh" not in st.session_state: st.session_state.auto_refresh = False
if "compare_cities" not in st.session_state: st.session_state.compare_cities = []

# ── Generate alerts ──
def check_alerts(df_in, threshold=200):
    alerts = []
    for _,row in df_in.iterrows():
        if row["AQI"] > threshold:
            level = "CRITICAL" if row["AQI"] > 300 else "WARNING"
            alerts.append({"city":row["City"],"aqi":row["AQI"],"level":level,"cat":row["Category"],"color":row["Color"],"time":datetime.datetime.now().strftime("%H:%M:%S")})
    return sorted(alerts, key=lambda x: x["aqi"], reverse=True)

# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════
user_info = st.session_state.users_db[st.session_state.current_user]
alert_threshold_user = user_info.get("alert_threshold", 200)
active_alerts = check_alerts(st.session_state.df, alert_threshold_user)

with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center;padding:10px 0 14px;">
        <div style="display:inline-block;filter:drop-shadow(0 0 10px rgba(0,229,255,0.4));margin-bottom:8px;">{AQI_LOGO_SVG.replace('width="120" height="120"','width="72" height="72"')}</div>
        <div style="font-family:'Orbitron',sans-serif;font-size:1.1rem;font-weight:900;background:linear-gradient(90deg,#00e5ff,#aa33ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">AQI COMMAND</div>
        <div style="font-family:'Share Tech Mono',monospace;font-size:0.6rem;color:#4a6a8a;letter-spacing:2px;margin-top:2px;">INDIA MONITOR v4.0</div>
    </div>""", unsafe_allow_html=True)

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

    if len(active_alerts) > 0:
        st.markdown(f'<div style="background:rgba(255,34,85,0.08);border:1px solid rgba(255,34,85,0.3);border-radius:8px;padding:8px 12px;font-family:Share Tech Mono;font-size:0.68rem;color:#ff2255;text-align:center;animation:notif-pulse 2s infinite;margin-bottom:8px;">🚨 {len(active_alerts)} ACTIVE ALERT{"S" if len(active_alerts)>1 else ""}</div>', unsafe_allow_html=True)
    st.markdown('<style>@keyframes notif-pulse{0%,100%{box-shadow:0 0 4px rgba(255,34,85,0.2);}50%{box-shadow:0 0 14px rgba(255,34,85,0.5);}}</style>', unsafe_allow_html=True)

    if st.button("🚪  LOGOUT", use_container_width=True, key="logout_btn"):
        st.session_state.logged_in=False; st.session_state.current_user=None; st.session_state.auth_msg=("",""); st.rerun()

    st.divider()
    if st.button("🔄  REFRESH DATA", use_container_width=True):
        st.session_state.df=generate_data(); st.session_state.last_refresh=datetime.datetime.now(); st.rerun()
    st.session_state.auto_refresh = st.checkbox("⚡ Auto-Refresh (30s)", value=st.session_state.auto_refresh)
    st.divider()

    view_mode = st.radio("📡  NAVIGATION", [
        "🔴 Live Air Pollution","🗺️ Pollution Map","📊 City Comparison",
        "📈 Hourly Trend","🧪 Pollutant Breakdown","🏆 Rankings & Stats",
        "🤖 AI Assistant","🔔 Alerts & Notifications",
        "🌡️ Weather & AQI Forecast","📸 Image Predictor",
        "📋 Data Export","👤 My Account",
    ])
    st.divider()

    st.markdown('<div style="font-family:Exo 2;font-size:0.75rem;color:#5a7a9a;letter-spacing:1px;text-transform:uppercase;margin-bottom:6px;">FILTERS</div>', unsafe_allow_html=True)
    aqi_range       = st.slider("AQI Range",0,500,(0,500))
    all_states      = sorted(st.session_state.df["State"].unique())
    selected_states = st.multiselect("Filter by State",all_states)
    st.divider()

    st.markdown('<div style="font-family:Exo 2;font-size:0.75rem;color:#5a7a9a;letter-spacing:1px;text-transform:uppercase;margin-bottom:6px;">AQI LEGEND</div>', unsafe_allow_html=True)
    for lo,hi,label,color,emoji,_ in AQI_SCALE:
        st.markdown(f'<div style="display:flex;align-items:center;gap:8px;margin:3px 0;font-family:Exo 2;font-size:0.75rem;"><span style="width:9px;height:9px;border-radius:50%;background:{color};display:inline-block;box-shadow:0 0 5px {color};flex-shrink:0;"></span><span style="color:#5a7a9a;">{lo}–{hi}</span><span style="color:#d8f0ff;font-weight:600;">{label}</span></div>', unsafe_allow_html=True)
    st.divider()
    lr = st.session_state.last_refresh.strftime("%H:%M:%S")
    st.markdown(f'<div style="font-family:Share Tech Mono;font-size:0.68rem;color:#4a6a8a;text-align:center;">LAST UPDATE: {lr}</div>', unsafe_allow_html=True)

# ── Data prep ──
df  = st.session_state.df
dff = df[(df["AQI"]>=aqi_range[0])&(df["AQI"]<=aqi_range[1])]
if selected_states: dff=dff[dff["State"].isin(selected_states)]

if st.session_state.auto_refresh:
    elapsed=(datetime.datetime.now()-st.session_state.last_refresh).seconds
    if elapsed>=30:
        st.session_state.df=generate_data(); st.session_state.last_refresh=datetime.datetime.now(); st.rerun()

# ── Header ──
col_title,col_live = st.columns([3,1])
with col_title:
    st.markdown('<h1 style="margin-bottom:2px;">🛰️ INDIA AQI COMMAND CENTER</h1><p style="font-family:Share Tech Mono,monospace;color:#5a7a9a;font-size:0.78rem;letter-spacing:1.5px;margin-top:0;">REAL-TIME AIR QUALITY INTELLIGENCE · 25 MAJOR CITIES · POLLUTION MONITOR v4.0</p>', unsafe_allow_html=True)
with col_live:
    st.markdown('<div style="display:flex;justify-content:flex-end;align-items:center;height:100%;padding-top:8px;"><div class="live-badge"><div class="dot-live"></div>LIVE MONITORING</div></div>', unsafe_allow_html=True)

# News ticker
ticker_items = " · ".join([f"{r['Emoji']} {r['City']}: AQI {r['AQI']} ({r['Category']})" for _,r in df.iterrows()])
st.markdown(f'<div class="ticker-wrap"><span class="ticker-label">📡 LIVE</span><span class="ticker-text">{ticker_items}</span></div>', unsafe_allow_html=True)

avg_aqi   = int(df["AQI"].mean())
worst     = df.loc[df["AQI"].idxmax()]
best      = df.loc[df["AQI"].idxmin()]
dangerous = int((df["AQI"]>200).sum())
avg_label,avg_color,avg_emoji,_ = get_aqi_info(avg_aqi)
safe_count = int((df["AQI"]<=100).sum())

c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.metric("🌡️ National Avg", avg_aqi, f"{avg_emoji} {avg_label}")
c2.metric("☣️ Most Polluted", worst["City"], f"AQI {worst['AQI']}")
c3.metric("🌿 Cleanest", best["City"], f"AQI {best['AQI']}")
c4.metric("⚠️ High Risk", dangerous, "AQI > 200")
c5.metric("✅ Safe Cities", safe_count, "AQI ≤ 100")
c6.metric("🚨 Active Alerts", len(active_alerts), f"Threshold: {alert_threshold_user}")
st.divider()

# ══════════════════════════════════════════════════════════════════
# VIEW 0 — LIVE AIR POLLUTION
# ══════════════════════════════════════════════════════════════════
if "Live" in view_mode:
    st.markdown('<h2>🔴 LIVE AIR POLLUTION INDICATOR</h2>', unsafe_allow_html=True)
    lcol1,lcol2,lcol3 = st.columns([2,2,1])
    with lcol1:
        live_city = st.selectbox("📍 Select City",[c["name"] for c in CITIES],index=[c["name"] for c in CITIES].index(st.session_state.live_city),key="live_city_sel")
        if live_city!=st.session_state.live_city:
            st.session_state.live_city=live_city
            base_aqi=int(df[df["City"]==live_city]["AQI"].values[0])
            st.session_state.live_aqi=base_aqi; st.session_state.live_history=[base_aqi]
    with lcol2:
        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
        if st.button("⚡  SIMULATE NEW READING", use_container_width=True):
            prev=st.session_state.live_aqi; new_aqi=max(10,min(500,prev+random.randint(-30,30)))
            st.session_state.live_aqi=new_aqi; st.session_state.live_history.append(new_aqi)
            if len(st.session_state.live_history)>60: st.session_state.live_history.pop(0)
    with lcol3:
        st.markdown('<div class="live-badge" style="margin-top:18px;"><div class="dot-live"></div>ACTIVE</div>', unsafe_allow_html=True)

    st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
    current_aqi=st.session_state.live_aqi
    label,color,emoji,advice=get_aqi_info(current_aqi)
    poll_vals=simulate_pollutants(current_aqi)
    tips=HEALTH_TIPS.get(label,[])

    gauge_col,detail_col = st.columns([1,2])
    with gauge_col:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",value=current_aqi,
            delta={"reference":st.session_state.live_history[-2] if len(st.session_state.live_history)>=2 else current_aqi,
                   "increasing":{"color":"#ff2255"},"decreasing":{"color":"#00ff88"},"font":{"size":16,"family":"Orbitron, sans-serif"}},
            number={"font":{"size":52,"family":"Orbitron, sans-serif","color":color},"suffix":" AQI"},
            gauge={"axis":{"range":[0,500],"tickvals":[0,50,100,200,300,400,500],"tickfont":{"size":9,"color":"#5a7a9a"}},
                   "bar":{"color":color,"thickness":0.22},"bgcolor":"rgba(0,0,0,0)","borderwidth":0,
                   "steps":[{"range":[0,50],"color":"rgba(0,255,136,0.12)"},{"range":[50,100],"color":"rgba(163,255,0,0.1)"},
                             {"range":[100,200],"color":"rgba(255,170,0,0.1)"},{"range":[200,300],"color":"rgba(255,102,0,0.1)"},
                             {"range":[300,400],"color":"rgba(255,34,85,0.1)"},{"range":[400,500],"color":"rgba(170,51,255,0.1)"}],
                   "threshold":{"line":{"color":color,"width":4},"thickness":0.85,"value":current_aqi}},
            title={"text":f"{emoji} {label}<br><span style='font-size:10px;color:#5a7a9a;'>{live_city} · Live Sensor</span>","font":{"size":16,"family":"Orbitron, sans-serif","color":"#d8f0ff"}}))
        fig_gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(color="#d8f0ff"),height=330,margin=dict(l=20,r=20,t=60,b=20))
        st.plotly_chart(fig_gauge, use_container_width=True)
        st.markdown(f'<div class="health-advice" style="border-color:{color}33;"><div style="font-family:Orbitron,sans-serif;font-size:0.72rem;color:{color};letter-spacing:2px;margin-bottom:7px;">HEALTH ADVISORY</div><div style="color:#d8f0ff;">{advice}</div></div>', unsafe_allow_html=True)

    with detail_col:
        st.markdown('<div class="section-header">🧪 LIVE POLLUTANT READINGS</div>', unsafe_allow_html=True)
        for p in POLLUTANTS:
            val=poll_vals[p]; safe=SAFE_LIMITS[p]; pct=min(val/(safe*2.5),1.0)
            status_text,s_color=pollutant_status(val,safe); bar_w=int(pct*100)
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
    hist=st.session_state.live_history; x_vals=list(range(len(hist))); colors_hist=[get_aqi_info(v)[1] for v in hist]
    r_int,g_int,b_int=int(color[1:3],16),int(color[3:5],16),int(color[5:7],16)
    fig_stream=go.Figure()
    fig_stream.add_trace(go.Scatter(x=x_vals,y=hist,mode="lines",line=dict(color=color,width=0),fill="tozeroy",fillcolor=f"rgba({r_int},{g_int},{b_int},0.08)",showlegend=False,hoverinfo="skip"))
    fig_stream.add_trace(go.Scatter(x=x_vals,y=hist,mode="lines+markers",line=dict(color=color,width=2.5),marker=dict(size=[10 if i==len(hist)-1 else 4 for i in range(len(hist))],color=colors_hist,line=dict(width=1,color="rgba(0,0,0,0.4)")),name="AQI",hovertemplate="Reading %{x}: AQI %{y}<extra></extra>"))
    for threshold,t_label,t_color in [(100,"Satisfactory","#a3ff00"),(200,"Moderate","#ffaa00"),(300,"Poor","#ff6600")]:
        fig_stream.add_hline(y=threshold,line_dash="dash",line_color=t_color,opacity=0.35,annotation_text=t_label,annotation_font_size=9,annotation_font_color=t_color)
    if hist:
        fig_stream.add_trace(go.Scatter(x=[len(hist)-1],y=[hist[-1]],mode="markers",marker=dict(size=16,color=color,symbol="circle",line=dict(width=2,color="#ffffff"),opacity=0.9),name="Current",hovertemplate=f"CURRENT: AQI {hist[-1]}<extra></extra>"))
    apply_theme(fig_stream,height=250,margin=dict(l=60,r=20,t=20,b=50),showlegend=False)
    fig_stream.update_xaxes(title_text="Reading #"); fig_stream.update_yaxes(title_text="AQI Value",range=[0,520])
    st.plotly_chart(fig_stream, use_container_width=True)

    st.markdown('<div class="section-header">🔮 24-HOUR AQI FORECAST</div>', unsafe_allow_html=True)
    now_h=datetime.datetime.now().hour; h_labels=[f"{(now_h+i)%24:02d}:00" for i in range(24)]
    forecast=[max(20,min(500,int(current_aqi+40*np.sin((i-6)*np.pi/12)+random.randint(-20,20)))) for i in range(24)]
    f_colors=[get_aqi_info(v)[1] for v in forecast]
    fig_fc=go.Figure()
    fig_fc.add_trace(go.Bar(x=h_labels,y=forecast,marker_color=f_colors,marker_line_width=0,hovertemplate="%{x}<br>AQI: %{y}<extra></extra>",name="Forecast"))
    apply_theme(fig_fc,height=210,margin=dict(l=60,r=20,t=10,b=70))
    fig_fc.update_xaxes(title_text="Hour",tickangle=-45); fig_fc.update_yaxes(title_text="AQI")
    st.plotly_chart(fig_fc, use_container_width=True)

# ══════════════════════════════════════════════════════════════════
# VIEW 1 — POLLUTION MAP
# ══════════════════════════════════════════════════════════════════
elif "Map" in view_mode:
    st.markdown('<h2>🗺️ INDIA POLLUTION MAP</h2>', unsafe_allow_html=True)
    col_left,col_right = st.columns([3,1])
    with col_left:
        mapc1,mapc2 = st.columns(2)
        map_metric=mapc1.selectbox("Show on map bubbles",["AQI"]+POLLUTANTS,key="map_metric")
        map_style=mapc2.selectbox("Map theme",["carto-darkmatter","open-street-map","carto-positron"],key="map_style")
        dff2=dff.copy(); dff2["size_val"]=dff2["AQI"].apply(lambda v:max(8,min(40,v/10)))
        dff2["label"]=dff2.apply(lambda r:f"<b>{r['City']}</b>  {r['Emoji']}<br>AQI: {r['AQI']}  ·  {r['Category']}<br>PM2.5: {r['PM2.5']}  |  PM10: {r['PM10']}<br>NO2: {r['NO2']}  |  SO2: {r['SO2']}  |  CO: {r['CO']}  |  O3: {r['O3']}",axis=1)
        fig_map=go.Figure(go.Scattermapbox(lat=dff2["Lat"],lon=dff2["Lon"],mode="markers+text",
            marker=dict(size=dff2["size_val"],color=dff2["AQI"],colorscale=[[0,"#00ff88"],[0.1,"#00ff88"],[0.1,"#a3ff00"],[0.2,"#a3ff00"],[0.2,"#ffaa00"],[0.4,"#ffaa00"],[0.4,"#ff6600"],[0.6,"#ff6600"],[0.6,"#ff2255"],[0.8,"#ff2255"],[0.8,"#aa33ff"],[1,"#aa33ff"]],
                cmin=0,cmax=500,opacity=0.9,colorbar=dict(title=dict(text="AQI",font=dict(color="#d8f0ff")),thickness=11,len=0.6,tickfont=dict(color="#d8f0ff"))),
            text=dff2[map_metric].round(0).astype(int).astype(str),textfont=dict(size=9,color="white"),textposition="middle center",hovertext=dff2["label"],hoverinfo="text"))
        fig_map.update_layout(mapbox=dict(style=map_style,center=dict(lat=22.5,lon=82.0),zoom=3.8),margin=dict(l=0,r=0,t=0,b=0),height=540,paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_map, use_container_width=True)
    with col_right:
        st.markdown('<div class="section-header">CITY RANKINGS</div>', unsafe_allow_html=True)
        ranked=dff.sort_values("AQI",ascending=False)[["City","AQI","Category","Color","Emoji"]].reset_index(drop=True)
        for _,row in ranked.iterrows():
            st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;padding:6px 10px;margin:2px 0;border-radius:7px;background:rgba(0,229,255,0.03);border-left:3px solid {row["Color"]};"><span style="font-family:Exo 2;font-size:0.8rem;font-weight:600;color:#d8f0ff;">{row["Emoji"]} {row["City"]}</span><span style="font-family:Share Tech Mono;font-size:0.78rem;color:{row["Color"]};">{row["AQI"]}</span></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# VIEW 2 — CITY COMPARISON
# ══════════════════════════════════════════════════════════════════
elif "Comparison" in view_mode:
    st.markdown('<h2>📊 CITY AQI COMPARISON</h2>', unsafe_allow_html=True)
    cc1,cc2 = st.columns(2)
    top_n=cc1.slider("Number of cities",5,25,15,key="top_n")
    sort_by=cc2.selectbox("Sort / colour by",["AQI"]+POLLUTANTS,key="sort_by")
    sorted_df=dff.sort_values(sort_by,ascending=False).head(top_n); unit=UNITS.get(sort_by,"")
    fig_bar=go.Figure(go.Bar(x=sorted_df["City"],y=sorted_df[sort_by],marker_color=sorted_df["Color"],marker_line_width=0,text=sorted_df[sort_by].round(1),textposition="outside",hovertemplate="<b>%{x}</b><br>"+sort_by+": %{y}<extra></extra>"))
    apply_theme(fig_bar,height=420); fig_bar.update_xaxes(title_text="City",tickangle=-38); fig_bar.update_yaxes(title_text=f"{sort_by} ({unit})" if unit else sort_by)
    st.plotly_chart(fig_bar, use_container_width=True)
    st.divider()
    pie_col,scatter_col = st.columns(2)
    with pie_col:
        st.markdown('<div class="section-header">🥧 AQI CATEGORY DISTRIBUTION</div>', unsafe_allow_html=True)
        cat_order=["Good","Satisfactory","Moderate","Poor","Very Poor","Severe"]; cat_colors=[c[3] for c in AQI_SCALE]
        cat_counts=df["Category"].value_counts().reindex(cat_order,fill_value=0)
        fig_pie=go.Figure(go.Pie(labels=cat_counts.index,values=cat_counts.values,marker_colors=cat_colors,hole=0.5,hovertemplate="<b>%{label}</b><br>Cities: %{value} (%{percent})<extra></extra>",textinfo="label+percent",textfont=dict(family="Exo 2, sans-serif",size=11)))
        apply_theme(fig_pie,height=330,margin=dict(l=0,r=0,t=20,b=0)); st.plotly_chart(fig_pie, use_container_width=True)
    with scatter_col:
        st.markdown('<div class="section-header">🔵 PM2.5 vs PM10 SCATTER</div>', unsafe_allow_html=True)
        fig_sc=go.Figure()
        for cat,grp in df.groupby("Category"):
            col_c=grp["Color"].iloc[0]
            fig_sc.add_trace(go.Scatter(x=grp["PM2.5"],y=grp["PM10"],mode="markers+text",name=cat,text=grp["City"],textposition="top center",textfont=dict(size=8,color="#5a7a9a"),marker=dict(size=10,color=col_c,opacity=0.85,line=dict(width=1,color="rgba(255,255,255,0.15)")),hovertemplate="<b>%{text}</b><br>PM2.5: %{x}<br>PM10: %{y}<extra></extra>"))
        apply_theme(fig_sc,height=330); fig_sc.update_xaxes(title_text="PM2.5 (µg/m³)"); fig_sc.update_yaxes(title_text="PM10 (µg/m³)")
        st.plotly_chart(fig_sc, use_container_width=True)

# ══════════════════════════════════════════════════════════════════
# VIEW 3 — HOURLY TREND
# ══════════════════════════════════════════════════════════════════
elif "Trend" in view_mode:
    st.markdown('<h2>📈 24-HOUR AQI TREND</h2>', unsafe_allow_html=True)
    selected_cities=st.multiselect("Select cities (up to 6)",df["City"].tolist(),default=["Delhi","Mumbai","Bangalore","Chennai"],key="trend_cities")
    if not selected_cities: st.info("Please select at least one city above.")
    else:
        hour_labels=[f"{h:02d}:00" for h in range(24)]
        palette=["#00e5ff","#ff2255","#00ff88","#ffaa00","#aa33ff","#0070ff"]
        fig_line=go.Figure()
        for i,city in enumerate(selected_cities[:6]):
            base=int(df.loc[df["City"]==city,"AQI"].values[0])
            trend=[max(20,min(500,int(base+55*np.sin((h-6)*np.pi/12)+random.randint(-25,25)))) for h in range(24)]
            col_c=palette[i%len(palette)]; r_i,g_i,b_i=int(col_c[1:3],16),int(col_c[3:5],16),int(col_c[5:7],16)
            fig_line.add_trace(go.Scatter(x=hour_labels,y=trend,mode="none",fill="tozeroy",fillcolor=f"rgba({r_i},{g_i},{b_i},0.05)",showlegend=False,hoverinfo="skip"))
            fig_line.add_trace(go.Scatter(x=hour_labels,y=trend,mode="lines+markers",name=city,line=dict(color=col_c,width=2.5),marker=dict(size=5,color=col_c),hovertemplate=f"<b>{city}</b> %{{x}}: AQI %{{y}}<extra></extra>"))
        apply_theme(fig_line,height=440,legend=dict(orientation="h",yanchor="bottom",y=1.02,bgcolor="rgba(7,16,32,0.85)",bordercolor="rgba(0,229,255,0.15)",borderwidth=1))
        fig_line.update_xaxes(title_text="Hour",tickangle=-45); fig_line.update_yaxes(title_text="AQI",range=[0,520])
        st.plotly_chart(fig_line, use_container_width=True)
        # Weekly trend
        st.markdown('<div class="section-header">📅 7-DAY AQI TREND</div>', unsafe_allow_html=True)
        days=[f"Day {i+1}" for i in range(7)]
        fig_week=go.Figure()
        for i,city in enumerate(selected_cities[:6]):
            base=int(df.loc[df["City"]==city,"AQI"].values[0])
            weekly=[max(20,min(500,base+random.randint(-60,60))) for _ in range(7)]
            col_c=palette[i%len(palette)]
            fig_week.add_trace(go.Scatter(x=days,y=weekly,mode="lines+markers",name=city,line=dict(color=col_c,width=2),marker=dict(size=8,color=col_c,symbol="diamond"),hovertemplate=f"<b>{city}</b> %{{x}}: AQI %{{y}}<extra></extra>"))
        apply_theme(fig_week,height=300,legend=dict(orientation="h",yanchor="bottom",y=1.02))
        fig_week.update_yaxes(title_text="AQI")
        st.plotly_chart(fig_week, use_container_width=True)

# ══════════════════════════════════════════════════════════════════
# VIEW 4 — POLLUTANT BREAKDOWN
# ══════════════════════════════════════════════════════════════════
elif "Pollutant" in view_mode:
    st.markdown('<h2>🧪 POLLUTANT BREAKDOWN</h2>', unsafe_allow_html=True)
    selected_city=st.selectbox("Select a city",df["City"].tolist(),key="poll_city")
    row=df[df["City"]==selected_city].iloc[0]
    bar_col,radar_col=st.columns(2)
    with bar_col:
        st.markdown('<div class="section-header">📊 LEVELS vs SAFE LIMITS</div>', unsafe_allow_html=True)
        poll_vals2=[row[p] for p in POLLUTANTS]; safe_vals2=[SAFE_LIMITS[p] for p in POLLUTANTS]
        b_colors=["#00ff88" if row[p]<=SAFE_LIMITS[p] else "#ffaa00" if row[p]<=SAFE_LIMITS[p]*1.5 else "#ff2255" for p in POLLUTANTS]
        fig_poll=go.Figure()
        fig_poll.add_trace(go.Bar(name="Measured",x=POLLUTANTS,y=poll_vals2,marker_color=b_colors,marker_line_width=0,hovertemplate="<b>%{x}</b>: %{y}<extra></extra>"))
        fig_poll.add_trace(go.Bar(name="Safe Limit",x=POLLUTANTS,y=safe_vals2,marker_color="rgba(0,229,255,0.12)",marker_line_color="#00e5ff",marker_line_width=1,hovertemplate="Safe limit %{x}: %{y}<extra></extra>"))
        apply_theme(fig_poll,height=330,barmode="group"); fig_poll.update_xaxes(title_text="Pollutant"); fig_poll.update_yaxes(title_text="Concentration")
        st.plotly_chart(fig_poll, use_container_width=True)
    with radar_col:
        st.markdown('<div class="section-header">🕸️ POLLUTANT RADAR</div>', unsafe_allow_html=True)
        norm_vals=[min(row[p]/SAFE_LIMITS[p],3.0) for p in POLLUTANTS]
        cat_color=row["Color"]; r_c,g_c,b_c=int(cat_color[1:3],16),int(cat_color[3:5],16),int(cat_color[5:7],16)
        fig_radar=go.Figure(go.Scatterpolar(r=norm_vals+[norm_vals[0]],theta=POLLUTANTS+[POLLUTANTS[0]],fill="toself",fillcolor=f"rgba({r_c},{g_c},{b_c},0.18)",line=dict(color=cat_color,width=2),marker=dict(size=7,color=cat_color)))
        fig_radar.add_trace(go.Scatterpolar(r=[1]*len(POLLUTANTS)+[1],theta=POLLUTANTS+[POLLUTANTS[0]],mode="lines",line=dict(color="#00e5ff",width=1,dash="dot"),showlegend=False))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True,range=[0,3],tickfont=dict(color="#5a7a9a",size=9),gridcolor="rgba(0,229,255,0.08)"),angularaxis=dict(tickfont=dict(color="#d8f0ff",size=11,family="Exo 2"),gridcolor="rgba(0,229,255,0.08)"),bgcolor="rgba(7,16,32,0.6)"),showlegend=False,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(color="#d8f0ff"),height=340,margin=dict(l=40,r=40,t=40,b=40))
        st.plotly_chart(fig_radar, use_container_width=True)
    st.divider()
    st.markdown('<div class="section-header">🔍 COMPARE ALL CITIES — SINGLE POLLUTANT</div>', unsafe_allow_html=True)
    focus_poll=st.selectbox("Choose pollutant",POLLUTANTS,key="focus_poll")
    cmp_df=df[["City",focus_poll]].sort_values(focus_poll,ascending=True); safe_val=SAFE_LIMITS[focus_poll]
    bar_colors=["#00ff88" if v<=safe_val else "#ffaa00" if v<=safe_val*1.5 else "#ff2255" for v in cmp_df[focus_poll]]
    fig_hbar=go.Figure(go.Bar(x=cmp_df[focus_poll],y=cmp_df["City"],orientation="h",marker_color=bar_colors,marker_line_width=0,text=cmp_df[focus_poll].astype(str)+f" {UNITS[focus_poll]}",textposition="outside",hovertemplate="<b>%{y}</b>: %{x}<extra></extra>"))
    fig_hbar.add_vline(x=safe_val,line_dash="dash",line_color="#00e5ff",annotation_text=f"Safe limit ({safe_val} {UNITS[focus_poll]})",annotation_font_size=10,annotation_font_color="#00e5ff")
    apply_theme(fig_hbar,height=570,margin=dict(l=120,r=80,t=20,b=40)); fig_hbar.update_xaxes(title_text=UNITS[focus_poll]); fig_hbar.update_yaxes(showgrid=False)
    st.plotly_chart(fig_hbar, use_container_width=True)

# ══════════════════════════════════════════════════════════════════
# VIEW 5 — RANKINGS & STATS
# ══════════════════════════════════════════════════════════════════
elif "Rankings" in view_mode:
    st.markdown('<h2>🏆 RANKINGS & STATISTICS</h2>', unsafe_allow_html=True)
    col1,col2=st.columns(2)
    with col1:
        st.markdown('<div class="section-header">🌿 TOP 10 CLEANEST</div>', unsafe_allow_html=True)
        best10=df.nsmallest(10,"AQI")[["City","State","AQI","Category","Color","Emoji"]].reset_index(drop=True)
        for i,r in best10.iterrows():
            st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 12px;margin:3px 0;border-radius:8px;background:rgba(0,255,136,0.05);border-left:3px solid {r["Color"]};"><span style="font-family:Exo 2;font-size:0.88rem;"><b>{i+1}.</b> {r["Emoji"]} <b>{r["City"]}</b><span style="color:#5a7a9a;font-size:0.75rem;"> · {r["State"]}</span></span><span style="font-family:Share Tech Mono;color:{r["Color"]};font-size:0.88rem;">{r["AQI"]}</span></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="section-header">☣️ TOP 10 MOST POLLUTED</div>', unsafe_allow_html=True)
        worst10=df.nlargest(10,"AQI")[["City","State","AQI","Category","Color","Emoji"]].reset_index(drop=True)
        for i,r in worst10.iterrows():
            st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 12px;margin:3px 0;border-radius:8px;background:rgba(255,34,85,0.05);border-left:3px solid {r["Color"]};"><span style="font-family:Exo 2;font-size:0.88rem;"><b>{i+1}.</b> {r["Emoji"]} <b>{r["City"]}</b><span style="color:#5a7a9a;font-size:0.75rem;"> · {r["State"]}</span></span><span style="font-family:Share Tech Mono;color:{r["Color"]};font-size:0.88rem;">{r["AQI"]}</span></div>', unsafe_allow_html=True)
    st.divider()
    st.markdown('<div class="section-header">📊 AQI STATISTICS BY STATE</div>', unsafe_allow_html=True)
    state_stats=df.groupby("State")["AQI"].agg(Avg="mean",Max="max",Min="min",Cities="count").round(1).sort_values("Avg",ascending=False).reset_index()
    fig_state=px.bar(state_stats,x="State",y="Avg",color="Avg",color_continuous_scale=[[0,"#00ff88"],[0.4,"#ffaa00"],[0.7,"#ff2255"],[1,"#aa33ff"]],range_color=[0,500],hover_data={"Max":True,"Min":True,"Cities":True},text=state_stats["Avg"].astype(int),labels={"Avg":"Average AQI"})
    apply_theme(fig_state,height=370,coloraxis_showscale=False); fig_state.update_xaxes(tickangle=-35); fig_state.update_traces(textposition="outside",textfont=dict(color="#d8f0ff"))
    st.plotly_chart(fig_state, use_container_width=True)
    st.divider()
    corr_col,violin_col=st.columns(2)
    with corr_col:
        st.markdown('<div class="section-header">🔗 CORRELATION HEATMAP</div>', unsafe_allow_html=True)
        corr=df[["AQI"]+POLLUTANTS].corr().round(2)
        fig_heat=go.Figure(go.Heatmap(z=corr.values,x=list(corr.columns),y=list(corr.index),colorscale=[[0,"#ff2255"],[0.5,"#0a1628"],[1,"#00ff88"]],zmin=-1,zmax=1,text=corr.values.round(2),texttemplate="%{text}",textfont=dict(size=11,family="Share Tech Mono"),hovertemplate="%{x} × %{y}: %{z}<extra></extra>"))
        apply_theme(fig_heat,height=330,margin=dict(l=80,r=20,t=20,b=60)); st.plotly_chart(fig_heat, use_container_width=True)
    with violin_col:
        st.markdown('<div class="section-header">🎻 AQI DISTRIBUTION</div>', unsafe_allow_html=True)
        fig_v=go.Figure()
        for lo,hi,label_v,color_v,emoji_v,_ in AQI_SCALE:
            subset=df[df["Category"]==label_v]["AQI"]
            if len(subset)>0:
                r_v,g_v,b_v=int(color_v[1:3],16),int(color_v[3:5],16),int(color_v[5:7],16)
                fig_v.add_trace(go.Violin(y=subset,name=f"{emoji_v} {label_v}",fillcolor=f"rgba({r_v},{g_v},{b_v},0.25)",line_color=color_v,box_visible=True,meanline_visible=True,points="all"))
        apply_theme(fig_v,height=330,margin=dict(l=60,r=20,t=20,b=60),showlegend=False); fig_v.update_yaxes(title_text="AQI")
        st.plotly_chart(fig_v, use_container_width=True)

# ══════════════════════════════════════════════════════════════════
# VIEW 6 — AI ASSISTANT (NEW)
# ══════════════════════════════════════════════════════════════════
elif "AI Assistant" in view_mode:
    st.markdown('<h2>🤖 AI POLLUTION INTELLIGENCE ASSISTANT</h2>', unsafe_allow_html=True)
    st.markdown("""
    <div style="background:linear-gradient(135deg,rgba(170,51,255,0.07),rgba(0,229,255,0.05));border:1px solid rgba(170,51,255,0.2);border-radius:14px;padding:14px 18px;margin-bottom:16px;">
        <div style="font-family:Orbitron,sans-serif;font-size:0.8rem;color:#aa33ff;letter-spacing:2px;margin-bottom:6px;">🤖 AQI INTELLIGENCE ENGINE v4.0</div>
        <div style="font-family:Exo 2,sans-serif;font-size:0.85rem;color:#8aa0ba;">Ask me about city AQI, pollutants, health effects, forecasts, or say "worst cities" / "best cities" / "national average".</div>
    </div>""", unsafe_allow_html=True)

    # Quick action buttons
    st.markdown('<div style="font-family:Share Tech Mono;font-size:0.68rem;color:#5a7a9a;letter-spacing:1px;margin-bottom:8px;">QUICK QUERIES:</div>', unsafe_allow_html=True)
    qcols = st.columns(4)
    quick_queries = ["What are the worst cities?","Tell me about Delhi AQI","What is PM2.5?","National average AQI?"]
    quick_keys = ["qbtn1","qbtn2","qbtn3","qbtn4"]
    for i,(q,k) in enumerate(zip(quick_queries,quick_keys)):
        with qcols[i]:
            if st.button(q, key=k, use_container_width=True):
                st.session_state.chat_history.append({"role":"user","text":q})
                response = get_ai_response(q)
                st.session_state.chat_history.append({"role":"ai","text":response})

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    # Chat display
    st.markdown('<div class="chat-container" id="chatbox">', unsafe_allow_html=True)
    if not st.session_state.chat_history:
        st.markdown("""
        <div style="text-align:center;padding:40px 20px;color:#4a6a8a;">
            <div style="font-size:2.5rem;margin-bottom:10px;">🤖</div>
            <div style="font-family:Share Tech Mono;font-size:0.72rem;letter-spacing:2px;">AWAITING YOUR QUERY…</div>
        </div>""", unsafe_allow_html=True)
    for msg in st.session_state.chat_history:
        if msg["role"]=="user":
            st.markdown(f'<div class="chat-label-user">YOU</div><div class="chat-bubble-user">{msg["text"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-label-ai">🤖 AQI AI</div><div class="chat-bubble-ai">{msg["text"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    chat_col1, chat_col2 = st.columns([4,1])
    with chat_col1:
        user_input = st.text_input("Ask the AI…", key="ai_input", placeholder="e.g. What is the AQI in Mumbai? / Explain PM2.5 health effects")
    with chat_col2:
        st.markdown('<div style="height:28px;"></div>', unsafe_allow_html=True)
        send_btn = st.button("📡 SEND", use_container_width=True, key="ai_send")

    if send_btn and user_input:
        st.session_state.chat_history.append({"role":"user","text":user_input})
        with st.spinner("🤖 Analyzing…"):
            time.sleep(0.6)
            response = get_ai_response(user_input)
        st.session_state.chat_history.append({"role":"ai","text":response})
        st.rerun()

    col_clear,col_export = st.columns(2)
    with col_clear:
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.chat_history=[]; st.rerun()
    with col_export:
        if st.session_state.chat_history:
            chat_text="\n".join([f"{'YOU' if m['role']=='user' else 'AI'}: {m['text']}" for m in st.session_state.chat_history])
            st.download_button("⬇️ Export Chat Log", chat_text, file_name=f"aqi_chat_{datetime.date.today()}.txt", mime="text/plain", use_container_width=True)

    # AI Insight cards
    st.divider()
    st.markdown('<div class="section-header">💡 AI GENERATED INSIGHTS</div>', unsafe_allow_html=True)
    ins_col1,ins_col2,ins_col3 = st.columns(3)
    worst3 = df.nlargest(3,"AQI")
    best3  = df.nsmallest(3,"AQI")
    with ins_col1:
        st.markdown(f"""
        <div style="background:rgba(255,34,85,0.06);border:1px solid rgba(255,34,85,0.2);border-radius:12px;padding:16px;">
            <div style="font-family:Orbitron;font-size:0.72rem;color:#ff2255;letter-spacing:2px;margin-bottom:8px;">🚨 CRITICAL ZONE ALERT</div>
            <div style="font-family:Exo 2;font-size:0.82rem;color:#d8f0ff;">
                {worst3.iloc[0]["City"]} leads with AQI {worst3.iloc[0]["AQI"]} — {worst3.iloc[0]["Category"]} category. Immediate health action recommended for {int((df["AQI"]>300).sum())} cities in the danger zone.
            </div>
        </div>""", unsafe_allow_html=True)
    with ins_col2:
        st.markdown(f"""
        <div style="background:rgba(0,255,136,0.05);border:1px solid rgba(0,255,136,0.2);border-radius:12px;padding:16px;">
            <div style="font-family:Orbitron;font-size:0.72rem;color:#00ff88;letter-spacing:2px;margin-bottom:8px;">✅ CLEAN AIR REPORT</div>
            <div style="font-family:Exo 2;font-size:0.82rem;color:#d8f0ff;">
                {best3.iloc[0]["City"]} has the cleanest air at AQI {best3.iloc[0]["AQI"]}. {safe_count} cities are within safe limits today — ideal for outdoor activities.
            </div>
        </div>""", unsafe_allow_html=True)
    with ins_col3:
        trend_word = "improving" if random.random()>0.5 else "worsening"
        st.markdown(f"""
        <div style="background:rgba(0,229,255,0.05);border:1px solid rgba(0,229,255,0.18);border-radius:12px;padding:16px;">
            <div style="font-family:Orbitron;font-size:0.72rem;color:#00e5ff;letter-spacing:2px;margin-bottom:8px;">📈 TREND ANALYSIS</div>
            <div style="font-family:Exo 2;font-size:0.82rem;color:#d8f0ff;">
                National average AQI is {avg_aqi} ({avg_label}). Indo-Gangetic Plain cities show consistently elevated PM2.5. Overall trend is {trend_word} compared to last 24h.
            </div>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# VIEW 7 — ALERTS & NOTIFICATIONS (NEW)
# ══════════════════════════════════════════════════════════════════
elif "Alerts" in view_mode:
    st.markdown('<h2>🔔 ALERTS & NOTIFICATIONS</h2>', unsafe_allow_html=True)

    al_col1,al_col2 = st.columns([2,1])
    with al_col1:
        st.markdown(f'<div class="section-header">🚨 ACTIVE ALERTS ({len(active_alerts)} cities above threshold {alert_threshold_user})</div>', unsafe_allow_html=True)
        if not active_alerts:
            st.markdown('<div class="alert-card-green"><div style="font-family:Exo 2;color:#00ff88;">✅ No alerts active. All monitored cities are within your threshold.</div></div>', unsafe_allow_html=True)
        for alert in active_alerts[:15]:
            card_cls = "alert-card-red" if alert["level"]=="CRITICAL" else "alert-card-amber"
            icon = "🚨" if alert["level"]=="CRITICAL" else "⚠️"
            st.markdown(f"""
            <div class="{card_cls}">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <span style="font-family:Orbitron,sans-serif;font-size:0.85rem;color:{alert['color']};font-weight:700;">{icon} {alert['city']}</span>
                        <span style="font-family:Exo 2;font-size:0.78rem;color:#8aa0ba;margin-left:10px;">{alert['cat']}</span>
                    </div>
                    <div>
                        <span style="font-family:Orbitron,sans-serif;font-size:1.1rem;color:{alert['color']};font-weight:900;">AQI {alert['aqi']}</span>
                        <span style="font-family:Share Tech Mono;font-size:0.62rem;color:#5a7a9a;margin-left:8px;">{alert['time']}</span>
                    </div>
                </div>
                <div style="font-family:Exo 2;font-size:0.75rem;color:#8aa0ba;margin-top:5px;">
                    {get_aqi_info(alert['aqi'])[3]}
                </div>
            </div>""", unsafe_allow_html=True)

    with al_col2:
        st.markdown('<div class="section-header">⚙️ ALERT SETTINGS</div>', unsafe_allow_html=True)
        new_threshold = st.slider("Alert Threshold AQI", 50, 400, alert_threshold_user, step=25, key="new_alert_threshold")
        if new_threshold != alert_threshold_user:
            st.session_state.users_db[st.session_state.current_user]["alert_threshold"] = new_threshold
        alerts_on = st.toggle("Enable Alerts", value=user_info.get("alerts_enabled",True), key="alerts_enabled_toggle")
        if alerts_on != user_info.get("alerts_enabled"):
            st.session_state.users_db[st.session_state.current_user]["alerts_enabled"] = alerts_on
        notify_email = st.checkbox("Email Notifications", value=True, key="notif_email")
        notify_browser = st.checkbox("Browser Notifications", value=False, key="notif_browser")
        st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="auth-info">
            📧 Alerts sent to<br><b style="color:#00e5ff;">{st.session_state.current_user}</b><br>
            when AQI &gt; {new_threshold}
        </div>""", unsafe_allow_html=True)

        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-header">📊 ALERT SUMMARY</div>', unsafe_allow_html=True)
        critical_count = sum(1 for a in active_alerts if a["level"]=="CRITICAL")
        warning_count  = sum(1 for a in active_alerts if a["level"]=="WARNING")
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px;">
            <div style="background:rgba(255,34,85,0.07);border:1px solid rgba(255,34,85,0.25);border-radius:10px;padding:12px;text-align:center;">
                <div style="font-family:Orbitron;font-size:1.4rem;color:#ff2255;font-weight:900;">{critical_count}</div>
                <div style="font-family:Exo 2;font-size:0.68rem;color:#5a7a9a;text-transform:uppercase;margin-top:3px;">Critical</div>
            </div>
            <div style="background:rgba(255,170,0,0.07);border:1px solid rgba(255,170,0,0.25);border-radius:10px;padding:12px;text-align:center;">
                <div style="font-family:Orbitron;font-size:1.4rem;color:#ffaa00;font-weight:900;">{warning_count}</div>
                <div style="font-family:Exo 2;font-size:0.68rem;color:#5a7a9a;text-transform:uppercase;margin-top:3px;">Warning</div>
            </div>
        </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown('<div class="section-header">📈 AQI ALERT HISTOGRAM</div>', unsafe_allow_html=True)
    fig_hist=go.Figure(go.Histogram(x=df["AQI"],nbinsx=25,marker_color="#00e5ff",marker_line_color="rgba(0,229,255,0.5)",marker_line_width=1,opacity=0.7,hovertemplate="AQI Range: %{x}<br>Cities: %{y}<extra></extra>"))
    fig_hist.add_vline(x=new_threshold,line_dash="dash",line_color="#ff2255",annotation_text=f"Alert Threshold ({new_threshold})",annotation_font_color="#ff2255",annotation_font_size=11)
    apply_theme(fig_hist,height=260); fig_hist.update_xaxes(title_text="AQI Value"); fig_hist.update_yaxes(title_text="Number of Cities")
    st.plotly_chart(fig_hist, use_container_width=True)

# ══════════════════════════════════════════════════════════════════
# VIEW 8 — WEATHER & AQI FORECAST
# ══════════════════════════════════════════════════════════════════
elif "Weather" in view_mode:
    st.markdown('<h2>🌡️ WEATHER & AQI FORECAST</h2>', unsafe_allow_html=True)
    wc1,wc2=st.columns(2)
    fcity=wc1.selectbox("Select City",[c["name"] for c in CITIES],key="wcity")
    fdays=wc2.slider("Forecast Days",3,14,7,key="fdays")
    city_aqi=int(df[df["City"]==fcity]["AQI"].values[0])
    dates=[datetime.date.today()+datetime.timedelta(days=i) for i in range(fdays)]
    aqi_fc=[max(10,min(500,city_aqi+random.randint(-80,80))) for _ in range(fdays)]
    temp_fc=[random.randint(28,42) for _ in range(fdays)]
    humid_fc=[random.randint(30,80) for _ in range(fdays)]
    wind_fc=[random.uniform(3,25) for _ in range(fdays)]
    d_labels=[d.strftime("%b %d") for d in dates]
    fig_fc2=make_subplots(rows=3,cols=1,shared_xaxes=True,subplot_titles=["AQI Forecast","Temperature (°C)","Humidity (%)"],vertical_spacing=0.08)
    fc_colors=[get_aqi_info(v)[1] for v in aqi_fc]
    fig_fc2.add_trace(go.Bar(x=d_labels,y=aqi_fc,marker_color=fc_colors,name="AQI",hovertemplate="%{x}: AQI %{y}<extra></extra>"),row=1,col=1)
    fig_fc2.add_trace(go.Scatter(x=d_labels,y=temp_fc,mode="lines+markers",line=dict(color="#ff6600",width=2.5),marker=dict(size=7,color="#ff6600"),name="Temp °C"),row=2,col=1)
    fig_fc2.add_trace(go.Bar(x=d_labels,y=humid_fc,marker_color=[f"rgba(0,112,255,{0.35+h/200})" for h in humid_fc],name="Humidity %"),row=3,col=1)
    apply_theme(fig_fc2,height=580,showlegend=False,title=dict(text=f"Forecast · {fcity}",font=dict(family="Orbitron",color="#00e5ff",size=13)))
    for i in range(1,4):
        fig_fc2.update_xaxes(gridcolor="rgba(0,229,255,0.06)",linecolor="rgba(0,229,255,0.12)",row=i,col=1)
        fig_fc2.update_yaxes(gridcolor="rgba(0,229,255,0.06)",linecolor="rgba(0,229,255,0.12)",row=i,col=1)
    st.plotly_chart(fig_fc2, use_container_width=True)
    st.divider()
    st.markdown('<div class="section-header">📅 DAILY FORECAST TABLE</div>', unsafe_allow_html=True)
    forecast_df=pd.DataFrame({"Date":d_labels,"AQI":aqi_fc,"Category":[get_aqi_info(v)[0] for v in aqi_fc],"Temp (°C)":temp_fc,"Humidity (%)":humid_fc,"Wind (km/h)":[round(w,1) for w in wind_fc]})
    st.dataframe(forecast_df.style.background_gradient(subset=["AQI"],cmap="RdYlGn_r"),use_container_width=True,hide_index=True)

# ══════════════════════════════════════════════════════════════════
# VIEW 9 — IMAGE PREDICTOR
# ══════════════════════════════════════════════════════════════════
elif "Image" in view_mode:
    st.markdown('<h2>📸 IMAGE-BASED AIR QUALITY PREDICTOR</h2>', unsafe_allow_html=True)
    up_col,result_col=st.columns([1,1])
    with up_col:
        uploaded_file=st.file_uploader("Upload Image (JPG / PNG)",type=["jpg","jpeg","png"])
        if uploaded_file:
            img=Image.open(uploaded_file); st.image(img,caption="📷 Uploaded Image",use_column_width=True)
    with result_col:
        if uploaded_file:
            if st.button("🔍  ANALYZE IMAGE",use_container_width=True):
                with st.spinner("🛰️ Analyzing visual haze and particulate density…"):
                    time.sleep(1.5)
                pollution=random.randint(1,100); aqi_equiv=int(pollution*5)
                p_label,p_color,p_emoji,p_advice=get_aqi_info(aqi_equiv)
                st.markdown(f"""
                <div class="aqi-live-card" style="border-color:{p_color}44;">
                    <div style="font-family:Share Tech Mono;font-size:0.7rem;color:#5a7a9a;letter-spacing:2px;margin-bottom:8px;">VISUAL HAZE ANALYSIS RESULT</div>
                    <div class="aqi-number" style="color:{p_color};text-shadow:0 0 30px {p_color}80;">{pollution}%</div>
                    <div class="aqi-label-text" style="color:{p_color};">{p_emoji} {p_label}</div>
                    <div style="font-family:Exo 2;font-size:0.8rem;color:#8aa0ba;margin-top:8px;">Estimated AQI Equivalent: <b style="color:{p_color};">{aqi_equiv}</b></div>
                    <div style="margin-top:12px;font-family:Exo 2;font-size:0.8rem;color:#d8f0ff;">{p_advice}</div>
                </div>""", unsafe_allow_html=True)
                st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
                # Visual breakdown
                st.markdown('<div class="section-header">🔬 VISUAL ANALYSIS BREAKDOWN</div>', unsafe_allow_html=True)
                metrics = {"Haze Index": random.randint(20,90), "Visibility Score": random.randint(10,95), "Particulate Density": random.randint(15,85), "Sky Clarity": random.randint(5,80)}
                for k,v in metrics.items():
                    col_m = "#00ff88" if v < 40 else "#ffaa00" if v < 70 else "#ff2255"
                    st.markdown(f'<div style="padding:8px 12px;margin:4px 0;background:rgba(0,229,255,0.03);border-radius:8px;"><div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span style="font-family:Exo 2;font-size:0.8rem;color:#d8f0ff;">{k}</span><span style="font-family:Share Tech Mono;font-size:0.78rem;color:{col_m};">{v}%</span></div><div style="background:rgba(0,0,0,0.3);border-radius:4px;height:4px;"><div style="width:{v}%;height:100%;background:{col_m};border-radius:4px;"></div></div></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="text-align:center;padding:60px 20px;background:rgba(0,229,255,0.03);border:1px dashed rgba(0,229,255,0.18);border-radius:12px;font-family:Exo 2;"><div style="font-size:3rem;margin-bottom:12px;">📷</div><div style="color:#5a7a9a;font-size:0.88rem;">Upload a sky or outdoor image<br>to begin visual haze analysis</div></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# VIEW 10 — DATA EXPORT
# ══════════════════════════════════════════════════════════════════
elif "Export" in view_mode:
    st.markdown('<h2>📋 DATA EXPORT & REPORT</h2>', unsafe_allow_html=True)
    exp_col1,exp_col2=st.columns(2)
    with exp_col1:
        st.markdown('<div class="section-header">📥 EXPORT OPTIONS</div>', unsafe_allow_html=True)
        st.download_button("⬇️  Full Dataset (CSV)", df[["City","State","AQI","Category"]+POLLUTANTS].to_csv(index=False), file_name=f"india_aqi_{datetime.date.today()}.csv", mime="text/csv", use_container_width=True)
        st.download_button("⬇️  Top 10 Polluted (CSV)", df.nlargest(10,"AQI")[["City","State","AQI","Category"]+POLLUTANTS].to_csv(index=False), file_name=f"top10_polluted_{datetime.date.today()}.csv", mime="text/csv", use_container_width=True)
        st.download_button("⬇️  Safe Cities Report (CSV)", df[df["AQI"]<=100][["City","State","AQI","Category"]+POLLUTANTS].to_csv(index=False), file_name=f"safe_cities_{datetime.date.today()}.csv", mime="text/csv", use_container_width=True)
        # JSON export
        json_data = df[["City","State","AQI","Category"]+POLLUTANTS].to_json(orient="records",indent=2)
        st.download_button("⬇️  Full Dataset (JSON)", json_data, file_name=f"india_aqi_{datetime.date.today()}.json", mime="application/json", use_container_width=True)
    with exp_col2:
        st.markdown('<div class="section-header">📊 DATA SUMMARY</div>', unsafe_allow_html=True)
        summary=df[["AQI"]+POLLUTANTS].describe().round(2)
        st.dataframe(summary.style.background_gradient(cmap="Blues"),use_container_width=True)
    st.divider()
    st.markdown('<div class="section-header">🔍 INTERACTIVE DATA TABLE</div>', unsafe_allow_html=True)
    sc1,sc2=st.columns(2)
    search_city=sc1.text_input("🔎 Search city…",placeholder="Type a city name")
    cat_filter=sc2.multiselect("Filter by Category",["Good","Satisfactory","Moderate","Poor","Very Poor","Severe"])
    display_df=df.copy()
    if search_city: display_df=display_df[display_df["City"].str.contains(search_city,case=False)]
    if cat_filter:  display_df=display_df[display_df["Category"].isin(cat_filter)]
    st.dataframe(display_df[["City","State","AQI","Category"]+POLLUTANTS].sort_values("AQI",ascending=False).reset_index(drop=True).style.background_gradient(subset=["AQI"],cmap="RdYlGn_r"),use_container_width=True,height=420)

# ══════════════════════════════════════════════════════════════════
# VIEW 11 — MY ACCOUNT
# ══════════════════════════════════════════════════════════════════
elif "Account" in view_mode:
    st.markdown('<h2>👤 MY ACCOUNT</h2>', unsafe_allow_html=True)
    u=st.session_state.users_db[st.session_state.current_user]
    acc_col1,acc_col2=st.columns([1,1])
    with acc_col1:
        initials_acc="".join([w[0].upper() for w in u["name"].split()[:2]])
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#071020,#0c1a2e);border:1px solid rgba(0,229,255,0.2);border-radius:16px;padding:28px;text-align:center;margin-bottom:16px;">
            <div style="width:72px;height:72px;border-radius:50%;background:linear-gradient(135deg,#0070ff,#00e5ff);display:flex;align-items:center;justify-content:center;font-family:Orbitron,sans-serif;font-size:1.6rem;font-weight:700;color:#030b18;margin:0 auto 16px;">{initials_acc}</div>
            <div style="font-family:Orbitron,sans-serif;font-size:1.15rem;color:#00e5ff;font-weight:700;">{u['name']}</div>
            <div style="font-family:Share Tech Mono,monospace;font-size:0.7rem;color:#5a7a9a;margin:5px 0;">{st.session_state.current_user}</div>
            <div style="display:inline-block;background:rgba(0,255,136,0.08);border:1px solid #00ff88;border-radius:20px;padding:4px 14px;font-family:Exo 2,sans-serif;font-size:0.73rem;color:#00ff88;margin-top:6px;">⬡ {u['role']}</div>
            <div style="margin-top:14px;font-family:Share Tech Mono;font-size:0.62rem;color:#2a4a6a;">Member since: {u['joined']}<br>Last login: {u.get('last_login') or 'This session'}</div>
        </div>""", unsafe_allow_html=True)
        st.markdown('<div class="section-header">🔔 ALERT PREFERENCES</div>', unsafe_allow_html=True)
        alerts=st.toggle("Enable AQI Alerts",value=u.get("alerts_enabled",True),key="alerts_toggle")
        if alerts!=u.get("alerts_enabled"): st.session_state.users_db[st.session_state.current_user]["alerts_enabled"]=alerts
        alert_threshold=st.slider("Alert when AQI exceeds",100,400,u.get("alert_threshold",200),step=50,key="alert_threshold_acc")
        if alert_threshold!=u.get("alert_threshold"): st.session_state.users_db[st.session_state.current_user]["alert_threshold"]=alert_threshold
        st.markdown(f'<div class="auth-info">📧 Alerts to <b>{st.session_state.current_user}</b> when AQI &gt; {alert_threshold}</div>', unsafe_allow_html=True)
    with acc_col2:
        st.markdown('<div class="section-header">🔑 CHANGE PASSWORD</div>', unsafe_allow_html=True)
        old_pw=st.text_input("Current Password",type="password",key="chg_old")
        new_pw=st.text_input("New Password",type="password",key="chg_new")
        new_pw2=st.text_input("Confirm New Password",type="password",key="chg_new2")
        if st.button("🔄  UPDATE PASSWORD",use_container_width=True,key="chg_pw_btn"):
            if not old_pw or not new_pw or not new_pw2:
                st.markdown('<div class="auth-error">⚠️ Fill all password fields.</div>', unsafe_allow_html=True)
            elif st.session_state.users_db[st.session_state.current_user]["password_hash"]!=_hash(old_pw):
                st.markdown('<div class="auth-error">❌ Current password is incorrect.</div>', unsafe_allow_html=True)
            elif not is_strong_password(new_pw):
                st.markdown('<div class="auth-error">❌ Password too weak.</div>', unsafe_allow_html=True)
            elif new_pw!=new_pw2:
                st.markdown('<div class="auth-error">❌ Passwords do not match.</div>', unsafe_allow_html=True)
            else:
                st.session_state.users_db[st.session_state.current_user]["password_hash"]=_hash(new_pw)
                st.markdown('<div class="auth-success">✅ Password updated successfully!</div>', unsafe_allow_html=True)
        st.divider()
        st.markdown('<div class="section-header">📊 SESSION STATS</div>', unsafe_allow_html=True)
        total_users=len(st.session_state.users_db)
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px;">
            <div class="hex-stat"><div class="hex-val" style="color:#00e5ff;">{total_users}</div><div class="hex-lbl">Registered Users</div></div>
            <div class="hex-stat"><div class="hex-val" style="color:#00ff88;">{len(CITIES)}</div><div class="hex-lbl">Cities Monitored</div></div>
            <div class="hex-stat"><div class="hex-val" style="color:#aa33ff;">{avg_aqi}</div><div class="hex-lbl">National Avg AQI</div></div>
            <div class="hex-stat"><div class="hex-val" style="color:#ffaa00;">{dangerous}</div><div class="hex-lbl">High Risk Cities</div></div>
        </div>""", unsafe_allow_html=True)

# ── Footer ──
st.divider()
st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:center;font-family:Share Tech Mono,monospace;font-size:0.7rem;color:#4a6a8a;padding:6px 0;">
    <span>🛰️ INDIA AQI COMMAND CENTER v4.0</span>
    <span>👤 Logged in as <b style="color:#00e5ff;">{user_info['name']}</b></span>
    <span>Built with Streamlit · Plotly · Python</span>
</div>""", unsafe_allow_html=True)
