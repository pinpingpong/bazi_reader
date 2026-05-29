import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai

from bazi import (
    calculate_bazi,
    STEMS, STEMS_EN, STEMS_EL,
    BRANCHES, BR_EN, ANIMALS, BR_EL, BR_POL,
    stem_elem, branch_elem,
)

load_dotenv()

st.set_page_config(page_title="AI BaZi Reader 八字", page_icon="☯", layout="centered")

# ── Styling ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background: #f8f7f4; }
  [data-testid="stForm"] { background: transparent; border: none; padding: 0; }
  div[data-testid="stNumberInput"] input,
  div[data-testid="stSelectbox"] div { border-radius: 8px !important; }
  .stButton > button {
    border-radius: 8px; border: 0.5px solid #aaa;
    background: #fff; font-weight: 500;
  }
  .stButton > button:hover { background: #f0eeeb; }
  hr { margin: 1rem 0; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
ECOL = {
    "Wood":  {"bg": "#EAF3DE", "tx": "#3B6D11", "bar": "#639922"},
    "Fire":  {"bg": "#FAECE7", "tx": "#993C1D", "bar": "#D85A30"},
    "Earth": {"bg": "#FAEEDA", "tx": "#854F0B", "bar": "#BA7517"},
    "Metal": {"bg": "#F1EFE8", "tx": "#5F5E5A", "bar": "#888780"},
    "Water": {"bg": "#E6F1FB", "tx": "#185FA5", "bar": "#378ADD"},
}

DM_DESC = {
    "Yang Wood":  "A great tree — upright, ambitious, always reaching for the sky. Leadership comes naturally.",
    "Yin Wood":   "A flower or vine — graceful, adaptable, tenacious. Bends but never breaks.",
    "Yang Fire":  "The sun — radiant, generous, commanding. Lights up every room.",
    "Yin Fire":   "A candle flame — warm, nurturing, perceptive. Illuminates quietly.",
    "Yang Earth": "A mountain — stable, trustworthy, patient. The bedrock others rely on.",
    "Yin Earth":  "Fertile soil — nurturing, receptive, practical. Makes things grow.",
    "Yang Metal": "A sword — decisive, principled, strong-willed. Cuts through confusion.",
    "Yin Metal":  "A jewel — refined, precise, detail-oriented. Seeks perfection.",
    "Yang Water": "The ocean — vast, deep, philosophical. Absorbs everything, flows everywhere.",
    "Yin Water":  "Morning dew — gentle, intuitive, emotionally perceptive. Feels everything.",
}


# ── Helpers ───────────────────────────────────────────────────────────────────
def get_api_key() -> str:
    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        return os.getenv("GEMINI_API_KEY", "")


def pillar_card(label: str, si: int, bi: int, is_dm: bool = False) -> str:
    se = stem_elem(si)
    c = ECOL[se]
    border  = "2px solid #378ADD" if is_dm else "0.5px solid #ddd"
    lbg     = "#E6F1FB" if is_dm else "#f4f3f0"
    ltx     = "#185FA5" if is_dm else "#999"
    dm_tag  = " · Day Master" if is_dm else ""
    return f"""
    <div style="border:{border};border-radius:12px;overflow:hidden;
                text-align:center;background:#fff;flex:1;min-width:0">
      <div style="font-size:10px;color:{ltx};background:{lbg};
                  padding:5px 0;letter-spacing:.04em">{label}{dm_tag}</div>
      <div style="padding:14px 6px 8px">
        <div style="font-size:30px;line-height:1;margin-bottom:3px">{STEMS[si]}</div>
        <div style="font-size:11px;color:#888">{STEMS_EN[si]}</div>
        <div style="margin:4px 0 6px">
          <span style="display:inline-block;font-size:10px;font-weight:500;
                       padding:2px 8px;border-radius:12px;
                       background:{c['bg']};color:{c['tx']}">{STEMS_EL[si]}</span>
        </div>
      </div>
      <div style="border-top:0.5px solid #eee;padding:10px 6px 12px;background:#f8f7f4">
        <div style="font-size:24px;line-height:1;margin-bottom:4px">{BRANCHES[bi]}</div>
        <div style="font-size:12px;font-weight:500">{ANIMALS[bi]}</div>
        <div style="font-size:10px;color:#888;margin-top:2px">{BR_EL[bi]} · {BR_POL[bi]}</div>
      </div>
    </div>"""


def build_prompt(year, month, day, hour, minute, gender, chart, current_year=2026) -> str:
    ys, yb = chart["year"]
    ms, mb = chart["month"]
    ds, db = chart["day"]
    hs, hb = chart["hour"]
    ec = chart["elements"]
    dm_name = STEMS_EL[ds]

    return f"""You are an expert BaZi (Four Pillars of Destiny) consultant with deep knowledge of Chinese metaphysics. Analyse the chart below and provide a warm, insightful, and practical reading.

**Birth:** {year}-{month:02d}-{day:02d}  {hour:02d}:{minute:02d}  (UTC+8)  |  Gender: {gender}

**Four Pillars:**
| Pillar | Stem | Branch |
|--------|------|--------|
| Hour   | {STEMS_EN[hs]} {STEMS[hs]} — {STEMS_EL[hs]} | {BR_EN[hb]} {BRANCHES[hb]} — {BR_EL[hb]} {BR_POL[hb]} ({ANIMALS[hb]}) |
| Day ★  | {STEMS_EN[ds]} {STEMS[ds]} — {STEMS_EL[ds]} | {BR_EN[db]} {BRANCHES[db]} — {BR_EL[db]} {BR_POL[db]} ({ANIMALS[db]}) |
| Month  | {STEMS_EN[ms]} {STEMS[ms]} — {STEMS_EL[ms]} | {BR_EN[mb]} {BRANCHES[mb]} — {BR_EL[mb]} {BR_POL[mb]} ({ANIMALS[mb]}) |
| Year   | {STEMS_EN[ys]} {STEMS[ys]} — {STEMS_EL[ys]} | {BR_EN[yb]} {BRANCHES[yb]} — {BR_EL[yb]} {BR_POL[yb]} ({ANIMALS[yb]}) |

**Day Master:** {dm_name} ({STEMS[ds]}) — {DM_DESC.get(dm_name, '')}

**Element Balance (stems + branch main qi):**
Wood {ec['Wood']}  |  Fire {ec['Fire']}  |  Earth {ec['Earth']}  |  Metal {ec['Metal']}  |  Water {ec['Water']}

Please structure your response with these seven sections:

1. **Character & Personality** — based on the Day Master and chart balance
2. **Strengths & Natural Talents** — what this person excels at
3. **Challenges & Growth Areas** — elements or patterns to be mindful of
4. **Career & Life Path** — suitable directions and vocations
5. **Relationships & Love** — approach to partnerships and compatibility
6. **Health Tendencies** — areas to watch based on elemental imbalances
7. **{current_year} Forecast** — what energies are active this year and key themes

Use relatable modern language alongside Chinese metaphysical concepts. Be specific, warm, and actionable — avoid vague generalities.
"""


# ── UI ────────────────────────────────────────────────────────────────────────
st.markdown("<h1 style='font-size:22px;font-weight:600;margin-bottom:2px'>BaZi Reader 八字</h1>",
            unsafe_allow_html=True)
st.markdown("<p style='color:#888;font-size:13px;margin-bottom:1.2rem'>AI-powered Four Pillars of Destiny analysis</p>",
            unsafe_allow_html=True)

with st.form("bazi_form"):
    c1, c2, c3 = st.columns(3)
    year   = c1.number_input("Year",       min_value=1900, max_value=2100, value=2004)
    month  = c2.number_input("Month",      min_value=1,    max_value=12,   value=12)
    day    = c3.number_input("Day",        min_value=1,    max_value=31,   value=2)

    c4, c5, c6 = st.columns(3)
    hour   = c4.number_input("Hour (0–23)", min_value=0, max_value=23, value=9)
    minute = c5.number_input("Minute",      min_value=0, max_value=59, value=31)
    gender = c6.selectbox("Gender", ["Female", "Male"])

    st.caption("UTC+8 — Singapore / HK / China / Malaysia. No longitude correction applied.")
    submitted = st.form_submit_button("Calculate & Analyse →", use_container_width=True)

if not submitted:
    st.stop()

# ── Calculate ─────────────────────────────────────────────────────────────────
chart = calculate_bazi(int(year), int(month), int(day), int(hour), int(minute))
ys, yb = chart["year"]
ms, mb = chart["month"]
ds, db = chart["day"]
hs, hb = chart["hour"]
ec     = chart["elements"]
dm_name = STEMS_EL[ds]

st.markdown("---")
st.markdown("<div style='font-size:11px;color:#888;margin-bottom:8px'>Four Pillars — Hour · Day · Month · Year</div>",
            unsafe_allow_html=True)

# Pillar cards
st.markdown(
    f'<div style="display:flex;gap:10px;margin-bottom:1.2rem">'
    f'{pillar_card("Hour 时", hs, hb)}'
    f'{pillar_card("Day 日",  ds, db, is_dm=True)}'
    f'{pillar_card("Month 月", ms, mb)}'
    f'{pillar_card("Year 年",  ys, yb)}'
    f'</div>',
    unsafe_allow_html=True,
)

# Day master box
st.markdown(f"""
<div style="border:0.5px solid #ddd;border-radius:12px;padding:.9rem 1.1rem;
            margin-bottom:1rem;background:#fff">
  <div style="font-size:11px;color:#888;margin-bottom:5px">Day Master 日主</div>
  <div style="font-size:15px;font-weight:600">{STEMS[ds]}{BRANCHES[db]} · {dm_name}</div>
  <div style="font-size:12px;color:#666;margin-top:4px">{DM_DESC.get(dm_name, '')}</div>
</div>""", unsafe_allow_html=True)

# Element balance
max_e = max(ec.values()) or 1
elem_html = "".join(
    f'<div style="background:{ECOL[el]["bg"]};border-radius:8px;padding:8px 4px;text-align:center;flex:1">'
    f'<div style="font-size:10px;font-weight:500;color:{ECOL[el]["tx"]};margin-bottom:3px">{el}</div>'
    f'<div style="font-size:18px;font-weight:500;color:{ECOL[el]["bar"]}">{ec[el]}</div>'
    f'<div style="height:3px;border-radius:2px;background:#ddd;margin:5px 6px 0">'
    f'<div style="height:3px;border-radius:2px;background:{ECOL[el]["bar"]};'
    f'width:{round(ec[el]/max_e*100)}%"></div></div></div>'
    for el in ["Wood", "Fire", "Earth", "Metal", "Water"]
)
st.markdown(
    f'<div style="font-size:11px;color:#888;margin-bottom:6px">Element Balance (stems + branch main qi)</div>'
    f'<div style="display:flex;gap:8px;margin-bottom:1.5rem">{elem_html}</div>',
    unsafe_allow_html=True,
)

# ── AI Analysis ───────────────────────────────────────────────────────────────
st.markdown("### AI Analysis")

api_key = get_api_key()
if not api_key:
    st.warning(
        "No Gemini API key found. "
        "Add `GEMINI_API_KEY=...` to your `.env` file (local) "
        "or Streamlit secrets (cloud) to enable AI analysis."
    )
    st.stop()

genai.configure(api_key=api_key)
prompt = build_prompt(int(year), int(month), int(day), int(hour), int(minute), gender, chart)

with st.spinner("Consulting the stars..."):
    try:
        model = genai.GenerativeModel("gemini-flash-latest")
        response = model.generate_content(prompt)
        st.markdown(response.text)
    except Exception as e:
        st.error(f"Gemini API error: {e}")

st.markdown(
    "<div style='font-size:11px;color:#999;margin-top:1rem'>"
    "Formula: advanced fractional solar-term model (20th/21st century C-values)."
    "</div>",
    unsafe_allow_html=True,
)
